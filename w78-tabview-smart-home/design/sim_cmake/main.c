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

#include "lvgl.h"
#include "SDL2/SDL.h"
#include "lv_sdl_window.h"
#include "ui.h"
#include "screens.h"
#include "nav_bind.h"
#include "nav_bind_table.h"

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

static void push_mouse(uint32_t type, int x, int y)
{
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
        lv_timer_handler();
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

int main(int argc, char **argv)
{
    int auto_mode = getenv("W78_AUTOTEST") != NULL;
    (void)argc; (void)argv;
    if (auto_mode) SDL_setenv("SDL_VIDEODRIVER", "dummy", 0);

    lv_init();
    hal_init(SIM_W, SIM_H);
    ui_init();
    nav_bind_init();

    if (getenv("W78_QUIT_TEST")) {          /* 自证窗口关闭链路：压一个 SDL_QUIT，应干净退出 0 */
        SDL_Event q;
        SDL_memset(&q, 0, sizeof(q));
        q.type = SDL_QUIT;
        SDL_PushEvent(&q);
        printf("[QUIT] SDL_QUIT queued\n");
    }

    if (auto_mode) {
        int rc;
        pump(5);
        rc = autotest();
        SDL_Quit();
        return rc;
    }

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
        lv_timer_handler();
        ui_tick();
        SDL_Delay(5);
    }
    return 0;
}
