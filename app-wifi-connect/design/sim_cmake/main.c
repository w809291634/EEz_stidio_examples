/*
 * app-wifi-connect 仿真入口：native 桥（动作实现 + 变量桥）+ 假 WiFi 驱动 + 自动演示。
 *
 * EEZ 侧已实现全部 UI（列表/密码面板/键盘/状态），本文件只做三件事：
 *   1. 实现 EEZ 动作（action_scan_start / wifi_pick_N / wifi_connect / ...）
 *   2. 实现 native 变量桥（get_var_/set_var_ —— EEZ 生成 vars.h 声明、这里给实现）
 *   3. 假 WiFi 驱动：扫描 2s 出 6 个假 AP；连接 2s 成功；密码"保存"到静态区（模拟 NVS）
 * 真机上把 3. 换成 esp_wifi 扫描/连接/NVS 即可，UI 零改动。
 */
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

#include "lvgl.h"
#include "SDL2/SDL.h"
#include "lv_sdl_window.h"
#include "ui.h"
#include "screens.h"        /* objects_t（objects.pwd_ta 等） */
#include "actions.h"        /* EEZ 生成的动作声明（action_xxx） */

#define SIM_W 480
#define SIM_H 320

/* =========================================================================
 * native 变量桥（EEZ 生成 vars.h 里声明的 get_var_/set_var_，在此给实现）
 * ========================================================================= */
static int32_t v_scan_state = 0, v_ap_count = 0, v_wifi_state = 0;
static int32_t v_g_pick = -1;
static char v_wifi_conn_ssid[33] = "";
static char v_g_pick_ssid[33] = "";
static char v_saved_ssid[33] = "";
static bool v_g_remember = false;
static char v_slot_ssid[6][33];
static int32_t v_slot_rssi[6];
static bool v_slot_lock[6];

int32_t  get_var_scan_state(void)      { return v_scan_state; }
void     set_var_scan_state(int32_t v) { v_scan_state = v; }
int32_t  get_var_ap_count(void)        { return v_ap_count; }
void     set_var_ap_count(int32_t v)   { v_ap_count = v; }
int32_t  get_var_wifi_state(void)      { return v_wifi_state; }
void     set_var_wifi_state(int32_t v) { v_wifi_state = v; }
const char *get_var_wifi_conn_ssid(void)          { return v_wifi_conn_ssid; }
void        set_var_wifi_conn_ssid(const char *s) { strncpy(v_wifi_conn_ssid, s, 32); }
int32_t  get_var_g_pick(void)      { return v_g_pick; }
void     set_var_g_pick(int32_t v) { v_g_pick = v; }
const char *get_var_g_pick_ssid(void)          { return v_g_pick_ssid; }
void        set_var_g_pick_ssid(const char *s) { strncpy(v_g_pick_ssid, s, 32); }
bool     get_var_g_remember(void)        { return v_g_remember; }
void     set_var_g_remember(bool v)      { v_g_remember = v; }
const char *get_var_saved_ssid(void)          { return v_saved_ssid; }
void        set_var_saved_ssid(const char *s) { strncpy(v_saved_ssid, s, 32); }

const char *get_var_wifi_slot0_ssid(void) { return v_slot_ssid[0]; }
void set_var_wifi_slot0_ssid(const char *s) { strncpy(v_slot_ssid[0], s, 32); }
const char *get_var_wifi_slot1_ssid(void) { return v_slot_ssid[1]; }
void set_var_wifi_slot1_ssid(const char *s) { strncpy(v_slot_ssid[1], s, 32); }
const char *get_var_wifi_slot2_ssid(void) { return v_slot_ssid[2]; }
void set_var_wifi_slot2_ssid(const char *s) { strncpy(v_slot_ssid[2], s, 32); }
const char *get_var_wifi_slot3_ssid(void) { return v_slot_ssid[3]; }
void set_var_wifi_slot3_ssid(const char *s) { strncpy(v_slot_ssid[3], s, 32); }
const char *get_var_wifi_slot4_ssid(void) { return v_slot_ssid[4]; }
void set_var_wifi_slot4_ssid(const char *s) { strncpy(v_slot_ssid[4], s, 32); }
const char *get_var_wifi_slot5_ssid(void) { return v_slot_ssid[5]; }
void set_var_wifi_slot5_ssid(const char *s) { strncpy(v_slot_ssid[5], s, 32); }
int32_t get_var_wifi_slot0_rssi(void) { return v_slot_rssi[0]; }
void set_var_wifi_slot0_rssi(int32_t v) { v_slot_rssi[0] = v; }
int32_t get_var_wifi_slot1_rssi(void) { return v_slot_rssi[1]; }
void set_var_wifi_slot1_rssi(int32_t v) { v_slot_rssi[1] = v; }
int32_t get_var_wifi_slot2_rssi(void) { return v_slot_rssi[2]; }
void set_var_wifi_slot2_rssi(int32_t v) { v_slot_rssi[2] = v; }
int32_t get_var_wifi_slot3_rssi(void) { return v_slot_rssi[3]; }
void set_var_wifi_slot3_rssi(int32_t v) { v_slot_rssi[3] = v; }
int32_t get_var_wifi_slot4_rssi(void) { return v_slot_rssi[4]; }
void set_var_wifi_slot4_rssi(int32_t v) { v_slot_rssi[4] = v; }
int32_t get_var_wifi_slot5_rssi(void) { return v_slot_rssi[5]; }
void set_var_wifi_slot5_rssi(int32_t v) { v_slot_rssi[5] = v; }
bool get_var_wifi_slot0_lock(void) { return v_slot_lock[0]; }
void set_var_wifi_slot0_lock(bool v) { v_slot_lock[0] = v; }
bool get_var_wifi_slot1_lock(void) { return v_slot_lock[1]; }
void set_var_wifi_slot1_lock(bool v) { v_slot_lock[1] = v; }
bool get_var_wifi_slot2_lock(void) { return v_slot_lock[2]; }
void set_var_wifi_slot2_lock(bool v) { v_slot_lock[2] = v; }
bool get_var_wifi_slot3_lock(void) { return v_slot_lock[3]; }
void set_var_wifi_slot3_lock(bool v) { v_slot_lock[3] = v; }
bool get_var_wifi_slot4_lock(void) { return v_slot_lock[4]; }
void set_var_wifi_slot4_lock(bool v) { v_slot_lock[4] = v; }
bool get_var_wifi_slot5_lock(void) { return v_slot_lock[5]; }
void set_var_wifi_slot5_lock(bool v) { v_slot_lock[5] = v; }

/* =========================================================================
 * EEZ 动作实现（EEZ 生成 actions.h 里声明的 action_xxx(lv_event_t*)）
 * ========================================================================= */
static const char *fake_aps[6] = { "Home_5G", "Office-2G", "Coffee_Shop",
                                   "Neighbor", "Guest", "TP-LINK_A02" };
static const int32_t fake_rssi[6] = { -41, -58, -67, -75, -82, -63 };
static const bool fake_lock[6] = { true, true, true, true, false, true };
static char pick_ssid_snapshot[33];

static void scan_done_cb(lv_timer_t *t)
{
    int i;
    for (i = 0; i < 6; i++) {
        switch (i) {
        case 0: set_var_wifi_slot0_ssid(fake_aps[0]); set_var_wifi_slot0_rssi(fake_rssi[0]); set_var_wifi_slot0_lock(fake_lock[0]); break;
        case 1: set_var_wifi_slot1_ssid(fake_aps[1]); set_var_wifi_slot1_rssi(fake_rssi[1]); set_var_wifi_slot1_lock(fake_lock[1]); break;
        case 2: set_var_wifi_slot2_ssid(fake_aps[2]); set_var_wifi_slot2_rssi(fake_rssi[2]); set_var_wifi_slot2_lock(fake_lock[2]); break;
        case 3: set_var_wifi_slot3_ssid(fake_aps[3]); set_var_wifi_slot3_rssi(fake_rssi[3]); set_var_wifi_slot3_lock(fake_lock[3]); break;
        case 4: set_var_wifi_slot4_ssid(fake_aps[4]); set_var_wifi_slot4_rssi(fake_rssi[4]); set_var_wifi_slot4_lock(fake_lock[4]); break;
        case 5: set_var_wifi_slot5_ssid(fake_aps[5]); set_var_wifi_slot5_rssi(fake_rssi[5]); set_var_wifi_slot5_lock(fake_lock[5]); break;
        }
    }
    set_var_ap_count(6);
    set_var_scan_state(2);
    printf("[WIFI] scan done: 6 APs\n");
    lv_timer_del(t);
}

void action_scan_start(lv_event_t *e)
{
    (void)e;
    set_var_scan_state(1);
    /* 假驱动：2s 后出结果（真机 = esp_wifi_scan_start + WIFI_EVENT_SCAN_DONE） */
    lv_timer_t *t = lv_timer_create(scan_done_cb, 2000, NULL);
    (void)t;
}

void action_wifi_pick_0(lv_event_t *e) { (void)e; set_var_g_pick(0); set_var_g_pick_ssid(get_var_wifi_slot0_ssid()); strncpy(pick_ssid_snapshot, get_var_wifi_slot0_ssid(), 32); }
void action_wifi_pick_1(lv_event_t *e) { (void)e; set_var_g_pick(1); set_var_g_pick_ssid(get_var_wifi_slot1_ssid()); strncpy(pick_ssid_snapshot, get_var_wifi_slot1_ssid(), 32); }
void action_wifi_pick_2(lv_event_t *e) { (void)e; set_var_g_pick(2); set_var_g_pick_ssid(get_var_wifi_slot2_ssid()); strncpy(pick_ssid_snapshot, get_var_wifi_slot2_ssid(), 32); }
void action_wifi_pick_3(lv_event_t *e) { (void)e; set_var_g_pick(3); set_var_g_pick_ssid(get_var_wifi_slot3_ssid()); strncpy(pick_ssid_snapshot, get_var_wifi_slot3_ssid(), 32); }
void action_wifi_pick_4(lv_event_t *e) { (void)e; set_var_g_pick(4); set_var_g_pick_ssid(get_var_wifi_slot4_ssid()); strncpy(pick_ssid_snapshot, get_var_wifi_slot4_ssid(), 32); }
void action_wifi_pick_5(lv_event_t *e) { (void)e; set_var_g_pick(5); set_var_g_pick_ssid(get_var_wifi_slot5_ssid()); strncpy(pick_ssid_snapshot, get_var_wifi_slot5_ssid(), 32); }

static void connect_done_cb(lv_timer_t *t)
{
    /* 假驱动：2s 后连接成功（真机 = esp_wifi_connect + WIFI_EVENT_STA_CONNECTED） */
    set_var_wifi_state(2);
    set_var_wifi_conn_ssid(pick_ssid_snapshot);
    if (get_var_g_remember()) {
        set_var_saved_ssid(pick_ssid_snapshot);   /* 真机 = nvs 写入 */
        printf("[WIFI] password saved (NVS simulated)\n");
    }
    printf("[WIFI] connected: %s\n", pick_ssid_snapshot);
    lv_timer_del(t);
}

void action_wifi_connect(lv_event_t *e)
{
    (void)e;
    const char *pwd = lv_textarea_get_text(objects.pwd_ta);
    printf("[WIFI] connect to '%s' pwd='%s' remember=%d\n",
           pick_ssid_snapshot, pwd, (int)get_var_g_remember());
    if (strlen(pwd) == 0 && pick_ssid_snapshot[0] != '\0') {
        /* 演示策略：空密码视为开放网络直连；真机按 esp_wifi_sta_config 校验 */
        printf("[WIFI] empty password (treated as open network in demo)\n");
    }
    set_var_wifi_state(1);
    lv_timer_t *t = lv_timer_create(connect_done_cb, 2000, NULL);
    (void)t;
}

void action_chk_remember(lv_event_t *e)
{
    (void)e;
    set_var_g_remember(!get_var_g_remember());
    printf("[WIFI] remember = %d\n", (int)get_var_g_remember());
}

void action_panel_cancel(lv_event_t *e)
{
    (void)e;
    set_var_g_pick(-1);
}

/* =========================================================================
 * 假指针单击（走真实 lv_indev 管线，不占真鼠标）+ 自动演示状态机
 * ========================================================================= */
static int32_t tap_x = 0, tap_y = 0;
static int tap_phase = -1;          /* -1 空闲 0..2 按下保持 3 释放 */
static lv_indev_t *tap_indev = NULL;

static void tap_read_cb(lv_indev_t *indev, lv_indev_data_t *data)
{
    if (tap_phase < 0 || tap_phase > 2) {
        data->state = LV_INDEV_STATE_RELEASED;
        return;
    }
    data->point.x = tap_x;
    data->point.y = tap_y;
    data->state = (tap_phase < 2) ? LV_INDEV_STATE_PRESSED
                                  : LV_INDEV_STATE_RELEASED;
    tap_phase++;
}

static void demo_tap(int32_t x, int32_t y)
{
    printf("[TAP] tap at %d,%d\n", (int)x, (int)y);
    tap_x = x; tap_y = y; tap_phase = 0;
    if (!tap_indev) {
        tap_indev = lv_indev_create();
        lv_indev_set_type(tap_indev, LV_INDEV_TYPE_POINTER);
        lv_indev_set_read_cb(tap_indev, tap_read_cb);
        lv_indev_set_display(tap_indev, lv_display_get_default());
    }
}

static bool demo_scan_fired = false;
static bool demo_pick_fired = false;
static bool demo_connect_fired = false;

static void demo_timer(lv_timer_t *t)
{
    static int tick = 0;
    static int wait = 0;
    tick++;
    if (!demo_scan_fired && tick >= 2) {
        action_scan_start(NULL);                    /* 自动扫描 */
        demo_scan_fired = true;
    }
    if (demo_scan_fired && !demo_pick_fired && get_var_scan_state() == 2) {
        demo_tap(240, 46 + 1 * 36 + 12);            /* 点第 2 行（开放网络 Guest） */
        demo_pick_fired = true;
    }
    if (demo_pick_fired && !demo_connect_fired && get_var_g_pick() == 1) {
        if (++wait >= 4) {                          /* 面板弹出后稍候点"连接" */
            demo_tap(40 + 60 + 75, 20 + 250 + 13);  /* 面板内连接按钮中心 */
            demo_connect_fired = true;
        }
    }
    if (tick % 4 == 0) {
        printf("[STATE] scan=%d aps=%d wifi=%d pick=%d | panel_hidden=%d "
               "hit1_hidden=%d hit1_clickable=%d\n",
               (int)get_var_scan_state(), (int)get_var_ap_count(),
               (int)get_var_wifi_state(), (int)get_var_g_pick(),
               lv_obj_has_flag(objects.panel_pwd, LV_OBJ_FLAG_HIDDEN) ? 1 : 0,
               lv_obj_has_flag(objects.hit_1, LV_OBJ_FLAG_HIDDEN) ? 1 : 0,
               lv_obj_has_flag(objects.hit_1, LV_OBJ_FLAG_CLICKABLE) ? 1 : 0);
    }
    if (get_var_wifi_state() == 2 && demo_connect_fired) {
        printf("[DEMO] done: connected, footer shows it\n");
        lv_timer_del(t);
    }
    (void)t;
}

static lv_display_t *hal_init(int32_t w, int32_t h)
{
    lv_display_t *disp = lv_sdl_window_create(w, h);
    lv_indev_t *mouse = lv_sdl_mouse_create();
    lv_indev_set_display(mouse, disp);
    lv_display_set_default(disp);
    return disp;
}

int main(int argc, char **argv)
{
    (void)argc; (void)argv;
    setvbuf(stdout, NULL, _IONBF, 0);   /* 重定向到文件也要实时可见 */
    lv_init();
    hal_init(SIM_W, SIM_H);
    ui_init();
    lv_timer_create(demo_timer, 500, NULL);

    while (1) {
        lv_tick_inc(2);
        lv_timer_handler();
        ui_tick();
        usleep(4000);
    }
    return 0;
}
