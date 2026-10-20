/*
 * native_vars.h — native 变量桥声明（EEZ 生成 vars.h 亦会声明；此处供内部引用）。
 */
#pragma once
#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

int32_t get_var_scan_state(void);      void set_var_scan_state(int32_t v);
int32_t get_var_wifi_state(void);      void set_var_wifi_state(int32_t v);
int32_t get_var_ap_count(void);        void set_var_ap_count(int32_t v);
const char *get_var_conn_ssid(void);   void set_var_conn_ssid(const char *s);
const char *get_var_pick_ssid(void);   void set_var_pick_ssid(const char *s);
bool get_var_g_remember(void);         void set_var_g_remember(bool v);

#ifdef __cplusplus
}
#endif
