/*
 * app-wifi-connect 仿真入口（v2：KB reference/10 硬件⇄UI 分离架构迷你版）。
 *
 * main 只做四件事：lv_init / hal_init / ui_init / user_io_init + 循环
 * （lv_timer_handler → ui_tick → user_io_tick）。业务全在 src/native：
 *   app_model(契约头+状态+命令环) + native_vars(变量桥) + native_actions(动作投递)
 *   + platform/io_pc(假 WiFi 驱动；真机换 io_esp)。
 * 自动演示：假 indev 走真实输入管线——开机自动扫描 → 点开放网络行 →
 *           点连接 → 底部显示"已连接"。[STATE] 每拍打印契约状态可断言。
 */
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <windows.h>    /* 截图自证：FindWindow/BitBlt 保存 BMP */

#include "lvgl.h"
#include "SDL2/SDL.h"
#include "lv_sdl_window.h"
#include "ui.h"
#include "app_model.h"
#include "vars.h"      /* EEZ 生成的 native 变量桥声明（get_var_*/...） */

#define SIM_W 480
#define SIM_H 320

/* ---- 假指针单击（走真实 lv_indev 管线，不占真鼠标）---- */
static int32_t tap_x = 0, tap_y = 0;
static int tap_phase = -1;
static lv_indev_t *tap_indev = NULL;

static void tap_read_cb(lv_indev_t *indev, lv_indev_data_t *data)
{
    if (tap_phase < 0 || tap_phase > 2) {
        data->state = LV_INDEV_STATE_RELEASED;
        return;
    }
    data->point.x = tap_x;
    data->point.y = tap_y;
    data->state = (tap_phase < 2) ? LV_INDEV_STATE_PRESSED
                                  : LV_INDEV_STATE_RELEASED;
    tap_phase++;
}

static void demo_tap(int32_t x, int32_t y)
{
    printf("[TAP] tap at %d,%d\n", (int)x, (int)y);
    tap_x = x; tap_y = y; tap_phase = 0;
    if (!tap_indev) {
        tap_indev = lv_indev_create();
        lv_indev_set_type(tap_indev, LV_INDEV_TYPE_POINTER);
        lv_indev_set_read_cb(tap_indev, tap_read_cb);
        lv_indev_set_display(tap_indev, lv_display_get_default());
    }
}

/* ---- 自动演示状态机 ---- */
static bool demo_scan_fired = false;
static bool demo_pick_fired = false;
static bool demo_connect_fired = false;

static void take_shot(const char *path);   /* fwd */

static void demo_timer(lv_timer_t *t)
{
    static int tick = 0;
    static int wait = 0;
    tick++;
    if (getenv("WIFI_REAL")) {
        /* ★ 真模式：全自动关闭，扫描/连接/取消全部由用户手动操作
         * （点"刷新"发起扫描）。这里只周期打印契约状态供观察。 */
        if (tick % 4 == 0) {
            printf("[STATE] scan=%d aps=%d wifi=%d pick='%s' conn='%s' rem=%d\n",
                   (int)get_var_scan_state(), (int)get_var_ap_count(),
                   (int)get_var_wifi_state(), get_var_pick_ssid(),
                   get_var_conn_ssid(), (int)get_var_g_remember());
        }
        return;
    }
    if (demo_scan_fired && !demo_pick_fired &&
            get_var_scan_state() == 2) {
        demo_tap(240, 46 + 1 * 36 + 12);   /* 点第 2 行（开放网络 Guest） */
        demo_pick_fired = true;
    }
    if (demo_pick_fired && !demo_connect_fired &&
            get_var_pick_ssid()[0] != '\0') {
        if (++wait >= 4) {                 /* 面板弹出后稍候点"连接" */
            demo_tap(40 + 60 + 75, 20 + 250 + 13);
            demo_connect_fired = true;
        }
    }
    if (tick % 4 == 0) {
        printf("[STATE] scan=%d aps=%d wifi=%d pick='%s' conn='%s' rem=%d\n",
               (int)get_var_scan_state(), (int)get_var_ap_count(),
               (int)get_var_wifi_state(), get_var_pick_ssid(),
               get_var_conn_ssid(), (int)get_var_g_remember());
    }
    if (get_var_wifi_state() == 2 && demo_connect_fired) {
        printf("[DEMO] done: connected, footer shows it\n");
        take_shot("shot_fake.bmp");
        if (getenv("WIFI_AUTOEXIT")) exit(0);   /* 无头验证用；正常运行保持交互 */
        lv_timer_del(t);
    }
    (void)t;
}

/* 自证渲染结果：lv_snapshot 从 LVGL 内部抓整屏（GPU 窗口截图抓不到内容） */
#include "src/others/snapshot/lv_snapshot.h"
static void take_shot(const char *path)
{
    lv_draw_buf_t *buf = lv_snapshot_take(lv_screen_active(), LV_COLOR_FORMAT_XRGB8888);
    if (!buf) { printf("[SHOT] snapshot failed\n"); return; }
    int w = (int)buf->header.w, h = (int)buf->header.h, stride = (int)buf->header.stride;
    unsigned char *src = (unsigned char *)buf->data;
    FILE *fp = fopen(path, "wb");
    if (fp) {
        int row = w * 4, data = row * h;
        unsigned char hd[54] = { 'B','M' };
        *(int *)(hd + 2) = 54 + data; *(int *)(hd + 10) = 54;
        *(int *)(hd + 14) = 40; *(int *)(hd + 18) = w;
        *(int *)(hd + 22) = -h; *(short *)(hd + 26) = 1;
        *(short *)(hd + 28) = 32; *(int *)(hd + 34) = data;
        fwrite(hd, 1, 54, fp);
        for (int y = 0; y < h; y++)
            fwrite(src + (long)y * stride, 1, row, fp);
        fclose(fp);
        printf("[SHOT] saved %s (%dx%d)\n", path, w, h);
    } else printf("[SHOT] fopen failed\n");
    lv_draw_buf_destroy(buf);
}

static lv_display_t *hal_init(int32_t w, int32_t h)
{
    lv_display_t *disp = lv_sdl_window_create(w, h);
    lv_sdl_window_set_title(disp, "WIFIDEMO");
    lv_indev_t *mouse = lv_sdl_mouse_create();
    lv_indev_set_display(mouse, disp);
    lv_display_set_default(disp);
    return disp;
}

int main(int argc, char **argv)
{
    (void)argc; (void)argv;
    setvbuf(stdout, NULL, _IONBF, 0);   /* 重定向到文件也实时可见 */
    lv_init();
    hal_init(SIM_W, SIM_H);
    ui_init();
    user_io_init();
    lv_timer_create(demo_timer, 500, NULL);

    while (1) {
        lv_tick_inc(2);
        lv_timer_handler();
        ui_tick();
        user_io_tick();
        usleep(4000);
    }
    return 0;
}
