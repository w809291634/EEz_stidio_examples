/*
 * native_vars.cpp — EEZ native 变量桥：get_var_* 从 app_model 契约状态读。
 * 本工程 UI 不回写状态（动作走 APP_OUT 通道），set_* 全部空实现。
 */
#include "app_model.h"
#include "native_vars.h"

int32_t get_var_scan_state(void) { return app_get_input_i(APP_IN_SCAN_STATE); }
void    set_var_scan_state(int32_t v) { (void)v; }

int32_t get_var_ap_count(void) { return app_get_input_i(APP_IN_AP_COUNT); }
void    set_var_ap_count(int32_t v) { (void)v; }

const char *get_var_scan_status(void) { return app_get_input_s(APP_IN_SCAN_STATUS); }
void        set_var_scan_status(const char *s) { (void)s; }
