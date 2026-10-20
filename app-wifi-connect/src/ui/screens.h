#ifndef EEZ_LVGL_UI_SCREENS_H
#define EEZ_LVGL_UI_SCREENS_H

#include <lvgl.h>

#ifdef __cplusplus
extern "C" {
#endif

// Screens

enum ScreensEnum {
    _SCREEN_ID_FIRST = 1,
    SCREEN_ID_MAIN = 1,
    _SCREEN_ID_LAST = 1
};

typedef struct _objects_t {
    lv_obj_t *main;
    lv_obj_t *lbl_title;
    lv_obj_t *lbl_scan;
    lv_obj_t *btn_refresh;
    lv_obj_t *obj0;
    lv_obj_t *lbl_ssid_0;
    lv_obj_t *lbl_lock_0;
    lv_obj_t *lbl_rssi_0;
    lv_obj_t *lbl_conn_0;
    lv_obj_t *hit_0;
    lv_obj_t *lbl_ssid_1;
    lv_obj_t *lbl_lock_1;
    lv_obj_t *lbl_rssi_1;
    lv_obj_t *lbl_conn_1;
    lv_obj_t *hit_1;
    lv_obj_t *lbl_ssid_2;
    lv_obj_t *lbl_lock_2;
    lv_obj_t *lbl_rssi_2;
    lv_obj_t *lbl_conn_2;
    lv_obj_t *hit_2;
    lv_obj_t *lbl_ssid_3;
    lv_obj_t *lbl_lock_3;
    lv_obj_t *lbl_rssi_3;
    lv_obj_t *lbl_conn_3;
    lv_obj_t *hit_3;
    lv_obj_t *lbl_ssid_4;
    lv_obj_t *lbl_lock_4;
    lv_obj_t *lbl_rssi_4;
    lv_obj_t *lbl_conn_4;
    lv_obj_t *hit_4;
    lv_obj_t *lbl_ssid_5;
    lv_obj_t *lbl_lock_5;
    lv_obj_t *lbl_rssi_5;
    lv_obj_t *lbl_conn_5;
    lv_obj_t *hit_5;
    lv_obj_t *lbl_state;
    lv_obj_t *panel_pwd;
    lv_obj_t *lbl_panel_title;
    lv_obj_t *pwd_ta;
    lv_obj_t *kb_main;
    lv_obj_t *lbl_remember;
    lv_obj_t *btn_connect;
    lv_obj_t *obj1;
    lv_obj_t *btn_cancel;
    lv_obj_t *obj2;
} objects_t;

extern objects_t objects;

void create_screen_main();
void tick_screen_main();

void tick_screen_by_id(enum ScreensEnum screenId);
void tick_screen(int screen_index);

void create_screens();

#ifdef __cplusplus
}
#endif

#endif /*EEZ_LVGL_UI_SCREENS_H*/