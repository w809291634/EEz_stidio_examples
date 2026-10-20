/*
 * native_actions.cpp — EEZ 动作实现。
 * 铁律：动作函数体只投递命令，业务在 io 层的 user_io_tick 排空里。
 */
#include "lvgl.h"
#include "app_model.h"
#include "../ui/actions.h"

void action_scan_start(lv_event_t *e)
{
    (void)e;
    app_value_t v;
    v.i = 1;
    app_set_output(APP_OUT_WIFI_SCAN, v);
}
