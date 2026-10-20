/*
 * native_vars.cpp — EEZ native 变量桥：get_var_* 从 app_model 契约状态读。
 * 本工程 UI 不回写状态（动作走 APP_OUT 通道），set_* 全部空实现
 * （EEZ 会为 native 变量同时声明 get/set，必须都给出本体）。
 */
#include "app_model.h"
#include "native_vars.h"

/* ---- 标量状态 ---- */
int32_t get_var_scan_state(void) { return app_get_input_i(APP_IN_SCAN_STATE); }
void    set_var_scan_state(int32_t v) { (void)v; }
int32_t get_var_wifi_state(void) { return app_get_input_i(APP_IN_WIFI_STATE); }
void    set_var_wifi_state(int32_t v) { (void)v; }
int32_t get_var_ap_count(void) { return app_get_input_i(APP_IN_AP_COUNT); }
void    set_var_ap_count(int32_t v) { (void)v; }
const char *get_var_conn_ssid(void) { return app_get_input_s(APP_IN_CONN_SSID); }
void        set_var_conn_ssid(const char *s) { (void)s; }
const char *get_var_pick_ssid(void) { return app_get_input_s(APP_IN_PICK_SSID); }
void        set_var_pick_ssid(const char *s) { (void)s; }
bool get_var_g_remember(void) { return app_get_input_b(APP_IN_REMEMBER); }
void set_var_g_remember(bool v) { (void)v; }

/* 槽位变量已随 v3 移除：扫描结果改由 wifi_ui_sync 的 C 渲染链表表达 */
