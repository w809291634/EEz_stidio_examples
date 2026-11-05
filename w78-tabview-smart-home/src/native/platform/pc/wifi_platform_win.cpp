/*
 * wifi_platform_win.cpp — PC 真接口后端：直接调 Windows wlanapi（不是模拟）。
 *
 * 扫描 = WlanScan + WlanGetAvailableNetworkList + WlanGetNetworkBssList；
 * 连接 = （必要时 WlanSetProfile 写 profile）+ WlanConnect；
 * 忘记 = WlanDeleteProfile（只删密码，不断已建立的连接，与假后端同口径）。
 *
 * 两个口径必须记住：
 * 1. 本文件是 PC 的**默认**后端——wifi_platform_pc.cpp 只有在看到
 *    WIFI_PC_FAKE=1 时才退回假世界；无头门禁与出图必须显式设它（P-0196）。
 * 2. mingw 的 wlanapi.h 把这些接口的字符串都声明成宽字符（LPCWSTR），
 *    所以 SSID/profile 名/profile XML 全部 UTF-16 ↔ UTF-8 转换，别按 ANSI 传。
 */
#ifndef WIFI_PLATFORM_DEVICE

#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>
#include <wchar.h>
#include <string.h>
#include <time.h>
#include <windows.h>
#include <wlanapi.h>
#include "app/wifi_model.h"
#include "app/wifi_text.h"
#include "platform/wifi_platform.h"
#include "wifi_platform_win.h"

/******************** 模块私有状态与常量 ********************/

#define WIN_AP_MAX        48
#define SCAN_WAIT_MS      2000     /* WlanScan 是异步的，2s 后再取表 */
#define CONNECT_POLL_MS    500     /* WlanConnect 也是异步的：每 0.5s 回查一次真值 */
#define CONNECT_GIVEUP_MS 10000    /* 10s 还没连上就判失败 */
#define PROF_NAME_CHARS   256

/* WLAN_AVAILABLE_NETWORK.dwFlags 的两个位，mingw 头里没给，值取自 MSDN */
#define AWN_CONNECTED     0x00000001
#define AWN_HAS_PROFILE   0x00000002

#define PROF_MAX          16

/* profile 名 ↔ 它的 SSID（名字可能带序号，如「YJT-1号楼办公 2」） */
typedef struct {
    WCHAR name[PROF_NAME_CHARS];
    char  ssid[33];
} prof_map_t;

typedef struct {
    wifi_ap_t ap;                       /* 对外快照（UI 只看到这一份） */
    WCHAR     profile[PROF_NAME_CHARS]; /* Windows 侧 profile 名，连接/删除用它 */
    UCHAR     raw[DOT11_SSID_MAX_LENGTH];
    ULONG     raw_len;
    int       has_profile;              /* 系统里是否已有它的 profile */
} win_ap_t;

static win_ap_t  s_aps[WIN_AP_MAX];
static int       s_cnt = 0, s_gen = 0;
static HANDLE    s_h = NULL;
static GUID      s_guid;
static int       s_scanning = 0, s_trying = 0;
static clock_t   s_t0 = 0, s_try_t0 = 0, s_try_next = 0;
static char      s_try_ssid[33];
static WCHAR     s_try_prof[PROF_NAME_CHARS];   /* 下发时用的 profile 名 */
static int       s_try_phase = 0;               /* 1=先扫一次 2=已下发 WlanConnect */
static UCHAR     s_try_raw[DOT11_SSID_MAX_LENGTH];   /* 目标 SSID 原始字节 */
static ULONG     s_try_raw_len = 0;
static WCHAR     s_try_profile[PROF_NAME_CHARS];     /* 目标 profile 名（认领通知的首选判据） */
static char      s_last_reason[APP_IN_STR_MAX];      /* 通知里拿到的失败原因（UTF-8） */
static volatile int s_notify_fail = 0;               /* 服务已明确判失败，主线程下一拍收 */

/******************** 小工具 ********************/

// 函数作用：拷宽字符串（不引额外的安全函数头）。 参数：src/dst/dst_chars。 返回值：无。
static void copy_w(const WCHAR *src, WCHAR *dst, int dst_chars)
{
    int i = 0;
    if (dst_chars <= 0) return;
    if (src) for (; i < dst_chars - 1 && src[i]; i++) dst[i] = src[i];
    dst[i] = L'\0';
}

// 函数作用：UTF-8 → UTF-16（wlanapi 的字符串参数都是宽字符）。
//          参数：u8：源；out/out_chars：目标。 返回值：成功 1，失败 0。
static int u8_to_w(const char *u8, WCHAR *out, int out_chars)
{
    if (!u8 || !out || out_chars <= 0) return 0;
    out[0] = L'\0';
    return MultiByteToWideChar(CP_UTF8, 0, u8, -1, out, out_chars) > 0;
}

// 函数作用：UTF-16 → UTF-8（LVGL 侧要 UTF-8）。 参数：w/out/out_sz。 返回值：out。
static char *w_to_u8(const WCHAR *w, char *out, int out_sz)
{
    if (out_sz > 0) out[0] = '\0';
    if (!w || !out || out_sz <= 0) return out;
    WideCharToMultiByte(CP_UTF8, 0, w, -1, out, out_sz, NULL, NULL);
    out[out_sz - 1] = '\0';
    return out;
}

// 函数作用：按 XML 规则抄写文本——SSID 与密码都可能含 & < " 等，不转义会写坏 profile。
//          参数：src：UTF-8 源；out/out_sz。 返回值：out。
static char *xml_esc(const char *src, char *out, int out_sz)
{
    int o = 0;
    const char *p = src ? src : "";
    for (; *p && o < out_sz - 8; p++) {
        const char *rep = NULL;
        switch (*p) {
        case '&':  rep = "&amp;";  break;
        case '<':  rep = "&lt;";   break;
        case '>':  rep = "&gt;";   break;
        case '"':  rep = "&quot;"; break;
        case '\'': rep = "&apos;"; break;
        default: break;
        }
        if (rep) { size_t l = strlen(rep); memcpy(out + o, rep, l); o += (int)l; }
        else     { out[o++] = *p; }
    }
    out[o] = '\0';
    return out;
}

// 函数作用：Windows 报的默认鉴权算法 → 界面文案。 参数：algo。 返回值：静态串。
//          注：WPA3-SAE 在这个 API 里仍报成 RSNA（Windows 自己也是这么显示的），
//          所以按 WPA2 显示；日志里带原始值，别把界面文案当成协议真值。
static const char *auth_str(DWORD algo)
{
    switch (algo) {
    case DOT11_AUTH_ALGO_80211_OPEN:  return "开放网络";
    case DOT11_AUTH_ALGO_WPA:
    case DOT11_AUTH_ALGO_WPA_PSK:     return "WPA";
    default:                          return "WPA2";
    }
}

static int cmp_ap(const void *a, const void *b)
{
    const wifi_ap_t *x = &((const win_ap_t *)a)->ap;
    const wifi_ap_t *y = &((const win_ap_t *)b)->ap;
    /* 分档：0 已连接 → 1 已保存（未连接）→ 2 其余 */
    {
        int tx = x->connected ? 0 : (x->saved ? 1 : 2);
        int ty = y->connected ? 0 : (y->saved ? 1 : 2);
        if (tx != ty) return tx - ty;
    }
    if (x->rssi != y->rssi) return y->rssi - x->rssi;
    return strcmp(x->ssid, y->ssid);
}

static void set_status(const char *fmt, const char *arg)
{
    char buf[APP_IN_STR_MAX];
    snprintf(buf, sizeof(buf), fmt, arg);
    app_set_input_s(APP_IN_SCAN_STATUS, buf);
}

// 函数作用：判断是否合法 UTF-8（不合法就用 ANSI 再转一次）。 参数：s。 返回值：1=合法。
static int utf8_valid(const char *s)
{
    const unsigned char *p = (const unsigned char *)s;
    while (*p) {
        int extra;
        if (*p < 0x80) extra = 0;
        else if ((*p & 0xE0) == 0xC0) extra = 1;
        else if ((*p & 0xF0) == 0xE0) extra = 2;
        else if ((*p & 0xF8) == 0xF0) extra = 3;
        else return 0;
        p++;
        for (int i = 0; i < extra; i++, p++)
            if ((*p & 0xC0) != 0x80) return 0;   /* 含 '\0' 也会在这里判失败 */
    }
    return 1;
}

// 函数作用：名字里有没有可见字符（全空白/全零就当没有名字）。 参数：s。 返回值：1=有可见字符。
static int has_visible(const char *s)
{
    for (; s && *s; s++)
        if ((unsigned char)*s > ' ') return 1;
    return 0;
}

// 函数作用：把 AP 广播的原始字节变成一个能显示的名字。
//          参数：raw/raw_len：原始字节；out/out_sz：目标。 返回值：out（可能为空串）。
//          很多路由器用 GBK 广播 SSID，直接当 UTF-8 画会整行空白，所以非法时按 ANSI 转一次。
static char *ssid_to_text(const UCHAR *raw, ULONG raw_len, char *out, int out_sz)
{
    WCHAR w[64];
    out[0] = '\0';
    if (!raw_len || raw_len >= (ULONG)out_sz) return out;
    memcpy(out, raw, raw_len);
    out[raw_len] = '\0';
    if (utf8_valid(out)) return out;
    if (MultiByteToWideChar(CP_ACP, 0, out, (int)raw_len, w, 64) > 0)
        w_to_u8(w, out, out_sz);
    return out;
}

// 函数作用：按 UTF-8 字符边界截断（snprintf 截断可能切坏半个汉字）。 参数：s/n。 返回值：无。
static void utf8_cut(char *s, int n)
{
    int i = (int)strlen(s);
    if (n <= 0) { if (s) s[0] = '\0'; return; }
    if (i < n) return;
    i = n - 1;
    while (i > 0 && ((unsigned char)s[i] & 0xC0) == 0x80) i--;
    s[i] = '\0';
}

// 函数作用：去掉系统文案末尾的标点/空白（"特定的网络不可用。"→"特定的网络不可用"）。
//          参数：s。 返回值：无（原地改）。
static void strip_tail(char *s)
{
    int n = (int)strlen(s);
    while (n > 0 && (s[n - 1] == ' ' || s[n - 1] == '.' ||
                     s[n - 1] == '\n' || s[n - 1] == '\r'))
        s[--n] = '\0';
    if (n >= 3 && (unsigned char)s[n - 3] == 0xE3 &&
        (unsigned char)s[n - 2] == 0x80 && (unsigned char)s[n - 1] == 0x82)   /* 。 */
        s[n - 3] = '\0';
}

// 函数作用：收 WLAN 通知——把"连接失败/断开"的原因码翻成系统文案存下来。
//          参数：d：通知数据；ctx：未用。 返回值：无。
//          只在后台线程写两个静态量，真正的状态迁移留给 win_io_sample()。
static void CALLBACK on_wlan_notify(PWLAN_NOTIFICATION_DATA d, PVOID ctx)
{
    const WLAN_CONNECTION_NOTIFICATION_DATA *cd;
    WCHAR buf[256];

    (void)ctx;
    if (!d) return;
    if (getenv("WIFI_WIN_DUMP"))            /* 排查：先看"到底收到什么"，再谈过滤 */
        printf("[WIN] notify src=%lu code=%lu size=%lu\n",
               (unsigned long)d->NotificationSource,
               (unsigned long)d->NotificationCode,
               (unsigned long)d->dwDataSize);
    if (d->NotificationSource != WLAN_NOTIFICATION_SOURCE_ACM) return;
    if (d->NotificationCode != wlan_notification_acm_connection_complete &&
        d->NotificationCode != wlan_notification_acm_connection_attempt_fail &&
        d->NotificationCode != wlan_notification_acm_disconnected) return;
    /* ★ 不能用 sizeof(WLAN_CONNECTION_NOTIFICATION_DATA)：它尾部带着
     *   strProfileXml[1] 的变长尾巴，sizeof 比实际 payload（实测 572 字节）大，
     *   于是所有通知都会被当成"太短"丢掉（本行最初就是这么写错的）。
     *   固定字段的终点是 strProfileXml 的偏移。 */
    if (!d->pData ||
        d->dwDataSize < (DWORD)offsetof(WLAN_CONNECTION_NOTIFICATION_DATA, strProfileXml))
        return;

    cd = (const WLAN_CONNECTION_NOTIFICATION_DATA *)d->pData;
    if (getenv("WIFI_WIN_DUMP"))
        printf("[WIN] notify cd: trying=%d ssidlen=%lu reason=%lu prof=%S\n",
               s_trying, (unsigned long)cd->dot11Ssid.uSSIDLength,
               (unsigned long)cd->wlanReasonCode, cd->strProfileName);
    /* 认领判据用 **profile 名**：通知里的 dot11Ssid 是按 ANSI 编码给的（实测中文 SSID
     * 17 字节 UTF-8 → 通知里只有 13 字节），拿空口原始字节比永远不相等。 */
    if (!s_trying) return;
    if (cd->strProfileName[0] && s_try_profile[0]) {
        if (wcscmp(cd->strProfileName, s_try_profile)) return;
    } else if (cd->dot11Ssid.uSSIDLength != s_try_raw_len ||
               memcmp(cd->dot11Ssid.ucSSID, s_try_raw, s_try_raw_len)) {
        return;
    }

    if (!cd->wlanReasonCode) { s_last_reason[0] = '\0'; return; }
    buf[0] = L'\0';
    if (WlanReasonCodeToString(cd->wlanReasonCode, 256, buf, NULL) == ERROR_SUCCESS &&
        buf[0])
        w_to_u8(buf, s_last_reason, (int)sizeof(s_last_reason));
    else   /* 厂商私有原因码翻不出文案，至少把码留住 */
        snprintf(s_last_reason, sizeof(s_last_reason), "错误码 %lu",
                 (unsigned long)cd->wlanReasonCode);
    strip_tail(s_last_reason);                /* 系统文案自带句号，括号里很丑 */
    s_notify_fail = 1;
    printf("[WIN] notify code=%lu reason=%lu \"%s\"\n",
           (unsigned long)d->NotificationCode, (unsigned long)cd->wlanReasonCode,
           s_last_reason);
}

// 函数作用：把一次连接判失败——文案与 CONN_STATE 必须一起改，否则转圈永远不收。
//          参数：ssid。 返回值：无。
//          有系统给的原因就带上（「连接失败 X（特定的网络不可用）」），用户不必再猜。
static void try_fail(const char *ssid)
{
    char buf[APP_IN_STR_MAX];
    app_set_input_i(APP_IN_CONN_STATE, 3);
    if (s_last_reason[0])
        snprintf(buf, sizeof(buf), "连接失败 %s（%s）",
                 ssid ? ssid : "", s_last_reason);
    else
        snprintf(buf, sizeof(buf), WIFI_TXT_CONNECT_FAIL, ssid ? ssid : "");
    utf8_cut(buf, (int)sizeof(buf));
    app_set_input_s(APP_IN_SCAN_STATUS, buf);
}

static win_ap_t *find_by_ssid(const char *ssid)
{
    if (!ssid) return NULL;
    for (int i = 0; i < s_cnt; i++)
        if (!strcmp(s_aps[i].ap.ssid, ssid)) return &s_aps[i];
    return NULL;
}

// 函数作用：从 profile XML 里抠出 <SSID><name>…</name>（宽字符），转成 UTF-8。
//          参数：xml：宽字符 XML；out/out_sz。 返回值：无。
//          ★ profile 名不一定等于 SSID：重名时 Windows 会存成「SSID 2」，
//            所以配对必须看 XML 里的 SSID，不能用名字猜。
static void ssid_from_xml(const WCHAR *xml, char *out, int out_sz)
{
    const WCHAR *a, *b, *e;
    WCHAR tmp[64];
    int n;

    out[0] = '\0';
    if (!xml) return;
    a = wcsstr(xml, L"<SSID>");
    if (!a) return;
    b = wcsstr(a, L"<name>");
    if (!b) return;
    b += 6;
    e = wcsstr(b, L"</name>");
    if (!e) return;
    n = (int)(e - b);
    if (n > 63) n = 63;
    memcpy(tmp, b, (size_t)n * sizeof(WCHAR));
    tmp[n] = L'\0';
    w_to_u8(tmp, out, out_sz);
}

// 函数作用：把系统 profile 库读成「profile 名 ↔ 它的 SSID」对照表。
//          参数：out/out_max。 返回值：条数。
static int load_profiles(prof_map_t *out, int out_max)
{
    PWLAN_PROFILE_INFO_LIST pl = NULL;
    int n = 0;

    if (!s_h) return 0;
    {
        DWORD rr = WlanGetProfileList(s_h, &s_guid, NULL, &pl);
        if (rr != ERROR_SUCCESS || !pl) {
            printf("[WIN] WlanGetProfileList 失败 rr=%lu\n", (unsigned long)rr);
            return 0;
        }
    }
    for (DWORD i = 0; i < pl->dwNumberOfItems && n < out_max; i++) {
        LPWSTR xml = NULL;
        DWORD flags = 0, rr;
        copy_w(pl->ProfileInfo[i].strProfileName, out[n].name, PROF_NAME_CHARS);
        out[n].ssid[0] = '\0';
        rr = WlanGetProfile(s_h, &s_guid, out[n].name, NULL, &xml, &flags, NULL);
        if (rr == ERROR_SUCCESS && xml) {
            ssid_from_xml(xml, out[n].ssid, (int)sizeof(out[n].ssid));
            if (getenv("WIFI_WIN_DUMP")) {       /* 看 <SSID> 附近到底长什么样 */
                char head[400];
                WCHAR cut[140];
                const WCHAR *at = wcsstr(xml, L"SSID");
                memcpy(cut, at ? at : xml, 139 * sizeof(WCHAR));
                cut[139] = L'\0';
                w_to_u8(cut, head, (int)sizeof(head));
                printf("[WIN]   xml@SSID: %s\n", head);
            }
            WlanFreeMemory(xml);
        }
        if (!out[n].ssid[0])                     /* 读不到 XML 就退回用名字 */
            w_to_u8(out[n].name, out[n].ssid, (int)sizeof(out[n].ssid));
        if (getenv("WIFI_WIN_DUMP")) {           /* %S 在窄 printf 里遇中文会截断，先转 UTF-8 */
            char nm[160];
            w_to_u8(out[n].name, nm, (int)sizeof(nm));
            printf("[WIN] profile \"%s\" -> ssid \"%s\" (getprofile rr=%lu)\n",
                   nm, out[n].ssid, (unsigned long)rr);
        }
        if (out[n].ssid[0]) n++;
    }
    WlanFreeMemory(pl);
    return n;
}

// 函数作用：按 SSID 在这张表里找 profile。 参数：map/n/ssid。 返回值：命中项或 NULL。
static prof_map_t *find_profile(prof_map_t *map, int n, const char *ssid)
{
    for (int i = 0; i < n; i++)
        if (!strcmp(map[i].ssid, ssid)) return &map[i];
    return NULL;
}


/******************** 查询：把系统真表搬进快照 ********************/

// 函数作用：把 AP 的 RSN IE 解出来（组播套件 / 单播套件 / AKM / RSN 能力位）。
//          参数：ie/len：IE 字节区；tag：前缀。 返回值：无。
//          用途：排查"看得见却连不上"——要能看出 AP 到底支不支持 AES-GCMP、要不要 PMF。
static void dump_rsn(const UCHAR *ie, ULONG len, const char *tag)
{
    for (ULONG k = 0; k + 2 <= len; k += 2 + ie[k + 1]) {
        const UCHAR *p = ie + k + 2;
        ULONG n = ie[k + 1];
        if (ie[k] != 48 || n < 8) continue;          /* 48 = RSN */
        printf("[WIN] %s RSN ver=%u group=%02x%02x%02x%02x",
               tag, (unsigned)(p[0] | (p[1] << 8)),
               p[2], p[3], p[4], p[5]);
        ULONG cnt = (ULONG)(p[6] | (p[7] << 8)), off = 8;
        for (ULONG i = 0; i < cnt && off + 4 <= n; i++, off += 4)
            printf(" pairwise=%02x%02x%02x%02x", p[off], p[off + 1], p[off + 2], p[off + 3]);
        if (off + 2 <= n) {
            ULONG akm = (ULONG)(p[off] | (p[off + 1] << 8));
            off += 2;
            for (ULONG i = 0; i < akm && off + 4 <= n; i++, off += 4)
                printf(" akm=%02x%02x%02x%02x", p[off], p[off + 1], p[off + 2], p[off + 3]);
        }
        if (off + 2 <= n)                      /* RSN capabilities：bit7=MFPR bit6=MFPC */
            printf(" caps=%02x%02x", p[off], p[off + 1]);
        printf("\n");
        return;
    }
}

// 函数作用：查一次真接口（可用网络 + BSS 信号），排序后刷新快照与代数。
//          参数：无。 返回值：1=成功，0=调用失败（快照保持原样）。
static int query(void)
{
    PWLAN_AVAILABLE_NETWORK_LIST p_net = NULL;
    PWLAN_BSS_LIST p_bss = NULL;
    prof_map_t map[PROF_MAX];
    int n = 0, map_n;


    if (!s_h) return 0;
    if (WlanGetAvailableNetworkList(s_h, &s_guid, 0, NULL, &p_net) != ERROR_SUCCESS) {
        printf("[WIN] 取可用网络列表失败\n");
        return 0;
    }
    /* profile 库是"已保存"的唯一真值；连名字一起读，因为名字可能≠SSID */
    map_n = load_profiles(map, PROF_MAX);
    /* BSS 表只用来拿 dBm 与频点；拿不到也要能出列表，所以不判返回值 */
    if (WlanGetNetworkBssList(s_h, &s_guid, NULL, dot11_BSS_type_any, FALSE,
                              NULL, &p_bss) != ERROR_SUCCESS)
        p_bss = NULL;

    for (DWORD i = 0; i < p_net->dwNumberOfItems && n < WIN_AP_MAX; i++) {
        const WLAN_AVAILABLE_NETWORK *an = &p_net->Network[i];
        if (!an->bNetworkConnectable) continue;
        if (an->dot11BssType != dot11_BSS_type_infrastructure) continue;
        if (an->dot11Ssid.uSSIDLength == 0 ||
            an->dot11Ssid.uSSIDLength > DOT11_SSID_MAX_LENGTH) continue;

        memset(&s_aps[n], 0, sizeof(s_aps[n]));
        s_aps[n].raw_len = an->dot11Ssid.uSSIDLength;
        memcpy(s_aps[n].raw, an->dot11Ssid.ucSSID, s_aps[n].raw_len);

        /* 名字优先用 Windows 已解码的 profile 名：中文 SSID 靠它才不会花屏。
         * 没存过密码的网络没有 profile 名，就按 AP 原样广播的字节当 UTF-8 用。 */
        if (an->strProfileName[0])
            w_to_u8(an->strProfileName, s_aps[n].ap.ssid,
                    (int)sizeof(s_aps[n].ap.ssid));
        else
            ssid_to_text(s_aps[n].raw, s_aps[n].raw_len,
                         s_aps[n].ap.ssid, (int)sizeof(s_aps[n].ap.ssid));
        /* 没有可见字符的名字（隐藏网络的全零/纯空白 SSID、GBK 乱码）会画成一行空行——不列 */
        if (!has_visible(s_aps[n].ap.ssid)) continue;
        if (an->strProfileName[0])
            copy_w(an->strProfileName, s_aps[n].profile, PROF_NAME_CHARS);
        else
            u8_to_w(s_aps[n].ap.ssid, s_aps[n].profile, PROF_NAME_CHARS);

        /* 同一个 SSID 可能有多个 BSS：取信号最强那条的 dBm 与中心频点 */
        int best = -999;
        unsigned long freq = 0;
        const WLAN_BSS_ENTRY *best_be = NULL;
        for (DWORD j = 0; p_bss && j < p_bss->dwNumberOfItems; j++) {
            const WLAN_BSS_ENTRY *be = &p_bss->wlanBssEntries[j];
            if (be->dot11Ssid.uSSIDLength != s_aps[n].raw_len) continue;
            if (memcmp(be->dot11Ssid.ucSSID, s_aps[n].raw, s_aps[n].raw_len)) continue;
            if (be->lRssi > best) {
                best = (int)be->lRssi;
                freq = be->ulChCenterFrequency;
                best_be = be;
            }
        }
        /* WIFI_WIN_DUMP=1：把最强那条 BSS 的 RSN IE 打出来（加密套件/PMF 要求） */
        /* ★ ulIeOffset 是相对**这条 BSS 条目**的偏移（不是列表起点），
         *   按 p_bss 加会读到别处（诊断一直没输出就是因为这个）。 */
        if (best_be && getenv("WIFI_WIN_DUMP") && best_be->ulIeSize >= 2)
            dump_rsn((const UCHAR *)best_be + best_be->ulIeOffset,
                     best_be->ulIeSize, s_aps[n].ap.ssid);
        s_aps[n].ap.rssi = best > -999 ? best
                                       : (int)an->wlanSignalQuality / 2 - 100;
        /* ulChCenterFrequency 单位 kHz */
        strncpy(s_aps[n].ap.band, freq >= 5900000 ? "6 GHz"
                        : freq >= 4900000 ? "5 GHz" : "2.4 GHz",
                sizeof(s_aps[n].ap.band) - 1);
        s_aps[n].ap.lock = an->bSecurityEnabled != FALSE;
        /* "已保存"以 **profile 库** 为准：可用网络条目的 HAS_PROFILE 位在真机上会漏报
         * （实测 profile 明明在，整表却一条 saved 都没有）。照它显示，已保存的网络
         * 会被当成"没存过密码"弹半页，用户输错一次就把好 profile 覆盖掉。 */
        {
            prof_map_t *pm = find_profile(map, map_n, s_aps[n].ap.ssid);
            s_aps[n].has_profile = pm != NULL ||
                                   (an->dwFlags & AWN_HAS_PROFILE) ||
                                   an->strProfileName[0] != 0;
            if (getenv("WIFI_WIN_DUMP"))
                printf("[WIN]   cmp ssid=\"%s\" len=%d map_n=%d hit=%d\n",
                       s_aps[n].ap.ssid, (int)strlen(s_aps[n].ap.ssid), map_n,
                       pm != NULL);
            s_aps[n].ap.saved = pm != NULL;
            if (!s_aps[n].ap.saved)
                s_aps[n].ap.saved = (an->dwFlags & AWN_HAS_PROFILE) ||
                                    an->strProfileName[0];
            /* ★ 连接/忘记要用 **真实 profile 名**：Windows 重名时会存成「SSID 2」，
             *   拿 SSID 去 WlanConnect 会变成"网络不可用"（本轮真机就踩在这）。 */
            if (pm) copy_w(pm->name, s_aps[n].profile, PROF_NAME_CHARS);
            else if (an->strProfileName[0])
                copy_w(an->strProfileName, s_aps[n].profile, PROF_NAME_CHARS);
            else
                u8_to_w(s_aps[n].ap.ssid, s_aps[n].profile, PROF_NAME_CHARS);
        }
        s_aps[n].ap.connected = (an->dwFlags & AWN_CONNECTED) != 0;
        strncpy(s_aps[n].ap.auth, auth_str(an->dot11DefaultAuthAlgorithm),
                sizeof(s_aps[n].ap.auth) - 1);

        /* 同一个 SSID 还是可能来两条（隐藏网、多 profile）：并成一行，
         * 信号取强的、状态位取或、profile 名保留先拿到的——否则列表里出现两行同名，
         * 点哪条都不知在连哪个。 */
        {
            int k, merged = 0;
            for (k = 0; k < n; k++) {
                if (s_aps[k].raw_len != s_aps[n].raw_len ||
                    memcmp(s_aps[k].raw, s_aps[n].raw, s_aps[n].raw_len)) continue;
                if (s_aps[n].ap.rssi > s_aps[k].ap.rssi) {
                    s_aps[k].ap.rssi = s_aps[n].ap.rssi;
                    strncpy(s_aps[k].ap.band, s_aps[n].ap.band,
                            sizeof(s_aps[k].ap.band) - 1);
                }
                s_aps[k].ap.connected = s_aps[k].ap.connected || s_aps[n].ap.connected;
                s_aps[k].ap.saved     = s_aps[k].ap.saved     || s_aps[n].ap.saved;
                s_aps[k].ap.lock      = s_aps[k].ap.lock      || s_aps[n].ap.lock;
                merged = 1;
                break;
            }
            if (merged) continue;
        }
        n++;
    }

    WlanFreeMemory(p_net);
    if (p_bss) WlanFreeMemory(p_bss);

    s_cnt = n;
    qsort(s_aps, (size_t)n, sizeof(s_aps[0]), cmp_ap);
    s_gen++;
    printf("[WIN] query: %d 个网络（gen=%d）\n", s_cnt, s_gen);
    /* 排查用：WIFI_WIN_DUMP=1 把每一行连 profile 名一起打出来 */
    if (getenv("WIFI_WIN_DUMP")) {
        for (int i = 0; i < s_cnt; i++) {
            char hex[3 * DOT11_SSID_MAX_LENGTH + 1];
            int o = 0;
            for (ULONG b = 0; b < s_aps[i].raw_len && o < (int)sizeof(hex) - 3; b++)
                o += snprintf(hex + o, sizeof(hex) - o, "%02x", s_aps[i].raw[b]);
            hex[o] = '\0';
            printf("[WIN] #%d \"%s\" %d dBm %s auth=%s lock=%d saved=%d conn=%d "
                   "rawlen=%lu raw=%s\n",
                   i, s_aps[i].ap.ssid, s_aps[i].ap.rssi, s_aps[i].ap.band,
                   s_aps[i].ap.auth, (int)s_aps[i].ap.lock,
                   (int)s_aps[i].ap.saved, (int)s_aps[i].ap.connected,
                   (unsigned long)s_aps[i].raw_len, hex);
        }
    }
    return 1;
}

// 函数作用：出「已发现 N 个网络」/空态文案。 参数：无。 返回值：无。
static void publish_found(void)
{
    char buf[APP_IN_STR_MAX];
    snprintf(buf, sizeof(buf), WIFI_TXT_FOUND, s_cnt);
    app_set_input_s(APP_IN_SCAN_STATUS,
                    s_cnt > 0 ? buf : WIFI_TXT_EMPTY);
}

/******************** 对外初始化与公开接口 ********************/

// 函数作用：打开 wlanapi 句柄并挑一个无线接口。 参数：无。 返回值：1=可用，0=不可用。
int win_io_open(void)
{
    DWORD ver = 0, n = 0;
    PWLAN_INTERFACE_INFO_LIST li = NULL;

    if (WlanOpenHandle(1, NULL, &ver, &s_h) != ERROR_SUCCESS) {
        printf("[WIN] WlanOpenHandle 失败（wlansvc 没起？）\n");
        s_h = NULL;
        return 0;
    }
    if (WlanEnumInterfaces(s_h, NULL, &li) != ERROR_SUCCESS || !li) {
        printf("[WIN] 枚举无线接口失败\n");
        WlanCloseHandle(s_h, NULL); s_h = NULL;
        return 0;
    }
    n = li->dwNumberOfItems;
    s_guid = li->InterfaceInfo[0].InterfaceGuid;
    for (DWORD i = 0; i < n; i++)                 /* 优先挑就绪的那个 */
        if (li->InterfaceInfo[i].isState != wlan_interface_state_not_ready) {
            s_guid = li->InterfaceInfo[i].InterfaceGuid;
            break;
        }
    printf("[WIN] 用接口 %S（%u 个接口）\n",
           li->InterfaceInfo[0].strInterfaceDescription, (unsigned)n);
    WlanFreeMemory(li);

    /* 订阅 ACM 通知：只有它能给出"为什么连不上"的系统文案（WlanReasonCodeToString）；
     * 取不到就算了——失败时退化成只写「连接失败 X」。 */
    if (WlanRegisterNotification(s_h, WLAN_NOTIFICATION_SOURCE_ACM, TRUE,
                                 on_wlan_notify, NULL, NULL, NULL) != ERROR_SUCCESS)
        printf("[WIN] 注册 WLAN 通知失败（失败原因将不可见）\n");
    return 1;
}

// 函数作用：关掉句柄。 参数：无。 返回值：无。
void win_io_close(void)
{
    if (s_h) { WlanCloseHandle(s_h, NULL); s_h = NULL; }
}

// 函数作用：发起真扫描并置扫描态。 参数：无。 返回值：无。
void win_io_scan(void)
{
    if (!s_h) return;
    if (WlanScan(s_h, &s_guid, NULL, NULL, NULL) != ERROR_SUCCESS)
        printf("[WIN] WlanScan 被拒（仍读缓存表）\n");
    s_scanning = 1;
    s_t0 = clock();
    app_set_input_i(APP_IN_SCAN_STATE, 1);
    app_set_input_s(APP_IN_SCAN_STATUS, WIFI_TXT_SCANNING);
}

// 函数作用：按已备好的 profile 名下发 WlanConnect。 参数：无。 返回值：无。
//          单独抽出来是因为现在要"先扫一次再下发"（见 s_try_phase）。
static void do_connect(void)
{
    WLAN_CONNECTION_PARAMETERS cp;
    DWORD rr;

    memset(&cp, 0, sizeof(cp));
    cp.wlanConnectionMode = wlan_connection_mode_profile;
    cp.strProfile = s_try_prof;
    cp.dot11BssType = dot11_BSS_type_infrastructure;
    rr = WlanConnect(s_h, &s_guid, &cp, NULL);
    if (rr != ERROR_SUCCESS) {
        printf("[WIN] WlanConnect 失败 rr=%lu\n", rr);
        s_trying = 0;
        try_fail(s_try_ssid);
        return;
    }
    printf("[WIN] WlanConnect 已下发：%s\n", s_try_ssid);
}

// 函数作用：推进扫描/连接计时，到点就重新查询并回写文案。 参数：无。 返回值：无。
void win_io_sample(void)
{
    double el = 0;

    if (s_scanning) {
        el = (double)(clock() - s_t0) * 1000.0 / CLOCKS_PER_SEC;
        if (el >= SCAN_WAIT_MS) {
            s_scanning = 0;
            if (query()) publish_found();
            app_set_input_i(APP_IN_SCAN_STATE, 2);
        }
    }
    if (s_trying) {
        double since = (double)(clock() - s_try_t0) * 1000.0 / CLOCKS_PER_SEC;
        /* 服务已经给出结论（通常是 2 秒内"网络不可用"）：立刻收圈报错，不干等 10 秒 */
        if (s_notify_fail) {
            s_notify_fail = 0;
            s_trying = 0;
            query();                              /* 顺手把列表状态摆正 */
            try_fail(s_try_ssid);
            return;
        }
        if ((double)(clock() - s_try_next) * 1000.0 / CLOCKS_PER_SEC >= 0) {
            const win_ap_t *t;
            s_try_next = clock() + (clock_t)(CONNECT_POLL_MS * CLOCKS_PER_SEC / 1000);
            query();                             /* 每秒回查一次，连上就立刻报成功 */
            t = find_by_ssid(s_try_ssid);
            if (t && t->ap.connected) {
                s_trying = 0;
                app_set_input_i(APP_IN_CONN_STATE, 2);
                set_status(WIFI_TXT_CONNECTED, s_try_ssid);
            } else if (since >= CONNECT_GIVEUP_MS) {
                s_trying = 0;
                try_fail(s_try_ssid);
            }
        }
    }
}

// 函数作用：真连接——需要时先写 profile（带密码），扫一次，再下发 WlanConnect。
//          参数：ssid：目标；password：可为空（用已存的 profile）。 返回值：无。
void win_io_connect(const char *ssid, const char *password)
{
    win_ap_t *t = find_by_ssid(ssid);
    WCHAR prof[PROF_NAME_CHARS];
    DWORD rr;

    if (!s_h) return;
    if (!t) { try_fail(ssid); return; }

    /* profile 名已经是宽字符，直接抄；万一为空就用 SSID 现推 */
    copy_w(t->profile, prof, PROF_NAME_CHARS);
    if (!prof[0] && !u8_to_w(t->ap.ssid, prof, PROF_NAME_CHARS)) {
        try_fail(t->ap.ssid);            /* 别留下"永远连接中" */
        return;
    }

    /* 没有现成 profile（开放网络 / 系统里被删了）→ 必须先建一个；
     * 给了密码（用户要改密码）→ 覆盖重建；否则直接拿已有的 profile 连。 */
    if (!t->has_profile || (password && password[0])) {
        char sname[160], spwd[128], xml[1600], shex[3 * DOT11_SSID_MAX_LENGTH + 1];
        WCHAR xmlW[1600];
        DWORD reason = 0;
        int o = 0, psk = (password && password[0]) != 0;
        xml_esc(t->ap.ssid, sname, (int)sizeof(sname));
        xml_esc(psk ? password : "", spwd, (int)sizeof(spwd));
        /* ★ 必须写 <hex>：只给 <name> 时 Windows 会把这个名字按 ANSI(GBK) 码页
         *   存成 SSID 字节——中文 SSID 就与空口那串 UTF-8 对不上，之后永远
         *   "找不到可见接入点"。hex 直接填空口原始字节，名字只用于显示。 */
        for (ULONG b = 0; b < t->raw_len && o < (int)sizeof(shex) - 3; b++)
            o += snprintf(shex + o, sizeof(shex) - o, "%02X", t->raw[b]);
        shex[o] = '\0';
        if (psk) {
            snprintf(xml, sizeof(xml),
                "<?xml version=\"1.0\"?>\n"
                "<WLANProfile xmlns=\"http://www.microsoft.com/networking/"
                "WLAN/profile/v1\">\n"
                "  <name>%s</name>\n"
                "  <SSIDConfig><SSID><hex>%s</hex><name>%s</name></SSID></SSIDConfig>\n"
                "  <connectionType>ESS</connectionType>\n"
                "  <connectionMode>manual</connectionMode>\n"
                "  <MSM><security>\n"
                "    <authEncryption><authentication>WPA2PSK</authentication>\n"
                "      <encryption>AES</encryption><useOneX>false</useOneX>"
                "</authEncryption>\n"
                "    <sharedKey><keyType>passPhrase</keyType><protected>false"
                "</protected><keyMaterial>%s</keyMaterial></sharedKey>\n"
                "  </security></MSM>\n"
                "</WLANProfile>\n", sname, shex, sname, spwd);
        } else {
            /* 开放网络：没有 sharedKey，authentication=open / encryption=none */
            snprintf(xml, sizeof(xml),
                "<?xml version=\"1.0\"?>\n"
                "<WLANProfile xmlns=\"http://www.microsoft.com/networking/"
                "WLAN/profile/v1\">\n"
                "  <name>%s</name>\n"
                "  <SSIDConfig><SSID><hex>%s</hex><name>%s</name></SSID></SSIDConfig>\n"
                "  <connectionType>ESS</connectionType>\n"
                "  <connectionMode>manual</connectionMode>\n"
                "  <MSM><security>\n"
                "    <authEncryption><authentication>open</authentication>"
                "<encryption>none</encryption><useOneX>false</useOneX>"
                "</authEncryption>\n"
                "  </security></MSM>\n"
                "</WLANProfile>\n", sname, shex, sname);
        }
        if (!u8_to_w(xml, xmlW, (int)(sizeof(xmlW) / sizeof(WCHAR)))) {
            try_fail(t->ap.ssid);
            return;
        }
        rr = WlanSetProfile(s_h, &s_guid, 0, xmlW, NULL, TRUE, NULL, &reason);
        if (rr != ERROR_SUCCESS) {
            printf("[WIN] WlanSetProfile 失败 rr=%lu reason=%lu\n", rr, reason);
            try_fail(t->ap.ssid);
            return;
        }
        /* 新 profile 的名字就是 XML 里的 <name>＝SSID */
        if (!u8_to_w(t->ap.ssid, prof, PROF_NAME_CHARS)) {
            try_fail(t->ap.ssid);
            return;
        }
    }

    copy_w(prof, s_try_prof, PROF_NAME_CHARS);
    strncpy(s_try_ssid, t->ap.ssid, sizeof(s_try_ssid) - 1);
    s_try_ssid[sizeof(s_try_ssid) - 1] = '\0';
    s_try_raw_len = t->raw_len;
    memcpy(s_try_raw, t->raw, s_try_raw_len);
    copy_w(prof, s_try_profile, PROF_NAME_CHARS);   /* 与下发时用的 profile 名一致 */
    s_last_reason[0] = '\0';                 /* 每次尝试都从零开始记原因 */
    s_notify_fail = 0;
    s_try_t0 = clock();
    s_try_next = clock() + (clock_t)(CONNECT_POLL_MS * CLOCKS_PER_SEC / 1000);
    s_try_phase = 2;
    s_trying = 1;
    app_set_input_i(APP_IN_CONN_STATE, 1);
    set_status(WIFI_TXT_CONNECTING, s_try_ssid);
    /* 直接下发，不再预扫描：实测加了预扫描反而出现
     * 「动态密钥交换未能在配置的时间范围内成功」（四次握手被扫描拖超时）。 */
    do_connect();
}

// 函数作用：真忘记——删掉系统里存的 profile（密码），不动已建立的连接。
//          参数：ssid：目标网络。 返回值：无。
void win_io_forget(const char *ssid)
{
    win_ap_t *t = find_by_ssid(ssid);
    DWORD rr;

    if (!s_h || !t) return;
    rr = WlanDeleteProfile(s_h, &s_guid, t->profile, NULL);
    printf("[WIN] WlanDeleteProfile %S → rr=%lu\n", t->profile, rr);
    if (query()) publish_found();
}

// 函数作用：断开指定网络；只有它确实是当前连接时才动（整口断开不认 SSID）。
//          参数：ssid：目标网络。 返回值：无。
void win_io_disconnect(const char *ssid)
{
    win_ap_t *t = find_by_ssid(ssid);
    char target[33];
    DWORD rr;

    if (!s_h) return;
    if (!t || !t->ap.connected) { set_status(WIFI_TXT_NOT_CONNECTED, ssid ? ssid : ""); return; }
    strncpy(target, t->ap.ssid, sizeof(target) - 1);
    target[sizeof(target) - 1] = '\0';

    rr = WlanDisconnect(s_h, &s_guid, NULL);
    printf("[WIN] WlanDisconnect %s -> rr=%lu\n", target, (unsigned long)rr);
    if (rr != ERROR_SUCCESS) { set_status(WIFI_TXT_DROP_FAIL, target); return; }
    query();                                  /* 立刻回查，列表状态跟上 */
    set_status(WIFI_TXT_DISCONNECTED, target);
}

const wifi_ap_t *win_io_ap_at(int index)
{
    if (index < 0 || index >= s_cnt) return NULL;
    return &s_aps[index].ap;
}

int win_io_ap_count(void) { return s_cnt; }
int win_io_ap_gen(void)   { return s_gen; }

#endif /* !WIFI_PLATFORM_DEVICE */
