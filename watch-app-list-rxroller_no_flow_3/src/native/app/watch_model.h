#ifndef WATCH_MODEL_H
#define WATCH_MODEL_H

#include <stdbool.h>
#include <stdint.h>

typedef struct {
    /* 运动与健康：sport_ms/started 均为 LVGL tick 时间基。 */
    bool sport_running; uint32_t sport_ms; int sport_steps;
    bool spo2_measuring; uint32_t spo2_started; int spo2_value;

    /* 消息与媒体：track 是当前曲目下标，music_ms 在单曲内循环。 */
    int unread; int track; bool music_playing; uint32_t music_ms;

    /* 闹钟与计时工具。 */
    bool alarm_on[3]; int alarm_hour; int alarm_min; uint8_t alarm_days;
    bool stopwatch_running; uint32_t stopwatch_ms;
    bool timer_running; int timer_left_ms;
    double calc_acc, calc_entry; char calc_op; bool calc_entering;

    /* 与手机交互及系统设置。 */
    bool find_phone_ringing; uint32_t find_phone_started;
    int brightness; bool brightness_auto; int volume; bool cue, vibration;
    int face; bool ble_connected, dnd, checking_update; uint32_t update_started;
} watch_model_t;

/* 全工程唯一业务真值；禁止在页面或 widget 内复制其中字段。 */
extern watch_model_t watch_model;

#endif
