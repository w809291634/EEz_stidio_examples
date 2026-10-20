/*
 * w14-w35-w62-chart-led-scale 仿真入口。
 * W14 Chart 在 EEZ 中是空壳（零属性）——series/数据全部在此处（ui_init 之后）用 C 补，
 * 并用 lv_timer 每 200ms 推进一个点（滚动正弦波）。
 */
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <math.h>

#include "lvgl.h"
#include "SDL2/SDL.h"
#include "lv_sdl_window.h"
#include "ui.h"
#include "screens.h"         /* objects_t（EEZ_FOR_LVGL 下 ui.h 不含它） */

#define SIM_W 480
#define SIM_H 320

static lv_obj_t *series;

static void feed_timer(lv_timer_t *t)
{
    static float ph = 0.0f;
    static uint32_t x = 0;
    ph += 0.35f;
    x++;
    /* 滚动正弦：每 200ms 追加一个点，超出可见范围自动左移 */
    lv_chart_set_next_value(objects.chart_main, series,
                            (int32_t)(50 + 45 * sinf(ph)));
    (void)x;
    (void)t;
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
    hal_init(SIM_W, SIM_H);
    ui_init();

    /* ---- W14 Chart：C 侧补 series（EEZ 空壳的唯一用法） ---- */
    {
        lv_obj_t *chart = objects.chart_main;
        lv_chart_set_type(chart, LV_CHART_TYPE_LINE);
        lv_chart_set_point_count(chart, 30);
        lv_chart_set_update_mode(chart, LV_CHART_UPDATE_MODE_SHIFT);
        series = lv_chart_add_series(chart, lv_color_hex(0x5B7CFA), LV_CHART_AXIS_PRIMARY_Y);
        lv_chart_set_range(chart, LV_CHART_AXIS_PRIMARY_Y, 0, 100);
        /* 初始填充 30 个点 */
        for (int i = 0; i < 30; i++) {
            lv_chart_set_next_value(chart, series,
                                    (int32_t)(50 + 45 * sinf(i * 0.35f)));
        }
        lv_timer_create(feed_timer, 200, NULL);
    }

    while (1) {
        lv_tick_inc(2);
        lv_timer_handler();
        ui_tick();
        usleep(4000);
    }
    return 0;
}
