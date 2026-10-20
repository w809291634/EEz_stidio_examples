/*
 * io_pc.cpp — PC 仿真实现：假 WiFi 世界（链表）+ 状态机 + 打印 UI 命令。
 * 真机 io_esp.cpp 用 esp_wifi/NVS 同语义替换：
 *   io_wifi_scan(v=1)  → esp_wifi_scan_start；SCAN_DONE 后建链表（本文件的 scan_fill_list）
 *   io_wifi_join(v=1)  → 密码取 APP_IN_PWD，esp_wifi_sta_config + esp_wifi_connect
 *   记住密码           → NVS 读写（本文件 s_saved_ssid 模拟）
 */
#ifndef APP_WIFI_REAL      /* 真模式（run_sim_realwifi.bat）编 io_win.cpp，本文件整体空编译 */
#include "../app_model.h"
#include "io_iface.h"
#include "lvgl.h"               /* 仅 lv_tick_get 计时 */
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

/* ---- 扫描结果链表（io 层所有）---- */
static wifi_ap_t *s_head = NULL;
static int  s_ap_count = 0;
static int  s_gen = 0;

static void list_clear(void)
{
    wifi_ap_t *p = s_head;
    while (p) { wifi_ap_t *n = p->next; free(p); p = n; }
    s_head = NULL; s_ap_count = 0;
}

static void list_add(const char *ssid, int rssi, bool lock)
{
    wifi_ap_t *node = (wifi_ap_t *)malloc(sizeof(wifi_ap_t));
    if (!node) return;
    strncpy(node->ssid, ssid, 32); node->ssid[32] = '\0';
    node->rssi = rssi; node->lock = lock; node->connected = false;
    node->next = NULL;
    if (!s_head) { s_head = node; }
    else {
        wifi_ap_t *p = s_head;
        while (p->next) p = p->next;
        p->next = node;
    }
    s_ap_count++;
}

const wifi_ap_t *wifi_ap_first(void) { return s_head; }
int  wifi_ap_count(void) { return s_ap_count; }
int  wifi_ap_gen(void) { return s_gen; }

/* ---- 状态机 ---- */
static int  s_scan_state = 0;        /* 0 未扫 1 扫描中 2 完成 */
static int  s_wifi_state = 0;        /* 0 未连 1 连接中 2 已连接 */
static long s_scan_t0 = -1;
static long s_join_t0 = -1;
static char s_join_ssid[33] = "";
static char s_saved_ssid[33] = "";   /* 模拟 NVS 的"已保存网络" */

static const char *FAKE_SSID[4] = { "Home_5G", "Office-2G", "Coffee_Shop", "Guest" };
static const int   FAKE_RSSI[4] = { -41, -58, -67, -75 };
static const bool  FAKE_LOCK[4] = { true, true, true, false };

void io_init(void)
{
    printf("[IO] io_init (pc fake wifi)\n");
}

static void scan_fill_list(void)
{
    list_clear();
    for (int i = 0; i < 4; i++) list_add(FAKE_SSID[i], FAKE_RSSI[i], FAKE_LOCK[i]);
    /* 演示：已连接网络在新扫描里保持 connected 标记 */
    if (s_wifi_state == 2) {
        for (wifi_ap_t *p = s_head; p; p = p->next) {
            if (strcmp(p->ssid, app_get_input_s(APP_IN_CONN_SSID)) == 0)
                p->connected = true;
        }
    }
    s_gen++;
}

void io_sample_inputs(void)
{
    long now = (long)lv_tick_get();

    /* 扫描状态机：2s 建链表 */
    if (s_scan_state == 1 && s_scan_t0 >= 0 && now - s_scan_t0 >= 2000) {
        scan_fill_list();
        s_scan_state = 2;
        app_set_input_i(APP_IN_SCAN_STATE, 2);
        app_set_input_i(APP_IN_AP_COUNT, s_ap_count);
        printf("[IO] scan done: %d APs (linked list)\n", s_ap_count);
    }

    /* 连接状态机：2s 出结果 */
    if (s_wifi_state == 1 && s_join_t0 >= 0 && now - s_join_t0 >= 2000) {
        s_wifi_state = 2;
        app_set_input_i(APP_IN_WIFI_STATE, 2);
        app_set_input_s(APP_IN_CONN_SSID, s_join_ssid);
        for (wifi_ap_t *p = s_head; p; p = p->next)
            p->connected = (strcmp(p->ssid, s_join_ssid) == 0);
        if (app_get_input_b(APP_IN_REMEMBER)) {
            strncpy(s_saved_ssid, s_join_ssid, 32);
            printf("[IO] password saved (NVS simulated)\n");
        }
        printf("[IO] connected: %s\n", s_join_ssid);
        s_gen++;   /* connected 标记变化 → UI 重建列表 */
    }
}

void io_wifi_scan(int v)
{
    if (v != 1 || s_scan_state == 1) return;
    s_scan_state = 1;
    s_scan_t0 = (long)lv_tick_get();
    app_set_input_i(APP_IN_SCAN_STATE, 1);
    printf("[IO] scan start\n");
}

void io_wifi_join(int v)
{
    (void)v;
    if (s_wifi_state == 1) return;
    strncpy(s_join_ssid, app_get_input_s(APP_IN_PICK_SSID), 32);
    printf("[IO] join '%s' pwd='%s'\n", s_join_ssid,
           app_get_input_s(APP_IN_PWD));
    s_wifi_state = 1;
    s_join_t0 = (long)lv_tick_get();
    app_set_input_i(APP_IN_WIFI_STATE, 1);
}

void io_pwd_cancel(int v)  { (void)v; }

void io_remember_toggle(int v)
{
    (void)v;
    bool cur = app_get_input_b(APP_IN_REMEMBER);
    app_set_input_b(APP_IN_REMEMBER, !cur);
    printf("[IO] remember = %d\n", !cur);
}

#endif /*APP_WIFI_REAL*/
