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
    lv_obj_t *lbl_status;
    lv_obj_t *btn_refresh;
    lv_obj_t *obj0;
    lv_obj_t *list_box;
    lv_obj_t *row_1;
    lv_obj_t *bar_1_1;
    lv_obj_t *bar_1_2;
    lv_obj_t *bar_1_3;
    lv_obj_t *bar_1_4;
    lv_obj_t *lbl_ssid_1;
    lv_obj_t *lbl_meta_1;
    lv_obj_t *lbl_state_1;
    lv_obj_t *row_2;
    lv_obj_t *bar_2_1;
    lv_obj_t *bar_2_2;
    lv_obj_t *bar_2_3;
    lv_obj_t *bar_2_4;
    lv_obj_t *lbl_ssid_2;
    lv_obj_t *lbl_meta_2;
    lv_obj_t *lbl_state_2;
    lv_obj_t *row_3;
    lv_obj_t *bar_3_1;
    lv_obj_t *bar_3_2;
    lv_obj_t *bar_3_3;
    lv_obj_t *bar_3_4;
    lv_obj_t *lbl_ssid_3;
    lv_obj_t *lbl_meta_3;
    lv_obj_t *lbl_state_3;
    lv_obj_t *row_4;
    lv_obj_t *bar_4_1;
    lv_obj_t *bar_4_2;
    lv_obj_t *bar_4_3;
    lv_obj_t *bar_4_4;
    lv_obj_t *lbl_ssid_4;
    lv_obj_t *lbl_meta_4;
    lv_obj_t *lbl_state_4;
    lv_obj_t *row_5;
    lv_obj_t *bar_5_1;
    lv_obj_t *bar_5_2;
    lv_obj_t *bar_5_3;
    lv_obj_t *bar_5_4;
    lv_obj_t *lbl_ssid_5;
    lv_obj_t *lbl_meta_5;
    lv_obj_t *lbl_state_5;
    lv_obj_t *row_6;
    lv_obj_t *bar_6_1;
    lv_obj_t *bar_6_2;
    lv_obj_t *bar_6_3;
    lv_obj_t *bar_6_4;
    lv_obj_t *lbl_ssid_6;
    lv_obj_t *lbl_meta_6;
    lv_obj_t *lbl_state_6;
    lv_obj_t *row_7;
    lv_obj_t *bar_7_1;
    lv_obj_t *bar_7_2;
    lv_obj_t *bar_7_3;
    lv_obj_t *bar_7_4;
    lv_obj_t *lbl_ssid_7;
    lv_obj_t *lbl_meta_7;
    lv_obj_t *lbl_state_7;
    lv_obj_t *row_8;
    lv_obj_t *bar_8_1;
    lv_obj_t *bar_8_2;
    lv_obj_t *bar_8_3;
    lv_obj_t *bar_8_4;
    lv_obj_t *lbl_ssid_8;
    lv_obj_t *lbl_meta_8;
    lv_obj_t *lbl_state_8;
    lv_obj_t *row_9;
    lv_obj_t *bar_9_1;
    lv_obj_t *bar_9_2;
    lv_obj_t *bar_9_3;
    lv_obj_t *bar_9_4;
    lv_obj_t *lbl_ssid_9;
    lv_obj_t *lbl_meta_9;
    lv_obj_t *lbl_state_9;
    lv_obj_t *row_10;
    lv_obj_t *bar_10_1;
    lv_obj_t *bar_10_2;
    lv_obj_t *bar_10_3;
    lv_obj_t *bar_10_4;
    lv_obj_t *lbl_ssid_10;
    lv_obj_t *lbl_meta_10;
    lv_obj_t *lbl_state_10;
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