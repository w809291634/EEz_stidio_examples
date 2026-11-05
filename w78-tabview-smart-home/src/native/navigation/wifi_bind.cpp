/* wifi_bind.cpp — no-flow 下的按钮接线（示例工程里这些是 EEZ action） */
#include "lvgl.h"
#include "wifi_bind.h"
#include "app/wifi_events.h"
#include "../../ui/screens.h"

static void on_disconnect(lv_event_t *e)
{
    (void)e;
    wifi_events_request_disconnect();
}

void wifi_bind_init(void)
{
    if (objects.btn_refresh)
        lv_obj_add_event_cb(objects.btn_refresh, action_scan_start, LV_EVENT_CLICKED, NULL);
    if (objects.btn_connect)
        lv_obj_add_event_cb(objects.btn_connect, action_wifi_connect, LV_EVENT_CLICKED, NULL);
    if (objects.btn_pwd_close)
        lv_obj_add_event_cb(objects.btn_pwd_close, action_pwd_cancel, LV_EVENT_CLICKED, NULL);
    if (objects.scrim)
        lv_obj_add_event_cb(objects.scrim, action_pwd_cancel, LV_EVENT_CLICKED, NULL);
    if (objects.dlg_scrim)
        lv_obj_add_event_cb(objects.dlg_scrim, action_dlg_cancel, LV_EVENT_CLICKED, NULL);
    if (objects.btn_dlg_forget)
        lv_obj_add_event_cb(objects.btn_dlg_forget, action_dlg_forget, LV_EVENT_CLICKED, NULL);
    if (objects.btn_dlg_disconnect)
        lv_obj_add_event_cb(objects.btn_dlg_disconnect, on_disconnect, LV_EVENT_CLICKED, NULL);
    if (objects.btn_dlg_cancel)
        lv_obj_add_event_cb(objects.btn_dlg_cancel, action_dlg_cancel, LV_EVENT_CLICKED, NULL);
}
