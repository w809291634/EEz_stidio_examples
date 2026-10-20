#ifndef EEZ_LVGL_UI_EVENTS_H
#define EEZ_LVGL_UI_EVENTS_H

#include <lvgl.h>

#ifdef __cplusplus
extern "C" {
#endif

extern void action_scan_start(lv_event_t * e);
extern void action_wifi_connect(lv_event_t * e);
extern void action_chk_remember(lv_event_t * e);
extern void action_panel_cancel(lv_event_t * e);
extern void action_wifi_pick_0(lv_event_t * e);
extern void action_wifi_pick_1(lv_event_t * e);
extern void action_wifi_pick_2(lv_event_t * e);
extern void action_wifi_pick_3(lv_event_t * e);
extern void action_wifi_pick_4(lv_event_t * e);
extern void action_wifi_pick_5(lv_event_t * e);

#ifdef __cplusplus
}
#endif

#endif /*EEZ_LVGL_UI_EVENTS_H*/