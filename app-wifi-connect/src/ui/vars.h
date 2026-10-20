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
extern int32_t get_var_ap_count();
extern void set_var_ap_count(int32_t value);
extern int32_t get_var_wifi_state();
extern void set_var_wifi_state(int32_t value);
extern const char *get_var_wifi_conn_ssid();
extern void set_var_wifi_conn_ssid(const char *value);
extern int32_t get_var_g_pick();
extern void set_var_g_pick(int32_t value);
extern const char *get_var_g_pick_ssid();
extern void set_var_g_pick_ssid(const char *value);
extern bool get_var_g_remember();
extern void set_var_g_remember(bool value);
extern const char *get_var_saved_ssid();
extern void set_var_saved_ssid(const char *value);
extern const char *get_var_wifi_slot0_ssid();
extern void set_var_wifi_slot0_ssid(const char *value);
extern int32_t get_var_wifi_slot0_rssi();
extern void set_var_wifi_slot0_rssi(int32_t value);
extern bool get_var_wifi_slot0_lock();
extern void set_var_wifi_slot0_lock(bool value);
extern const char *get_var_wifi_slot1_ssid();
extern void set_var_wifi_slot1_ssid(const char *value);
extern int32_t get_var_wifi_slot1_rssi();
extern void set_var_wifi_slot1_rssi(int32_t value);
extern bool get_var_wifi_slot1_lock();
extern void set_var_wifi_slot1_lock(bool value);
extern const char *get_var_wifi_slot2_ssid();
extern void set_var_wifi_slot2_ssid(const char *value);
extern int32_t get_var_wifi_slot2_rssi();
extern void set_var_wifi_slot2_rssi(int32_t value);
extern bool get_var_wifi_slot2_lock();
extern void set_var_wifi_slot2_lock(bool value);
extern const char *get_var_wifi_slot3_ssid();
extern void set_var_wifi_slot3_ssid(const char *value);
extern int32_t get_var_wifi_slot3_rssi();
extern void set_var_wifi_slot3_rssi(int32_t value);
extern bool get_var_wifi_slot3_lock();
extern void set_var_wifi_slot3_lock(bool value);
extern const char *get_var_wifi_slot4_ssid();
extern void set_var_wifi_slot4_ssid(const char *value);
extern int32_t get_var_wifi_slot4_rssi();
extern void set_var_wifi_slot4_rssi(int32_t value);
extern bool get_var_wifi_slot4_lock();
extern void set_var_wifi_slot4_lock(bool value);
extern const char *get_var_wifi_slot5_ssid();
extern void set_var_wifi_slot5_ssid(const char *value);
extern int32_t get_var_wifi_slot5_rssi();
extern void set_var_wifi_slot5_rssi(int32_t value);
extern bool get_var_wifi_slot5_lock();
extern void set_var_wifi_slot5_lock(bool value);

#ifdef __cplusplus
}
#endif

#endif /*EEZ_LVGL_UI_VARS_H*/