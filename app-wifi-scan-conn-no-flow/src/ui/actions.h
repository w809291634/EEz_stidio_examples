#ifndef EEZ_LVGL_UI_EVENTS_H
#define EEZ_LVGL_UI_EVENTS_H

#include <lvgl.h>

#ifdef __cplusplus
extern "C" {
#endif

extern void action_scan_start(lv_event_t * e);
extern void action_wifi_connect(lv_event_t * e);
extern void action_pwd_cancel(lv_event_t * e);
extern void action_dlg_forget(lv_event_t * e);
extern void action_dlg_cancel(lv_event_t * e);

#ifdef __cplusplus
}
#endif

#endif /*EEZ_LVGL_UI_EVENTS_H*/