#ifndef EEZ_LVGL_UI_SCREENS_H
#define EEZ_LVGL_UI_SCREENS_H

#include <lvgl.h>

#ifdef __cplusplus
extern "C" {
#endif

// Screens

enum ScreensEnum {
    _SCREEN_ID_FIRST = 1,
    SCREEN_ID_A = 1,
    SCREEN_ID_B = 2,
    SCREEN_ID_C = 3,
    _SCREEN_ID_LAST = 3
};

typedef struct _objects_t {
    lv_obj_t *a;
    lv_obj_t *b;
    lv_obj_t *c;
    lv_obj_t *host_a;
    lv_obj_t *a_title;
    lv_obj_t *a_hint;
    lv_obj_t *host_b;
    lv_obj_t *b_title;
    lv_obj_t *b_hint;
    lv_obj_t *host_c;
    lv_obj_t *c_title;
    lv_obj_t *c_hint;
} objects_t;

extern objects_t objects;

void create_screen_a();
void tick_screen_a();

void create_screen_b();
void tick_screen_b();

void create_screen_c();
void tick_screen_c();

void tick_screen_by_id(enum ScreensEnum screenId);
void tick_screen(int screen_index);

void create_screens();

#ifdef __cplusplus
}
#endif

#endif /*EEZ_LVGL_UI_SCREENS_H*/