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
    lv_obj_t *overlay_root;
    lv_obj_t *scrim;
    lv_obj_t *sheet;
    lv_obj_t *sheet_handle;
    lv_obj_t *lbl_pwd_ssid;
    lv_obj_t *btn_pwd_close;
    lv_obj_t *obj1;
    lv_obj_t *pwd_ta;
    lv_obj_t *btn_connect;
    lv_obj_t *obj2;
    lv_obj_t *kb_main;
    lv_obj_t *dlg_root;
    lv_obj_t *dlg_scrim;
    lv_obj_t *dlg_card;
    lv_obj_t *lbl_dlg_title;
    lv_obj_t *lbl_dlg_ssid;
    lv_obj_t *lbl_dlg_hint;
    lv_obj_t *btn_dlg_forget;
    lv_obj_t *obj3;
    lv_obj_t *btn_dlg_cancel;
    lv_obj_t *obj4;
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