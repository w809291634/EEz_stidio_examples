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
#include "screens.h"        /* objects_t：全局对象表（list_box 等） */
#include "app_model.h"      /* native 契约：app_get_input_i / APP_IN_SCAN_STATE */

extern void ui_init(void);
extern void ui_tick(void);
extern void user_io_init(void);   /* native：扫描状态机 + 契约状态初始化 */
extern void user_io_tick(void);   /* native：每拍排空命令 + 推进扫描 + 同步列表 */

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
            app_get_input_i(APP_IN_SCAN_STATE) == 2) {
        take_shot("shot_fake.bmp");
        shot = 1;
        if (getenv("WIFI_AUTOEXIT")) exit(0);
    }
}

/* ---- 无头滚动测试：注入真实 SDL 鼠标事件，走完整 indev 链路 ---- */
static uint32_t sdl_window_id(void)
{
    /* 返回 0 = 不存在的窗口 ID：lv_sdl_mouse_handler 里
     * lv_sdl_get_disp_from_win_id(0) 返回 NULL → 走 fallback
     * （disp==NULL 时用第一个 read_cb==sdl_mouse_read 的 indev，不校验
     * display 归属）。实测用真实窗口 ID 反而因 display 归属不匹配被丢弃。 */
    return 0;
}

/* 往 SDL 事件队列压一个鼠标事件（lv_sdl_mouse 轮询时消费→LVGL indev） */
static void push_mouse(uint32_t type, int x, int y)
{
    SDL_Event e;
    SDL_memset(&e, 0, sizeof(e));
    e.type = type;
    e.button.windowID = sdl_window_id();
    e.button.button = SDL_BUTTON_LEFT;
    e.button.state = (type == SDL_MOUSEBUTTONDOWN) ? SDL_PRESSED
                                                   : SDL_RELEASED;
    e.button.x = x;
    e.button.y = y;
    SDL_PushEvent(&e);
}

static int push_motion_ret(int x, int y)
{
    SDL_Event e;
    SDL_memset(&e, 0, sizeof(e));
    e.type = SDL_MOUSEMOTION;
    e.motion.windowID = sdl_window_id();
    e.motion.x = x;
    e.motion.y = y;
    return SDL_PushEvent(&e);
}

#define push_motion(x, y) (void)push_motion_ret((x), (y))

/* 在 list_box 区域内按下一行并向上拖 dy：返回拖动后的 scroll_y */
static int drag_scroll_test(int px, int py, int dy, int frames)
{
    extern objects_t objects;   /* screens.h：全局对象表 */
    lv_indev_t *mi = lv_indev_get_next(NULL);
    while (mi && lv_indev_get_type(mi) != LV_INDEV_TYPE_POINTER)
        mi = lv_indev_get_next(mi);

    /* 每步都要等状态真正就绪：SDL 事件经 sdl_event_handler timer 消费，
     * push 后不会立即生效；且若 indev 残留 PRESSED（上次 UP 被丢弃），
     * LVGL 不会重走 press 分支——必须先 UP 再 DOWN 并各自等待。 */
    push_mouse(SDL_MOUSEBUTTONUP, 0, 0);
    for (int w = 0; w < 20; w++) {
        { SDL_Event e; while (SDL_PollEvent(&e)) lv_sdl_mouse_handler(&e); }
        SDL_Delay(5); lv_timer_handler();
        if (mi && lv_indev_get_state(mi) == LV_INDEV_STATE_RELEASED) break;
    }

    push_mouse(SDL_MOUSEBUTTONDOWN, px, py);
    for (int w = 0; w < 20; w++) {
        { SDL_Event e; while (SDL_PollEvent(&e)) lv_sdl_mouse_handler(&e); }
        SDL_Delay(5); lv_timer_handler();
        if (mi && lv_indev_get_state(mi) == LV_INDEV_STATE_PRESSED &&
                lv_indev_get_active_obj()) break;
    }
    if (mi)
        printf("[DRAG] press ready: state=%d act=%p\n",
               (int)lv_indev_get_state(mi), (void *)lv_indev_get_active_obj());

    for (int i = 1; i <= frames; i++) {
        push_motion(px, py - dy * i / frames);
        { SDL_Event e; while (SDL_PollEvent(&e)) lv_sdl_mouse_handler(&e); }
        SDL_Delay(8); lv_timer_handler();
    }
    push_mouse(SDL_MOUSEBUTTONUP, px, py - dy);
    { SDL_Event e; while (SDL_PollEvent(&e)) lv_sdl_mouse_handler(&e); }
    SDL_Delay(8); lv_timer_handler();
    return (int)lv_obj_get_scroll_y(objects.list_box);
}

/* WIFI_SCROLLTEST=1：扫描完成后在列表上拖拽，验证滚动链路 */
static void scroll_test_hooks(void)
{
    static int done = 0, wait = 0;
    if (!getenv("WIFI_SCROLLTEST") || done) return;
    if (app_get_input_i(APP_IN_SCAN_STATE) != 2) { wait = 0; return; }
    /* user_io_tick() 在本函数之前调用：scan done 的同拍已填好列表，
     * 所以 scan_state==2 第一帧即可测（截图钩子会同帧 exit，不能等） */
    if (++wait < 1) return;
    done = 1;
    extern objects_t objects;
    lv_obj_t *lb = objects.list_box;
    int32_t before = lv_obj_get_scroll_y(lb);
    /* 按在第 3 行（y=180）向上拖 120px：能滚说明链路通 */
    int after = drag_scroll_test(240, 180, 120, 12);
    printf("[SCROLLTEST] list_box scroll_y: %d -> %d (%s)\n",
           (int)before, after,
           after > before ? "PASS 滚动生效" : "FAIL 仍滑不动");
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
        scroll_test_hooks();
        headless_hooks();
        usleep(4000);
    }

    return 0;
}
