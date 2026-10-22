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
#include "watch_list_config.h"  /* ★ 观感目标值的唯一出处，断言从这里取 */
#include "src/others/snapshot/lv_snapshot.h"

/* 断言里的目标值一律写 CFG(...)，一眼看得出不是夹具自己编的数 */
#define CFG(n) (n)

/* 中心图标在屏幕上真正占用的边长（含缩放） */
#define ICON_ON_SCREEN_PX  (CFG(ICON_PX) * CFG(SCALE_CENTER_PCT) / 100)

/* 缩放分档公式（与上游 rx_update_item_scale 同式）：
 * 离中心 d 个行距时 = 最小档 + 剩余比例 ×(满档-最小档)。
 * SPAN=3 时 d=0/1/2/3 → 100 / 67 / 33 / 0 % —— 就是用户要的"0 33 66 100"。 */
#define SCALE_AT(d) (CFG(EDGE_SCALE) + \
                     ((d) >= CFG(SCALE_SPAN_PITCHES) ? 0 : \
                      (CFG(SCALE_SPAN_PITCHES) - (d)) * (CFG(SCALE_MAX) - CFG(EDGE_SCALE)) \
                      / CFG(SCALE_SPAN_PITCHES)))

/* 任意带符号距离 d（px）上的连续缩放值，用来验"过程线性" */
#define SCALE_CONT(d) (CFG(EDGE_SCALE) + \
                       (LV_ABS(d) >= CFG(ROW_PITCH) * CFG(SCALE_SPAN_PITCHES) ? 0 : \
                        (CFG(ROW_PITCH) * CFG(SCALE_SPAN_PITCHES) - LV_ABS(d)) \
                        * (CFG(SCALE_MAX) - CFG(EDGE_SCALE)) \
                        / (CFG(ROW_PITCH) * CFG(SCALE_SPAN_PITCHES))))

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

/* EEZ 出的表盘是竖胶囊：410×502 上 LV_RADIUS_CIRCLE 钳到半径 = 短边一半 205
 * ⇒ 上下各一个半圆顶、中间一段直边。点在胶囊内的判据 = 到中轴最近点的距离 ≤ R。 */
static bool dial_inside(int x, int y)
{
    int r = SIM_W / 2;
    int cy = (y < r) ? r : ((y > SIM_H - r) ? SIM_H - r : y);
    return (x - r) * (x - r) + (y - cy) * (y - cy) <= r * r;
}

static void autotest_hooks(void)
{
    static int ticks = 0;
    static int c0, c2, c3, center_before;
    static int fling_from, fling_settle, fling_center, fling_stage, fling_expect;
    static int lin_d[2], lin_s[2], lin_n = 0;
    static int fling_throw;
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
    /* "过程线性"的证据只能在**飞行途中**采：静止时行都对齐在整行距上。
     * 又因为 span=1 ⇒ 线性带只有最后 1 个行距那么宽（|d|<100px），
     * 固定拍数采不到，所以动画期间逐拍采、命中带内就记两帧。 */
    if (lin_n < 2 && watch_list_is_animating()) {
        int d = watch_list_row_distance(10);
        int s = watch_list_row_scale(10);
        if (d != 0 && s > CFG(EDGE_SCALE) && s < CFG(SCALE_MAX)
            && (lin_n == 0 || d != lin_d[lin_n - 1])) {
            printf("[LIN] d=%d scale=%d 线性期望=%d\n", d, s,
                   SCALE_CONT(d));
            lin_d[lin_n] = d; lin_s[lin_n] = s; lin_n++;
        }
    }
    if (ticks == 400) {
        int s0 = watch_list_row_scale(10);
        int cx = watch_list_center_icon_x();
        int cy = watch_list_center_icon_y();
        int lx = watch_list_center_icon_layout_x();
        int iw = watch_list_center_icon_w();
        c0 = watch_list_row_scale(9);   /* 离中心 1 行 */
        c2 = watch_list_row_scale(8);   /* 离中心 2 行 */
        c3 = watch_list_row_scale(7);   /* 离中心 3 行 */
        snprintf(b1, sizeof(b1), "center=%d scale=%d", watch_list_center_index(), s0);
        expect("惯性收敛后中心行 = 10", watch_list_center_index() == 10, b1);
        snprintf(b2, sizeof(b2), "scale 10=%d > 9=%d", s0, c0);
        expect("中心行缩放最大（穹顶成立）", s0 > c0, b2);
        snprintf(b3, sizeof(b3), "行9=%d 行8=%d 行7=%d（SPAN=%d 的 67/33/0%%）",
                 c0, c2, c3, CFG(SCALE_SPAN_PITCHES));
        /* 不写死形状：按 config 的 SPAN/EDGE 反推每一档应有的缩放，逐行核对。
         * 规则 = 选中 100%、离中心 SPAN 行到底、中间线性 ⇒ 4 档就是 100/67/33/0。 */
        expect("缩放按 SPAN 线性分档（0/33/66/100 那一套）",
               c0 == SCALE_AT(1) && c2 == SCALE_AT(2) && c3 == SCALE_AT(3), b3);
        /* ★ 三条观感判据的目标值全部来自 watch_list_config.h，不写死在这里。
         *   判的是**屏幕上**的中心（含上游对整行的 transform 缩放），不是布局坐标。 */
        snprintf(b4, sizeof(b4), "渲染中心 x=%d，屏宽 %d 的 %d%% = %d（布局中心 %d）",
                 cx, SIM_W, CFG(CENTER_X_PCT), SIM_W * CFG(CENTER_X_PCT) / 100,
                 watch_list_center_icon_layout_x());
        expect("中心图标落在 config 指定的横向位置",
               cx > 0 && LV_ABS(cx - SIM_W * CFG(CENTER_X_PCT) / 100) <= 2, b4);
        snprintf(b4, sizeof(b4), "渲染中心 y=%d，屏高 %d 的 %d%% = %d",
                 cy, SIM_H, CFG(CENTER_Y_PCT), SIM_H * CFG(CENTER_Y_PCT) / 100);
        expect("中心图标垂直居中",
               cy > 0 && LV_ABS(cy - SIM_H * CFG(CENTER_Y_PCT) / 100) <= 2, b4);
        /* FX-024 防再犯：中心档 ≠100% 时，布局中心必然偏离渲染中心。
         * 光有"落在 config 指定的横向位置"那条挡不住回退——把标定改回
         * lv_obj_get_coords（布局口径）它照样绿，只是量到的不是你看到的。 */
        snprintf(b4, sizeof(b4), "布局=%d 渲染=%d 偏离=%d px（中心档 %d/256）",
                 lx, cx, lx - cx, CFG(SCALE_MAX));
        expect("横向落点量的是渲染坐标（不是布局坐标）",
               CFG(SCALE_MAX) == 256 || LV_ABS(lx - cx) > 2, b4);
        /* ★ lv_obj_get_coords 量的是**布局**尺寸，不含 transform 缩放。
         *   屏幕上真正看到的大小 = ICON_PX × SCALE_CENTER_PCT/100，另有一条断言。 */
        snprintf(b4, sizeof(b4), "布局宽=%d，config ICON_PX=%d", iw, CFG(ICON_PX));
        expect("图标位图布局尺寸 = config 的 ICON_PX",
               iw > 0 && LV_ABS(iw - CFG(ICON_PX)) <= 2, b4);
        snprintf(b4, sizeof(b4), "屏幕上应为 %d px（%d × %d%%），行距 %d",
                 ICON_ON_SCREEN_PX, CFG(ICON_PX), CFG(SCALE_CENTER_PCT),
                 CFG(ROW_PITCH));
        expect("中心图标屏幕尺寸 = ICON_PX × SCALE_CENTER_PCT",
               ICON_ON_SCREEN_PX <= CFG(ROW_PITCH), b4);
        /* 横向落点右移以后，最外侧可见行的"图标+文字"会往右上/右下圆顶里钻。
         * 只判中心 ±1 行：再往外的行本来就该被胶囊裁掉，不参与判定。
         * 胶囊是凸集 ⇒ 四角都在内即整块都在内。 */
        {
            const int chk = 1;
            int ci = watch_list_center_index(), k, bad = 0, worst = -1;
            for (k = ci - chk; k <= ci + chk; k++) {
                int x1, y1, x2, y2;
                if (!watch_list_row_box(k, &x1, &y1, &x2, &y2)) continue;
                if (x2 > worst) worst = x2;
                if (!(dial_inside(x1, y1) && dial_inside(x2, y1)
                      && dial_inside(x1, y2) && dial_inside(x2, y2))) bad++;
            }
            snprintf(b4, sizeof(b4), "越界行数=%d，最右内容 x=%d（屏宽 %d）",
                     bad, worst, SIM_W);
            expect("中心±1 行的图标+文字不越出胶囊", bad == 0, b4);
        }
        /* ★ 缩放曲线口径：选中最大、离中心 SPAN 行到底、中间线性。
         *   所以"最小档"应当出现在第 SPAN 行，而不是第 1 行。 */
        snprintf(b4, sizeof(b4), "第 %d 行 scale=%d，最小档=%d",
                 CFG(SCALE_SPAN_PITCHES),
                 watch_list_row_scale(10 + CFG(SCALE_SPAN_PITCHES)), CFG(EDGE_SCALE));
        expect("离中心 SPAN 行处到底（未选中最小）",
               watch_list_row_scale(10 + CFG(SCALE_SPAN_PITCHES)) == CFG(EDGE_SCALE),
               b4);
        snprintf(b4, sizeof(b4), "中心=%d，满档=%d（config SCALE_CENTER_PCT=%d%%）",
                 s0, CFG(SCALE_MAX), CFG(SCALE_CENTER_PCT));
        expect("中心行是满档（可比位图更大）", s0 == CFG(SCALE_MAX), b4);
        /* ★ "过程中是线性的"：拿途中采到的 (distance, scale) 反代公式核对。
         *   线性式见 SCALE_CONT()：全部由 config 反推，不写死形状。 */
        {
            int k, bad = 0, want, got;
            for (k = 0; k < lin_n; k++) {
                want = SCALE_CONT(lin_d[k]);
                if (LV_ABS(lin_s[k] - want) > 4) { bad = 1; got = lin_s[k]; }
            }
            snprintf(b4, sizeof(b4), "采到 %d 帧：d=%d→s=%d、d=%d→s=%d",
                     lin_n,
                     lin_n > 0 ? lin_d[0] : 0, lin_n > 0 ? lin_s[0] : 0,
                     lin_n > 1 ? lin_d[1] : 0, lin_n > 1 ? lin_s[1] : 0);
            expect("缩放随距离线性过渡（途中采样核对）",
                   lin_n == 2 && !bad, b4);
            (void)got;
        }
        watch_list_dump("center10");
        watch_list_cull();
        if (!getenv("WATCH_NOSHOT")) take_shot("shot_center10.bmp");
    }
    /* ---- 快滑惯性：250px（=2.5 行距）应当一次跨 3 行，而不是一格一格 ---- */
    if (ticks == 420) {
        fling_from = watch_list_center_index();
        /* 抛 2.5 个行距 => 四舍五入应当正好跨 3 行。用行距表达，行距改了不失效 */
        fling_throw = -(watch_list_row_pitch() * 5 / 2);
        watch_list_fling(fling_throw);  /* 负=手指上滑=往后翻（行号增大） */
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
