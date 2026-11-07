/* boot_selftest.c — 开机自检页（LVGL 顶层覆盖层）
 *
 * 流程：自检（0→100%，单行动态字条）→ 删除覆盖层 → PC 播放真实 MP4 → 主界面。
 * 设计规则：进度条下方只有一条字条，随检测项切换；不出现编号列表。
 */
#include "boot_selftest.h"

#include <stdio.h>

#include "lvgl.h"
#include "fonts.h"

#ifndef ESP_PLATFORM
#include "platform/pc/sim_video.h"
#endif

#define COL_BG      0x080D18
#define COL_BG2     0x0F1829
#define COL_ACCENT  0x4CC2FF
#define COL_T1      0xEEF4FC
#define COL_T2      0xD6E2F0
#define COL_T3      0x7E90A8
#define COL_TRACK   0x1A2535
#define COL_LOGO    0x16263E
#define COL_LOGO_BD 0x3A688F

static lv_obj_t *s_root;
static lv_obj_t *s_bar;
static lv_obj_t *s_arc;
static lv_obj_t *s_pct;
static lv_obj_t *s_status;
static lv_timer_t *s_timer;
static int s_progress;
static bool s_done;

static const char *status_text(int p)
{
    if (p < 20) return "正在检查内存…";
    if (p < 45) return "正在检查显示…";
    if (p < 70) return "正在检查 Wi-Fi 模块…";
    if (p < 90) return "正在检查存储…";
    return "自检完成，正在进入…";
}

static lv_obj_t *box(lv_obj_t *parent, int x, int y, int w, int h, int radius,
                     lv_color_t bg, lv_opa_t opa)
{
    lv_obj_t *o = lv_obj_create(parent);
    lv_obj_remove_style_all(o);
    lv_obj_set_pos(o, x, y);
    lv_obj_set_size(o, w, h);
    lv_obj_set_style_bg_color(o, bg, 0);
    lv_obj_set_style_bg_opa(o, opa, 0);
    lv_obj_set_style_radius(o, radius, 0);
    lv_obj_clear_flag(o, LV_OBJ_FLAG_SCROLLABLE);
    return o;
}

static lv_obj_t *label(lv_obj_t *parent, int x, int y, int w, const char *txt,
                       const lv_font_t *font, lv_color_t color,
                       lv_text_align_t align)
{
    lv_obj_t *l = lv_label_create(parent);
    lv_obj_remove_style_all(l);
    lv_obj_set_pos(l, x, y);
    if (w > 0) lv_obj_set_width(l, w);
    lv_label_set_text(l, txt);
    lv_obj_set_style_text_font(l, font, 0);
    lv_obj_set_style_text_color(l, color, 0);
    lv_obj_set_style_text_align(l, align, 0);
    return l;
}

static void finish(void)
{
    if (s_timer) {
        lv_timer_delete(s_timer);
        s_timer = NULL;
    }
    if (s_root) {
        lv_obj_delete(s_root);
        s_root = NULL;
        s_bar = s_arc = s_pct = s_status = NULL;
    }
    s_progress = 100;
    s_done = true;
#ifndef ESP_PLATFORM
    sim_video_play_boot();        /* 自检结束后播放真实 MP4 */
#endif
}

static void tick_cb(lv_timer_t *t)
{
    char buf[8];
    LV_UNUSED(t);
    if (!s_root) return;
    s_progress++;
    if (s_progress >= 100) {
        finish();
        return;
    }
    lv_bar_set_value(s_bar, s_progress, LV_ANIM_OFF);
    lv_arc_set_value(s_arc, s_progress);
    snprintf(buf, sizeof(buf), "%d%%", s_progress);
    lv_label_set_text(s_pct, buf);
    lv_label_set_text(s_status, status_text(s_progress));
}

void boot_selftest_start(void)
{
    lv_obj_t *o;
    lv_obj_t *l;

    if (s_root || s_done) return;

    s_root = lv_obj_create(lv_layer_top());
    lv_obj_remove_style_all(s_root);
    lv_obj_set_size(s_root, lv_pct(100), lv_pct(100));
    lv_obj_set_style_bg_color(s_root, lv_color_hex(COL_BG), 0);
    lv_obj_set_style_bg_grad_color(s_root, lv_color_hex(COL_BG2), 0);
    lv_obj_set_style_bg_grad_dir(s_root, LV_GRAD_DIR_VER, 0);
    lv_obj_set_style_bg_opa(s_root, LV_OPA_COVER, 0);
    lv_obj_clear_flag(s_root, LV_OBJ_FLAG_SCROLLABLE);

    /* 品牌 */
    o = box(s_root, 40, 34, 30, 30, 9, lv_color_hex(COL_ACCENT), LV_OPA_COVER);
    label(o, 0, 3, 30, "H", &lv_font_montserrat_16, lv_color_hex(COL_BG),
          LV_TEXT_ALIGN_CENTER);
    label(s_root, 82, 37, 0, "HAVEN HOME", &lv_font_montserrat_20,
          lv_color_hex(COL_T1), LV_TEXT_ALIGN_LEFT);
    label(s_root, 82, 62, 0, "系统自检", &ui_font_cn12,
          lv_color_hex(COL_T3), LV_TEXT_ALIGN_LEFT);
    label(s_root, 700, 40, 60, "v1.0.0", &lv_font_montserrat_14,
          lv_color_hex(COL_T3), LV_TEXT_ALIGN_RIGHT);

    /* 中央徽标 + 房子 */
    o = box(s_root, 344, 72, 112, 112, 28, lv_color_hex(COL_LOGO), LV_OPA_COVER);
    lv_obj_set_style_border_color(o, lv_color_hex(COL_LOGO_BD), 0);
    lv_obj_set_style_border_width(o, 1, 0);
    box(o, 34, 76, 44, 32, 2, lv_color_white(), LV_OPA_COVER);
    box(o, 48, 90, 16, 18, 1, lv_color_hex(0x1E3452), LV_OPA_COVER);
    {
        static lv_point_precise_t roof_l[] = {{400, 118}, {370, 148}};
        static lv_point_precise_t roof_r[] = {{400, 118}, {430, 148}};
        lv_obj_t *ln = lv_line_create(s_root);
        lv_line_set_points(ln, roof_l, 2);
        lv_obj_set_style_line_width(ln, 10, 0);
        lv_obj_set_style_line_color(ln, lv_color_white(), 0);
        lv_obj_set_style_line_rounded(ln, true, 0);
        ln = lv_line_create(s_root);
        lv_line_set_points(ln, roof_r, 2);
        lv_obj_set_style_line_width(ln, 10, 0);
        lv_obj_set_style_line_color(ln, lv_color_white(), 0);
        lv_obj_set_style_line_rounded(ln, true, 0);
    }

    /* 环形进度（42% 起手） */
    s_arc = lv_arc_create(s_root);
    lv_obj_set_size(s_arc, 176, 176);
    lv_obj_set_pos(s_arc, 312, 40);
    lv_obj_remove_style(s_arc, NULL, LV_PART_KNOB);
    lv_obj_set_style_opa(s_arc, LV_OPA_TRANSP, LV_PART_KNOB);
    lv_obj_clear_flag(s_arc, LV_OBJ_FLAG_CLICKABLE);
    lv_arc_set_bg_angles(s_arc, 0, 360);
    lv_arc_set_rotation(s_arc, 270);
    lv_arc_set_range(s_arc, 0, 100);
    lv_arc_set_value(s_arc, 1);
    lv_obj_set_style_arc_width(s_arc, 3, LV_PART_MAIN);
    lv_obj_set_style_arc_color(s_arc, lv_color_hex(0x2A3B52), LV_PART_MAIN);
    lv_obj_set_style_arc_width(s_arc, 3, LV_PART_INDICATOR);
    lv_obj_set_style_arc_color(s_arc, lv_color_hex(COL_ACCENT), LV_PART_INDICATOR);

    {
        lv_obj_t *title = label(s_root, 0, 222, 800, "系统初始化", &ui_font_cn12,
                                lv_color_hex(COL_T1), LV_TEXT_ALIGN_CENTER);
        lv_obj_set_style_text_letter_space(title, 2, 0);
    }
    label(s_root, 0, 254, 800, "正在检查硬件与网络", &ui_font_cn12,
          lv_color_hex(COL_T3), LV_TEXT_ALIGN_CENTER);

    /* 进度条 + 百分比 */
    label(s_root, 140, 286, 120, "自检进度", &ui_font_cn12,
          lv_color_hex(COL_T3), LV_TEXT_ALIGN_LEFT);
    s_pct = label(s_root, 560, 282, 100, "1%", &lv_font_montserrat_16,
                  lv_color_hex(COL_T2), LV_TEXT_ALIGN_RIGHT);
    s_bar = lv_bar_create(s_root);
    lv_obj_set_pos(s_bar, 140, 300);
    lv_obj_set_size(s_bar, 520, 8);
    lv_bar_set_range(s_bar, 0, 100);
    lv_bar_set_value(s_bar, 1, LV_ANIM_OFF);
    lv_obj_set_style_radius(s_bar, 4, LV_PART_MAIN);
    lv_obj_set_style_bg_color(s_bar, lv_color_hex(COL_TRACK), LV_PART_MAIN);
    lv_obj_set_style_radius(s_bar, 4, LV_PART_INDICATOR);
    lv_obj_set_style_bg_color(s_bar, lv_color_hex(COL_ACCENT), LV_PART_INDICATOR);

    /* 单行动态字条 */
    box(s_root, 300, 334, 8, 8, 4, lv_color_hex(COL_ACCENT), LV_OPA_COVER);
    l = label(s_root, 316, 332, 0, status_text(s_progress), &ui_font_cn12,
              lv_color_hex(COL_T2), LV_TEXT_ALIGN_LEFT);
    s_status = l;

    /* 页脚 */
    box(s_root, 40, 432, 720, 1, 0, lv_color_hex(0x202C3E), LV_OPA_COVER);
    label(s_root, 40, 444, 120, "请勿断电", &ui_font_cn12,
          lv_color_hex(COL_T3), LV_TEXT_ALIGN_LEFT);
    label(s_root, 640, 444, 120, "HAVEN HOME", &ui_font_cn12,
          lv_color_hex(COL_T3), LV_TEXT_ALIGN_RIGHT);

    s_progress = 1;
    s_done = false;
    s_timer = lv_timer_create(tick_cb, 20, NULL);
}

bool boot_selftest_active(void)
{
    return s_root != NULL;
}

int boot_selftest_progress(void)
{
    return s_progress;
}
