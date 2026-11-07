/*
 * w78 智能家居 —— PC 仿真入口（design/sim_cmake/main.c）
 *
 * 800×480；EEZ no-flow 工程：ui_init() 建屏并载主控，导航由 src/native/nav_bind.c
 * 按 nav_bind_table.h 统一挂回调。
 *
 * 无头验证：W78_AUTOTEST=1
 *   逐条 NAV_BIND 边注入真实 SDL 鼠标事件（走 LVGL indev 命中测试），
 *   断言 lv_screen_active() == 目标屏；返回边先 seed 一条来路再点。
 *   全 PASS 退出码 0，否则打印 FAIL 列表并非 0。
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "lvgl.h"
#include "SDL2/SDL.h"
#include "lv_sdl_window.h"
#include "ui.h"
#include "screens.h"
#include "nav_bind.h"
#include "ui_bg.h"
#include "value_bind.h"
#include "ui_behavior.h"
#include "platform/pc/sim_reads.h"
#include "platform/pc/sim_fs.h"
#include "platform/pc/sim_video.h"
#include "app/boot_selftest.h"
#include "nav_bind_table.h"
#include "app/wifi_logic.h"
#include "app/wifi_events.h"
#include "navigation/wifi_bind.h"
#include "navigation/wifi_nav.h"
#include "widgets/wifi_busy/wifi_busy.h"
#include "app/wifi_model.h"
#include "platform/wifi_platform.h"
#include "src/others/snapshot/lv_snapshot.h"

#define SIM_W 800
#define SIM_H 480

/* lv_sdl_private.h 里的内部函数：把 SDL 事件喂给鼠标 indev（真命中测试） */
void lv_sdl_mouse_handler(SDL_Event *event);

static lv_display_t *hal_init(int32_t w, int32_t h)
{
    lv_group_set_default(lv_group_create());
    lv_display_t *disp = lv_sdl_window_create(w, h);
    lv_indev_t *mouse = lv_sdl_mouse_create();
    lv_indev_set_group(mouse, lv_group_get_default());
    lv_indev_set_display(mouse, disp);
    lv_display_set_default(disp);
    return disp;
}

static void take_shot_obj(lv_obj_t *obj, const char *path)
{
    lv_draw_buf_t *buf = lv_snapshot_take(obj, LV_COLOR_FORMAT_XRGB8888);
    if (!buf) { printf("[SHOT] snapshot failed\n"); return; }
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
        for (int y = 0; y < h; y++)
            fwrite(src + y * stride, 1, row, fp);
        fclose(fp);
        printf("[SHOT] saved %s (%dx%d)\n", path, w, h);
    }
    lv_draw_buf_destroy(buf);
}

static void take_shot(const char *path)
{
    take_shot_obj(lv_screen_active(), path);
}

static void push_mouse(uint32_t type, int x, int y){
    SDL_Event e;
    SDL_memset(&e, 0, sizeof(e));
    e.type = type;
    e.button.windowID = 0;      /* 0: 让 lv_sdl_mouse 走默认 indev 查找 */
    e.button.button = SDL_BUTTON_LEFT;
    e.button.state = (type == SDL_MOUSEBUTTONDOWN) ? SDL_PRESSED : SDL_RELEASED;
    e.button.x = x;
    e.button.y = y;
    SDL_PushEvent(&e);
}

static void pump(int frames)
{
    int i;
    for (i = 0; i < frames; i++) {
        SDL_Event e;
        while (SDL_PollEvent(&e)) lv_sdl_mouse_handler(&e);
        SDL_Delay(10);
        lv_tick_inc(10);
        lv_timer_handler();
        sim_reads_tick();
    }
}

static void click_obj(lv_obj_t *obj)
{
    lv_area_t a;
    int x, y;
    lv_indev_t *mi = lv_indev_get_next(NULL);
    while (mi && lv_indev_get_type(mi) != LV_INDEV_TYPE_POINTER)
        mi = lv_indev_get_next(mi);
    lv_obj_get_coords(obj, &a);
    x = (a.x1 + a.x2) / 2;
    y = (a.y1 + a.y2) / 2;
    pump(6);                              /* 排空上一帧 + 等 indev 采样周期 */
    push_mouse(SDL_MOUSEBUTTONUP, x, y);
    pump(6);
    push_mouse(SDL_MOUSEBUTTONDOWN, x, y);
    pump(8);                              /* 等 indev 读到 PRESSED 并派发 */
    push_mouse(SDL_MOUSEBUTTONUP, x, y);
    pump(8);                              /* 等 CLICKED 派发 + 页面加载 */
    (void)mi;
}

static int autotest(void)
{
    int i, pass = 0, fail = 0;
    printf("[NAV] 开始：%d 条边\n", NAV_BIND_COUNT);
    for (i = 0; i < NAV_BIND_COUNT; i++) {
        const nav_bind_entry_t *b = &NAV_BIND[i];
        lv_obj_t *obj = *b->obj;
        int expect;
        if (!obj) {
            printf("[NAV] FAIL %s 对象为空\n", b->back ? "(back)" : "(nav)");
            fail++;
            continue;
        }
        if (b->back) {
            loadScreen((enum ScreensEnum)b->src);   /* 返回键属于源屏，必须先把它显示出来 */
            pump(4);
            nav_bind_seed(b->src, SCREEN_ID_MAIN);
            expect = SCREEN_ID_MAIN;
        } else {
            nav_bind_seed(b->src, 0);
            loadScreen((enum ScreensEnum)b->src);
            pump(3);
            expect = b->dst;
        }
        click_obj(obj);
        if (lv_screen_active() == nav_screen_obj(expect) && nav_bind_current() == expect) {
            pass++;
        } else {
            printf("[NAV] FAIL edge#%d src=%d dst=%d back=%d active=%p expect=%p\n",
                   i, b->src, b->dst, b->back,
                   (void *)lv_screen_active(), (void *)nav_screen_obj(expect));
            fail++;
        }
    }
    printf("[NAV] %d/%d PASS%s\n", pass, NAV_BIND_COUNT, fail ? "（有 FAIL）" : " 全部通过");
    return fail ? 1 : 0;
}

static int behavior_test(void)
{
    int fail = 0;
    const char *txt;

#define CHECK(cond, msg) do { \
    if (!(cond)) { printf("[UI_BEHAVIOR] FAIL %s\n", msg); fail++; } \
} while (0)

    lv_screen_load(objects.detail_curtain);
    pump(6);
    click_obj(objects.detail_curtain_hw02);       /* 全开 */
    pump(6);
    CHECK(lv_slider_get_value(objects.detail_curtain_hw01_sl) == 100, "curtain 100");
    txt = lv_label_get_text(objects.detail_curtain_r02);
    printf("[UI_BEHAVIOR] curtain slider=%d r02='%s'\n",
           (int)lv_slider_get_value(objects.detail_curtain_hw01_sl), txt ? txt : "(null)");
    CHECK(txt && strstr(txt, "100"), "curtain label 100");
    click_obj(objects.detail_curtain_hw03);       /* 半开 */
    pump(6);
    CHECK(lv_slider_get_value(objects.detail_curtain_hw01_sl) == 50, "curtain 50");
    click_obj(objects.detail_curtain_hw04);       /* 全关 */
    pump(6);
    CHECK(lv_slider_get_value(objects.detail_curtain_hw01_sl) == 0, "curtain 0");

    lv_screen_load(objects.detail_ac);
    pump(6);
    click_obj(objects.detail_ac_hw02);            /* 温度 + */
    pump(4);
    printf("[UI_BEHAVIOR] ac_temp=%d\n", ui_behavior_ac_temp());
    CHECK(ui_behavior_ac_temp() == 240, "ac +0.5");
    txt = lv_label_get_text(objects.detail_ac_hr02);
    CHECK(txt && strstr(txt, "24.0"), "ac label 24.0");
    click_obj(objects.detail_ac_hw04);            /* 制热 */
    pump(4);
    printf("[UI_BEHAVIOR] ac_mode=%d\n", ui_behavior_ac_mode());
    CHECK(ui_behavior_ac_mode() == 1, "ac heat");
    txt = lv_label_get_text(objects.detail_ac_hr01);
    CHECK(txt && strstr(txt, "制热"), "ac header heat");
    click_obj(objects.detail_ac_hw08);            /* 高风 */
    pump(4);
    printf("[UI_BEHAVIOR] fan=%d\n", ui_behavior_fan());
    CHECK(ui_behavior_fan() == 2, "fan high");

    lv_screen_load(objects.main);
    pump(6);
    click_obj(objects.main_hw02);                 /* 离家 */
    pump(4);
    printf("[UI_BEHAVIOR] scene=%d\n", ui_behavior_scene());
    CHECK(ui_behavior_scene() == 1, "scene leave");

    printf("[UI_BEHAVIOR] %s\n", fail ? "FAIL" : "PASS");
#undef CHECK
    return fail ? 1 : 0;
}

static int sim_test(void)
{
    char a[64], b[64], c[64], d[64], e[64], f[64], g[64], h[64];
    const char *t;
    int i;
    pump(4);
#define GRAB(dst, obj) do { \
        t = (obj) ? lv_label_get_text(obj) : ""; \
        snprintf(dst, sizeof(dst), "%s", t ? t : ""); } while (0)
    GRAB(a, objects.main_hr03);
    GRAB(c, objects.detail_sensor_hr03);
    GRAB(e, objects.energy_hr03);
    GRAB(g, objects.detail_light_hr05);
    for (i = 0; i < 50; i++) {          /* SDL 端口用真实时钟（SDL_GetTicks），等 1.5s 才过 1 个外部读节拍 */
        SDL_Delay(30);
        lv_timer_handler();
        sim_reads_tick();
    }
    GRAB(b, objects.main_hr03);
    GRAB(d, objects.detail_sensor_hr03);
    GRAB(f, objects.energy_hr03);
    GRAB(h, objects.detail_light_hr05);
    printf("[SIM] main_hr03 '%s' → '%s'\n", a, b);
    printf("[SIM] sensor_temp '%s' → '%s'\n", c, d);
    printf("[SIM] energy_hr03 '%s' → '%s'\n", e, f);
    printf("[SIM] light_min '%s' → '%s'\n", g, h);
    i = strcmp(g, h) != 0;              /* 分钟计数每秒必增，作为"外部读在变"的硬判据 */
    printf("[SIM] %s\n", i ? "PASS" : "FAIL");
#undef GRAB
    return i ? 0 : 1;
}

static int fs_test(void)
{
    lv_fs_file_t f;
    uint32_t br = 0;
    char buf[64] = { 0 };
    int ok;
    lv_fs_res_t r = lv_fs_open(&f, "A:/assets/fs_probe.txt", LV_FS_MODE_RD);
    if (r != LV_FS_RES_OK) {
        printf("[FS] open A:/assets/fs_probe.txt FAIL res=%d\n", (int)r);
        return 1;
    }
    lv_fs_read(&f, buf, sizeof(buf) - 1, &br);
    lv_fs_close(&f);
    printf("[FS] read %u bytes: '%s'\n", (unsigned)br, buf);
    ok = strstr(buf, "w78-fs-ok") != NULL;
    printf("[FS] %s\n", ok ? "PASS" : "FAIL");
    return ok ? 0 : 1;
}

static int boot_test(void)
{
    int i, shot = 0;
    boot_selftest_start();
    for (i = 0; i < 6000 && (boot_selftest_active() || sim_video_active()); i++) {
        if (i == 40) take_shot_obj(lv_layer_top(), "tmp/boot_selftest.bmp");
        if (!shot && sim_video_frames() >= 30) {
            take_shot_obj(lv_layer_top(), "tmp/boot_video.bmp");
            shot = 1;
        }
        pump(2);
    }
    printf("[BOOT] selftest=%d video=%d active=%d\n", boot_selftest_progress(),
           sim_video_frames(), (int)sim_video_active());
    take_shot("tmp/main_bg.bmp");            /* 视频结束后主界面：目检固定背景图 */
    i = (boot_selftest_progress() == 100 && sim_video_frames() > 0 && !sim_video_active());
    printf("[BOOT] %s\n", i ? "PASS" : "FAIL");
    return i ? 0 : 1;
}

int main(int argc, char **argv)
{
    int auto_mode = getenv("W78_AUTOTEST") != NULL ||
                    getenv("W78_UI_BEHAVIOR_TEST") != NULL ||
                    getenv("W78_FS_TEST") != NULL ||
                    getenv("W78_BOOT_TEST") != NULL;
    setvbuf(stdout, NULL, _IONBF, 0);
    (void)argc; (void)argv;
    if (auto_mode) SDL_setenv("SDL_VIDEODRIVER", "dummy", 0);

    lv_init();
    sim_fs_init();
    hal_init(SIM_W, SIM_H);
    ui_init();
    ui_bg_apply();                           /* 固定背景图：A:/assets/ui_bg.png */
    nav_bind_init();
    value_bind_init();
    ui_behavior_init();
    sim_reads_init();

    if (getenv("W78_UI_BEHAVIOR_TEST")) {
        int rc;
        pump(5);
        rc = behavior_test();
        SDL_Quit();
        return rc;
    }

    if (getenv("W78_FS_TEST")) {           /* 自证：A: 能读到工程内文件 */
        int rc;
        pump(2);
        rc = fs_test();
        SDL_Quit();
        return rc;
    }

    if (getenv("W78_BOOT_TEST")) {         /* 自证：开机动画按帧播完并自动收起 */
        int rc;
        rc = boot_test();
        SDL_Quit();
        return rc;
    }

    if (getenv("W78_SIM_TEST")) {          /* 自证：外部读真的在变 */
        int rc;
        pump(5);
        rc = sim_test();
        SDL_Quit();
        return rc;
    }

    if (getenv("W78_QUIT_TEST")) {          /* 自证窗口关闭链路：压一个 SDL_QUIT，应干净退出 0 */
        SDL_Event q;
        SDL_memset(&q, 0, sizeof(q));
        q.type = SDL_QUIT;
        SDL_PushEvent(&q);
        printf("[QUIT] SDL_QUIT queued\n");
    }

    if (getenv("W78_WIFI_TEST")) {          /* ⑦-1 自证：PC 端真 wlanapi 扫描 → 平台接口 */
        int i, n;
        io_init();
        io_wifi_scan(1);
        for (i = 0; i < 80; i++) {
            io_sample_inputs();
            if (app_get_input_i(APP_IN_SCAN_STATE) == 2) break;
            SDL_Delay(100);
        }
        n = wifi_ap_count();
        printf("[WIFI] scan_state=%d ap_count=%d gen=%d\n",
               (int)app_get_input_i(APP_IN_SCAN_STATE), n, wifi_ap_gen());
        for (i = 0; i < n; i++) {
            const wifi_ap_t *a = wifi_ap_at(i);
            printf("[WIFI] %d | %s | %s | %d dBm | %s | lock=%d saved=%d conn=%d\n",
                   i, a->ssid, a->auth, a->rssi, a->band,
                   (int)a->lock, (int)a->saved, (int)a->connected);
        }
        SDL_Quit();
        return 0;
    }

    if (getenv("W78_SHOT_ALL")) {          /* 逐屏截图，供目检 */
        int i;
        wifi_bind_init();
        user_io_init();
        { app_value_t sv; sv.i = 1; app_set_output(APP_OUT_WIFI_SCAN, sv); }
        for (i = 0; i < 80; i++) { user_io_tick(); sim_reads_tick(); lv_tick_inc(50); lv_timer_handler(); SDL_Delay(50); if (app_get_input_i(APP_IN_SCAN_STATE) == 2) break; }
        for (i = 0; i < 8; i++) { user_io_tick(); sim_reads_tick(); lv_tick_inc(30); lv_timer_handler(); SDL_Delay(30); }
#define SHOT_ONE(sid, field) do {             lv_screen_load(nav_screen_obj(sid));             for (i = 0; i < 8; i++) { lv_tick_inc(30); lv_timer_handler(); sim_reads_tick(); SDL_Delay(20); }             take_shot("tmp/sim_" #field ".bmp");         } while (0);
        NAV_PAGE_LIST(SHOT_ONE)
        SDL_Quit();
        return 0;
    }

    if (getenv("W78_WIFI_FLOW_TEST")) {   /* 假世界连接闭环：扫描→选网→密码→连接成功 */
        int i, ok = 0;
        char target[33] = "";
        const wifi_ap_t *pick = NULL;
        wifi_bind_init();
        user_io_init();
        nav_bind_goto(SCREEN_ID_WIFI);
        { app_value_t sv; sv.i = 1; app_set_output(APP_OUT_WIFI_SCAN, sv); }
        for (i = 0; i < 120; i++) {
            user_io_tick(); lv_tick_inc(50); lv_timer_handler(); SDL_Delay(50);
            if (app_get_input_i(APP_IN_SCAN_STATE) == 2) break;
        }
        for (i = 0; i < wifi_ap_count(); i++) {
            const wifi_ap_t *a = wifi_ap_at(i);
            if (a->lock && !a->saved && !a->connected) { pick = a; break; }
        }
        if (!pick) {
            printf("[WIFI_FLOW] FAIL no locked AP\n");
            SDL_Quit();
            return 1;
        }
        snprintf(target, sizeof(target), "%s", pick->ssid);   /* resort 后 pick 会失效 */
        wifi_events_select(target);
        wifi_nav_open_sheet(target);
        for (i = 0; i < 10; i++) {
            user_io_tick(); lv_tick_inc(30); lv_timer_handler(); SDL_Delay(30);
        }
        lv_textarea_set_text(objects.pwd_ta, "12345678");
        /* flowtest 只验后端闭环；按钮命中由 uitest 单独验，这里直接投递连接命令 */
        wifi_events_request_connect();
        for (i = 0; i < 160; i++) {
            int k;
            user_io_tick(); lv_tick_inc(50); lv_timer_handler(); SDL_Delay(50);
            /* conn 状态会被 logic 当帧消费掉，直接看后端 AP 的 connected 事实 */
            for (k = 0; k < wifi_ap_count(); k++) {
                const wifi_ap_t *a = wifi_ap_at(k);
                if (strcmp(a->ssid, target) == 0 && a->connected) { ok = 1; break; }
            }
            if (ok) break;
        }
        printf("[WIFI_FLOW] ssid=%s connected=%d %s\n",
               target, ok, ok ? "PASS" : "FAIL");
        SDL_Quit();
        return ok ? 0 : 1;
    }

    if (getenv("W78_WIFI_UI_TEST")) {
        int i, conn = -1, saw = 0, n, ok = 0;
        char target[33] = "";
        const wifi_ap_t *pick = NULL;
        wifi_bind_init();
        user_io_init();
        nav_bind_goto(SCREEN_ID_WIFI);
        { app_value_t sv; sv.i = 1; app_set_output(APP_OUT_WIFI_SCAN, sv); }
        for (i = 0; i < 120; i++) {
            user_io_tick(); lv_tick_inc(50); lv_timer_handler(); SDL_Delay(50);
            if ((i % 10) == 0) printf("[WIFI_UI] wait i=%d scan=%d cnt=%d\n", i, (int)app_get_input_i(APP_IN_SCAN_STATE), wifi_ap_count());
            if (app_get_input_i(APP_IN_SCAN_STATE) == 2) break;
        }
        for (i = 0; i < 10; i++) { user_io_tick(); lv_tick_inc(30); lv_timer_handler(); SDL_Delay(30); }
        n = wifi_ap_count();
        printf("[WIFI_UI] ap_count=%d\n", n);
        take_shot("tmp/wifi_ui.bmp");
        for (i = 0; i < n; i++) {
            const wifi_ap_t *a = wifi_ap_at(i);
            if (a->saved && !a->connected) {
                wifi_events_select(a->ssid);
                wifi_nav_open_dialog(a->ssid);
                pump(12);
                take_shot("tmp/wifi_dialog.bmp");
                wifi_nav_close_dialog();
                break;
            }
        }
        for (i = 0; i < n; i++) {
            const wifi_ap_t *a = wifi_ap_at(i);
            if (a->lock && !a->saved && !a->connected) { pick = a; break; }
        }
        if (pick) {
            snprintf(target, sizeof(target), "%s", pick->ssid);
            wifi_events_select(target);
            wifi_nav_open_sheet(target);
            for (i = 0; i < 10; i++) { user_io_tick(); lv_tick_inc(30); lv_timer_handler(); SDL_Delay(30); }
            pump(6);
            take_shot("tmp/wifi_sheet.bmp");
            lv_textarea_set_text(objects.pwd_ta, "12345678");
            click_obj(objects.btn_connect);
            for (i = 0; i < 160; i++) {
                int k;
                user_io_tick(); lv_tick_inc(50); lv_timer_handler(); SDL_Delay(50);
                conn = (int)app_get_input_i(APP_IN_CONN_STATE);
                if (conn == 1 && !saw) { saw = 1; pump(25); take_shot("tmp/wifi_connecting.bmp"); }
                for (k = 0; k < wifi_ap_count(); k++) {
                    const wifi_ap_t *a = wifi_ap_at(k);
                    if (strcmp(a->ssid, target) == 0 && a->connected) { ok = 1; break; }
                }
                if (ok || conn == 3) break;
            }
            for (i = 0; i < 12; i++) { user_io_tick(); lv_tick_inc(30); lv_timer_handler(); SDL_Delay(30); }
            printf("[WIFI_UI] conn=%d connected=%d %s\n",
                   conn, ok, ok ? "PASS" : "FAIL");
            take_shot("tmp/wifi_flow.bmp");
        }
        SDL_Quit();
        return (pick && ok) ? 0 : 1;
    }

    if (getenv("W78_AUTOTEST")) {
        int rc;
        pump(5);
        rc = autotest();
        SDL_Quit();
        return rc;
    }

    wifi_bind_init();
    user_io_init();
    boot_selftest_start();                   /* 开机自检 → 真实 MP4 → 主界面 */
    for (;;) {
        SDL_Event e;
        while (SDL_PollEvent(&e)) {
            /* 自己轮询了 SDL 事件，就得自己处理关闭/退出；
             * 全丢给文件内部的鼠标 handler 会吞掉 SDL_QUIT（窗口关不掉） */
            if (e.type == SDL_QUIT ||
                    (e.type == SDL_WINDOWEVENT &&
                     e.window.event == SDL_WINDOWEVENT_CLOSE)) {
                SDL_Quit();
                return 0;
            }
            lv_sdl_mouse_handler(&e);
        }
        lv_tick_inc(5);
        lv_timer_handler();
        ui_tick();
        user_io_tick();
        sim_reads_tick();
        SDL_Delay(5);
    }
    return 0;
}
