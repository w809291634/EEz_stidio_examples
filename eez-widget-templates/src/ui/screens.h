#ifndef EEZ_LVGL_UI_SCREENS_H
#define EEZ_LVGL_UI_SCREENS_H

#include <lvgl/lvgl.h>

#ifdef __cplusplus
extern "C" {
#endif

// Screens

enum ScreensEnum {
    _SCREEN_ID_FIRST = 1,
    SCREEN_ID_LABEL = 1,
    SCREEN_ID_BUTTON = 2,
    SCREEN_ID_SWITCH = 3,
    SCREEN_ID_ARC = 4,
    SCREEN_ID_BAR = 5,
    SCREEN_ID_CHART = 6,
    SCREEN_ID_CHECKBOX = 7,
    SCREEN_ID_CONTAINER = 8,
    SCREEN_ID_DROPDOWN = 9,
    SCREEN_ID_KEYBOARD = 10,
    SCREEN_ID_LED = 11,
    SCREEN_ID_LIST = 12,
    SCREEN_ID_PANEL = 13,
    SCREEN_ID_ROLLER = 14,
    SCREEN_ID_SCALE = 15,
    SCREEN_ID_SLIDER = 16,
    SCREEN_ID_SPINNER = 17,
    SCREEN_ID_TEXTAREA = 18,
    _SCREEN_ID_LAST = 18
};

typedef struct _objects_t {
    lv_obj_t *label;
    lv_obj_t *button;
    lv_obj_t *switch;
    lv_obj_t *arc;
    lv_obj_t *bar;
    lv_obj_t *chart;
    lv_obj_t *checkbox;
    lv_obj_t *container;
    lv_obj_t *dropdown;
    lv_obj_t *keyboard;
    lv_obj_t *led;
    lv_obj_t *list;
    lv_obj_t *panel;
    lv_obj_t *roller;
    lv_obj_t *scale;
    lv_obj_t *slider;
    lv_obj_t *spinner;
    lv_obj_t *textarea;
    lv_obj_t *obj0;
    lv_obj_t *obj1;
} objects_t;

extern objects_t objects;

void create_screen_label();
void tick_screen_label();

void create_screen_button();
void tick_screen_button();

void create_screen_switch();
void tick_screen_switch();

void create_screen_arc();
void tick_screen_arc();

void create_screen_bar();
void tick_screen_bar();

void create_screen_chart();
void tick_screen_chart();

void create_screen_checkbox();
void tick_screen_checkbox();

void create_screen_container();
void tick_screen_container();

void create_screen_dropdown();
void tick_screen_dropdown();

void create_screen_keyboard();
void tick_screen_keyboard();

void create_screen_led();
void tick_screen_led();

void create_screen_list();
void tick_screen_list();

void create_screen_panel();
void tick_screen_panel();

void create_screen_roller();
void tick_screen_roller();

void create_screen_scale();
void tick_screen_scale();

void create_screen_slider();
void tick_screen_slider();

void create_screen_spinner();
void tick_screen_spinner();

void create_screen_textarea();
void tick_screen_textarea();

void tick_screen_by_id(enum ScreensEnum screenId);
void tick_screen(int screen_index);

void create_screens();

#ifdef __cplusplus
}
#endif

#endif /*EEZ_LVGL_UI_SCREENS_H*/