/*
 * wifi_nav.cpp — 模态显隐的实现（只动 objects.* 的可见性与标题文案）
 *
 * 为什么显隐只能在这里：EEZ 的 hiddenFlag 是**逐对象字面量**，且本工程 EEZ 侧
 * 不持有任何变量，所以整块模态必须靠 overlay_root / dlg_root 这一个父容器原子显隐
 * （kit cases/B16）。
 */
#include <stdio.h>
#include "lvgl.h"
#include "wifi_nav.h"
#include "../../ui/screens.h"

/******************** 模块私有状态与常量 ********************/

static bool s_sheet_open = false;    /* 半页是否在前台 */
static bool s_dlg_open = false;      /* 对话框是否在前台 */
static bool s_animating = false;     /* 半页动画（入场/退场）是否还在跑 */
static bool s_closing = false;       /* 退场动画进行中（结束时才真正隐藏） */
static lv_opa_t s_scrim_opa = 0;     /* 遮罩目标不透明度（首次打开时记下来） */

#define SHEET_ANIM_MS 200

/******************** 入场动画 ********************/

// 函数作用：动画执行器：改 translate_y（纯绘制位移，不动布局值）。 参数：var/v。 返回值：无。
static void anim_y_cb(void *var, int32_t v)
{
    lv_obj_set_style_translate_y((lv_obj_t *)var, v, LV_PART_MAIN);
}

// 函数作用：动画执行器：改背景不透明度。 参数：var/v。 返回值：无。
static void anim_opa_cb(void *var, int32_t v)
{
    lv_obj_set_style_bg_opa((lv_obj_t *)var, (lv_opa_t)v, LV_PART_MAIN);
}

// 函数作用：入场动画结束。 参数：a：动画。 返回值：无。
static void anim_ready_cb(lv_anim_t *a)
{
    (void)a;
    s_animating = false;
}

// 函数作用：把半页/遮罩的动画相关样式复位（关闭或互斥切走时用）。 参数：无。 返回值：无。
static void sheet_reset(void)
{
    if (objects.sheet) {
        lv_anim_delete(objects.sheet, anim_y_cb);
        lv_obj_set_style_translate_y(objects.sheet, 0, LV_PART_MAIN);
    }
    if (objects.scrim) {
        lv_anim_delete(objects.scrim, anim_opa_cb);
        if (s_scrim_opa)
            lv_obj_set_style_bg_opa(objects.scrim, s_scrim_opa, LV_PART_MAIN);
    }
    s_animating = false;
}

// 函数作用：半页入场——遮罩淡入 + 半页自底部上滑。 参数：无。 返回值：无。
static void sheet_anim_in(void)
{
    int32_t h;
    lv_anim_t a;

    if (!objects.sheet || !objects.scrim) return;
    if (!s_scrim_opa)                       /* 先记下设计值，再拿 0 起步 */
        s_scrim_opa = lv_obj_get_style_bg_opa(objects.scrim, LV_PART_MAIN);
    h = lv_obj_get_height(objects.sheet);

    lv_anim_delete(objects.sheet, anim_y_cb);
    lv_anim_delete(objects.scrim, anim_opa_cb);
    lv_obj_set_style_translate_y(objects.sheet, h, LV_PART_MAIN);   /* 起点：屏外 */
    lv_obj_set_style_bg_opa(objects.scrim, LV_OPA_TRANSP, LV_PART_MAIN);

    lv_anim_init(&a);
    lv_anim_set_var(&a, objects.sheet);
    lv_anim_set_values(&a, h, 0);
    lv_anim_set_duration(&a, SHEET_ANIM_MS);
    lv_anim_set_exec_cb(&a, anim_y_cb);
    lv_anim_set_path_cb(&a, lv_anim_path_ease_out);
    lv_anim_set_ready_cb(&a, anim_ready_cb);
    lv_anim_start(&a);
    s_animating = true;

    lv_anim_init(&a);
    lv_anim_set_var(&a, objects.scrim);
    lv_anim_set_values(&a, 0, (int32_t)s_scrim_opa);
    lv_anim_set_duration(&a, SHEET_ANIM_MS);
    lv_anim_set_exec_cb(&a, anim_opa_cb);
    lv_anim_set_path_cb(&a, lv_anim_path_ease_out);
    lv_anim_start(&a);
}

// 函数作用：退场动画结束——这时才真正隐藏整块模态。 参数：a：动画。 返回值：无。
static void anim_close_ready_cb(lv_anim_t *a)
{
    (void)a;
    if (objects.overlay_root) lv_obj_add_flag(objects.overlay_root, LV_OBJ_FLAG_HIDDEN);
    s_closing = false;
    s_animating = false;
    printf("[UI] sheet hidden\n");
}

// 函数作用：半页退场——滑下去 + 遮罩淡出（与入场对称，可被打断）。 参数：无。 返回值：无。
static void sheet_anim_out(void)
{
    int32_t h, from;
    lv_anim_t a;

    if (!objects.sheet || !objects.scrim) {          /* 没有控件就直接隐藏 */
        if (objects.overlay_root) lv_obj_add_flag(objects.overlay_root, LV_OBJ_FLAG_HIDDEN);
        s_closing = false;
        s_animating = false;
        return;
    }
    h = lv_obj_get_height(objects.sheet);
    from = lv_obj_get_style_translate_y(objects.sheet, LV_PART_MAIN);

    lv_anim_delete(objects.sheet, anim_y_cb);
    lv_anim_delete(objects.scrim, anim_opa_cb);

    lv_anim_init(&a);
    lv_anim_set_var(&a, objects.sheet);
    lv_anim_set_values(&a, from, h);
    lv_anim_set_duration(&a, SHEET_ANIM_MS);
    lv_anim_set_exec_cb(&a, anim_y_cb);
    lv_anim_set_path_cb(&a, lv_anim_path_ease_in);
    lv_anim_set_ready_cb(&a, anim_close_ready_cb);
    lv_anim_start(&a);
    s_closing = true;
    s_animating = true;

    lv_anim_init(&a);
    lv_anim_set_var(&a, objects.scrim);
    lv_anim_set_values(&a, (int32_t)lv_obj_get_style_bg_opa(objects.scrim, LV_PART_MAIN), 0);
    lv_anim_set_duration(&a, SHEET_ANIM_MS);
    lv_anim_set_exec_cb(&a, anim_opa_cb);
    lv_anim_set_path_cb(&a, lv_anim_path_ease_in);
    lv_anim_start(&a);
}

/******************** 对外初始化与公开接口 ********************/

// 函数作用：查询半页是否在前台。 参数：无。 返回值：true 表示显示中。
bool wifi_nav_sheet_open(void) { return s_sheet_open; }

// 函数作用：查询对话框是否在前台。 参数：无。 返回值：true 表示显示中。
bool wifi_nav_dialog_open(void) { return s_dlg_open; }

// 函数作用：半页入场动画是否还在跑。 参数：无。 返回值：true 表示动画中。
bool wifi_nav_animating(void) { return s_animating; }

// 函数作用：打开连接半页并填标题，同时关掉对话框（模态互斥）。
//          参数：ssid：目标网络名。 返回值：无。
void wifi_nav_open_sheet(const char *ssid)
{
    if (!objects.overlay_root) return;
    if (ssid && objects.lbl_pwd_ssid) lv_label_set_text(objects.lbl_pwd_ssid, ssid);
    if (objects.pwd_ta) lv_textarea_set_text(objects.pwd_ta, "");
    s_dlg_open = false;
    if (objects.dlg_root) lv_obj_add_flag(objects.dlg_root, LV_OBJ_FLAG_HIDDEN);
    s_sheet_open = true;
    s_closing = false;                       /* 退场途中又被打开：以这次为准 */
    lv_obj_remove_flag(objects.overlay_root, LV_OBJ_FLAG_HIDDEN);
    sheet_anim_in();
    printf("[UI] sheet open: %s\n", ssid ? ssid : "");
}

// 函数作用：关闭连接半页。 参数：无。 返回值：无（未打开时不动，避免重复日志）。
void wifi_nav_close_sheet(void)
{
    if (!s_sheet_open) return;
    s_sheet_open = false;                    /* 逻辑上立刻算关闭；视觉上等动画收尾 */
    sheet_anim_out();
    printf("[UI] sheet close\n");
}

// 函数作用：打开「忘记此网络」对话框并填 SSID，同时关掉半页。 参数：ssid：目标网络名。 返回值：无。
void wifi_nav_open_dialog(const char *ssid)
{
    if (!objects.dlg_root) return;
    if (ssid && objects.lbl_dlg_ssid) lv_label_set_text(objects.lbl_dlg_ssid, ssid);
    s_sheet_open = false;
    sheet_reset();                           /* 互斥切走：取消退场动画并立刻隐藏 */
    s_closing = false;
    if (objects.overlay_root) lv_obj_add_flag(objects.overlay_root, LV_OBJ_FLAG_HIDDEN);
    s_dlg_open = true;
    lv_obj_remove_flag(objects.dlg_root, LV_OBJ_FLAG_HIDDEN);
    printf("[UI] dialog open: %s\n", ssid ? ssid : "");
}

// 函数作用：关闭对话框。 参数：无。 返回值：无。
void wifi_nav_close_dialog(void)
{
    if (!s_dlg_open) return;
    s_dlg_open = false;
    if (objects.dlg_root) lv_obj_add_flag(objects.dlg_root, LV_OBJ_FLAG_HIDDEN);
    printf("[UI] dialog close\n");
}
