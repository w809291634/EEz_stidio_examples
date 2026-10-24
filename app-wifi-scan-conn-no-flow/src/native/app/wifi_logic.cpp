/*
 * wifi_logic.cpp — 初始化 + 每拍调度（本层不读 objects.*）
 *
 * 分工：命令在这里分发，但**去向**交给 navigation、**回显**交给 view、
 * **硬件动作**交给 platform；本文件因此可以脱离 LVGL 单测。
 */
#include <stdio.h>
#include "wifi_logic.h"
#include "wifi_model.h"
#include "wifi_view.h"
#include "navigation/wifi_nav.h"
#include "widgets/wifi_busy/wifi_busy.h"   /* 连接中的全屏转圈 */
#include "platform/wifi_platform.h"

/******************** 模块私有小工具 ********************/

// 函数作用：字符串里有没有可见字符（纯空白也算空）。 参数：s。 返回值：1=有。
static int has_visible_char(const char *s)
{
    for (; s && *s; s++)
        if ((unsigned char)*s > ' ') return 1;
    return 0;
}

/******************** 对外初始化与调度 ********************/

// 函数作用：初始化平台后端（发布初始文案与扫描态）。 参数：无。 返回值：无。
void user_io_init(void)
{
    io_init();
}

// 函数作用：每拍排空命令环、推进平台状态、请求视图刷新。 参数：无。 返回值：无。
void user_io_tick(void)
{
    app_output_id_t id;
    app_value_t v;
    char pwd[APP_IN_STR_MAX];

    while (app_pop_output(&id, &v)) {
        switch (id) {
        case APP_OUT_WIFI_SCAN: io_wifi_scan(v.i); break;
        case APP_OUT_WIFI_CONNECT: {
            /* 密码只能由 view 层从 objects.pwd_ta 取（本层不碰 objects）；
             * 直连场景（已保存/开放网络）pwd 为空串，后端自己判断要不要存密码。
             * 交互口径（用户 2026-10-24 定）：点「连接」→ 收半页 → 全屏转圈锁住操作，
             * 结果出来才收圈，标题栏写「已连接 / 连接失败 X」。 */
            const char *sel = app_get_input_s(APP_IN_SEL_SSID);
            const char *pw = wifi_view_password(pwd, (int)sizeof(pwd));
            char busy[APP_IN_STR_MAX];

            /* 用户口径（2026-10-24）：半页路径密码不能空——空密码连它注定失败，
             * 还白转一圈圈。就地提示，不关窗、不发起连接。 */
            if (wifi_nav_sheet_open() && !has_visible_char(pw)) {
                app_set_input_s(APP_IN_SCAN_STATUS, "请输入密码");
                break;
            }
            io_wifi_connect(sel, pw);
            wifi_nav_close_sheet();
            snprintf(busy, sizeof(busy), "正在连接 %s…", sel);
            wifi_busy_show(busy);
            break;
        }
        case APP_OUT_PWD_CANCEL: wifi_nav_close_sheet(); break;
        case APP_OUT_DLG_FORGET:
            io_wifi_forget(app_get_input_s(APP_IN_SEL_SSID));
            wifi_nav_close_dialog();
            break;
        case APP_OUT_DLG_CANCEL: wifi_nav_close_dialog(); break;
        default: break;
        }
    }
    io_sample_inputs();

    /* 后端报的连接结果在这里消费掉：无论成败都收起转圈，文案由后端已写好。 */
    switch ((int)app_get_input_i(APP_IN_CONN_STATE)) {
    case 2:
    case 3:
        wifi_busy_hide();
        app_set_input_i(APP_IN_CONN_STATE, 0);
        break;
    default: break;
    }

    wifi_view_sync();
}
