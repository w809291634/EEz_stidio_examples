#ifndef EEZ_LVGL_UI_SCREENS_H
#define EEZ_LVGL_UI_SCREENS_H

#include <lvgl.h>

#ifdef __cplusplus
extern "C" {
#endif

// Screens

enum ScreensEnum {
    _SCREEN_ID_FIRST = 1,
    SCREEN_ID_TAB_MAIN = 1,
    SCREEN_ID_APP_SPORT = 2,
    SCREEN_ID_APP_HR = 3,
    SCREEN_ID_APP_SLEEP = 4,
    SCREEN_ID_APP_SPO2 = 5,
    SCREEN_ID_APP_WEATHER = 6,
    SCREEN_ID_APP_MSG = 7,
    SCREEN_ID_APP_MUSIC = 8,
    SCREEN_ID_APP_ALARM = 9,
    SCREEN_ID_APP_STOPWATCH = 10,
    SCREEN_ID_APP_TIMER = 11,
    SCREEN_ID_APP_CALC = 12,
    SCREEN_ID_APP_COMPASS = 13,
    SCREEN_ID_APP_FINDPHONE = 14,
    SCREEN_ID_APP_SETTINGS = 15,
    SCREEN_ID_ALARM_EDITOR = 16,
    SCREEN_ID_SET_BRIGHTNESS = 17,
    SCREEN_ID_SET_SOUND = 18,
    SCREEN_ID_SET_FACESTYLE = 19,
    SCREEN_ID_SET_BT = 20,
    SCREEN_ID_SET_DND = 21,
    SCREEN_ID_SET_ABOUT = 22,
    _SCREEN_ID_LAST = 22
};

typedef struct _objects_t {
    lv_obj_t *tab_main;
    lv_obj_t *app_sport;
    lv_obj_t *app_hr;
    lv_obj_t *app_sleep;
    lv_obj_t *app_spo2;
    lv_obj_t *app_weather;
    lv_obj_t *app_msg;
    lv_obj_t *app_music;
    lv_obj_t *app_alarm;
    lv_obj_t *app_stopwatch;
    lv_obj_t *app_timer;
    lv_obj_t *app_calc;
    lv_obj_t *app_compass;
    lv_obj_t *app_findphone;
    lv_obj_t *app_settings;
    lv_obj_t *alarm_editor;
    lv_obj_t *set_brightness;
    lv_obj_t *set_sound;
    lv_obj_t *set_facestyle;
    lv_obj_t *set_bt;
    lv_obj_t *set_dnd;
    lv_obj_t *set_about;
    lv_obj_t *tv_main;
    lv_obj_t *tab_watchface;
    lv_obj_t *watchface_watchface_t0_l;
    lv_obj_t *watchface_watchface_t1_l;
    lv_obj_t *watchface_watchface_t2_l;
    lv_obj_t *watchface_watchface_wf_stats_v0_l;
    lv_obj_t *watchface_watchface_wf_stats_l0_l;
    lv_obj_t *watchface_watchface_wf_stats_v1_l;
    lv_obj_t *watchface_watchface_wf_stats_l1_l;
    lv_obj_t *watchface_watchface_wf_stats_v2_l;
    lv_obj_t *watchface_watchface_wf_stats_l2_l;
    lv_obj_t *watchface_watchface_wf_pager_d0_c;
    lv_obj_t *watchface_watchface_wf_pager_d1_c;
    lv_obj_t *tab_applist;
    lv_obj_t *al_roller_host;
    lv_obj_t *app_sport_app_sport_back_b;
    lv_obj_t *app_sport_b_app_sport_back_t_l;
    lv_obj_t *app_sport_app_sport_title_l;
    lv_obj_t *app_sport_app_sport_t0_l;
    lv_obj_t *app_sport_app_sport_t1_l;
    lv_obj_t *app_sport_app_sport_sp_steps_lb_l;
    lv_obj_t *app_sport_app_sport_sp_steps_vl_l;
    lv_obj_t *app_sport_sp_steps_bar;
    lv_obj_t *app_sport_app_sport_sp_dist_lb_l;
    lv_obj_t *app_sport_app_sport_sp_dist_vl_l;
    lv_obj_t *app_sport_sp_dist_bar;
    lv_obj_t *app_sport_app_sport_sp_start_b;
    lv_obj_t *app_sport_b_app_sport_sp_start_t_l;
    lv_obj_t *app_hr_app_hr_back_b;
    lv_obj_t *app_hr_b_app_hr_back_t_l;
    lv_obj_t *app_hr_app_hr_title_l;
    lv_obj_t *app_hr_app_hr_t0_l;
    lv_obj_t *app_hr_app_hr_t1_l;
    lv_obj_t *app_hr_app_hr_hr_week_b0_c;
    lv_obj_t *app_hr_app_hr_hr_week_b1_c;
    lv_obj_t *app_hr_app_hr_hr_week_b2_c;
    lv_obj_t *app_hr_app_hr_hr_week_b3_c;
    lv_obj_t *app_hr_app_hr_hr_week_b4_c;
    lv_obj_t *app_hr_app_hr_hr_week_b5_c;
    lv_obj_t *app_hr_app_hr_hr_week_b6_c;
    lv_obj_t *app_hr_app_hr_hr_week_lb0_l;
    lv_obj_t *app_hr_app_hr_hr_week_lb1_l;
    lv_obj_t *app_hr_app_hr_hr_week_lb2_l;
    lv_obj_t *app_hr_app_hr_hr_week_lb3_l;
    lv_obj_t *app_hr_app_hr_hr_week_lb4_l;
    lv_obj_t *app_hr_app_hr_hr_week_lb5_l;
    lv_obj_t *app_hr_app_hr_hr_week_lb6_l;
    lv_obj_t *app_hr_app_hr_t2_l;
    lv_obj_t *app_sleep_app_sleep_back_b;
    lv_obj_t *app_sleep_b_app_sleep_back_t_l;
    lv_obj_t *app_sleep_app_sleep_title_l;
    lv_obj_t *app_sleep_app_sleep_t0_l;
    lv_obj_t *app_sleep_app_sleep_t1_l;
    lv_obj_t *app_sleep_app_sleep_sl_stages_s0_c;
    lv_obj_t *app_sleep_app_sleep_sl_stages_s1_c;
    lv_obj_t *app_sleep_app_sleep_sl_stages_s2_c;
    lv_obj_t *app_sleep_app_sleep_sl_stages_s3_c;
    lv_obj_t *app_sleep_app_sleep_sl_legend_p0_c;
    lv_obj_t *app_sleep_app_sleep_sl_legend_t0_l;
    lv_obj_t *app_sleep_app_sleep_sl_legend_p1_c;
    lv_obj_t *app_sleep_app_sleep_sl_legend_t1_l;
    lv_obj_t *app_sleep_app_sleep_sl_legend_p2_c;
    lv_obj_t *app_sleep_app_sleep_sl_legend_t2_l;
    lv_obj_t *app_sleep_app_sleep_t2_l;
    lv_obj_t *app_spo2_app_spo2_back_b;
    lv_obj_t *app_spo2_b_app_spo2_back_t_l;
    lv_obj_t *app_spo2_app_spo2_title_l;
    lv_obj_t *app_spo2_so_ring;
    lv_obj_t *app_spo2_app_spo2_t0_l;
    lv_obj_t *app_spo2_app_spo2_t1_l;
    lv_obj_t *app_spo2_app_spo2_t2_l;
    lv_obj_t *app_spo2_app_spo2_so_measure_b;
    lv_obj_t *app_spo2_b_app_spo2_so_measure_t_l;
    lv_obj_t *app_weather_app_weather_back_b;
    lv_obj_t *app_weather_b_app_weather_back_t_l;
    lv_obj_t *app_weather_app_weather_title_l;
    lv_obj_t *app_weather_app_weather_t0_l;
    lv_obj_t *app_weather_app_weather_t1_l;
    lv_obj_t *app_weather_app_weather_wt_hours_r0_l_l;
    lv_obj_t *app_weather_app_weather_wt_hours_r0_r_l;
    lv_obj_t *app_weather_app_weather_wt_hours_r1_l_l;
    lv_obj_t *app_weather_app_weather_wt_hours_r1_r_l;
    lv_obj_t *app_weather_app_weather_wt_hours_r2_l_l;
    lv_obj_t *app_weather_app_weather_wt_hours_r2_r_l;
    lv_obj_t *app_weather_app_weather_wt_hours_r3_l_l;
    lv_obj_t *app_weather_app_weather_wt_hours_r3_r_l;
    lv_obj_t *app_weather_app_weather_t2_l;
    lv_obj_t *app_msg_app_msg_back_b;
    lv_obj_t *app_msg_b_app_msg_back_t_l;
    lv_obj_t *app_msg_app_msg_title_l;
    lv_obj_t *app_msg_app_msg_t0_l;
    lv_obj_t *app_msg_app_msg_ms_list_r0_l_l;
    lv_obj_t *app_msg_app_msg_ms_list_r0_r_l;
    lv_obj_t *app_msg_app_msg_ms_list_r1_l_l;
    lv_obj_t *app_msg_app_msg_ms_list_r1_r_l;
    lv_obj_t *app_msg_app_msg_ms_list_r2_l_l;
    lv_obj_t *app_msg_app_msg_ms_list_r2_r_l;
    lv_obj_t *app_msg_app_msg_ms_clear_b;
    lv_obj_t *app_msg_b_app_msg_ms_clear_t_l;
    lv_obj_t *app_music_app_music_back_b;
    lv_obj_t *app_music_b_app_music_back_t_l;
    lv_obj_t *app_music_app_music_title_l;
    lv_obj_t *app_music_app_music_mu_disc_c;
    lv_obj_t *app_music_app_music_mu_disc_hole_c;
    lv_obj_t *app_music_app_music_t0_l;
    lv_obj_t *app_music_app_music_t1_l;
    lv_obj_t *app_music_app_music_mu_prog_vl_l;
    lv_obj_t *app_music_mu_prog_bar;
    lv_obj_t *app_music_app_music_mu_ctrl_g0_b;
    lv_obj_t *app_music_b_app_music_mu_ctrl_g0_t_l;
    lv_obj_t *app_music_app_music_mu_ctrl_g1_b;
    lv_obj_t *app_music_b_app_music_mu_ctrl_g1_t_l;
    lv_obj_t *app_music_app_music_mu_ctrl_g2_b;
    lv_obj_t *app_music_b_app_music_mu_ctrl_g2_t_l;
    lv_obj_t *app_alarm_app_alarm_back_b;
    lv_obj_t *app_alarm_b_app_alarm_back_t_l;
    lv_obj_t *app_alarm_app_alarm_title_l;
    lv_obj_t *app_alarm_app_alarm_t0_l;
    lv_obj_t *app_alarm_app_alarm_t1_l;
    lv_obj_t *app_alarm_app_alarm_al_list_r0_l_l;
    lv_obj_t *app_alarm_app_alarm_al_list_r0_r_l;
    lv_obj_t *app_alarm_app_alarm_al_list_r1_l_l;
    lv_obj_t *app_alarm_app_alarm_al_list_r1_r_l;
    lv_obj_t *app_alarm_app_alarm_al_list_r2_l_l;
    lv_obj_t *app_alarm_app_alarm_al_list_r2_r_l;
    lv_obj_t *app_alarm_app_alarm_al_add_b;
    lv_obj_t *app_alarm_b_app_alarm_al_add_t_l;
    lv_obj_t *app_stopwatch_app_stopwatch_back_b;
    lv_obj_t *app_stopwatch_b_app_stopwatch_back_t_l;
    lv_obj_t *app_stopwatch_app_stopwatch_title_l;
    lv_obj_t *app_stopwatch_app_stopwatch_t0_l;
    lv_obj_t *app_stopwatch_app_stopwatch_sw_start_b;
    lv_obj_t *app_stopwatch_b_app_stopwatch_sw_start_t_l;
    lv_obj_t *app_stopwatch_app_stopwatch_sw_reset_b;
    lv_obj_t *app_stopwatch_b_app_stopwatch_sw_reset_t_l;
    lv_obj_t *app_timer_app_timer_back_b;
    lv_obj_t *app_timer_b_app_timer_back_t_l;
    lv_obj_t *app_timer_app_timer_title_l;
    lv_obj_t *app_timer_tm_ring;
    lv_obj_t *app_timer_app_timer_t0_l;
    lv_obj_t *app_timer_app_timer_tm_pause_b;
    lv_obj_t *app_timer_b_app_timer_tm_pause_t_l;
    lv_obj_t *app_timer_app_timer_tm_cancel_b;
    lv_obj_t *app_timer_b_app_timer_tm_cancel_t_l;
    lv_obj_t *app_calc_app_calc_back_b;
    lv_obj_t *app_calc_b_app_calc_back_t_l;
    lv_obj_t *app_calc_app_calc_title_l;
    lv_obj_t *app_calc_app_calc_t0_l;
    lv_obj_t *app_calc_app_calc_ca_keys_k0_b;
    lv_obj_t *app_calc_b_app_calc_ca_keys_k0_t_l;
    lv_obj_t *app_calc_app_calc_ca_keys_k1_b;
    lv_obj_t *app_calc_b_app_calc_ca_keys_k1_t_l;
    lv_obj_t *app_calc_app_calc_ca_keys_k2_b;
    lv_obj_t *app_calc_b_app_calc_ca_keys_k2_t_l;
    lv_obj_t *app_calc_app_calc_ca_keys_k3_b;
    lv_obj_t *app_calc_b_app_calc_ca_keys_k3_t_l;
    lv_obj_t *app_calc_app_calc_ca_keys_k4_b;
    lv_obj_t *app_calc_b_app_calc_ca_keys_k4_t_l;
    lv_obj_t *app_calc_app_calc_ca_keys_k5_b;
    lv_obj_t *app_calc_b_app_calc_ca_keys_k5_t_l;
    lv_obj_t *app_calc_app_calc_ca_keys_k6_b;
    lv_obj_t *app_calc_b_app_calc_ca_keys_k6_t_l;
    lv_obj_t *app_calc_app_calc_ca_keys_k7_b;
    lv_obj_t *app_calc_b_app_calc_ca_keys_k7_t_l;
    lv_obj_t *app_calc_app_calc_ca_keys_k8_b;
    lv_obj_t *app_calc_b_app_calc_ca_keys_k8_t_l;
    lv_obj_t *app_calc_app_calc_ca_keys_k9_b;
    lv_obj_t *app_calc_b_app_calc_ca_keys_k9_t_l;
    lv_obj_t *app_calc_app_calc_ca_keys_k10_b;
    lv_obj_t *app_calc_b_app_calc_ca_keys_k10_t_l;
    lv_obj_t *app_calc_app_calc_ca_keys_k11_b;
    lv_obj_t *app_calc_b_app_calc_ca_keys_k11_t_l;
    lv_obj_t *app_calc_app_calc_ca_keys_k12_b;
    lv_obj_t *app_calc_b_app_calc_ca_keys_k12_t_l;
    lv_obj_t *app_calc_app_calc_ca_keys_k13_b;
    lv_obj_t *app_calc_b_app_calc_ca_keys_k13_t_l;
    lv_obj_t *app_calc_app_calc_ca_keys_k14_b;
    lv_obj_t *app_calc_b_app_calc_ca_keys_k14_t_l;
    lv_obj_t *app_calc_app_calc_ca_keys_k15_b;
    lv_obj_t *app_calc_b_app_calc_ca_keys_k15_t_l;
    lv_obj_t *app_calc_app_calc_ca_keys_k16_b;
    lv_obj_t *app_calc_b_app_calc_ca_keys_k16_t_l;
    lv_obj_t *app_calc_app_calc_ca_keys_k17_b;
    lv_obj_t *app_calc_b_app_calc_ca_keys_k17_t_l;
    lv_obj_t *app_calc_app_calc_ca_keys_k18_b;
    lv_obj_t *app_calc_b_app_calc_ca_keys_k18_t_l;
    lv_obj_t *app_compass_app_compass_back_b;
    lv_obj_t *app_compass_b_app_compass_back_t_l;
    lv_obj_t *app_compass_app_compass_title_l;
    lv_obj_t *app_compass_cp_ring;
    lv_obj_t *app_compass_app_compass_t0_l;
    lv_obj_t *app_compass_app_compass_t1_l;
    lv_obj_t *app_compass_app_compass_t2_l;
    lv_obj_t *app_compass_app_compass_t3_l;
    lv_obj_t *app_compass_app_compass_t4_l;
    lv_obj_t *app_compass_app_compass_t5_l;
    lv_obj_t *app_compass_app_compass_t6_l;
    lv_obj_t *app_compass_app_compass_t7_l;
    lv_obj_t *app_compass_app_compass_t8_l;
    lv_obj_t *app_compass_app_compass_t9_l;
    lv_obj_t *app_findphone_app_findphone_back_b;
    lv_obj_t *app_findphone_b_app_findphone_back_t_l;
    lv_obj_t *app_findphone_app_findphone_title_l;
    lv_obj_t *app_findphone_app_findphone_fp_phone_c;
    lv_obj_t *app_findphone_app_findphone_t1_l;
    lv_obj_t *app_findphone_app_findphone_fp_ring_b;
    lv_obj_t *app_findphone_b_app_findphone_fp_ring_t_l;
    lv_obj_t *app_findphone_app_findphone_t2_l;
    lv_obj_t *app_settings_app_settings_back_b;
    lv_obj_t *app_settings_b_app_settings_back_t_l;
    lv_obj_t *app_settings_app_settings_title_l;
    lv_obj_t *app_settings_app_settings_se_list_r0_l_l;
    lv_obj_t *app_settings_app_settings_se_list_r0_r_l;
    lv_obj_t *app_settings_app_settings_se_list_r1_l_l;
    lv_obj_t *app_settings_app_settings_se_list_r1_r_l;
    lv_obj_t *app_settings_app_settings_se_list_r2_l_l;
    lv_obj_t *app_settings_app_settings_se_list_r2_r_l;
    lv_obj_t *app_settings_app_settings_se_list_r3_l_l;
    lv_obj_t *app_settings_app_settings_se_list_r3_r_l;
    lv_obj_t *app_settings_app_settings_se_list_r4_l_l;
    lv_obj_t *app_settings_app_settings_se_list_r4_r_l;
    lv_obj_t *app_settings_app_settings_se_list_r5_l_l;
    lv_obj_t *app_settings_app_settings_se_list_r5_r_l;
    lv_obj_t *alarm_editor_alarm_editor_back_b;
    lv_obj_t *alarm_editor_b_alarm_editor_back_t_l;
    lv_obj_t *alarm_editor_alarm_editor_title_l;
    lv_obj_t *alarm_editor_alarm_editor_ae_hour_up_b;
    lv_obj_t *alarm_editor_b_alarm_editor_ae_hour_up_t_l;
    lv_obj_t *alarm_editor_alarm_editor_ae_hour_dn_b;
    lv_obj_t *alarm_editor_b_alarm_editor_ae_hour_dn_t_l;
    lv_obj_t *alarm_editor_alarm_editor_ae_min_up_b;
    lv_obj_t *alarm_editor_b_alarm_editor_ae_min_up_t_l;
    lv_obj_t *alarm_editor_alarm_editor_ae_min_dn_b;
    lv_obj_t *alarm_editor_b_alarm_editor_ae_min_dn_t_l;
    lv_obj_t *alarm_editor_alarm_editor_t0_l;
    lv_obj_t *alarm_editor_alarm_editor_t1_l;
    lv_obj_t *alarm_editor_alarm_editor_t2_l;
    lv_obj_t *alarm_editor_alarm_editor_ae_days_c0_b;
    lv_obj_t *alarm_editor_b_alarm_editor_ae_days_c0_t_l;
    lv_obj_t *alarm_editor_alarm_editor_ae_days_c1_b;
    lv_obj_t *alarm_editor_b_alarm_editor_ae_days_c1_t_l;
    lv_obj_t *alarm_editor_alarm_editor_ae_days_c2_b;
    lv_obj_t *alarm_editor_b_alarm_editor_ae_days_c2_t_l;
    lv_obj_t *alarm_editor_alarm_editor_ae_days_c3_b;
    lv_obj_t *alarm_editor_b_alarm_editor_ae_days_c3_t_l;
    lv_obj_t *alarm_editor_alarm_editor_ae_days_c4_b;
    lv_obj_t *alarm_editor_b_alarm_editor_ae_days_c4_t_l;
    lv_obj_t *alarm_editor_alarm_editor_ae_days_c5_b;
    lv_obj_t *alarm_editor_b_alarm_editor_ae_days_c5_t_l;
    lv_obj_t *alarm_editor_alarm_editor_ae_days_c6_b;
    lv_obj_t *alarm_editor_b_alarm_editor_ae_days_c6_t_l;
    lv_obj_t *alarm_editor_alarm_editor_ae_opts_r0_l_l;
    lv_obj_t *alarm_editor_alarm_editor_ae_opts_r0_r_l;
    lv_obj_t *alarm_editor_alarm_editor_ae_opts_r1_l_l;
    lv_obj_t *alarm_editor_alarm_editor_ae_opts_r1_r_l;
    lv_obj_t *alarm_editor_alarm_editor_ae_save_b;
    lv_obj_t *alarm_editor_b_alarm_editor_ae_save_t_l;
    lv_obj_t *set_brightness_set_brightness_back_b;
    lv_obj_t *set_brightness_b_set_brightness_back_t_l;
    lv_obj_t *set_brightness_set_brightness_title_l;
    lv_obj_t *set_brightness_br_slider;
    lv_obj_t *set_brightness_set_brightness_t0_l;
    lv_obj_t *set_brightness_set_brightness_br_auto_t_l;
    lv_obj_t *set_brightness_br_auto;
    lv_obj_t *set_sound_set_sound_back_b;
    lv_obj_t *set_sound_b_set_sound_back_t_l;
    lv_obj_t *set_sound_set_sound_title_l;
    lv_obj_t *set_sound_sd_vol;
    lv_obj_t *set_sound_set_sound_t0_l;
    lv_obj_t *set_sound_set_sound_sd_cue_t_l;
    lv_obj_t *set_sound_sd_cue;
    lv_obj_t *set_sound_set_sound_sd_vib_t_l;
    lv_obj_t *set_sound_sd_vib;
    lv_obj_t *set_facestyle_set_facestyle_back_b;
    lv_obj_t *set_facestyle_b_set_facestyle_back_t_l;
    lv_obj_t *set_facestyle_set_facestyle_title_l;
    lv_obj_t *set_facestyle_set_facestyle_fs_items_f0_c;
    lv_obj_t *set_facestyle_set_facestyle_fs_items_v0_l;
    lv_obj_t *set_facestyle_set_facestyle_fs_items_n0_l;
    lv_obj_t *set_facestyle_set_facestyle_fs_items_f1_c;
    lv_obj_t *set_facestyle_set_facestyle_fs_items_v1_l;
    lv_obj_t *set_facestyle_set_facestyle_fs_items_n1_l;
    lv_obj_t *set_facestyle_set_facestyle_fs_items_f2_c;
    lv_obj_t *set_facestyle_set_facestyle_fs_items_v2_l;
    lv_obj_t *set_facestyle_set_facestyle_fs_items_n2_l;
    lv_obj_t *set_facestyle_set_facestyle_fs_apply_b;
    lv_obj_t *set_facestyle_b_set_facestyle_fs_apply_t_l;
    lv_obj_t *set_bt_set_bt_back_b;
    lv_obj_t *set_bt_b_set_bt_back_t_l;
    lv_obj_t *set_bt_set_bt_title_l;
    lv_obj_t *set_bt_set_bt_t0_l;
    lv_obj_t *set_bt_set_bt_t1_l;
    lv_obj_t *set_bt_set_bt_bt_others_r0_l_l;
    lv_obj_t *set_bt_set_bt_bt_others_r0_r_l;
    lv_obj_t *set_bt_set_bt_bt_others_r1_l_l;
    lv_obj_t *set_bt_set_bt_bt_others_r1_r_l;
    lv_obj_t *set_bt_set_bt_bt_disc_b;
    lv_obj_t *set_bt_b_set_bt_bt_disc_t_l;
    lv_obj_t *set_dnd_set_dnd_back_b;
    lv_obj_t *set_dnd_b_set_dnd_back_t_l;
    lv_obj_t *set_dnd_set_dnd_title_l;
    lv_obj_t *set_dnd_set_dnd_dn_on_t_l;
    lv_obj_t *set_dnd_dn_on;
    lv_obj_t *set_dnd_set_dnd_dn_sched_r0_l_l;
    lv_obj_t *set_dnd_set_dnd_dn_sched_r0_r_l;
    lv_obj_t *set_dnd_set_dnd_dn_sched_r1_l_l;
    lv_obj_t *set_dnd_set_dnd_dn_sched_r1_r_l;
    lv_obj_t *set_dnd_set_dnd_t0_l;
    lv_obj_t *set_about_set_about_back_b;
    lv_obj_t *set_about_b_set_about_back_t_l;
    lv_obj_t *set_about_set_about_title_l;
    lv_obj_t *set_about_set_about_ab_list_r0_l_l;
    lv_obj_t *set_about_set_about_ab_list_r0_r_l;
    lv_obj_t *set_about_set_about_ab_list_r1_l_l;
    lv_obj_t *set_about_set_about_ab_list_r1_r_l;
    lv_obj_t *set_about_set_about_ab_list_r2_l_l;
    lv_obj_t *set_about_set_about_ab_list_r2_r_l;
    lv_obj_t *set_about_set_about_ab_list_r3_l_l;
    lv_obj_t *set_about_set_about_ab_list_r3_r_l;
    lv_obj_t *set_about_set_about_ab_list_r4_l_l;
    lv_obj_t *set_about_set_about_ab_list_r4_r_l;
    lv_obj_t *set_about_set_about_ab_update_b;
    lv_obj_t *set_about_b_set_about_ab_update_t_l;
} objects_t;

extern objects_t objects;

void create_screen_tab_main();
void tick_screen_tab_main();

void create_screen_app_sport();
void tick_screen_app_sport();

void create_screen_app_hr();
void tick_screen_app_hr();

void create_screen_app_sleep();
void tick_screen_app_sleep();

void create_screen_app_spo2();
void tick_screen_app_spo2();

void create_screen_app_weather();
void tick_screen_app_weather();

void create_screen_app_msg();
void tick_screen_app_msg();

void create_screen_app_music();
void tick_screen_app_music();

void create_screen_app_alarm();
void tick_screen_app_alarm();

void create_screen_app_stopwatch();
void tick_screen_app_stopwatch();

void create_screen_app_timer();
void tick_screen_app_timer();

void create_screen_app_calc();
void tick_screen_app_calc();

void create_screen_app_compass();
void tick_screen_app_compass();

void create_screen_app_findphone();
void tick_screen_app_findphone();

void create_screen_app_settings();
void tick_screen_app_settings();

void create_screen_alarm_editor();
void tick_screen_alarm_editor();

void create_screen_set_brightness();
void tick_screen_set_brightness();

void create_screen_set_sound();
void tick_screen_set_sound();

void create_screen_set_facestyle();
void tick_screen_set_facestyle();

void create_screen_set_bt();
void tick_screen_set_bt();

void create_screen_set_dnd();
void tick_screen_set_dnd();

void create_screen_set_about();
void tick_screen_set_about();

void tick_screen_by_id(enum ScreensEnum screenId);
void tick_screen(int screen_index);

void create_screens();

#ifdef __cplusplus
}
#endif

#endif /*EEZ_LVGL_UI_SCREENS_H*/