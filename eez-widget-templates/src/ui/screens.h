#ifndef EEZ_LVGL_UI_SCREENS_H
#define EEZ_LVGL_UI_SCREENS_H

#include <lvgl.h>

#ifdef __cplusplus
extern "C" {
#endif

// Screens

enum ScreensEnum {
    _SCREEN_ID_FIRST = 1,
    SCREEN_ID_TPL_LABEL = 1,
    SCREEN_ID_TPL_BUTTON = 2,
    SCREEN_ID_TPL_CONTAINER = 3,
    SCREEN_ID_TPL_PANEL = 4,
    SCREEN_ID_TPL_SWITCH = 5,
    SCREEN_ID_TPL_SLIDER = 6,
    SCREEN_ID_TPL_BAR = 7,
    SCREEN_ID_TPL_ARC = 8,
    SCREEN_ID_TPL_CHART = 9,
    SCREEN_ID_TPL_SCALE = 10,
    SCREEN_ID_TPL_LED = 11,
    SCREEN_ID_TPL_CHECKBOX = 12,
    SCREEN_ID_TPL_DROPDOWN = 13,
    SCREEN_ID_TPL_ROLLER = 14,
    SCREEN_ID_TPL_TEXTAREA = 15,
    SCREEN_ID_TPL_KEYBOARD = 16,
    SCREEN_ID_TPL_LIST = 17,
    SCREEN_ID_TPL_SPINNER = 18,
    _SCREEN_ID_LAST = 18
};

typedef struct _objects_t {
    lv_obj_t *tpl_label;
    lv_obj_t *tpl_button;
    lv_obj_t *tpl_container;
    lv_obj_t *tpl_panel;
    lv_obj_t *tpl_switch;
    lv_obj_t *tpl_slider;
    lv_obj_t *tpl_bar;
    lv_obj_t *tpl_arc;
    lv_obj_t *tpl_chart;
    lv_obj_t *tpl_scale;
    lv_obj_t *tpl_led;
    lv_obj_t *tpl_checkbox;
    lv_obj_t *tpl_dropdown;
    lv_obj_t *tpl_roller;
    lv_obj_t *tpl_textarea;
    lv_obj_t *tpl_keyboard;
    lv_obj_t *tpl_list;
    lv_obj_t *tpl_spinner;
    lv_obj_t *w_label;
    lv_obj_t *w_button;
    lv_obj_t *tpl_button_label;
    lv_obj_t *w_container;
    lv_obj_t *w_panel;
    lv_obj_t *w_switch;
    lv_obj_t *w_slider;
    lv_obj_t *w_bar;
    lv_obj_t *w_arc;
    lv_obj_t *w_chart;
    lv_obj_t *w_scale;
    lv_obj_t *w_led;
    lv_obj_t *w_checkbox;
    lv_obj_t *w_dropdown;
    lv_obj_t *w_roller;
    lv_obj_t *w_textarea;
    lv_obj_t *w_keyboard;
    lv_obj_t *w_list;
    lv_obj_t *w_spinner;
} objects_t;

extern objects_t objects;

void create_screen_tpl_label();
void tick_screen_tpl_label();

void create_screen_tpl_button();
void tick_screen_tpl_button();

void create_screen_tpl_container();
void tick_screen_tpl_container();

void create_screen_tpl_panel();
void tick_screen_tpl_panel();

void create_screen_tpl_switch();
void tick_screen_tpl_switch();

void create_screen_tpl_slider();
void tick_screen_tpl_slider();

void create_screen_tpl_bar();
void tick_screen_tpl_bar();

void create_screen_tpl_arc();
void tick_screen_tpl_arc();

void create_screen_tpl_chart();
void tick_screen_tpl_chart();

void create_screen_tpl_scale();
void tick_screen_tpl_scale();

void create_screen_tpl_led();
void tick_screen_tpl_led();

void create_screen_tpl_checkbox();
void tick_screen_tpl_checkbox();

void create_screen_tpl_dropdown();
void tick_screen_tpl_dropdown();

void create_screen_tpl_roller();
void tick_screen_tpl_roller();

void create_screen_tpl_textarea();
void tick_screen_tpl_textarea();

void create_screen_tpl_keyboard();
void tick_screen_tpl_keyboard();

void create_screen_tpl_list();
void tick_screen_tpl_list();

void create_screen_tpl_spinner();
void tick_screen_tpl_spinner();

void tick_screen_by_id(enum ScreensEnum screenId);
void tick_screen(int screen_index);

void create_screens();

#ifdef __cplusplus
}
#endif

#endif /*EEZ_LVGL_UI_SCREENS_H*/