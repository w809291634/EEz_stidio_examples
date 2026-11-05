/*
 * wifi_events.cpp — 输入 → 命令（唯一出口）
 *
 * 铁律：本文件只写"选中哪条网络"和投递命令，不碰 LVGL 对象、不直接调平台。
 * 业务在 app/wifi_logic.cpp 的每拍排空里落地，PC 与真机共用同一条链。
 */
#include <string.h>
#include "wifi_events.h"
#include "wifi_model.h"
#include "../../ui/actions.h"

/******************** 事件回调 ********************/

// 函数作用：记下本次操作针对哪个网络（行手势与按钮动作共用）。
//          参数：ssid：网络名，NULL 视为空。 返回值：无。
void wifi_events_select(const char *ssid)
{
    app_set_input_s(APP_IN_SEL_SSID, ssid ? ssid : "");
}

// 函数作用：投递「连接选中网络」命令。 参数：无。 返回值：无。
void wifi_events_request_connect(void)
{
    app_value_t v;
    v.i = 0;
    app_set_output(APP_OUT_WIFI_CONNECT, v);
}

// 函数作用：投递「断开选中网络」命令。 参数：无。 返回值：无。
void wifi_events_request_disconnect(void)
{
    app_value_t v;
    v.i = 0;
    app_set_output(APP_OUT_WIFI_DISCONNECT, v);
}

// 函数作用：投递「开始扫描」命令。 参数：e：LVGL 事件（未使用）。 返回值：无。
void action_scan_start(lv_event_t *e)
{
    (void)e;
    app_value_t v;
    v.i = 1;
    app_set_output(APP_OUT_WIFI_SCAN, v);
}

// 函数作用：半页「连 接」→ 投递连接命令（目标已由开半页时记下）。 参数：e：未使用。 返回值：无。
void action_wifi_connect(lv_event_t *e)
{
    (void)e;
    wifi_events_request_connect();
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

// 函数作用：对话框「断 开」→ 投递断开命令。 参数：e：未使用。 返回值：无。
void action_wifi_disconnect(lv_event_t *e)
{
    (void)e;
    wifi_events_request_disconnect();
}

// 函数作用：投递「关闭对话框」命令。 参数：e：未使用。 返回值：无。
void action_dlg_cancel(lv_event_t *e)
{
    (void)e;
    app_value_t v;
    v.i = 0;
    app_set_output(APP_OUT_DLG_CANCEL, v);
}
