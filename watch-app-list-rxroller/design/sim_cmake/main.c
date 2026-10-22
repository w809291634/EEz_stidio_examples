/*
 * watch-app-list-rxroller 的 PC 仿真入口
 * ---------------------------------------------------------------------------
 * 本工程是 no-flow + native 移植件（上游 rxwind7/Rxroller，MIT）：
 *  - 分辨率 410x502，与 EEZ 工程 displayWidth/Height 一致（preflight 第 2 组硬判）。
 *  - flowSupport=false => ui_init() 走 create_screens() 分支，没有 eez_flow_tick；
 *    EEZ 只出整屏宿主 + 标题 + 状态行，滚轮列表在 watch_list_create() 里建。
 *  - WATCH_AUTOTEST=1：无头自证（11 条 [ASSERT]，走行级 API）。
 *  - WATCH_DRAGTEST=1：走真 indev 的合成 SDL 拖动（2 条 [ASSERT]）。
 *    判据设计与缺陷史见 FIXLOG.md；取证开关见 README §4。
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
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

/* 22 行列表的**真实**末行下标（N-1）。样式②要求它不许当中心，
 * 夹具就是拿这个下标去请求，看有没有被拉回 watch_list_center_max()。 */
#define WATCH_TEST_LAST_ROW 21

/* ---- WATCH_AUTOTEST=1：无头自证（合成拖动 + dump + 拍屏），不需要人点鼠标 ----
 * 判据形态是"关系"而不是绝对值：
 *   ① 同屏图标的 scale 有区间（max > min）⇒ 穹顶缩放生效（中间大两边小）；
 *   ② 拖动后中心项（center）变了 ⇒ 吸附到了另一项；
 *   ③ 拖动后 visible 数量级不变 ⇒ 没有把整屏拖成空白。
 * 具体数字见 [LIST] 行，由 design/preflight.py 里同一套断言复核。 */
/* 取证用拍屏：读显示的活动绘制缓冲，不用 lv_snapshot_take（见 FIXLOG FX-005）。 */
static void take_shot(const char *path)
{
    lv_display_t *disp = lv_display_get_default();
    lv_draw_buf_t *buf;
    int w, h, stride, row, y;
    unsigned char *src;
    FILE *fp;

    /* ★ 禁止在这里调 lv_refr_now()，原因见 FIXLOG FX-005 */
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
    fflush(stdout);
}

/*==== 合成"真拖动"：SDL 事件队列 → LVGL indev → 行/根回调，端到端复现 FX-011 ====
 * ★ 按下事件必须同时填 motion.x/y：上游 lv_sdl_mouse.c:166-168 读的是那两个字段，
 *   不是 button.x/y。漏填会让按下点落在 (0,0)，见 FIXLOG FX-012。 */
static lv_display_t *s_disp = NULL;

static void drag_send(uint32_t type, int x, int y)
{
    SDL_Event e;
    SDL_Window *win = s_disp ? lv_sdl_window_get_window(s_disp) : NULL;
    uint32_t win_id = win ? SDL_GetWindowID(win) : 0;

    memset(&e, 0, sizeof(e));
    e.type               = type;
    e.button.windowID    = win_id;
    e.button.which       = SDL_TOUCH_MOUSEID;
    e.button.button      = SDL_BUTTON_LEFT;
    e.button.state       = (type == SDL_MOUSEBUTTONDOWN) ? SDL_PRESSED : SDL_RELEASED;
    e.button.x           = (Sint32)x;
    e.button.y           = (Sint32)y;
    e.motion.windowID    = win_id;
    e.motion.which       = SDL_TOUCH_MOUSEID;
    e.motion.x           = (Sint32)x;   /* ★ BUTTONDOWN 也读这里 */
    e.motion.y           = (Sint32)y;
    SDL_PushEvent(&e);
}

/* 让 LVGL 采样一次（indev 的 read 由 lv_timer_handler 驱动） */
static void drag_pump(int ms)
{
    lv_tick_inc(ms);
    lv_timer_handler();
    ui_tick();
}

/* 手指从上往下拖 = 内容跟手下移 = 翻向更早的行（拖到顶）；dy 取负即反向 */
static void synthetic_drag(int dy_total, int steps)
{
    int x = 200, y0 = 120, i, dy = dy_total / steps;

    drag_send(SDL_MOUSEBUTTONDOWN, x, y0);
    drag_pump(20);
    for (i = 1; i <= steps; i++) {
        drag_send(SDL_MOUSEMOTION, x, y0 + dy * i);
        drag_pump(20);
    }
    drag_send(SDL_MOUSEBUTTONUP, x, y0 + dy * steps);
    drag_pump(20);
}

static void dragtest_hooks(void)
{
    static int ticks = 0, settle = 0, last = -1, phase = 0, repeats = 0;
    char b[96];

    if (!getenv("WATCH_DRAGTEST")) return;
    ticks++;
    if (watch_list_center_index() < 0) return;

    if (ticks == 60) {
        printf("[DRAG] 起始中心=%d，往下拖 340px 松手%c",
               watch_list_center_index(), 10);
        fflush(stdout);
        synthetic_drag(340, 10);
        return;
    }
    if (phase == 1) {                    /* 反向：连拖多次一路到底 */
        synthetic_drag(-340, 10);
        if (++repeats < 9) return;
        phase = 2;
        settle = 0; last = -1;
        return;
    }

    if (ticks > 60 && !watch_list_is_animating()) {
        int c = watch_list_center_index();
        if (c == last) settle++;
        else { last = c; settle = 0; }
        if (settle != 15) return;

        if (phase == 0) {
            snprintf(b, sizeof(b), "中心=%d（第 %d 个），期望弹回 %d（第 %d 个）",
                     c, c + 1, watch_list_center_min(), watch_list_center_min() + 1);
            expect("真拖动到顶：松手弹回顶部第 n 个",
                   c == watch_list_center_min(), b);
            if (!getenv("WATCH_NOSHOT")) take_shot("shot_drag_top.bmp");
            phase = 1; repeats = 0;
            settle = 0; last = -1;
        } else if (phase == 2) {
            snprintf(b, sizeof(b), "中心=%d（第 %d 个），期望弹回 %d（第 %d 个）",
                     c, c + 1, watch_list_center_max(), watch_list_center_max() + 1);
            expect("真拖动到底：松手弹回底部倒数第 n 个",
                   c == watch_list_center_max(), b);
            if (!getenv("WATCH_NOSHOT")) take_shot("shot_drag_bottom.bmp");
            exit(0);
        }
    }
}

static void autotest_hooks(void)
{
    static int ticks = 0;
    static int c0, c2, c3, center_before;
    static int fling_from, fling_settle, fling_center, fling_stage, fling_expect;
    static char b1[96], b2[96], b3[96], b4[96];

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
        /* 样式②的初始态：上游建轮时把中心摆在行 0，本工程必须起步就在下界 */
        snprintf(b1, sizeof(b1), "起始中心=%d（允许下界=%d）",
                 center_before, watch_list_center_min());
        expect("起步不吸在首行", center_before == watch_list_center_min(), b1);
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
        int cx = watch_list_center_icon_x();
        c0 = watch_list_row_scale(9);   /* 离中心 1 行 */
        c2 = watch_list_row_scale(8);   /* 离中心 2 行 */
        c3 = watch_list_row_scale(7);   /* 离中心 3 行 */
        snprintf(b1, sizeof(b1), "center=%d scale=%d", watch_list_center_index(), s0);
        expect("惯性收敛后中心行 = 10", watch_list_center_index() == 10, b1);
        snprintf(b2, sizeof(b2), "scale 10=%d > 9=%d", s0, c0);
        expect("中心行缩放最大（穹顶成立）", s0 > c0, b2);
        snprintf(b3, sizeof(b3), "%d > %d > %d", c0, c2, c3);
        expect("离中心越远缩放单调衰减", c0 > c2 && c2 > c3, b3);
        /* 样式①：中心行的图标中心 = 屏宽 1/3（410/3 = 137），容差 ±2px */
        snprintf(b4, sizeof(b4), "图标中心 x=%d，屏宽 %d 的 1/%d = %d",
                 cx, SIM_W, 3, SIM_W / 3);
        expect("中心图标落在横向 1/3 处",
               cx > 0 && LV_ABS(cx - SIM_W / 3) <= 2, b4);
        watch_list_dump("center10");
        watch_list_cull();
        if (!getenv("WATCH_NOSHOT")) take_shot("shot_center10.bmp");
    }
    /* ---- 快滑惯性：250px（=2.5 行距）应当一次跨 3 行，而不是一格一格 ---- */
    if (ticks == 420) {
        fling_from = watch_list_center_index();
        watch_list_fling(-250);         /* 负=手指上滑=往后翻（行号增大） */
        fling_expect = fling_from + 3;
        fling_stage = 1;
    }
    /* ---- 判据顺序：先断言行程放开（能停在行 0 / 行 21），再断言松手弹回。
     *      必须 anim=true：无动画分支上游做模运算回绕，会掩盖真实落点（FX-010）。---- */
    if (fling_stage == 2) { fling_from = watch_list_center_index();
                            watch_list_center_no_clamp(0, true);
                            fling_expect = 0; fling_stage = 3; }
    if (fling_stage == 4) { watch_list_snap_edge();
                            fling_expect = watch_list_center_min(); fling_stage = 5; }
    if (fling_stage == 6) { fling_from = watch_list_center_index();
                            watch_list_center_no_clamp(WATCH_TEST_LAST_ROW, true);
                            fling_expect = WATCH_TEST_LAST_ROW; fling_stage = 7; }
    if (fling_stage == 8) { watch_list_snap_edge();
                            fling_expect = watch_list_center_max(); fling_stage = 9; }
    if (fling_stage == 10) { fling_from = watch_list_center_index();
                             watch_list_fling(-250);          /* 已弹回末位允许行，再抛 */
                             fling_expect = watch_list_center_max(); fling_stage = 11; }

    /* 统一的"落定后判一次"状态机：动画停 + 中心连续 15 拍不变才算落定 */
    if (fling_stage > 0 && !watch_list_is_animating()) {
        static const char *const WHAT[] = {
            "", "快滑一次跨多行并吸附到整行",
            "", "首行可以拖到正中（行程不限）",
            "", "松手弹回顶部第 n 个",
            "", "末行可以拖到正中（行程不限）",
            "", "松手弹回底部倒数第 n 个",
            "", "末尾快滑钳住不越界" };
        int c = watch_list_center_index();

        if (c == fling_center) fling_settle++;
        else { fling_center = c; fling_settle = 0; }
        if (fling_settle == 15) {
            snprintf(b4, sizeof(b4), "%d -> %d（期望 %d，弹回区间 [%d,%d]）",
                     fling_from, c, fling_expect,
                     watch_list_center_min(), watch_list_center_max());
            expect(WHAT[fling_stage], c == fling_expect, b4);
            watch_list_dump("settle");
            watch_list_cull();
            if (fling_stage == 1 && !getenv("WATCH_NOSHOT")) take_shot("shot_fling.bmp");
            if (fling_stage == 5 && !getenv("WATCH_NOSHOT")) take_shot("shot_snap_top.bmp");
            if (fling_stage == 9 && !getenv("WATCH_NOSHOT")) take_shot("shot_bounds.bmp");
            fling_from = c;
            fling_stage += 1;   /* 奇数档=断言，偶数档=发起下一次动作 */
            fling_settle = 0;
            fling_center = -1;
            if (fling_stage > 11 && getenv("WATCH_AUTOEXIT")) exit(0);
        }
    }
}

static lv_display_t * hal_init(int32_t w, int32_t h)
{    lv_group_set_default(lv_group_create());

    lv_display_t * disp = lv_sdl_window_create(w, h);

    lv_indev_t * mouse = lv_sdl_mouse_create();
    lv_indev_set_group(mouse, lv_group_get_default());
    lv_indev_set_display(mouse, disp);
    lv_display_set_default(disp);

    /* 自证模式下摘掉真鼠标，防止一次手滑把观测量歪（见 FIXLOG FX-013）。
     *   WATCH_DRAGTEST 例外：它要用 indev。人工上手用 WATCH_ALLOWMOUSE=1。 */
    if (s_disp == NULL) s_disp = disp;
    if (getenv("WATCH_AUTOTEST") && !getenv("WATCH_DRAGTEST")
        && !getenv("WATCH_ALLOWMOUSE")) {
        lv_indev_delete(mouse);
        return disp;
    }

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
        dragtest_hooks();
        usleep(4000);
    }

    return 0;
}
