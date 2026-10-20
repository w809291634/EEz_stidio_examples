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
    lv_obj_t *tv_pages;
    lv_obj_t *tab_drop;
    lv_obj_t *obj0;
    lv_obj_t *dd_main;
    lv_obj_t *lbl_dd;
    lv_obj_t *obj1;
    lv_obj_t *tab_roll;
    lv_obj_t *obj2;
    lv_obj_t *roller_main;
    lv_obj_t *lbl_roll;
    lv_obj_t *obj3;
    lv_obj_t *tab_sw;
    lv_obj_t *obj4;
    lv_obj_t *sw_off;
    lv_obj_t *sw_on;
    lv_obj_t *obj5;
    lv_obj_t *obj6;
    lv_obj_t *obj7;
    lv_obj_t *tab_chk;
    lv_obj_t *obj8;
    lv_obj_t *chk_a;
    lv_obj_t *chk_b;
    lv_obj_t *obj9;
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