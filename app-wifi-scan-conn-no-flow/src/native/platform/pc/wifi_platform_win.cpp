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
#include <string.h>
#include <time.h>
#include <windows.h>
#include <wlanapi.h>
#include "app/wifi_model.h"
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

typedef struct {
    wifi_ap_t ap;                       /* 对外快照（UI 只看到这一份） */
    WCHAR     profile[PROF_NAME_CHARS]; /* Windows 侧 profile 名，连接/删除用它 */
    UCHAR     raw[DOT11_SSID_MAX_LENGTH];
    ULONG     raw_len;
} win_ap_t;

static win_ap_t  s_aps[WIN_AP_MAX];
static int       s_cnt = 0, s_gen = 0;
static HANDLE    s_h = NULL;
static GUID      s_guid;
static int       s_scanning = 0, s_trying = 0;
static clock_t   s_t0 = 0, s_try_t0 = 0, s_try_next = 0;
static char      s_try_ssid[33];

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
    if (x->connected != y->connected) return x->connected ? -1 : 1;
    if (x->rssi != y->rssi) return y->rssi - x->rssi;
    return strcmp(x->ssid, y->ssid);
}

static void set_status(const char *fmt, const char *arg)
{
    char buf[APP_IN_STR_MAX];
    snprintf(buf, sizeof(buf), fmt, arg);
    app_set_input_s(APP_IN_SCAN_STATUS, buf);
}

// 函数作用：把一次连接判失败——文案与 CONN_STATE 必须一起改，否则半页永远不关。
//          参数：ssid。 返回值：无。
static void try_fail(const char *ssid)
{
    app_set_input_i(APP_IN_CONN_STATE, 3);
    set_status("连接失败 %s", ssid ? ssid : "");
}

static win_ap_t *find_by_ssid(const char *ssid)
{
    if (!ssid) return NULL;
    for (int i = 0; i < s_cnt; i++)
        if (!strcmp(s_aps[i].ap.ssid, ssid)) return &s_aps[i];
    return NULL;
}

// 函数作用：该 SSID 在系统 profile 库里是否存在。 参数：pl：profile 列表；ssid：UTF-8 名。 返回值：1/0。
static int profile_list_has(PWLAN_PROFILE_INFO_LIST pl, const char *ssid)
{
    WCHAR w[33];
    if (!pl || !ssid || !ssid[0]) return 0;
    if (!u8_to_w(ssid, w, (int)(sizeof(w) / sizeof(WCHAR)))) return 0;
    for (DWORD i = 0; i < pl->dwNumberOfItems; i++)
        if (!wcscmp(pl->ProfileInfo[i].strProfileName, w)) return 1;
    return 0;
}

/******************** 查询：把系统真表搬进快照 ********************/

// 函数作用：查一次真接口（可用网络 + BSS 信号），排序后刷新快照与代数。
//          参数：无。 返回值：1=成功，0=调用失败（快照保持原样）。
static int query(void)
{
    PWLAN_AVAILABLE_NETWORK_LIST p_net = NULL;
    PWLAN_BSS_LIST p_bss = NULL;
    PWLAN_PROFILE_INFO_LIST p_prof = NULL;
    int n = 0;

    if (!s_h) return 0;
    if (WlanGetAvailableNetworkList(s_h, &s_guid, 0, NULL, &p_net) != ERROR_SUCCESS) {
        printf("[WIN] 取可用网络列表失败\n");
        return 0;
    }
    /* profile 库是"已保存"的唯一真值；取不到就退回用条目标志位 */
    if (WlanGetProfileList(s_h, &s_guid, NULL, &p_prof) != ERROR_SUCCESS)
        p_prof = NULL;
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
        else {
            memcpy(s_aps[n].ap.ssid, s_aps[n].raw, s_aps[n].raw_len);
            s_aps[n].ap.ssid[s_aps[n].raw_len] = '\0';
        }
        /* 隐藏网络广播的 SSID 是全零字节（netsh 里就显示成空名字），
         * 收进来就是一行没有名字的空白行——不列出来。 */
        if (!s_aps[n].ap.ssid[0]) continue;
        if (an->strProfileName[0])
            copy_w(an->strProfileName, s_aps[n].profile, PROF_NAME_CHARS);
        else
            u8_to_w(s_aps[n].ap.ssid, s_aps[n].profile, PROF_NAME_CHARS);

        /* 同一个 SSID 可能有多个 BSS：取信号最强那条的 dBm 与中心频点 */
        int best = -999;
        unsigned long freq = 0;
        for (DWORD j = 0; p_bss && j < p_bss->dwNumberOfItems; j++) {
            const WLAN_BSS_ENTRY *be = &p_bss->wlanBssEntries[j];
            if (be->dot11Ssid.uSSIDLength != s_aps[n].raw_len) continue;
            if (memcmp(be->dot11Ssid.ucSSID, s_aps[n].raw, s_aps[n].raw_len)) continue;
            if (be->lRssi > best) { best = (int)be->lRssi; freq = be->ulChCenterFrequency; }
        }
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
        s_aps[n].ap.saved = profile_list_has(p_prof, s_aps[n].ap.ssid);
        if (!s_aps[n].ap.saved)
            s_aps[n].ap.saved = (an->dwFlags & AWN_HAS_PROFILE) || an->strProfileName[0];
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
    if (p_prof) WlanFreeMemory(p_prof);

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
    snprintf(buf, sizeof(buf), "已发现 %d 个网络", s_cnt);
    app_set_input_s(APP_IN_SCAN_STATUS,
                    s_cnt > 0 ? buf : "未发现网络，请重新扫描");
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
    printf("[WIN] 用接口 %S（%u 个接口）\n", li->InterfaceInfo[0].strInterfaceDescription, n);
    WlanFreeMemory(li);
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
    app_set_input_s(APP_IN_SCAN_STATUS, "正在扫描…");
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
        if ((double)(clock() - s_try_next) * 1000.0 / CLOCKS_PER_SEC >= 0) {
            const win_ap_t *t;
            s_try_next = clock() + (clock_t)(CONNECT_POLL_MS * CLOCKS_PER_SEC / 1000);
            query();                             /* 每秒回查一次，连上就立刻报成功 */
            t = find_by_ssid(s_try_ssid);
            if (t && t->ap.connected) {
                s_trying = 0;
                app_set_input_i(APP_IN_CONN_STATE, 2);
                set_status("已连接 %s", s_try_ssid);
            } else if (since >= CONNECT_GIVEUP_MS) {
                s_trying = 0;
                try_fail(s_try_ssid);
            }
        }
    }
}

// 函数作用：真连接——需要时先写 profile（带密码），再 WlanConnect。
//          参数：ssid：目标；password：可为空（用已存的 profile）。 返回值：无。
void win_io_connect(const char *ssid, const char *password)
{
    win_ap_t *t = find_by_ssid(ssid);
    WLAN_CONNECTION_PARAMETERS cp;
    WCHAR prof[PROF_NAME_CHARS];
    DWORD rr;

    if (!s_h) return;
    if (!t) { try_fail(ssid); return; }

    /* profile 名已经是宽字符，直接抄；万一为空就用 SSID 现推 */
    copy_w(t->profile, prof, PROF_NAME_CHARS);
    if (!prof[0] && !u8_to_w(t->ap.ssid, prof, PROF_NAME_CHARS)) return;

    if (password && password[0]) {
        char sname[160], spwd[128], xml[1600];
        WCHAR xmlW[1600];
        DWORD reason = 0;
        xml_esc(t->ap.ssid, sname, (int)sizeof(sname));
        xml_esc(password, spwd, (int)sizeof(spwd));
        snprintf(xml, sizeof(xml),
            "<?xml version=\"1.0\"?>\n"
            "<WLANProfile xmlns=\"http://www.microsoft.com/networking/"
            "WLAN/profile/v1\">\n"
            "  <name>%s</name>\n"
            "  <SSIDConfig><SSID><name>%s</name></SSID></SSIDConfig>\n"
            "  <connectionType>ESS</connectionType>\n"
            "  <connectionMode>manual</connectionMode>\n"
            "  <MSM><security>\n"
            "    <authEncryption><authentication>WPA2PSK</authentication>\n"
            "      <encryption>AES</encryption><useOneX>false</useOneX>"
            "</authEncryption>\n"
            "    <sharedKey><keyType>passPhrase</keyType><protected>false"
            "</protected><keyMaterial>%s</keyMaterial></sharedKey>\n"
            "  </security></MSM>\n"
            "</WLANProfile>\n", sname, sname, spwd);
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
        if (!u8_to_w(t->ap.ssid, prof, PROF_NAME_CHARS)) return;
    }

    memset(&cp, 0, sizeof(cp));
    cp.wlanConnectionMode = wlan_connection_mode_profile;
    cp.strProfile = prof;
    cp.dot11BssType = dot11_BSS_type_infrastructure;
    rr = WlanConnect(s_h, &s_guid, &cp, NULL);
    if (rr != ERROR_SUCCESS) {
        printf("[WIN] WlanConnect 失败 rr=%lu\n", rr);
        try_fail(t->ap.ssid);
        return;
    }
    strncpy(s_try_ssid, t->ap.ssid, sizeof(s_try_ssid) - 1);
    s_try_ssid[sizeof(s_try_ssid) - 1] = '\0';
    s_try_t0 = clock();
    s_try_next = clock() + (clock_t)(CONNECT_POLL_MS * CLOCKS_PER_SEC / 1000);
    s_trying = 1;
    app_set_input_i(APP_IN_CONN_STATE, 1);
    set_status("正在连接 %s…", s_try_ssid);
    printf("[WIN] WlanConnect 已下发：%s\n", s_try_ssid);
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

const wifi_ap_t *win_io_ap_at(int index)
{
    if (index < 0 || index >= s_cnt) return NULL;
    return &s_aps[index].ap;
}

int win_io_ap_count(void) { return s_cnt; }
int win_io_ap_gen(void)   { return s_gen; }

#endif /* !WIFI_PLATFORM_DEVICE */
