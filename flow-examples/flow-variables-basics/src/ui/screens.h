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
    lv_obj_t *cap_count;
    lv_obj_t *val_count;
    lv_obj_t *val_tpl;
    lv_obj_t *cap_status;
    lv_obj_t *val_status;
    lv_obj_t *cap_bar;
    lv_obj_t *bar_count;
    lv_obj_t *cap_sld;
    lv_obj_t *sld_count;
    lv_obj_t *btn_add;
    lv_obj_t *obj0;
    lv_obj_t *btn_many;
    lv_obj_t *obj1;
    lv_obj_t *btn_eval;
    lv_obj_t *obj2;
    lv_obj_t *btn_local;
    lv_obj_t *obj3;
    lv_obj_t *cap_flow;
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