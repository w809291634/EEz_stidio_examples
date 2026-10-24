/*
 * wifi_view.cpp — 扫描态文案与刷新按钮的投影（只读 model/平台快照，只写 objects.*）
 *
 * 分层口径（kit reference/12 轻量版）：本层不改业务真值、不建行、不管显隐。
 * 行在 widgets/wifi_list，模态去向在 navigation/wifi_nav。
 */
#include "lvgl.h"
#include "wifi_view.h"
#include "wifi_model.h"
#include "platform/wifi_platform.h"       /* wifi_ap_gen：列表内容代数 */
#include "widgets/wifi_list/wifi_list.h"
#include "../../ui/screens.h"

/******************** 模块私有状态与常量 ********************/

static int s_last_gen = -1;      /* 已渲染的列表代数 */
static int s_last_state = -1;    /* 已回显的扫描态 */

/******************** 对外初始化与公开接口 ********************/

// 函数作用：把扫描态投影到标题文案与刷新按钮，并在代数变化时请求重建列表。
//          参数：无。 返回值：无。
void wifi_view_sync(void)
{
    if (!objects.list_box || !objects.lbl_status || !objects.btn_refresh)
        return;

    int gen = wifi_ap_gen();   /* 内容代数（io 层 publish +1） */
    int state = (int)app_get_input_i(APP_IN_SCAN_STATE);

    /* 状态文案 + 刷新按钮（状态变化时更新一次即可） */
    if (state != s_last_state) {
        lv_label_set_text(objects.lbl_status, app_get_input_s(APP_IN_SCAN_STATUS));
        lv_obj_t *bl = lv_obj_get_child(objects.btn_refresh, 0);
        if (bl) lv_label_set_text(bl, state == 1 ? "扫描中" : "刷 新");
        if (state == 1)
            lv_obj_remove_flag(objects.btn_refresh, LV_OBJ_FLAG_CLICKABLE);
        else
            lv_obj_add_flag(objects.btn_refresh, LV_OBJ_FLAG_CLICKABLE);
        s_last_state = state;
    }

    /* 内容没变（gen 不变）就不重建——避免每拍 clean/add 抖动 */
    if (gen == s_last_gen) return;

    wifi_list_rebuild(state);
    s_last_gen = gen;
}
