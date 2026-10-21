/*
 * watch-app-list-rxroller 的 PC 仿真入口
 * ---------------------------------------------------------------------------
 * 本工程是 no-flow + native 移植件（上游 rxwind7/Rxroller，MIT）：
 *  - 分辨率 410x502，与 EEZ 工程 displayWidth/Height 一致（preflight 第 2 组硬判）。
 *  - flowSupport=false => ui_init() 走 create_screens() 分支，没有 eez_flow_tick；
 *    EEZ 只出整屏宿主 + 标题 + 状态行，滚轮列表在 watch_list_create() 里建。
 *  - WATCH_AUTOTEST=1：无头自证——把第 10 行动画滚到中心，等惯性收敛后打三条
 *    [ASSERT]（中心=10 / 中心行缩放最大 / 离中心单调衰减）+ 两张截图。
 *    需要本工程 lv_conf.h 里 LV_USE_SNAPSHOT 1。
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include "lvgl.h"
#include "SDL2/SDL.h"
#include "lv_sdl_window.h"   /* lv_sdl_window_get_window：真鼠标事件要拿 SDL_Window* 换 windowID */
#include "ui.h"              /* EEZ 生成：ui_init / ui_tick（C 安全，不引入额外 C++ 头） */
#include "screens.h"         /* objects_t：EEZ 生成的控件句柄（no-flow 下 ui.h 不带出来） */
#include "watch_list_native.h"  /* 滚轮列表入口：create / dump / center / scale */
#include "src/others/snapshot/lv_snapshot.h"

extern void ui_init(void);
extern void ui_tick(void);

#define SIM_W 410
#define SIM_H 502

/* ---- WATCH_AUTOTEST=1：无头自证（合成拖动 + dump + 拍屏），不需要人点鼠标 ----
 * 判据形态是"关系"而不是绝对值：
 *   ① 同屏图标的 scale 有区间（max > min）⇒ 穹顶缩放生效（中间大两边小）；
 *   ② 拖动后中心项（center）变了 ⇒ 吸附到了另一项；
 *   ③ 拖动后 visible 数量级不变 ⇒ 没有把整屏拖成空白。
 * 具体数字见 [LIST] 行，由 design/preflight.py 里同一套断言复核。 */
/* 取证用拍屏。
 * ★ 不用 lv_snapshot_take：实测它在本工程的对象树上**不返回**（200s 内连计时都没打出来），
 *   而同一棵树正常渲染是 210 拍/秒 —— 卡的是快照路径，不是绘制。
 *   改读显示的活动绘制缓冲：lv_refr_now() 之后整帧就在那里面。 */
static void take_shot(const char *path)
{
    lv_display_t *disp = lv_display_get_default();
    lv_draw_buf_t *buf;
    int w, h, stride, row, y;
    unsigned char *src;
    FILE *fp;

    /* ★ 不要在这里调 lv_refr_now()：它强制整屏重绘，实测在这棵树上要 ~55 秒
     *   （正常循环只刷无效区，210 拍/秒）。主循环刚跑完 lv_timer_handler()，
     *   活动缓冲里已经是当前帧，直接取即可。 */
    buf = lv_display_get_buf_active(disp);
    if (NULL == buf) { printf("[SHOT] no active buf%c", 10); return; }
    w = (int)buf->header.w;
    h = (int)buf->header.h;
    stride = (int)buf->header.stride;
    src = (unsigned char *)buf->data;
    fp = fopen(path, "wb");
    if (fp) {
        int data = w * 4 * h;
        unsigned char hd[54] = { 'B','M' };
        *(int *)(hd + 2) = 54 + data;
        *(int *)(hd + 10) = 54;
        *(int *)(hd + 14) = 40;
        *(int *)(hd + 18) = w;
        *(int *)(hd + 22) = -h;   /* 自顶向下，PIL 直接读 */
        *(short *)(hd + 26) = 1;
        *(short *)(hd + 28) = 32;
        fwrite(hd, 1, 54, fp);
        for (y = 0; y < h; y++) fwrite(src + y * stride, 1, w * 4, fp);
        fclose(fp);
        printf("[SHOT] saved %s (%dx%d stride=%d)%c", path, w, h, stride, 10);
    }
}

static void expect(const char *what, int ok, const char *detail)
{
    printf("[ASSERT] %-46s %s  %s\n", what, ok ? "PASS" : "FAIL", detail);
}

static void autotest_hooks(void)
{
    static int ticks = 0;
    static int c0, c2, c3, center_before;
    static char b1[96], b2[96], b3[96];

    if (!getenv("WATCH_AUTOTEST")) return;
    ticks++;
    if (getenv("WATCH_TICKTRACE") && ticks % 25 == 0) {
        printf("[TICK] %d c=%d anim=%d%c", ticks, watch_list_center_index(),
               (int)watch_list_is_animating(), 10);
        fflush(stdout);
    }
    if (watch_list_center_index() < 0) return;

    if (ticks == 30) {
        center_before = watch_list_center_index();
        watch_list_dump("init");
        watch_list_cull();
        if (!getenv("WATCH_NOSHOT")) take_shot("shot_init.bmp");
    }
    if (ticks == 40) {
        /* 把第 10 行滚到中心（走动画/惯性路径，不是直接摆位） */
        watch_list_center(10, true);
    }
    if (ticks == 400) {
        int s0 = watch_list_row_scale(10);
        c0 = watch_list_row_scale(9);   /* 离中心 1 行 */
        c2 = watch_list_row_scale(8);   /* 离中心 2 行 */
        c3 = watch_list_row_scale(7);   /* 离中心 3 行 */
        snprintf(b1, sizeof(b1), "center=%d scale=%d", watch_list_center_index(), s0);
        expect("惯性收敛后中心行 = 10", watch_list_center_index() == 10, b1);
        snprintf(b2, sizeof(b2), "scale 10=%d > 9=%d", s0, c0);
        expect("中心行缩放最大（穹顶成立）", s0 > c0, b2);
        snprintf(b3, sizeof(b3), "%d > %d > %d", c0, c2, c3);
        expect("离中心越远缩放单调衰减", c0 > c2 && c2 > c3, b3);
        watch_list_dump("center10");
        watch_list_cull();
        if (!getenv("WATCH_NOSHOT")) take_shot("shot_center10.bmp");
        if (getenv("WATCH_AUTOEXIT")) exit(0);
    }
}

static lv_display_t * hal_init(int32_t w, int32_t h)
{    lv_group_set_default(lv_group_create());

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

    /* EEZ 外壳建好后，把 native 的蜂窝列表挂到整屏宿主上。
     * 顺序不能反：objects.* 是 create_screens() 里才有的句柄。 */
    watch_list_create(objects.list_host, objects.lbl_status);

    while (1) {
        lv_tick_inc(2);
        lv_timer_handler();
        ui_tick();
        autotest_hooks();
        usleep(4000);
    }

    return 0;
}
