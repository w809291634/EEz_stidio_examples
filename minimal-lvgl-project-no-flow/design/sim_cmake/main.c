/*
 * EEZ 示例 PC 仿真入口（design/sim_cmake/main.c）
 * ---------------------------------------------------------------------------
 * 编译进 PC_SIM 的 `main` 可执行（CMakeLists 非 FreeRTOS 分支把 SIM_MAIN_DIR/main.c 直接引用）。
 *
 * 本工程是 minimal-lvgl-project 的 **no_flow 变体**：EEZ Flow 运行时已关闭
 * （.eez-project 的 flowSupport / generateSourceCodeForEezFramework 均为 False）。
 * EEZ Studio 因此生成纯 LVGL 分支代码——不发射 eez-flow.cpp/h，ui_init() / ui_tick()
 * 直接走 create_screens() / tick_screen()，不再调用 eez_flow_init()。
 *
 * 设计要点：
 *  - 分辨率固定 480x320，与 EEZ 示例工程基线（displayWidth/Height）一致。
 *  - #include "ui.h" 不再引入 eez-flow.h（EEZ_FOR_LVGL 未定义），ui_init / ui_tick
 *    即为纯 LVGL 的初始化与每帧刷新，可被本 C 文件直接调用。
 *  - 手势（GESTURE）由 SDL 鼠标/触摸驱动，原生 LVGL 监听 LV_EVENT_GESTURE，
 *    无需 EEZ flow 运行时即可验收（EEZ Studio 的 Run 预览不产生 GESTURE，见 P-0141）。
 *
 * 切换目标工程：运行示例目录下的 run_sim.bat（它把本目录绝对路径注入 SIM_TARGET_PROJ_DIR）。
 *
 * 注意：不要定义 SDL_MAIN_HANDLED。PC_SIM 链接了 libSDL2main，SDL_main.h 会把本文件的
 * main 重命名为 SDL_main，由 libSDL2main 提供的入口调用，否则链接报 undefined SDL_main。
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "lvgl.h"
#include "SDL2/SDL.h"
#include "lv_sdl_window.h"   /* lv_sdl_window_get_window：真鼠标事件要拿 SDL_Window* 换 windowID */
#include "ui.h"              /* EEZ 生成：ui_init / ui_tick（C 安全，不引入额外 C++ 头） */
#include "app/sim_fs.h"      /* PC 文件系统：A: → 工程根 */

extern void ui_init(void);
extern void ui_tick(void);

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

int main(int argc, char **argv)
{
    (void)argc;
    (void)argv;

    if (getenv("SIM_FS_TEST")) {
        int rc;
        SDL_setenv("SDL_VIDEODRIVER", "dummy", 0);
        lv_init();
        sim_fs_init();
        rc = fs_test();
        SDL_Quit();
        return rc;
    }

    lv_init();
    sim_fs_init();
    hal_init(SIM_W, SIM_H);

    ui_init();

    while (1) {
        lv_tick_inc(2);
        lv_timer_handler();
        ui_tick();
        usleep(4000);
    }

    return 0;
}
