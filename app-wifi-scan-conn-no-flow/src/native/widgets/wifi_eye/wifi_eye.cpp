/*
 * wifi_eye.cpp — 密码框「眼睛」：按住 → 明文 + 换闭眼图标；松开/丢失 → 星号 + 睁眼图标。
 *
 * 图标用 LVGL 自带的符号字形（LV_SYMBOL_EYE_OPEN/CLOSE），字体用 Montserrat——
 * 本工程的 cn14 子集里没有这两个字形。位置跟随 objects.pwd_ta，不写死坐标。
 */
#include <stdio.h>
#include "lvgl.h"
#include "wifi_eye.h"
#include "widgets/wifi_skin.h"
#include "../../../ui/screens.h"

/******************** 模块私有状态与常量 ********************/

/* 眼睛尺寸与配色在 widgets/wifi_skin.h */

static lv_obj_t *s_eye = NULL;
static lv_obj_t *s_lbl = NULL;

// 函数作用：切密码可见性并同步图标。 参数：reveal：1=明文。 返回值：无。
static void apply_reveal(bool reveal)
{
    if (!objects.pwd_ta) return;
    lv_textarea_set_password_mode(objects.pwd_ta, !reveal);
    if (s_lbl) {
        lv_label_set_text(s_lbl, reveal ? LV_SYMBOL_EYE_CLOSE : LV_SYMBOL_EYE_OPEN);
        lv_obj_set_style_text_color(s_lbl,
                                    lv_color_hex(reveal ? C_ACTIVE : C_IDLE),
                                    LV_PART_MAIN);
    }
}

// 函数作用：眼睛按下/松开的处理。 参数：e：LVGL 事件。 返回值：无。
static void eye_event_cb(lv_event_t *e)
{
    switch (lv_event_get_code(e)) {
    case LV_EVENT_PRESSED:                    /* 按住：看密码 */
        apply_reveal(true);
        break;
    case LV_EVENT_RELEASED:
    case LV_EVENT_PRESS_LOST:                 /* 松开/滑出：恢复星号 */
        apply_reveal(false);
        break;
    default:
        break;
    }
}

/******************** 对外初始化与公开接口 ********************/

// 函数作用：在输入框右端建眼睛（幂等）。 参数：无。 返回值：无。
void wifi_eye_init(void)
{
    if (s_eye || !objects.sheet || !objects.pwd_ta) return;

    /* 文字别钻到眼睛底下 */
    lv_obj_set_style_pad_right(objects.pwd_ta, EYE_PAD_R, LV_PART_MAIN);

    s_eye = lv_obj_create(objects.sheet);
    lv_obj_remove_style_all(s_eye);
    lv_obj_set_size(s_eye, EYE_W, EYE_H);
    /* ★ 先刷新布局，再按输入框的实测矩形算坐标：初始化时 EEZ 刚建完屏，
     *   坐标还没算；而且 align_to 在这套 remove_style_all 的控件上不落地
     *   （实测 eye 停在 0,0 或被放到偏左 38px）。 */
    lv_obj_update_layout(objects.sheet);
    lv_obj_set_pos(s_eye,
                   lv_obj_get_x(objects.pwd_ta) + lv_obj_get_width(objects.pwd_ta)
                       - EYE_W - 6,
                   lv_obj_get_y(objects.pwd_ta)
                       + (lv_obj_get_height(objects.pwd_ta) - EYE_H) / 2);
    lv_obj_add_flag(s_eye, LV_OBJ_FLAG_CLICKABLE);
    lv_obj_add_event_cb(s_eye, eye_event_cb, LV_EVENT_ALL, NULL);

    s_lbl = lv_label_create(s_eye);
    lv_obj_set_style_text_font(s_lbl, &lv_font_montserrat_16, LV_PART_MAIN);
    lv_obj_set_style_text_color(s_lbl, lv_color_hex(C_IDLE), LV_PART_MAIN);
    lv_label_set_text(s_lbl, LV_SYMBOL_EYE_OPEN);
    lv_obj_center(s_lbl);
    printf("[UI] eye ready\n");
}

// 函数作用：取眼睛对象（夹具用）。 参数：无。 返回值：对象或 NULL。
lv_obj_t *wifi_eye_handle(void) { return s_eye; }
