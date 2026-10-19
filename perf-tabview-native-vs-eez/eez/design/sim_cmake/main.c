/*
 * perf-eez-tabview 仿真入口（EEZ 侧）：EEZ 生成的 tabview + 资源打点。
 */
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include "lvgl.h"
#include "SDL2/SDL.h"
#include "lv_sdl_window.h"
#include "ui.h"

#define SIM_W 480
#define SIM_H 320

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
    hal_init(SIM_W, SIM_H);
    ui_init();
    perf_report("after ui_init");
    lv_timer_create(perf_timer, 3000, NULL);

    while (1) {
        lv_tick_inc(2);
        lv_timer_handler();
        ui_tick();
        usleep(4000);
    }
    return 0;
}
