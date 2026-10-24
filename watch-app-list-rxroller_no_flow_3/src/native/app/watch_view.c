/*
 * watch_view.c —— 业务状态到 EEZ objects.* 的集中投影。
 * 本文件只读 watch_model 与平台快照；不得修改业务状态、绑定事件或切换页面。
 */
#include <stdint.h>
#include <stdio.h>

#include "lvgl.h"
#include "screens.h"
#include "app/watch_model.h"
#include "app/watch_view.h"
#include "platform/watch_platform.h"

extern objects_t objects;

/* ===== 1. 私有常量与安全写入工具 ===== */
static const char *const TRACKS[] = { "夜曲", "晴天", "稻香" };
static const char *const ARTISTS[] = { "周杰伦 · 十一月的萧邦", "周杰伦 · 叶惠美", "周杰伦 · 魔杰座" };

static void set_text(lv_obj_t *obj, const char *text) { if (obj) lv_label_set_text(obj, text); }
static void set_switch(lv_obj_t *obj, bool on)
{
    if (!obj) return;
    if (on) lv_obj_add_state(obj, LV_STATE_CHECKED);
    else lv_obj_remove_state(obj, LV_STATE_CHECKED);
}
static void set_bar(lv_obj_t *obj, int value) { if (obj) lv_bar_set_value(obj, value, LV_ANIM_OFF); }
static void set_arc(lv_obj_t *obj, int value) { if (obj) lv_arc_set_value(obj, value); }
static void format_time(char *out, size_t n, uint32_t ms, bool hundredths)
{
    uint32_t total = ms / 1000;
    if (hundredths) snprintf(out, n, "%02u:%02u.%02u", (unsigned)(total / 60),
                             (unsigned)(total % 60), (unsigned)((ms / 10) % 100));
    else snprintf(out, n, "%02u:%02u", (unsigned)(total / 60), (unsigned)(total % 60));
}

/* ===== 2. 主表盘快照 ===== */
void watch_view_render_watchface(void)
{
    char b[24];
    int year, month, day, hour, minute;
    uint32_t sec = lv_tick_get() / 1000;
    int heart_rate = 72 + (int)(sec % 9) - 4;
    int battery = 80 - (int)((sec / 1800) % 5);

    if (watch_platform_get_local_time(&year, &month, &day, &hour, &minute)) {
        snprintf(b, sizeof(b), "%02d:%02d", hour, minute);
        set_text(objects.watchface_watchface_t0_l, b);
        set_text(objects.watchface_watchface_t1_l, hour < 12 ? "AM" : "PM");
        snprintf(b, sizeof(b), "%04d-%02d-%02d", year, month, day);
        set_text(objects.watchface_watchface_t2_l, b);
    }
    snprintf(b, sizeof(b), "%d", watch_model.sport_steps);
    set_text(objects.watchface_watchface_wf_stats_v0_l, b);
    snprintf(b, sizeof(b), "%d", heart_rate);
    set_text(objects.watchface_watchface_wf_stats_v1_l, b);
    snprintf(b, sizeof(b), "%d%%", battery);
    set_text(objects.watchface_watchface_wf_stats_v2_l, b);
}

/* ===== 3. 功能页状态投影 ===== */
void watch_view_render_sport(void)
{
    char b[32];
    snprintf(b, sizeof(b), "%d", watch_model.sport_steps);
    set_text(objects.app_sport_app_sport_sp_steps_vl_l, b);
    snprintf(b, sizeof(b), "%.1fkm", watch_model.sport_steps * 0.00061f);
    set_text(objects.app_sport_app_sport_sp_dist_vl_l, b);
    set_bar(objects.app_sport_sp_steps_bar, watch_model.sport_steps * 100 / 12500);
    set_bar(objects.app_sport_sp_dist_bar, watch_model.sport_steps * 100 / 10000);
    set_text(objects.app_sport_b_app_sport_sp_start_t_l, watch_model.sport_running ? "暂停" : "开始");
}

void watch_view_render_spo2(void)
{
    char b[16];
    if (watch_model.spo2_measuring) {
        set_text(objects.app_spo2_app_spo2_t0_l, "--%");
        set_text(objects.app_spo2_app_spo2_t1_l, "测量");
        set_arc(objects.app_spo2_so_ring, 45);
    } else {
        snprintf(b, sizeof(b), "%d%%", watch_model.spo2_value);
        set_text(objects.app_spo2_app_spo2_t0_l, b);
        set_text(objects.app_spo2_app_spo2_t1_l, "正常");
        set_arc(objects.app_spo2_so_ring, watch_model.spo2_value);
    }
    set_text(objects.app_spo2_b_app_spo2_so_measure_t_l, "开始测量");
}

void watch_view_render_messages(void)
{
    char b[24];
    snprintf(b, sizeof(b), "%d 条未读", watch_model.unread);
    set_text(objects.app_msg_app_msg_t0_l, b);
    set_text(objects.app_msg_b_app_msg_ms_clear_t_l, "全部清除");
}

void watch_view_render_music(void)
{
    char b[32];
    uint32_t sec = watch_model.music_ms / 1000;
    set_text(objects.app_music_app_music_t0_l, TRACKS[watch_model.track]);
    set_text(objects.app_music_app_music_t1_l, ARTISTS[watch_model.track]);
    snprintf(b, sizeof(b), "%u:%02u / 3:45", (unsigned)(sec / 60), (unsigned)(sec % 60));
    set_text(objects.app_music_app_music_mu_prog_vl_l, b);
    set_bar(objects.app_music_mu_prog_bar, (int)(sec * 100 / 225));
    set_text(objects.app_music_b_app_music_mu_ctrl_g1_t_l, watch_model.music_playing ? "||" : "▶");
}

void watch_view_render_alarm(void)
{
    char b[24];
    snprintf(b, sizeof(b), "%02d:%02d", watch_model.alarm_hour, watch_model.alarm_min);
    set_text(objects.app_alarm_app_alarm_t0_l, b);
    set_text(objects.app_alarm_app_alarm_al_list_r0_r_l, watch_model.alarm_on[0] ? "开" : "关");
    set_text(objects.app_alarm_app_alarm_al_list_r1_r_l, watch_model.alarm_on[1] ? "开" : "关");
    set_text(objects.app_alarm_app_alarm_al_list_r2_r_l, watch_model.alarm_on[2] ? "开" : "关");
}

void watch_view_render_stopwatch(void)
{
    char b[20];
    format_time(b, sizeof(b), watch_model.stopwatch_ms, true);
    set_text(objects.app_stopwatch_app_stopwatch_t0_l, b);
    set_text(objects.app_stopwatch_b_app_stopwatch_sw_start_t_l,
             watch_model.stopwatch_running ? "暂停" : "开始");
}

void watch_view_render_timer(void)
{
    char b[16];
    uint32_t left = watch_model.timer_left_ms > 0 ? (uint32_t)watch_model.timer_left_ms : 0;
    format_time(b, sizeof(b), left, false);
    set_text(objects.app_timer_app_timer_t0_l, b);
    set_arc(objects.app_timer_tm_ring, (int)(left * 100 / (5 * 60 * 1000)));
    set_text(objects.app_timer_b_app_timer_tm_pause_t_l, watch_model.timer_running ? "暂停" : "继续");
}

void watch_view_render_calc(void)
{
    char b[32];
    double value = watch_model.calc_entering ? watch_model.calc_entry : watch_model.calc_acc;
    snprintf(b, sizeof(b), "%.8g", value);
    set_text(objects.app_calc_app_calc_t0_l, b);
}

void watch_view_render_editor(void)
{
    char b[4];
    snprintf(b, sizeof(b), "%02d", watch_model.alarm_hour);
    set_text(objects.alarm_editor_alarm_editor_t0_l, b);
    snprintf(b, sizeof(b), "%02d", watch_model.alarm_min);
    set_text(objects.alarm_editor_alarm_editor_t2_l, b);
    set_switch(objects.alarm_editor_alarm_editor_ae_days_c0_b, (watch_model.alarm_days & 0x01) != 0);
    set_switch(objects.alarm_editor_alarm_editor_ae_days_c1_b, (watch_model.alarm_days & 0x02) != 0);
    set_switch(objects.alarm_editor_alarm_editor_ae_days_c2_b, (watch_model.alarm_days & 0x04) != 0);
    set_switch(objects.alarm_editor_alarm_editor_ae_days_c3_b, (watch_model.alarm_days & 0x08) != 0);
    set_switch(objects.alarm_editor_alarm_editor_ae_days_c4_b, (watch_model.alarm_days & 0x10) != 0);
    set_switch(objects.alarm_editor_alarm_editor_ae_days_c5_b, (watch_model.alarm_days & 0x20) != 0);
    set_switch(objects.alarm_editor_alarm_editor_ae_days_c6_b, (watch_model.alarm_days & 0x40) != 0);
}

void watch_view_render_face_picker(void)
{
    lv_obj_t *nodes[] = {
        objects.set_facestyle_set_facestyle_fs_items_f0_c,
        objects.set_facestyle_set_facestyle_fs_items_f1_c,
        objects.set_facestyle_set_facestyle_fs_items_f2_c
    };
    int i;
    for (i = 0; i < 3; i++) {
        if (i == watch_model.face) {
            lv_obj_add_state(nodes[i], LV_STATE_CHECKED);
            lv_obj_set_style_border_width(nodes[i], 3, LV_PART_MAIN);
            lv_obj_set_style_border_color(nodes[i], lv_color_hex(0xff5b8d), LV_PART_MAIN);
        } else {
            lv_obj_remove_state(nodes[i], LV_STATE_CHECKED);
            lv_obj_set_style_border_width(nodes[i], 2, LV_PART_MAIN);
            lv_obj_set_style_border_color(nodes[i], lv_color_hex(0x3a3a48), LV_PART_MAIN);
        }
    }
}

void watch_view_render_find_phone(void)
{
    set_text(objects.app_findphone_b_app_findphone_fp_ring_t_l, "让手机响铃");
}

void watch_view_render_settings(void)
{
    char b[32];
    lv_slider_set_value(objects.set_brightness_br_slider, watch_model.brightness, LV_ANIM_OFF);
    snprintf(b, sizeof(b), "%d%%", watch_model.brightness);
    set_text(objects.set_brightness_set_brightness_t0_l, b);
    set_switch(objects.set_brightness_br_auto, watch_model.brightness_auto);
    lv_slider_set_value(objects.set_sound_sd_vol, watch_model.volume, LV_ANIM_OFF);
    snprintf(b, sizeof(b), "提示音量 %d%%", watch_model.volume);
    set_text(objects.set_sound_set_sound_t0_l, b);
    set_switch(objects.set_sound_sd_cue, watch_model.cue);
    set_switch(objects.set_sound_sd_vib, watch_model.vibration);
    set_switch(objects.set_dnd_dn_on, watch_model.dnd);
    set_text(objects.set_bt_set_bt_t0_l, watch_model.ble_connected ? "已连接" : "BLE OFF");
    set_text(objects.set_bt_set_bt_t1_l, watch_model.ble_connected ? "yjt-Watch · Xiaomi 14" : "BLE OFF");
    set_text(objects.set_bt_b_set_bt_bt_disc_t_l, watch_model.ble_connected ? "断开连接" : "BLE ON");
    set_text(objects.set_about_b_set_about_ab_update_t_l, watch_model.checking_update ? "..." : "检查更新");
}

/* ===== 4. 组合刷新与一次性主题应用 ===== */
void watch_view_render_all(void)
{
    watch_view_render_watchface();
    watch_view_render_sport();
    watch_view_render_spo2();
    watch_view_render_messages();
    watch_view_render_music();
    watch_view_render_alarm();
    watch_view_render_stopwatch();
    watch_view_render_timer();
    watch_view_render_calc();
    watch_view_render_editor();
    watch_view_render_face_picker();
    watch_view_render_find_phone();
    watch_view_render_settings();
}

void watch_view_apply_face_theme(void)
{
    static const uint32_t COLORS[] = { 0xff5b8d, 0x2bd97c, 0x9a6bff };
    lv_obj_set_style_text_color(objects.watchface_watchface_t0_l,
                                lv_color_hex(COLORS[watch_model.face]), LV_PART_MAIN);
}
