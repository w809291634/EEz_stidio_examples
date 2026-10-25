/*
 * wifi_busy.cpp — 「连接中」全屏遮罩 + 转圈（见 wifi_busy.h）
 *
 * 口径（用户 2026-10-24 定）：点「连接」后半页收起，改由这层盖住整屏转圈，
 * 期间不可操作；连上或失败都收遮罩，结果写标题栏。
 */
#include <stdio.h>
#include "lvgl.h"
#include "wifi_busy.h"
#include "widgets/wifi_skin.h"
#include "../../../ui/screens.h"
#include "../../../ui/fonts.h"

/******************** 模块私有状态与常量 ********************/

/* 遮罩/转圈的参数在 widgets/wifi_skin.h */

static lv_obj_t *s_root;         /* 整屏遮罩（懒建，避免和 EEZ 建屏顺序耦合） */
static lv_obj_t *s_lbl;

/******************** 对外初始化与公开接口 ********************/

// 函数作用：懒建遮罩 + 转圈 + 文案；建在 objects.main 最上层。 参数：无。 返回值：根对象。
static lv_obj_t *ensure_root(void)
{
    if (s_root) return s_root;
    if (!objects.main) return NULL;

    s_root = lv_obj_create(objects.main);
    /* ★ 顺序不能反：lv_obj_remove_style_all() 会把 local style 一起删掉，
     *   而 width/height 就是 local style——先设尺寸再清样式，遮罩会变成 0×0，
     *   hit test 全穿过去，"期间不可操作"就是句空话（[NAV] 断言抓到过）。 */
    lv_obj_remove_style_all(s_root);
    lv_obj_set_size(s_root, LV_HOR_RES, LV_VER_RES);
    lv_obj_set_pos(s_root, 0, 0);
    lv_obj_set_style_bg_color(s_root, lv_color_hex(C_MASK), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(s_root, MASK_OPA, LV_PART_MAIN);
    lv_obj_remove_flag(s_root, LV_OBJ_FLAG_SCROLLABLE);
    /* ★ CLICKABLE 是"期间不可操作"的全部机制：hit test 停在这层，
     *   下面的列表 / 半页 / 对话框都收不到事件（不靠逐个禁用控件）。 */
    lv_obj_add_flag(s_root, LV_OBJ_FLAG_CLICKABLE);

    lv_obj_t *sp = lv_spinner_create(s_root);
    /* lv_spinner 的动效是"弧长伸缩 + 旋转"（起点 0→360、终点 angle→360+angle，
     * 两条曲线不同步）。angle 越大伸缩越夸张：120° 时弧长在 120~210° 之间抻，
     * 看着像一坨在变形；用户 2026-10-25 定：保留伸缩、幅度要小 → 30°（30~120°）。 */
    lv_spinner_set_anim_params(sp, BUSY_SPIN_MS, BUSY_SPIN_ARC);
    lv_obj_set_style_arc_width(sp, BUSY_SPIN_W, LV_PART_MAIN);
    lv_obj_set_style_arc_width(sp, BUSY_SPIN_W, LV_PART_INDICATOR);
    lv_obj_set_size(sp, BUSY_SPIN_SIZE, BUSY_SPIN_SIZE);
    lv_obj_set_style_arc_color(sp, lv_color_hex(0x26314A), LV_PART_MAIN);
    lv_obj_set_style_arc_color(sp, lv_color_hex(C_PRI), LV_PART_INDICATOR);
    lv_obj_align(sp, LV_ALIGN_CENTER, 0, -14);

    s_lbl = lv_label_create(s_root);
    lv_obj_set_style_text_font(s_lbl, &ui_font_cn14, LV_PART_MAIN);
    lv_obj_set_style_text_color(s_lbl, lv_color_hex(C_TEXT1), LV_PART_MAIN);
    lv_label_set_text(s_lbl, "连接中…");
    lv_obj_set_width(s_lbl, LV_HOR_RES - 32);
    lv_label_set_long_mode(s_lbl, LV_LABEL_LONG_WRAP);
    lv_obj_set_style_text_align(s_lbl, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN);
    lv_obj_align(s_lbl, LV_ALIGN_CENTER, 0, 52);
    return s_root;
}

// 函数作用：盖上整屏开始转圈。 参数：txt：圈下方文案，NULL 用默认。 返回值：无。
void wifi_busy_show(const char *txt)
{
    lv_obj_t *root = ensure_root();
    if (!root) return;
    if (s_lbl) lv_label_set_text(s_lbl, (txt && txt[0]) ? txt : "连接中…");
    lv_obj_remove_flag(root, LV_OBJ_FLAG_HIDDEN);
    lv_obj_move_foreground(root);
    printf("[UI] busy show: %s\n", (txt && txt[0]) ? txt : "连接中…");
}

// 函数作用：收起遮罩。 参数：无。 返回值：无。
void wifi_busy_hide(void)
{
    if (!s_root || lv_obj_has_flag(s_root, LV_OBJ_FLAG_HIDDEN)) return;
    lv_obj_add_flag(s_root, LV_OBJ_FLAG_HIDDEN);
    printf("[UI] busy hide\n");
}

// 函数作用：遮罩是否在前台。 参数：无。 返回值：true 表示正在挡住操作。
bool wifi_busy_visible(void)
{
    return s_root && !lv_obj_has_flag(s_root, LV_OBJ_FLAG_HIDDEN);
}
