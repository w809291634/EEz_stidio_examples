/*
 * watch_logic.c —— 初始化与持续状态调度。
 * 按钮绑定放 watch_events.c，所有 UI 投影放 watch_view.c；本文件不直接访问 objects.*。
 */
#include <stdint.h>

#include "lvgl.h"
#include "app/watch_events.h"
#include "app/watch_logic.h"
#include "app/watch_model.h"
#include "app/watch_view.h"
#include "platform/watch_platform.h"

/* ===== 1. 调度器私有状态 ===== */
static uint32_t s_last_tick;

/* ===== 2. 统一 100ms tick =====
 * 所有“随时间变化”的状态都在这里推进；单击事件始终由 watch_events.c 立即处理。 */
static void logic_tick(lv_timer_t *timer)
{
    uint32_t now = lv_tick_get();
    uint32_t dt;
    (void)timer;

    if (!s_last_tick) {
        s_last_tick = now;
        return;
    }
    dt = lv_tick_elaps(s_last_tick);
    s_last_tick = now;

    if (watch_model.sport_running) {
        watch_model.sport_ms += dt;
        watch_model.sport_steps = 8523 + (int)(watch_model.sport_ms / 700);
        watch_view_render_sport();
    }

    /* 表盘时间、心率和电量是快照，按 tick 刷新而不是由某个按钮驱动。 */
    watch_view_render_watchface();

    if (watch_model.stopwatch_running) {
        watch_model.stopwatch_ms += dt;
        watch_view_render_stopwatch();
    }
    if (watch_model.timer_running) {
        watch_model.timer_left_ms -= (int)dt;
        if (watch_model.timer_left_ms <= 0) {
            watch_model.timer_left_ms = 0;
            watch_model.timer_running = false;
        }
        watch_view_render_timer();
    }
    if (watch_model.music_playing) {
        watch_model.music_ms = (watch_model.music_ms + dt) % (225u * 1000u);
        watch_view_render_music();
    }
    if (watch_model.spo2_measuring && lv_tick_elaps(watch_model.spo2_started) >= 1600) {
        watch_model.spo2_measuring = false;
        watch_model.spo2_value = 98;
        watch_view_render_spo2();
    }
    if (watch_model.checking_update && lv_tick_elaps(watch_model.update_started) >= 1200) {
        watch_model.checking_update = false;
        watch_view_render_settings();
    }
    if (watch_model.find_phone_ringing && lv_tick_elaps(watch_model.find_phone_started) >= 8000) {
        watch_model.find_phone_ringing = false;
        watch_platform_find_phone(false);
        watch_view_render_find_phone();
    }
}

/* ===== 3. 对外初始化入口 =====
 * 由 navigation 在 UI 与动态导航点击区均创建后调用一次。 */
void watch_logic_init(void)
{
    watch_events_bind();
    watch_view_render_all();
    watch_platform_set_brightness(watch_model.brightness, watch_model.brightness_auto);
    watch_platform_set_sound(watch_model.volume, watch_model.cue, watch_model.vibration);
    lv_timer_create(logic_tick, 100, NULL);
}
