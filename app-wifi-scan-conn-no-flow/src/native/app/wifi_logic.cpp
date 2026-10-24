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
#include "platform/wifi_platform.h"

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
    while (app_pop_output(&id, &v)) {
        switch (id) {
        case APP_OUT_WIFI_SCAN: io_wifi_scan(v.i); break;
        /* ⑦-1 只做导航闭环：关闭类命令在这里落地；
         * 需要后端的（真连/真忘记）仍留 TODO，但要先让界面退得出去。 */
        case APP_OUT_WIFI_CONNECT:            /* TODO(⑦-2): io_wifi_connect(ssid, pwd) */
            printf("[CMD] wifi_connect（后端未接，⑦-2）\n");
            break;
        case APP_OUT_PWD_CANCEL: wifi_nav_close_sheet(); break;
        case APP_OUT_DLG_FORGET:                      /* TODO(⑦-2): io_wifi_forget(ssid) */
            printf("[CMD] dlg_forget（后端未接，⑦-2）\n");
            wifi_nav_close_dialog();
            break;
        case APP_OUT_DLG_CANCEL: wifi_nav_close_dialog(); break;
        default: break;
        }
    }
    io_sample_inputs();
    wifi_view_sync();
}
