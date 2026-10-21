/*
 * EEZ 示例 PC 仿真入口（design/sim_cmake/main.c）
 * ---------------------------------------------------------------------------
 * 编译进 PC_SIM 的 `main` 可执行（CMakeLists 非 FreeRTOS 分支把 SIM_MAIN_DIR/main.c 直接引用）。
 *
 * 设计要点：
 *  - 分辨率固定 480x320，与 EEZ 示例工程基线（displayWidth/Height）一致。
 *  - #include "ui.h" 会间接引入 eez-flow.h：该头文件头部自带 `#define EEZ_FOR_LVGL 1`
 *    且公共 API 用 extern "C" 包装（C/C++ 兼容），因此本 C 文件可直接调用
 *    ui_init() / ui_tick() 而无需在 lv_conf.h 里再定义 EEZ_FOR_LVGL。
 *  - ui_init() 内部无条件调用 eez_flow_init()（EEZ 9.29 生成的 ui.c 已是纯 flow 工程），
 *    手势切屏等 flow 动作自动生效，无需额外接线。
 *  - 手势（GESTURE）由 SDL 鼠标/触摸驱动产生，EEZ flow 运行时监听 LV_EVENT_GESTURE，
 *    故手势行为可在本 PC 仿真里验收（EEZ Studio 的 Run 预览不产生 GESTURE，见 P-0141）。
 *
 * 切换目标工程：运行示例目录下的 run_sim.bat（它把本目录绝对路径注入 SIM_TARGET_PROJ_DIR）。
 *
 * 注意：不要定义 SDL_MAIN_HANDLED。PC_SIM 链接了 libSDL2main，SDL_main.h 会把本文件的
 * main 重命名为 SDL_main，由 libSDL2main 提供的入口调用，否则链接报 undefined SDL_main。
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include "lvgl.h"
#include "SDL2/SDL.h"
#include "lv_sdl_window.h"   /* lv_sdl_window_get_window：真鼠标事件要拿 SDL_Window* 换 windowID */
#include "ui.h"              /* EEZ 生成：ui_init / ui_tick（C 安全，不引入额外 C++ 头） */

#include "screens.h"          /* objects_t：拿控件做量化断言 + 合成点击 */
#include "src/others/snapshot/lv_snapshot.h"

extern void ui_init(void);
extern void ui_tick(void);

/* ---- FLOW_AUTOTEST=1：无头自证（截图 + 几何 + 游标读数），不需要人点鼠标 ----
 * 时序（1 拍 = 一圈主循环）：
 *   20        拍"播放前"
 *   30        合成点击"播放"（speed=1，0→3 s）
 *   300/600/900  各点一次"读游标"（走本工程自己的 Flow.pageTimelinePosition() 通道）
 *   320/620/920  打印几何 —— 三个采样点的值都落在首尾之间 ⇒ 证明是插值不是跳变
 *   1000      合成点击"跳帧"（speed=0）
 *   1030      拍"跳帧后" + 打状态，退出
 * 三件事一次验掉：① 中文字体真的渲染（截图里按钮文案/g_status 的"无意义"）；
 *                  ② 页面时间线插值真的生效；③ speed=0 真的立即跳帧。 */
static void take_shot(const char *path)
{
    lv_draw_buf_t *buf = lv_snapshot_take(lv_screen_active(), LV_COLOR_FORMAT_XRGB8888);
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
        *(int *)(hd + 22) = -h;          /* 自顶向下，PIL 直接读 */
        *(short *)(hd + 26) = 1;
        *(short *)(hd + 28) = 32;
        fwrite(hd, 1, 54, fp);           /* ← 文件头（少了这行 PIL 打不开） */
        for (int y = 0; y < h; y++) fwrite(src + y * stride, 1, row, fp);
        fclose(fp);
        printf("[SHOT] saved %s\n", path);
    }
    lv_draw_buf_destroy(buf);
}

static void dump_geom(const char *tag)
{
    printf("[GEOM] %-6s card x=%4d y=%4d w=%4d opa=%3d rot=%4d | shadow w=%4d | %s | %s\n", tag,
           (int)lv_obj_get_x(objects.card), (int)lv_obj_get_y(objects.card),
           (int)lv_obj_get_width(objects.card),
           (int)lv_obj_get_style_opa(objects.card, LV_PART_MAIN),
           (int)lv_obj_get_style_transform_rotation(objects.card, LV_PART_MAIN) / 10,
           (int)lv_obj_get_width(objects.shadow),
           lv_label_get_text(objects.lbl_pos), lv_label_get_text(objects.lbl_status));
}

static void autotest_hooks(void)
{
    static int ticks = 0;
    if (!getenv("FLOW_AUTOTEST")) return;
    ticks++;
    if (getenv("FLOW_TICKTRACE") && ticks <= 25) { printf("[TICK] %d%c", ticks, 10); fflush(stdout); }
    if (ticks == 20) { take_shot("shot_before.bmp"); dump_geom("before"); }
    if (ticks == 30) lv_obj_send_event(objects.btn_play, LV_EVENT_CLICKED, NULL);
    if (ticks == 250 || ticks == 400 || ticks == 550)
        lv_obj_send_event(objects.btn_probe, LV_EVENT_CLICKED, NULL);
    if (ticks == 270) { take_shot("shot_mid1.bmp"); dump_geom("mid1"); }
    if (ticks == 420) { take_shot("shot_mid2.bmp"); dump_geom("mid2"); }
    if (ticks == 570) { take_shot("shot_mid3.bmp"); dump_geom("mid3"); }
    if (ticks == 700) lv_obj_send_event(objects.btn_rew, LV_EVENT_CLICKED, NULL);
    if (ticks == 720) dump_geom("rew-mid");
    if (ticks == 1100) {
        lv_obj_send_event(objects.btn_probe, LV_EVENT_CLICKED, NULL);
    }
    if (ticks == 1120) { take_shot("shot_rew.bmp"); dump_geom("rew-end"); }
    if (ticks == 1160) lv_obj_send_event(objects.btn_jump, LV_EVENT_CLICKED, NULL);
    if (ticks == 1170) lv_obj_send_event(objects.btn_probe, LV_EVENT_CLICKED, NULL);
    if (ticks == 1190) {
        take_shot("shot_after.bmp"); dump_geom("jump");
        if (getenv("FLOW_AUTOEXIT")) exit(0);
    }
}

#define SIM_W 480
#define SIM_H 320

static lv_display_t * hal_init(int32_t w, int32_t h)
{
    lv_group_set_default(lv_group_create());

    lv_display_t * disp = lv_sdl_window_create(w, h);

    lv_indev_t * mouse = lv_sdl_mouse_create();
    lv_indev_set_group(mouse, lv_group_get_default());
    lv_indev_set_display(mouse, disp);
    lv_display_set_default(disp);

    LV_IMAGE_DECLARE(mouse_cursor_icon);   /* 仿真器自带光标位图（main/src/mouse_cursor_icon.c） */
    lv_obj_t * cursor_obj = lv_image_create(lv_screen_active());
    lv_image_set_src(cursor_obj, &mouse_cursor_icon);
    lv_indev_set_cursor(mouse, cursor_obj);

    lv_indev_t * mousewheel = lv_sdl_mousewheel_create();
    lv_indev_set_display(mousewheel, disp);
    lv_indev_set_group(mousewheel, lv_group_get_default());

    lv_indev_t * kb = lv_sdl_keyboard_create();
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

    while (1) {
        lv_tick_inc(2);
        lv_timer_handler();
        ui_tick();
        autotest_hooks();
        usleep(4000);
    }

    return 0;
}
