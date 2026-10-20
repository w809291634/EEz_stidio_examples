#ifndef EEZ_LVGL_UI_VARS_H
#define EEZ_LVGL_UI_VARS_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// enum declarations

// Flow global variables

enum FlowGlobalVariables {
    FLOW_GLOBAL_VARIABLE_NONE
};

// Native global variables

extern int32_t get_var_scan_state();
extern void set_var_scan_state(int32_t value);
extern int32_t get_var_wifi_state();
extern void set_var_wifi_state(int32_t value);
extern int32_t get_var_ap_count();
extern void set_var_ap_count(int32_t value);
extern const char *get_var_conn_ssid();
extern void set_var_conn_ssid(const char *value);
extern const char *get_var_pick_ssid();
extern void set_var_pick_ssid(const char *value);
extern bool get_var_g_remember();
extern void set_var_g_remember(bool value);

#ifdef __cplusplus
}
#endif

#endif /*EEZ_LVGL_UI_VARS_H*/