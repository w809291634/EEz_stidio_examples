/*
 * wifi_events.cpp — EEZ 动作回调的实现（输入 → 命令）
 *
 * 铁律：动作函数体**只投递命令**，不碰 LVGL 对象、不直接调平台。
 * 业务在 app/wifi_logic.cpp 的每拍排空里落地，真机与 PC 共用同一条链。
 */
#include "lvgl.h"
#include "wifi_model.h"
#include "../../ui/actions.h"

/******************** 事件回调 ********************/

// 函数作用：投递「开始扫描」命令。 参数：e：LVGL 事件（未使用）。 返回值：无。
void action_scan_start(lv_event_t *e)
{
    (void)e;
    app_value_t v;
    v.i = 1;
    app_set_output(APP_OUT_WIFI_SCAN, v);
}

// 函数作用：投递「连接该网络」命令（密码由 view 侧从 pwd_ta 取）。 参数：e：未使用。 返回值：无。
void action_wifi_connect(lv_event_t *e)
{
    (void)e;
    app_value_t v;
    v.i = 0;
    app_set_output(APP_OUT_WIFI_CONNECT, v);
}

// 函数作用：投递「关闭连接半页」命令。 参数：e：未使用。 返回值：无。
void action_pwd_cancel(lv_event_t *e)
{
    (void)e;
    app_value_t v;
    v.i = 0;
    app_set_output(APP_OUT_PWD_CANCEL, v);
}

// 函数作用：投递「忘记此网络」命令。 参数：e：未使用。 返回值：无。
void action_dlg_forget(lv_event_t *e)
{
    (void)e;
    app_value_t v;
    v.i = 0;
    app_set_output(APP_OUT_DLG_FORGET, v);
}

// 函数作用：投递「关闭对话框」命令。 参数：e：未使用。 返回值：无。
void action_dlg_cancel(lv_event_t *e)
{
    (void)e;
    app_value_t v;
    v.i = 0;
    app_set_output(APP_OUT_DLG_CANCEL, v);
}
