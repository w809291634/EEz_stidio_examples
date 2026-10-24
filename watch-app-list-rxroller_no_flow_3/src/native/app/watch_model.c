#include "app/watch_model.h"

watch_model_t watch_model = {
    .sport_steps = 8523, .spo2_value = 97, .unread = 3,
    .alarm_on = { true, false, true }, .alarm_hour = 7, .alarm_min = 0,
    .alarm_days = 0x1f, .timer_left_ms = 5 * 60 * 1000,
    .brightness = 70, .brightness_auto = true, .volume = 50,
    .cue = true, .vibration = false, .ble_connected = true
};
