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

extern void ui_init(void);
extern void ui_tick(void);
extern void user_io_init(void);   /* native：扫描状态机 + 契约状态初始化 */
extern void user_io_tick(void);   /* native：每拍排空命令 + 推进扫描 + 同步列表 */

extern int32_t get_var_scan_state(void);   /* native 变量桥（vars.h 声明） */
extern int32_t get_var_ap_count(void);

/* 自证渲染：lv_snapshot 从 LVGL 内部抓整屏（系统截图抓不到内容） */
#include "src/others/snapshot/lv_snapshot.h"

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
        *(int *)(hd + 22) = -h;
        *(short *)(hd + 26) = 1;
        *(short *)(hd + 28) = 32;
        fwrite(hd, 1, 54, fp);          /* ← 文件头（少了这行 PIL 打不开） */
        for (int y = 0; y < h; y++)
            fwrite(src + y * stride, 1, row, fp);
        fclose(fp);
        printf("[SHOT] saved %s\n", path);
    }
    lv_draw_buf_destroy(buf);
}

/* 无头验证钩子：WIFI_AUTOSCAN=1 自动扫一次；WIFI_SHOT=1 在完成后截图 */
static void headless_hooks(void)
{
    static int scanned = 0, shot = 0, ticks = 0;
    ticks++;
    if (getenv("WIFI_AUTOSCAN") && !scanned && ticks > 40) {
        extern void action_scan_start(lv_event_t * e);
        action_scan_start(NULL);
        scanned = 1;
        printf("[HOOK] autoscan fired\n");
    }
    if (getenv("WIFI_SHOT") && scanned && !shot &&
            get_var_scan_state() == 2) {
        take_shot("shot_fake.bmp");
        shot = 1;
        if (getenv("WIFI_AUTOEXIT")) exit(0);
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
    user_io_init();      /* 扫描状态机 / 契约状态（必须在 ui_init 之后：要拿 objects） */

    while (1) {
        lv_tick_inc(2);
        lv_timer_handler();
        ui_tick();
        user_io_tick();   /* 排空命令 + 推进扫描 + 同步 10 个槽 */
        headless_hooks();
        usleep(4000);
    }

    return 0;
}
