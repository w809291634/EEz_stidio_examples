/*
 * native_actions.cpp — EEZ 动作实现。
 * ★ 铁律（KB reference/10 §3）：动作函数体只有一行投递（app_set_output /
 *   app_set_input），不写业务分支、不碰驱动——业务在 io 层的 user_io_tick 排空里。
 * 唯一例外：wifi_connect 需要从密码框取键盘输入（LVGL 侧数据），捕获进
 *   APP_IN_PWD 后投递 JOIN，io 层连接时取用。
 */
#include "lvgl.h"
#include "app_model.h"

/* EEZ 生成 actions.h 声明的是 action_xxx(lv_event_t*)，这里按需再包一层 */
#include "../ui/actions.h"
#include "../ui/screens.h"   /* objects.pwd_ta */
#include "../ui/screens.h"   /* objects.pwd_ta */

void action_scan_start(lv_event_t *e)
{
    (void)e;
    app_value_t v; v.i = 1;
    app_set_output(APP_OUT_WIFI_SCAN, v);
}


void action_wifi_connect(lv_event_t *e)
{
    (void)e;
    /* 键盘输入在密码框里（textarea 不绑变量，input 型绑定会被 tick 覆盖打字），
       在这里捕获进契约，io 层连接时取用 */
    app_set_input_s(APP_IN_PWD, lv_textarea_get_text(objects.pwd_ta));
    app_value_t v; v.i = 1;
    app_set_output(APP_OUT_WIFI_JOIN, v);
}

void action_panel_cancel(lv_event_t *e)
{
    (void)e;
    app_set_input_s(APP_IN_PICK_SSID, "");   /* 清选中 → 面板 hiddenFlag 生效 */
}

void action_chk_remember(lv_event_t *e)
{
    (void)e;
    app_value_t v; v.i = 1;
    app_set_output(APP_OUT_REMEMBER_TOGGLE, v);
}
