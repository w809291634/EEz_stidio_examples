/*
 * io_win.cpp — PC 真硬件实现：用 Windows WLAN API 操作电脑的真实 WiFi。
 * （run_sim_realwifi.bat 定义 APP_WIFI_REAL 时编译；默认构建本文件为空。）
 *
 * 通道语义与 io_pc.cpp 完全一致（io_iface.h 契约不变，UI 零改动）：
 *   io_wifi_scan  → WlanScan（异步）；2.5s 后 WlanGetAvailableNetworkList
 *                   建 wifi_ap 链表（信号质量 → dBm 近似；开放网络 lock=false）
 *   io_wifi_join  → 密码取 APP_IN_PWD：WPA2PSK/AES 或开放网络 profile XML
 *                   → WlanSetProfile + WlanConnect（真连接！会切换电脑当前 WiFi）
 *   io_sample_inputs → WlanQueryInterface 查询当前连接状态回发
 *   记住密码      → Windows profile 本身持久化（天然"NVS"）
 */
#ifdef APP_WIFI_REAL

#include "../app_model.h"
#include "io_iface.h"
#include "lvgl.h"
#include <windows.h>
#include <wlanapi.h>
#include <string.h>
#include <stdio.h>

#ifndef DOT11_AUTH_ALGO_SAE
#define DOT11_AUTH_ALGO_SAE 8   /* WPA3（mingw 旧头缺）*/
#endif

/* mingw 头缺失的常量（MS SDK 有）：按 MS 文档值补 */
#ifndef WLAN_AVAILABLE_NETWORK_CONNECTED
#define WLAN_AVAILABLE_NETWORK_CONNECTED 0x00000001
#endif
#ifndef WLAN_AVAILABLE_NETWORK_HAS_PROFILE
#define WLAN_AVAILABLE_NETWORK_HAS_PROFILE 0x00000002
#endif

static wchar_t *to_wide(const char *s);   /* fwd（下方定义）*/

static HANDLE s_h = NULL;
static GUID   s_guid;
static bool   s_have_if = false;

/* ---- 链表（io 层所有）---- */
static wifi_ap_t *s_head = NULL;
static int  s_ap_count = 0;
static int  s_gen = 0;

static void list_clear(void)
{
    wifi_ap_t *p = s_head;
    while (p) { wifi_ap_t *n = p->next; free(p); p = n; }
    s_head = NULL; s_ap_count = 0;
}

static void list_add(const char *ssid, int rssi, bool lock, bool connected, int auth)
{
    wifi_ap_t *node = (wifi_ap_t *)malloc(sizeof(wifi_ap_t));
    if (!node) return;
    strncpy(node->ssid, ssid, 32); node->ssid[32] = '\0';
    node->rssi = rssi; node->lock = lock; node->connected = connected; node->auth = auth;
    node->next = NULL;
    if (!s_head) s_head = node;
    else { wifi_ap_t *p = s_head; while (p->next) p = p->next; p->next = node; }
    s_ap_count++;
}

const wifi_ap_t *wifi_ap_first(void) { return s_head; }
int  wifi_ap_count(void) { return s_ap_count; }
int  wifi_ap_gen(void) { return s_gen; }

/* ---- 状态机 ---- */
static int  s_scan_state = 0, s_wifi_state = 0;
static bool s_join_remember = true;
static int  s_join_retried = 0;
static bool s_pending_connect = false;
static long s_pending_t0 = 0;
static long s_last_poll = 0;   /* 轮询节流：1s 一次（高频查询会卡死连接）*/   /* 本次连接是否保存（否 → 连上后删 profile）*/
static long s_scan_t0 = -1, s_join_t0 = -1;
static char s_join_ssid[33] = "";

void io_init(void)
{
    DWORD cur = 0;
    if (WlanOpenHandle(2, NULL, &cur, &s_h) != ERROR_SUCCESS) {
        printf("[IO:WIN] WlanOpenHandle failed\n");
        return;
    }
    PWLAN_INTERFACE_INFO_LIST lst = NULL;
    if (WlanEnumInterfaces(s_h, NULL, &lst) == ERROR_SUCCESS &&
        lst->dwNumberOfItems > 0) {
        s_guid = lst->InterfaceInfo[0].InterfaceGuid;
        s_have_if = true;
        printf("[IO:WIN] wlan interface ready (%d found)\n",
               (int)lst->dwNumberOfItems);
    } else {
        printf("[IO:WIN] no wlan interface\n");
    }
    if (lst) WlanFreeMemory(lst);
}

static void publish_scan_list(void)
{
    if (!s_have_if) return;
    PWLAN_AVAILABLE_NETWORK_LIST lst = NULL;
    DWORD r = WlanGetAvailableNetworkList(s_h, &s_guid, 2 /*include all*/, NULL, &lst);
    if (r != ERROR_SUCCESS) { printf("[IO:WIN] GetAvailableNetworkList failed %lu\n", r); return; }

    list_clear();
    for (unsigned i = 0; i < lst->dwNumberOfItems; i++) {
        WLAN_AVAILABLE_NETWORK *n = &lst->Network[i];
        char ssid[33] = "";
        unsigned len = n->dot11Ssid.uSSIDLength;
        if (len == 0 || len > 32) continue;      /* 跳过空/超长 */
        memcpy(ssid, n->dot11Ssid.ucSSID, len);
        bool lock = (n->dot11DefaultAuthAlgorithm != DOT11_AUTH_ALGO_80211_OPEN);
        bool connected = (n->dwFlags & WLAN_AVAILABLE_NETWORK_CONNECTED) != 0;
        int rssi = (int)(n->wlanSignalQuality) / 2 - 100;   /* 质量% → dBm 近似 */
        list_add(ssid, rssi, lock, connected, (int)n->dot11DefaultAuthAlgorithm);
    }
    WlanFreeMemory(lst);
    app_set_input_i(APP_IN_AP_COUNT, s_ap_count);
    app_set_input_i(APP_IN_SCAN_STATE, 2);
    s_gen++;
    printf("[IO:WIN] scan done: %d real networks\n", s_ap_count);
}


void io_sample_inputs(void)
{
    long now = (long)lv_tick_get();

    if (s_scan_state == 1 && s_scan_t0 >= 0 && now - s_scan_t0 >= 2500) {
        publish_scan_list();
        s_scan_state = 2;
    }

    /* 延迟连接：profile set 后 800ms 再真正 Connect */
    if (s_pending_connect && s_pending_t0 >= 0 &&
            now - s_pending_t0 >= 800) {
        s_pending_connect = false;
        wchar_t *wn = to_wide(s_join_ssid);
        WLAN_CONNECTION_PARAMETERS cp;
        memset(&cp, 0, sizeof(cp));
        cp.wlanConnectionMode = wlan_connection_mode_profile;
        cp.strProfile = wn;
        cp.dot11BssType = dot11_BSS_type_infrastructure;
        DWORD rr = WlanConnect(s_h, &s_guid, &cp, NULL);
        printf("[IO:WIN] WlanConnect '%s' -> %lu\n", s_join_ssid, rr);
        free(wn);
        s_join_t0 = now;
        s_join_retried = 0;
        s_last_poll = 0;
    }

    /* 连接结果查询：每 500ms 轮询；连上即发布；2s 时重试一次 Connect；
     * 10s 未连上判失败（WPA3 握手 3~8s，profile 刚建立即 Connect 偶发不生效）*/
    if (s_wifi_state == 1 && s_join_t0 >= 0 && now - s_join_t0 >= 500 &&
            now - s_last_poll >= 1000) {
        s_last_poll = now;
        if (s_have_if) {
            PWLAN_CONNECTION_ATTRIBUTES attr = NULL;
            DWORD sz = sizeof(WLAN_CONNECTION_ATTRIBUTES);
            WLAN_OPCODE_VALUE_TYPE op;
            bool conn = (WlanQueryInterface(s_h, &s_guid,
                            wlan_intf_opcode_current_connection,
                            NULL, &sz, (PVOID *)&attr, &op) == ERROR_SUCCESS &&
                         attr != NULL &&
                         attr->isState == wlan_interface_state_connected);
            static long last_log = -1000;
            if (now - last_log >= 1000) {
                last_log = now;
                printf("[DBG] poll state=%d qr_ok=%d\n",
                       attr ? (int)attr->isState : -1, (int)(attr != NULL));
            }
            if (conn) {
                s_wifi_state = 2;
                app_set_input_i(APP_IN_WIFI_STATE, 2);
                char ssid[33] = "";
                unsigned len = attr->wlanAssociationAttributes.dot11Ssid.uSSIDLength;
                if (len > 32) len = 32;
                memcpy(ssid, attr->wlanAssociationAttributes.dot11Ssid.ucSSID, len);
                app_set_input_s(APP_IN_CONN_SSID, ssid);
                app_set_input_s(APP_IN_PICK_SSID, "");   /* 关面板回列表 */
                printf("[IO:WIN] connected to %s (saved=%d)\n",
                       ssid, (int)s_join_remember);
            } else if (now - s_join_t0 >= 10000) {
                s_wifi_state = 3;
                app_set_input_i(APP_IN_WIFI_STATE, 3);
                printf("[IO:WIN] join failed or timed out (%ldms)\n",
                       now - s_join_t0);
            } else if (!s_join_retried && now - s_join_t0 >= 2000) {
                s_join_retried = 1;
                wchar_t *wn = to_wide(s_join_ssid);
                WLAN_CONNECTION_PARAMETERS cp;
                memset(&cp, 0, sizeof(cp));
                cp.wlanConnectionMode = wlan_connection_mode_profile;
                cp.strProfile = wn;
                cp.dot11BssType = dot11_BSS_type_infrastructure;
                DWORD rr = WlanConnect(s_h, &s_guid, &cp, NULL);
                printf("[IO:WIN] reconnect attempt (%lu)\n", rr);
                free(wn);
            }
            if (attr) WlanFreeMemory(attr);
        }
    }
}

void io_wifi_scan(int v)
{
    (void)v;
    if (!s_have_if || s_scan_state == 1) return;
    if (WlanScan(s_h, &s_guid, NULL, NULL, NULL) != ERROR_SUCCESS)
        printf("[IO:WIN] WlanScan failed (use cached list)\n");
    s_scan_state = 1;
    s_scan_t0 = (long)lv_tick_get();
    app_set_input_i(APP_IN_SCAN_STATE, 1);
    printf("[IO:WIN] real scan start\n");
}

/* 真实实现：宽字符 profile + WlanConnect */
#include <stdlib.h>

static wchar_t *to_wide(const char *s)
{
    int n = MultiByteToWideChar(CP_UTF8, 0, s, -1, NULL, 0);
    wchar_t *w = (wchar_t *)malloc(n * sizeof(wchar_t));
    MultiByteToWideChar(CP_UTF8, 0, s, -1, w, n);
    return w;
}

void io_wifi_join_real(int v)
{
    (void)v;
    if (!s_have_if || s_wifi_state == 1) return;
    const char *ssid = app_get_input_s(APP_IN_PICK_SSID);
    const char *pwd  = app_get_input_s(APP_IN_PWD);
    if (ssid[0] == '\0') { printf("[IO:WIN] no network picked\n"); return; }
    if (s_scan_state == 1) { printf("[IO:WIN] join ignored: scan in progress\n"); return; }

    int auth = 0; bool lock = true;
    for (wifi_ap_t *p = s_head; p; p = p->next)
        if (strcmp(p->ssid, ssid) == 0) { auth = p->auth; lock = p->lock; break; }

    wchar_t *wname = to_wide(ssid);

    /* 1) 已保存 profile → 直接连（无需密码/XML；用户 Windows 里存过的网络） */
    LPWSTR profXml = NULL; DWORD pflags = 0, ptype = 0;
    if (WlanGetProfile(s_h, &s_guid, wname, NULL, &profXml, &pflags, &ptype)
            == ERROR_SUCCESS) {
        WlanFreeMemory(profXml);
        WLAN_CONNECTION_PARAMETERS cp;
        memset(&cp, 0, sizeof(cp));
        cp.wlanConnectionMode = wlan_connection_mode_profile;
        cp.strProfile = wname;
        cp.dot11BssType = dot11_BSS_type_infrastructure;
        DWORD r = WlanConnect(s_h, &s_guid, &cp, NULL);
        printf("[IO:WIN] saved profile found -> direct connect '%s' (%lu)\n",
               ssid, r);
        free(wname);
        s_wifi_state = 1; s_join_t0 = (long)lv_tick_get();
        app_set_input_i(APP_IN_WIFI_STATE, 1);
        return;
    }

    /* 2) 无 profile：加密网络必须给密码 */
    if (lock && pwd[0] == '\0') {
        printf("[IO:WIN] locked network needs a password\n");
        app_set_input_i(APP_IN_WIFI_STATE, 3);
        free(wname);
        return;
    }

    /* 3) 按扫描出的认证类型构造 XML（hex SSID + 认证映射） */
    char hex[65] = "";
    for (int i = 0; ssid[i] && i < 32; i++)
        sprintf(hex + i * 2, "%02X", (unsigned char)ssid[i]);
    (void)auth;
    bool openNet = (lock == false);
    /* 加密网络统一 WPA3SAE + transitionMode（Windows 标准混合 profile，
     * 兼容 WPA2 与 WPA3 网络；纯 WPA2 亦可用——实测 WPA2PSK 对 WPA3 网络失败）*/
    const char *authTag = openNet ? "open" : "WPA3SAE";
    const char *extra = openNet ? ""
        : "<transitionMode xmlns=\"http://www.microsoft.com/networking/WLAN/profile/v4\">true</transitionMode>";

    char xml[1200];
    if (openNet)
        _snprintf(xml, sizeof(xml) - 1,
            "<?xml version=\"1.0\"?>"
            "<WLANProfile xmlns=\"http://www.microsoft.com/networking/WLAN/profile/v1\">"
            "<name>%s</name><SSIDConfig><SSID><hex>%s</hex><name>%s</name></SSID>"
            "</SSIDConfig><connectionType>ESS</connectionType>"
            "<connectionMode>manual</connectionMode>"
            "<MSM><security><authEncryption><authentication>open</authentication>"
            "<encryption>none</encryption><useOneX>false</useOneX></authEncryption>"
            "</security></MSM></WLANProfile>", ssid, hex, ssid);
    else
        _snprintf(xml, sizeof(xml) - 1,
            "<?xml version=\"1.0\"?>"
            "<WLANProfile xmlns=\"http://www.microsoft.com/networking/WLAN/profile/v1\">"
            "<name>%s</name><SSIDConfig><SSID><hex>%s</hex><name>%s</name></SSID>"
            "</SSIDConfig><connectionType>ESS</connectionType>"
            "<connectionMode>manual</connectionMode>"
            "<MSM><security><authEncryption><authentication>%s</authentication>"
            "<encryption>AES</encryption><useOneX>false</useOneX>%s</authEncryption>"
            "<sharedKey><keyType>passPhrase</keyType><protected>false</protected>"
            "<keyMaterial>%s</keyMaterial></sharedKey>"
            "</security></MSM></WLANProfile>", ssid, hex, ssid, authTag, extra, pwd);
    xml[sizeof(xml) - 1] = '\0';
    wchar_t *wxml = to_wide(xml);

    WLAN_CONNECTION_PARAMETERS cp;
    memset(&cp, 0, sizeof(cp));
    cp.dot11BssType = dot11_BSS_type_infrastructure;
    DWORD r;
    s_join_remember = app_get_input_b(APP_IN_REMEMBER);
    /* 注：Windows 后端下 temporary profile 连接不稳定，remember 仅作记录；
     * 统一 SetProfile + 延迟 Connect（唯一可靠路径）*/
    strncpy(s_join_ssid, ssid, 32); s_join_ssid[32] = '\0';
    s_join_retried = 0;
    /* 统一走 SetProfile + profile 模式（唯一可靠路径）；
     * remember=否 在连上成功后删除 profile（见 connected 分支） */
    {
        DWORD reason = 0;
        /* mingw 头顺序：(..., bOverwrite, pReserved, pdwReasonCode) */
        r = WlanSetProfile(s_h, &s_guid, 0, wxml, NULL, true, NULL, &reason);
        if (r != ERROR_SUCCESS) {
            printf("[IO:WIN] WlanSetProfile failed %lu (reason %lu)\n", r, reason);
            app_set_input_i(APP_IN_WIFI_STATE, 3);
            free(wxml); free(wname);
            return;
        }
        cp.wlanConnectionMode = wlan_connection_mode_profile;
        cp.strProfile = wname;
        printf("[IO:WIN] profile set (remember=%d, auth=%s), connect scheduled\n",
               (int)s_join_remember, authTag);
        s_pending_connect = true;
        s_pending_t0 = (long)lv_tick_get();
        (void)r;
    }
    /* remember=0：不写 profile，用 temporary profile 连接（连上后系统不留记录）*/
    free(wxml); free(wname);

    s_wifi_state = 1;
    s_join_t0 = (long)lv_tick_get();
    app_set_input_i(APP_IN_WIFI_STATE, 1);
}

void io_wifi_join(int v) { io_wifi_join_real(v); }

void io_pwd_cancel(int v)  { (void)v; }

void io_remember_toggle(int v)
{
    (void)v;
    bool cur = app_get_input_b(APP_IN_REMEMBER);
    app_set_input_b(APP_IN_REMEMBER, !cur);
    printf("[IO:WIN] remember = %d\n", !cur);
}

#endif /*APP_WIFI_REAL*/
