/*
 * watch_events.c —— EEZ 输入事件到业务状态迁移。
 * 回调只负责“输入→model→平台命令→请求 view 刷新”；不承担 tick 或页面路由。
 */
#include <stdint.h>

#include "lvgl.h"
#include "screens.h"
#include "app/watch_events.h"
#include "app/watch_model.h"
#include "app/watch_view.h"
#include "platform/watch_platform.h"

extern objects_t objects;

/* ===== 1. 纯业务辅助 ===== */
static void apply_calc(char operation)
{
    if (watch_model.calc_op == '+') watch_model.calc_acc += watch_model.calc_entry;
    else if (watch_model.calc_op == '-') watch_model.calc_acc -= watch_model.calc_entry;
    else if (watch_model.calc_op == '*') watch_model.calc_acc *= watch_model.calc_entry;
    else if (watch_model.calc_op == '/' && watch_model.calc_entry != 0.0) watch_model.calc_acc /= watch_model.calc_entry;
    else if (!watch_model.calc_op) watch_model.calc_acc = watch_model.calc_entry;
    watch_model.calc_entry = 0.0;
    watch_model.calc_entering = false;
    watch_model.calc_op = operation;
}

/* ===== 2. 运动、健康、媒体事件 ===== */
static void on_sport(lv_event_t *event)
{
    (void)event;
    watch_model.sport_running = !watch_model.sport_running;
    watch_view_render_sport();
}

static void on_spo2(lv_event_t *event)
{
    (void)event;
    if (watch_model.spo2_measuring) return;
    watch_model.spo2_measuring = true;
    watch_model.spo2_started = lv_tick_get();
    watch_platform_start_spo2();
    watch_view_render_spo2();
}

static void on_clear_messages(lv_event_t *event)
{
    (void)event;
    watch_model.unread = 0;
    watch_view_render_messages();
}

static void on_music(lv_event_t *event)
{
    int command = (int)(intptr_t)lv_event_get_user_data(event);
    if (command == 0) { watch_model.track = (watch_model.track + 2) % 3; watch_model.music_ms = 0; }
    else if (command == 2) { watch_model.track = (watch_model.track + 1) % 3; watch_model.music_ms = 0; }
    else watch_model.music_playing = !watch_model.music_playing;
    watch_platform_media_command(command);
    watch_view_render_music();
}

static void on_find_phone(lv_event_t *event)
{
    (void)event;
    watch_model.find_phone_ringing = !watch_model.find_phone_ringing;
    watch_model.find_phone_started = lv_tick_get();
    watch_platform_find_phone(watch_model.find_phone_ringing);
    watch_view_render_find_phone();
}

/* ===== 3. 闹钟、计时和计算器事件 ===== */
static void on_alarm_toggle(lv_event_t *event)
{
    int index = (int)(intptr_t)lv_event_get_user_data(event);
    if (index >= 0 && index < 3) watch_model.alarm_on[index] = !watch_model.alarm_on[index];
    watch_view_render_alarm();
}

static void on_hour(lv_event_t *event)
{
    watch_model.alarm_hour = (watch_model.alarm_hour + (int)(intptr_t)lv_event_get_user_data(event) + 24) % 24;
    watch_view_render_editor();
}

static void on_min(lv_event_t *event)
{
    watch_model.alarm_min = (watch_model.alarm_min + (int)(intptr_t)lv_event_get_user_data(event) + 60) % 60;
    watch_view_render_editor();
}

static void on_day(lv_event_t *event)
{
    watch_model.alarm_days ^= (uint8_t)(1u << (int)(intptr_t)lv_event_get_user_data(event));
    watch_view_render_editor();
}

static void on_alarm_add(lv_event_t *event)
{
    (void)event;
    watch_model.alarm_hour = 7;
    watch_model.alarm_min = 0;
    watch_model.alarm_days = 0x1f;
    watch_view_render_editor();
}

static void on_alarm_save(lv_event_t *event)
{
    (void)event;
    watch_model.alarm_on[0] = true;
    watch_view_render_alarm();
}

static void on_stopwatch_start(lv_event_t *event)
{
    (void)event;
    watch_model.stopwatch_running = !watch_model.stopwatch_running;
    watch_view_render_stopwatch();
}

static void on_stopwatch_reset(lv_event_t *event)
{
    (void)event;
    watch_model.stopwatch_running = false;
    watch_model.stopwatch_ms = 0;
    watch_view_render_stopwatch();
}

static void on_timer_pause(lv_event_t *event)
{
    (void)event;
    watch_model.timer_running = !watch_model.timer_running;
    watch_view_render_timer();
}

static void on_timer_cancel(lv_event_t *event)
{
    (void)event;
    watch_model.timer_running = false;
    watch_model.timer_left_ms = 5 * 60 * 1000;
    watch_view_render_timer();
}

static void on_calc(lv_event_t *event)
{
    static const char keys[] = { 'C','S','%','/','7','8','9','*','4','5','6','-','1','2','3','+','0','.', '=' };
    int index = (int)(intptr_t)lv_event_get_user_data(event);
    char key = (index >= 0 && index < (int)sizeof(keys)) ? keys[index] : 'C';
    if (key >= '0' && key <= '9') {
        watch_model.calc_entry = watch_model.calc_entering ? watch_model.calc_entry * 10.0 + (key - '0') : (key - '0');
        watch_model.calc_entering = true;
    } else if (key == '.') {
        watch_model.calc_entering = true;
    } else if (key == 'C') {
        watch_model.calc_acc = 0.0;
        watch_model.calc_entry = 0.0;
        watch_model.calc_op = 0;
        watch_model.calc_entering = false;
    } else if (key == 'S') {
        watch_model.calc_entry = -watch_model.calc_entry;
        watch_model.calc_entering = true;
    } else if (key == '%') {
        watch_model.calc_entry /= 100.0;
        watch_model.calc_entering = true;
    } else if (key == '=') {
        apply_calc(0);
    } else {
        apply_calc(key);
    }
    watch_view_render_calc();
}

/* ===== 4. 设置与表盘事件 ===== */
static void on_brightness(lv_event_t *event)
{
    (void)event;
    watch_model.brightness = lv_slider_get_value(objects.set_brightness_br_slider);
    watch_platform_set_brightness(watch_model.brightness, watch_model.brightness_auto);
    watch_view_render_settings();
}

static void on_brightness_auto(lv_event_t *event)
{
    (void)event;
    watch_model.brightness_auto = lv_obj_has_state(objects.set_brightness_br_auto, LV_STATE_CHECKED);
    watch_platform_set_brightness(watch_model.brightness, watch_model.brightness_auto);
    watch_view_render_settings();
}

static void on_volume(lv_event_t *event)
{
    (void)event;
    watch_model.volume = lv_slider_get_value(objects.set_sound_sd_vol);
    watch_platform_set_sound(watch_model.volume, watch_model.cue, watch_model.vibration);
    watch_view_render_settings();
}

static void on_cue(lv_event_t *event)
{
    (void)event;
    watch_model.cue = lv_obj_has_state(objects.set_sound_sd_cue, LV_STATE_CHECKED);
    watch_platform_set_sound(watch_model.volume, watch_model.cue, watch_model.vibration);
    watch_view_render_settings();
}

static void on_vibration(lv_event_t *event)
{
    (void)event;
    watch_model.vibration = lv_obj_has_state(objects.set_sound_sd_vib, LV_STATE_CHECKED);
    watch_platform_set_sound(watch_model.volume, watch_model.cue, watch_model.vibration);
    watch_view_render_settings();
}

static void on_face(lv_event_t *event)
{
    watch_model.face = (int)(intptr_t)lv_event_get_user_data(event);
    watch_view_render_face_picker();
}

static void on_face_apply(lv_event_t *event)
{
    (void)event;
    watch_view_apply_face_theme();
}

static void on_bt(lv_event_t *event)
{
    (void)event;
    watch_model.ble_connected = !watch_model.ble_connected;
    if (!watch_model.ble_connected) watch_platform_ble_disconnect();
    watch_view_render_settings();
}

static void on_dnd(lv_event_t *event)
{
    (void)event;
    watch_model.dnd = lv_obj_has_state(objects.set_dnd_dn_on, LV_STATE_CHECKED);
    watch_view_render_settings();
}

static void on_update(lv_event_t *event)
{
    (void)event;
    watch_model.checking_update = true;
    watch_model.update_started = lv_tick_get();
    watch_platform_check_update();
    watch_view_render_settings();
}

/* ===== 5. 原生补充点击区与对外绑定 =====
 * 父对象来自 EEZ；透明层只补足纯展示 label 无法接收事件的区域。 */
static lv_obj_t *make_hit(lv_obj_t *parent, int x, int y, int w, int h,
                          lv_event_cb_t callback, intptr_t data)
{
    lv_obj_t *hit = lv_obj_create(parent);
    lv_obj_remove_style_all(hit);
    lv_obj_set_pos(hit, x, y);
    lv_obj_set_size(hit, w, h);
    lv_obj_add_flag(hit, LV_OBJ_FLAG_CLICKABLE);
    lv_obj_add_event_cb(hit, callback, LV_EVENT_CLICKED, (void *)data);
    return hit;
}

void watch_events_bind(void)
{
    const lv_obj_t *face_nodes[] = {
        objects.set_facestyle_set_facestyle_fs_items_f0_c,
        objects.set_facestyle_set_facestyle_fs_items_f1_c,
        objects.set_facestyle_set_facestyle_fs_items_f2_c
    };
    const lv_obj_t *calc_nodes[] = {
        objects.app_calc_app_calc_ca_keys_k0_b, objects.app_calc_app_calc_ca_keys_k1_b,
        objects.app_calc_app_calc_ca_keys_k2_b, objects.app_calc_app_calc_ca_keys_k3_b,
        objects.app_calc_app_calc_ca_keys_k4_b, objects.app_calc_app_calc_ca_keys_k5_b,
        objects.app_calc_app_calc_ca_keys_k6_b, objects.app_calc_app_calc_ca_keys_k7_b,
        objects.app_calc_app_calc_ca_keys_k8_b, objects.app_calc_app_calc_ca_keys_k9_b,
        objects.app_calc_app_calc_ca_keys_k10_b, objects.app_calc_app_calc_ca_keys_k11_b,
        objects.app_calc_app_calc_ca_keys_k12_b, objects.app_calc_app_calc_ca_keys_k13_b,
        objects.app_calc_app_calc_ca_keys_k14_b, objects.app_calc_app_calc_ca_keys_k15_b,
        objects.app_calc_app_calc_ca_keys_k16_b, objects.app_calc_app_calc_ca_keys_k17_b,
        objects.app_calc_app_calc_ca_keys_k18_b
    };
    lv_obj_t *days[] = {
        objects.alarm_editor_alarm_editor_ae_days_c0_b, objects.alarm_editor_alarm_editor_ae_days_c1_b,
        objects.alarm_editor_alarm_editor_ae_days_c2_b, objects.alarm_editor_alarm_editor_ae_days_c3_b,
        objects.alarm_editor_alarm_editor_ae_days_c4_b, objects.alarm_editor_alarm_editor_ae_days_c5_b,
        objects.alarm_editor_alarm_editor_ae_days_c6_b
    };
    int i;

    lv_obj_add_event_cb(objects.app_sport_app_sport_sp_start_b, on_sport, LV_EVENT_CLICKED, NULL);
    lv_obj_add_event_cb(objects.app_spo2_app_spo2_so_measure_b, on_spo2, LV_EVENT_CLICKED, NULL);
    lv_obj_add_event_cb(objects.app_msg_app_msg_ms_clear_b, on_clear_messages, LV_EVENT_CLICKED, NULL);
    lv_obj_add_event_cb(objects.app_music_app_music_mu_ctrl_g0_b, on_music, LV_EVENT_CLICKED, (void *)0);
    lv_obj_add_event_cb(objects.app_music_app_music_mu_ctrl_g1_b, on_music, LV_EVENT_CLICKED, (void *)1);
    lv_obj_add_event_cb(objects.app_music_app_music_mu_ctrl_g2_b, on_music, LV_EVENT_CLICKED, (void *)2);
    lv_obj_add_event_cb(objects.app_alarm_app_alarm_al_add_b, on_alarm_add, LV_EVENT_CLICKED, NULL);
    lv_obj_add_event_cb(objects.alarm_editor_alarm_editor_ae_save_b, on_alarm_save, LV_EVENT_CLICKED, NULL);
    lv_obj_add_event_cb(objects.app_stopwatch_app_stopwatch_sw_start_b, on_stopwatch_start, LV_EVENT_CLICKED, NULL);
    lv_obj_add_event_cb(objects.app_stopwatch_app_stopwatch_sw_reset_b, on_stopwatch_reset, LV_EVENT_CLICKED, NULL);
    lv_obj_add_event_cb(objects.app_timer_app_timer_tm_pause_b, on_timer_pause, LV_EVENT_CLICKED, NULL);
    lv_obj_add_event_cb(objects.app_timer_app_timer_tm_cancel_b, on_timer_cancel, LV_EVENT_CLICKED, NULL);
    lv_obj_add_event_cb(objects.app_findphone_app_findphone_fp_ring_b, on_find_phone, LV_EVENT_CLICKED, NULL);
    lv_obj_add_event_cb(objects.alarm_editor_alarm_editor_ae_hour_up_b, on_hour, LV_EVENT_CLICKED, (void *)1);
    lv_obj_add_event_cb(objects.alarm_editor_alarm_editor_ae_hour_dn_b, on_hour, LV_EVENT_CLICKED, (void *)-1);
    lv_obj_add_event_cb(objects.alarm_editor_alarm_editor_ae_min_up_b, on_min, LV_EVENT_CLICKED, (void *)1);
    lv_obj_add_event_cb(objects.alarm_editor_alarm_editor_ae_min_dn_b, on_min, LV_EVENT_CLICKED, (void *)-1);
    lv_obj_add_event_cb(objects.set_brightness_br_slider, on_brightness, LV_EVENT_VALUE_CHANGED, NULL);
    lv_obj_add_event_cb(objects.set_brightness_br_auto, on_brightness_auto, LV_EVENT_VALUE_CHANGED, NULL);
    lv_obj_add_event_cb(objects.set_sound_sd_vol, on_volume, LV_EVENT_VALUE_CHANGED, NULL);
    lv_obj_add_event_cb(objects.set_sound_sd_cue, on_cue, LV_EVENT_VALUE_CHANGED, NULL);
    lv_obj_add_event_cb(objects.set_sound_sd_vib, on_vibration, LV_EVENT_VALUE_CHANGED, NULL);
    lv_obj_add_event_cb(objects.set_facestyle_set_facestyle_fs_apply_b, on_face_apply, LV_EVENT_CLICKED, NULL);
    lv_obj_add_event_cb(objects.set_bt_set_bt_bt_disc_b, on_bt, LV_EVENT_CLICKED, NULL);
    lv_obj_add_event_cb(objects.set_dnd_dn_on, on_dnd, LV_EVENT_VALUE_CHANGED, NULL);
    lv_obj_add_event_cb(objects.set_about_set_about_ab_update_b, on_update, LV_EVENT_CLICKED, NULL);

    for (i = 0; i < 3; i++) make_hit(objects.app_alarm, 98, 252 + i * 46, 270, 46, on_alarm_toggle, i);
    for (i = 0; i < 7; i++) lv_obj_add_event_cb(days[i], on_day, LV_EVENT_CLICKED, (void *)(intptr_t)i);
    for (i = 0; i < 3; i++) {
        make_hit(objects.set_facestyle, 47 + i * 130, 174, 112, 112, on_face, i);
        lv_obj_add_flag((lv_obj_t *)face_nodes[i], LV_OBJ_FLAG_CHECKABLE);
    }
    for (i = 0; i < 19; i++) lv_obj_add_event_cb((lv_obj_t *)calc_nodes[i], on_calc, LV_EVENT_CLICKED, (void *)(intptr_t)i);
}
