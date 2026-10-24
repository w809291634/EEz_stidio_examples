/*
 * watch 工程 PC 仿真入口（design/sim_cmake/main.c）
 * ---------------------------------------------------------------------------
 * no flow + native 导航（第⑤步口径：先接跳转，细节功能第⑦步）：
 *  - 分辨率 466x466，与 EEZ 工程 displayWidth/Height 一致。
 *  - flowSupport=false ⇒ ui_init() 走 create_screens() 分支；
 *    watch_nav_init() 在其后（objects.* 句柄建好才能绑）。
 *  - WATCH_AUTOTEST=1：无头导航自证——按清单表逐条 tap 跳转并断言落点，
 *    每屏拍一张 BMP 到当前目录（sim.py 收集对照 designer/）。
 *    需要本工程 lv_conf.h 里 LV_USE_SNAPSHOT 1。
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "lvgl.h"
#include "SDL2/SDL.h"
#include "lv_sdl_window.h"
#include "ui.h"
#include "screens.h"
#include "navigation/watch_nav.h"
#include "widgets/applist/watch_list_native.h"
#include "src/others/snapshot/lv_snapshot.h"

extern objects_t objects;
extern void ui_init(void);
extern void ui_tick(void);

#define SIM_W 466
#define SIM_H 466

static void take_shot(const char *path)
{
    lv_draw_buf_t *buf = lv_snapshot_take(lv_screen_active(), LV_COLOR_FORMAT_XRGB8888);
    if (!buf) { printf("[SHOT] snapshot failed %s\n", path); return; }
    int w = (int)buf->header.w, h = (int)buf->header.h;
    int stride = (int)buf->header.stride;
    unsigned char *src = (unsigned char *)buf->data;
    FILE *fp = fopen(path, "wb");
    if (fp) {
        int row = w * 4, data = row * h;
        unsigned char hd[54] = { 'B','M' };
        *(int *)(hd + 2) = 54 + data;
        *(int *)(hd + 10) = 54;
        *(int *)(hd + 14) = 40;
        *(int *)(hd + 18) = w;
        *(int *)(hd + 22) = -h;
        *(short *)(hd + 26) = 1;
        *(short *)(hd + 28) = 32;
        fwrite(hd, 1, 54, fp);
        for (int y = 0; y < h; y++) fwrite(src + y * stride, 1, row, fp);
        fclose(fp);
        printf("[SHOT] saved %s\n", path);
    }
    lv_draw_buf_destroy(buf);
}

static void pump(int n)
{
    for (int i = 0; i < n; i++) {
        lv_tick_inc(5);
        lv_timer_handler();
        usleep(5000);
    }
}

static int g_pass, g_fail;

static void expect_scr(lv_obj_t *want, const char *tag)
{
    int ok = (lv_screen_active() == want);
    printf("[NAV] %-40s %s\n", tag, ok ? "PASS" : "FAIL");
    if (ok) g_pass++; else g_fail++;
}

static void expect_tab(int want, const char *tag)
{
    int ok = (lv_tabview_get_tab_act(objects.tv_main) == want);
    printf("[NAV] %-40s %s\n", tag, ok ? "PASS" : "FAIL");
    if (ok) g_pass++; else g_fail++;
}

static void expect_center(int want, const char *tag)
{
    int got = watch_list_center_index();
    int ok = (got == want);
    printf("[NAV] %-40s %s (got=%d want=%d)\n", tag, ok ? "PASS" : "FAIL", got, want);
    if (ok) g_pass++; else g_fail++;
}

static void expect_text(lv_obj_t *obj, const char *want, const char *tag)
{
    const char *got = obj ? lv_label_get_text(obj) : "<null>";
    int ok = (strcmp(got, want) == 0);
    printf("[LOGIC] %-36s %s (got=%s want=%s)\n", tag, ok ? "PASS" : "FAIL", got, want);
    if (ok) g_pass++; else g_fail++;
}

static void expect_clock_from_pc(void)
{
    const char *clock = lv_label_get_text(objects.watchface_watchface_t0_l);
    int ok = strlen(clock) == 5 && clock[2] == ':';
    printf("[LOGIC] %-36s %s (clock=%s)\n", "表盘读取 PC 本地时间", ok ? "PASS" : "FAIL", clock);
    if (ok) g_pass++; else g_fail++;
}

static void tap(lv_obj_t *o)
{
    lv_obj_send_event(o, LV_EVENT_CLICKED, NULL);
    pump(6);
}

static void logic_smoke(void)
{
    /* 这些检查直接驱动生成控件的事件，覆盖第⑦步状态层的本地可闭环功能。 */
    tap(objects.app_msg_app_msg_ms_clear_b);
    expect_text(objects.app_msg_app_msg_t0_l, "0 条未读", "消息清空");

    tap(objects.app_stopwatch_app_stopwatch_sw_start_b);
    pump(24);
    {
        const char *v = lv_label_get_text(objects.app_stopwatch_app_stopwatch_t0_l);
        int ok = strcmp(v, "00:00.00") != 0;
        printf("[LOGIC] %-36s %s (value=%s)\n", "秒表开始计时", ok ? "PASS" : "FAIL", v);
        if (ok) g_pass++; else g_fail++;
    }
    tap(objects.app_stopwatch_app_stopwatch_sw_reset_b);
    expect_text(objects.app_stopwatch_app_stopwatch_t0_l, "00:00.00", "秒表复位");

    tap(objects.app_timer_app_timer_tm_cancel_b);
    expect_text(objects.app_timer_app_timer_t0_l, "05:00", "倒计时取消复位");

    tap(objects.app_calc_app_calc_ca_keys_k12_b); /* 1 */
    tap(objects.app_calc_app_calc_ca_keys_k15_b); /* + */
    tap(objects.app_calc_app_calc_ca_keys_k13_b); /* 2 */
    tap(objects.app_calc_app_calc_ca_keys_k18_b); /* = */
    expect_text(objects.app_calc_app_calc_t0_l, "3", "计算器 1+2");

    tap(objects.app_spo2_app_spo2_so_measure_b);
    expect_text(objects.app_spo2_app_spo2_t1_l, "测量", "血氧进入测量态");
    pump(330);
    expect_text(objects.app_spo2_app_spo2_t0_l, "98%", "血氧测量完成");

    tap(objects.alarm_editor_alarm_editor_ae_hour_up_b);
    expect_text(objects.alarm_editor_alarm_editor_t0_l, "08", "闹钟小时步进");
    tap(objects.alarm_editor_alarm_editor_ae_save_b);
    expect_text(objects.app_alarm_app_alarm_t0_l, "08:00", "闹钟保存回显");

    lv_slider_set_value(objects.set_brightness_br_slider, 82, LV_ANIM_OFF);
    lv_obj_send_event(objects.set_brightness_br_slider, LV_EVENT_VALUE_CHANGED, NULL);
    expect_text(objects.set_brightness_set_brightness_t0_l, "82%", "亮度滑条回显");

    tap(objects.set_bt_set_bt_bt_disc_b);
    expect_text(objects.set_bt_set_bt_t0_l, "BLE OFF", "蓝牙断开模拟态");

    /* ae_save 的真实导航会切到 app_alarm；导航回归从 tab1 的标准入口继续。 */
    if (lv_screen_active() != objects.tab_main)
        lv_screen_load_anim(objects.tab_main, LV_SCR_LOAD_ANIM_NONE, 0, 0, false);
    lv_tabview_set_active(objects.tv_main, 1, LV_ANIM_OFF);
    pump(4);
}

static const char *APP_TAGS[14] = {
    "app_sport", "app_hr", "app_sleep", "app_spo2", "app_weather", "app_msg",
    "app_music", "app_alarm", "app_stopwatch", "app_timer", "app_calc",
    "app_compass", "app_findphone", "app_settings" };
static const char *SET_TAGS[6] = {
    "set_brightness", "set_sound", "set_facestyle", "set_bt", "set_dnd",
    "set_about" };

static void nav_walk(void)
{
    char path[128];

    printf("[NAV] ===== 导航闭环自证（清单表 44 项中的跳转边） =====\n");

    /* tab_main：tab0 表盘 + tab1 applist（tabview 原生滑切，这里直接 API 切） */
    snprintf(path, sizeof(path), "shot_tab_main_tab0.bmp");
    take_shot(path);
    lv_tabview_set_active(objects.tv_main, 1, LV_ANIM_OFF);
    pump(16);   /* 跨过 60ms 定时器：落点每拍校验，等它稳再拍 */
    expect_tab(1, "tabview 切到 applist");
    take_shot("shot_applist.bmp");
    expect_clock_from_pc();
    logic_smoke();

    /* 边界回归：首尾可以被拖过中心，但静止后必须回弹到第 2 / 倒数第 2 项。 */
    watch_list_center_no_clamp(0, false);
    watch_list_snap_edge();
    pump(80);
    expect_center(watch_list_center_min(), "首项不能留在中心");
    watch_list_center_no_clamp(watch_list_center_max() + 1, false);
    watch_list_snap_edge();
    pump(80);
    expect_center(watch_list_center_max(), "末项不能留在中心");
    watch_list_center(watch_list_center_min(), false);
    pump(4);

    /* 横向穿透：右滑(dx>0)=上一页，左滑=下一页（全屏子对象不该吃掉父级切页） */
    {
        int ok1, ok2;
        lv_tabview_set_active(objects.tv_main, 1, LV_ANIM_OFF);
        pump(4);
        watch_list_swipe_to(120, 4);
        pump(4);
        ok1 = (lv_tabview_get_tab_act(objects.tv_main) == 0);
        watch_list_swipe_to(-120, 4);
        pump(4);
        ok2 = (lv_tabview_get_tab_act(objects.tv_main) == 1);
        printf("[NAV] %-40s %s\n", "右滑回表盘（横向穿透）", ok1 ? "PASS" : "FAIL");
        if (ok1) g_pass++; else g_fail++;
        printf("[NAV] %-40s %s\n", "左滑进 applist（横向穿透）", ok2 ? "PASS" : "FAIL");
        if (ok2) g_pass++; else g_fail++;
    }

    /* applist 滚轮 14 行 → 各 APP 页 → back 回 applist */
    for (int i = 0; i < 14; i++) {
        lv_obj_t *row = watch_nav_app_row(i);
        if (!row) { printf("[NAV] row %d MISSING\n", i); g_fail++; continue; }
        tap(row);
        expect_scr(watch_nav_app_screen(i), APP_TAGS[i]);
        snprintf(path, sizeof(path), "shot_%s.bmp", APP_TAGS[i]);
        take_shot(path);
        /* 页内 back 钮：app_* 的 back 句柄在 screens.h；统一从 objects 取 */
        lv_obj_t *back = NULL;
        /* 用行内首个可点钮不行——back 是屏的直接子件，按 identifier 顺序不可达；
         * 直接触发绑定的回调等价：找屏上带 CLICKED cb 的 back 钮。
         * 简化：watch_nav 暴露的屏对象里第 2 个子件规律不保证，改用事件重放：
         * 通过 lv_obj_get_child 遍历找有 event 的按钮。 */
        uint32_t n = lv_obj_get_child_count(watch_nav_app_screen(i));
        for (uint32_t k = 0; k < n && !back; k++) {
            lv_obj_t *c = lv_obj_get_child(watch_nav_app_screen(i), k);
            if (lv_obj_has_flag(c, LV_OBJ_FLAG_CLICKABLE) &&
                lv_obj_get_width(c) <= 44) back = c;   /* back 钮 40px 宽 */
        }
        if (back) {
            tap(back);
            expect_tab(1, "back → applist tab");
            if (i == 0)
                expect_center(watch_list_center_min(), "点击首项返回后仍停第 2 项");
            if (i == 13)
                expect_center(watch_list_center_max(), "点击末项返回后仍停倒数第 2 项");
        }
        else { printf("[NAV] back button not found on %s\n", APP_TAGS[i]); g_fail++; }
    }

    /* 闹钟链：al_add → editor → ae_save → app_alarm → back → applist */
    tap(watch_nav_app_row(7));                       /* 闹钟行 */
    {
        lv_obj_t *scr = watch_nav_app_screen(7);
        lv_obj_t *al_add = NULL;
        uint32_t n = lv_obj_get_child_count(scr);
        for (uint32_t k = 0; k < n; k++) {
            lv_obj_t *c = lv_obj_get_child(scr, k);
            if (lv_obj_has_flag(c, LV_OBJ_FLAG_CLICKABLE) &&
                lv_obj_get_width(c) > 100) { al_add = c; break; }
        }
        if (al_add) { tap(al_add); expect_scr(objects.alarm_editor, "al_add → alarm_editor"); }
    }
    take_shot("shot_alarm_editor.bmp");
    {
        uint32_t n = lv_obj_get_child_count(objects.alarm_editor);
        for (uint32_t k = 0; k < n; k++) {
            lv_obj_t *c = lv_obj_get_child(objects.alarm_editor, k);
            if (lv_obj_has_flag(c, LV_OBJ_FLAG_CLICKABLE) &&
                lv_obj_get_width(c) >= 140 && lv_obj_get_y(c) > 380) {
                tap(c);   /* ae_save */
                expect_scr(objects.app_alarm, "ae_save → app_alarm");
                break;
            }
        }
    }

    /* 设置链：6 行 → set_* → back；fs_apply → tab0 */
    tap(watch_nav_app_row(13));                      /* 设置行 */
    for (int i = 0; i < 6; i++) {
        tap(watch_nav_set_hit(i));
        expect_scr(watch_nav_set_screen(i), SET_TAGS[i]);
        char p2[128];
        snprintf(p2, sizeof(p2), "shot_%s.bmp", SET_TAGS[i]);
        take_shot(p2);
        if (i == 2) {   /* set_facestyle：fs_apply（底部大按钮）→ tab_main tab0 */
            lv_obj_t *scr = watch_nav_set_screen(2);
            uint32_t n = lv_obj_get_child_count(scr);
            for (uint32_t k = 0; k < n; k++) {
                lv_obj_t *c = lv_obj_get_child(scr, k);
                if (lv_obj_has_flag(c, LV_OBJ_FLAG_CLICKABLE) &&
                    lv_obj_get_width(c) >= 140 && lv_obj_get_y(c) > 300) {
                    tap(c);
                    expect_scr(objects.tab_main, "fs_apply → tab_main");
                    expect_tab(0, "fs_apply 后在表盘 tab");
                    lv_tabview_set_active(objects.tv_main, 1, LV_ANIM_OFF);
                    pump(2);
                    break;
                }
            }
        } else {
            lv_obj_t *scr = watch_nav_set_screen(i);
            uint32_t n = lv_obj_get_child_count(scr);
            lv_obj_t *back = NULL;
            for (uint32_t k = 0; k < n && !back; k++) {
                lv_obj_t *c = lv_obj_get_child(scr, k);
                if (lv_obj_has_flag(c, LV_OBJ_FLAG_CLICKABLE) &&
                    lv_obj_get_width(c) <= 44) back = c;
            }
            if (back) { tap(back); expect_scr(objects.app_settings, "back → app_settings"); }
        }
    }

    printf("[NAV] ===== RESULT: PASS %d / FAIL %d =====\n", g_pass, g_fail);
    if (getenv("WATCH_AUTOEXIT")) exit(g_fail ? 2 : 0);
}

static lv_display_t *hal_init(int32_t w, int32_t h)
{
    lv_group_set_default(lv_group_create());
    lv_display_t *disp = lv_sdl_window_create(w, h);
    lv_indev_t *mouse = lv_sdl_mouse_create();
    lv_indev_set_group(mouse, lv_group_get_default());
    lv_indev_set_display(mouse, disp);
    lv_display_set_default(disp);
    LV_IMAGE_DECLARE(mouse_cursor_icon);
    lv_obj_t *cursor_obj = lv_image_create(lv_screen_active());
    lv_image_set_src(cursor_obj, &mouse_cursor_icon);
    lv_indev_set_cursor(mouse, cursor_obj);
    lv_indev_t *wheel = lv_sdl_mousewheel_create();
    lv_indev_set_display(wheel, disp);
    lv_indev_set_group(wheel, lv_group_get_default());
    lv_indev_t *kb = lv_sdl_keyboard_create();
    lv_indev_set_display(kb, disp);
    lv_indev_set_group(kb, lv_group_get_default());
    return disp;
}

int main(int argc, char **argv)
{
    (void)argc;
    (void)argv;

    lv_init();
    hal_init(SIM_W, SIM_H);
    ui_init();
    watch_nav_init();

    static int ticks = 0;
    if (getenv("WATCH_AUTOTEST")) {
        /* 无头模式：不进窗口循环，直接走完导航再退 */
        pump(20);
        nav_walk();
    }

    while (1) {
        lv_tick_inc(2);
        lv_timer_handler();
        ui_tick();
        usleep(4000);
        (void)ticks;
    }
    return 0;
}
