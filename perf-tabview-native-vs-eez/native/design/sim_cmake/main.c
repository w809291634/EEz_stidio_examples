/*
 * native 侧仿真入口：纯 LVGL 创建与 EEZ 侧完全同构的 tabview（无 EEZ/无 flow），
 * 逐控件对应 eez/build_example.py：tabview(隐藏栏) + 2 Tab ×（1 图标块 + 2 标签）。
 * 资源打点与 EEZ 侧相同（lv_mem_monitor）。
 */
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include "lvgl.h"
#include "SDL2/SDL.h"
#include "lv_sdl_window.h"

#define SIM_W 480
#define SIM_H 320

static lv_obj_t *make_icon(lv_obj_t *parent, uint32_t c1, uint32_t c2)
{
    lv_obj_t *ic = lv_obj_create(parent);
    lv_obj_remove_style_all(ic);
    lv_obj_set_size(ic, 64, 64);
    lv_obj_align(ic, LV_ALIGN_LEFT_MID, 0, 0);
    lv_obj_set_style_radius(ic, 16, 0);
    lv_obj_set_style_bg_opa(ic, LV_OPA_COVER, 0);
    lv_obj_set_style_bg_color(ic, lv_color_hex(c1), 0);
    lv_obj_set_style_bg_grad_color(ic, lv_color_hex(c2), 0);
    lv_obj_set_style_bg_grad_dir(ic, LV_GRAD_DIR_VER, 0);
    return ic;
}

static lv_obj_t *make_label(lv_obj_t *parent, const char *txt, uint32_t color,
                            int32_t x, int32_t y, int32_t w, int32_t h)
{
    lv_obj_t *l = lv_label_create(parent);
    lv_label_set_text(l, txt);
    lv_obj_set_style_text_color(l, lv_color_hex(color), 0);
    lv_obj_set_pos(l, x, y);
    lv_obj_set_size(l, w, h);
    return l;
}

static void build_tab(lv_obj_t *tv, const char *name, uint32_t bg,
                      uint32_t c1, uint32_t c2)
{
    lv_obj_t *page = lv_tabview_add_tab(tv, name);
    lv_obj_set_style_bg_color(page, lv_color_hex(bg), 0);
    lv_obj_set_style_bg_opa(page, LV_OPA_COVER, 0);
    make_icon(page, c1, c2);
    make_label(page, "APP ONE", 0xFFFFFF, 140, 110 - 100, 280, 40);
    make_label(page, "sample app row for perf test", 0x8A94A6,
               140, 160 - 100, 280, 30);
}

static void perf_report(const char *tag)
{
    lv_mem_monitor_t m;
    lv_mem_monitor(&m);
    printf("[PERF] %-14s heap: total=%u used=%u free=%u used_pct=%u%% "
           "max_used=%u frag=%u%%\n",
           tag, (unsigned)m.total_size,
           (unsigned)(m.total_size - m.free_size), (unsigned)m.free_size,
           (unsigned)m.used_pct, (unsigned)m.max_used, (unsigned)m.frag_pct);
    fflush(stdout);
}

static void perf_timer(lv_timer_t *t)
{
    perf_report("steady+3s");
    lv_timer_del(t);
}

static lv_display_t *hal_init(int32_t w, int32_t h)
{
    lv_display_t *disp = lv_sdl_window_create(w, h);
    lv_indev_t *mouse = lv_sdl_mouse_create();
    lv_indev_set_display(mouse, disp);
    lv_display_set_default(disp);
    return disp;
}

int main(int argc, char **argv)
{
    (void)argc; (void)argv;
    lv_init();
    lv_display_t *disp = hal_init(SIM_W, SIM_H);
    (void)disp;

    lv_obj_t *scr = lv_screen_active();
    lv_obj_set_style_bg_color(scr, lv_color_hex(0x101828), 0);

    lv_obj_t *tv = lv_tabview_create(scr);
    lv_obj_set_size(tv, SIM_W, SIM_H);
    lv_tabview_set_tab_bar_position(tv, LV_DIR_TOP);
    lv_tabview_set_tab_bar_size(tv, 0);
    build_tab(tv, "one", 0x103A6B, 0x5B7CFA, 0x8B5CF6);
    build_tab(tv, "two", 0x14532D, 0x2FA46A, 0x6CB05C);

    perf_report("after build");
    lv_timer_create(perf_timer, 3000, NULL);

    while (1) {
        lv_tick_inc(2);
        lv_timer_handler();
        usleep(4000);
    }
    return 0;
}
