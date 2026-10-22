/*
 * watch_list_native.c —— 用 Rxroller 搭的 22 行应用列表（本工程界面主体）
 *
 * 分工（no-flow 口径）：
 *   EEZ 出：410x502 屏、宿主容器 objects.list_host、标题、状态行、中文字体条目；
 *   这里出：滚轮件本体（弧线排布 + 逐行按离中心距离缩放 + 惯性 + 点击）。
 *
 * 为什么不走 EEZ Flow：scroll_snap 轴与"逐子项 transform_scale"不在 EEZ 属性面内
 * （实测 asar：scroll_snap 只出现在 WASM 符号表与 LVGL 常量字符串表里，
 * 没有 widget 属性定义）。Flow 版参照工程（桌面的 Design Watch）能做到，
 * 是靠 97 个 action 写 / 15ms 堆出来的；这里一次遍历就够。
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "lvgl.h"
#include "watch_list_native.h"
#include "app_rows.h"
#include "rxroller/Rxroller.h"
#include "fonts.h"          /* EEZ 生成：ui_font_cn14 */

/*---- 观感参数（对齐 Design Watch 参考图：行距 100、图标 76、边缘缩到 ~59%）----*/
#define ROW_PITCH        100     /* rxroller_config_t.icon_distance：相邻行中心距 */
#define ROW_W            300     /* 行容器宽（big_w） */
#define ROW_H            100     /* 行容器高（big_h） */
#define EDGE_SCALE       150     /* 0..255，边缘行缩放；150/255 ≈ 59% */
#define CURVE_RADIUS     900     /* 弧线半径 px。420 时第 3 行横向漂 ~150px 太夸张
                                    （参考图只要轻微弧线），放宽到 900 */
#define ANIM_TIME        300

static lv_obj_t *s_wheel = NULL;
static lv_obj_t *s_status = NULL;

/* 拖动判定：按拍**累计最大位移**，超过阈值就忽略随之而来的 CLICKED。
 * ★ 为什么不能只比"按下点 vs 松手点"：LVGL 在 `scroll_obj == NULL 且没有
 *   PRESS_LOCK` 时**每个读周期都重新搜索按下对象**（lv_indev.c:1216-1219），
 *   换对象时把 last_point 重置成当前点并给新对象再发一次 PRESSED ⇒ 按下点会被
 *   中途刷新，位移永远算不出来（第一版就是这么失效的）。
 *   所以两道一起上：① 行加 PRESS_LOCK 锁住手势目标；② 自己按拍累计位移兜底。
 * 阈值 15px：行距 100px，轻点的手指抖动远小于它，任何有效拖动都远大于它。 */
#define DRAG_CLICK_IGNORE_PX 15
static lv_point_t s_press_pt;
static bool s_press_valid = false;
static int s_press_travel = 0;

/* 快滑惯性（本工程自己加，上游没有——`inertia_divisor` 是死字段：
 * Rxroller.c 只在配置兜底里写了一次 20，之后全文再无任何读取）。
 * 做法：PRESSING 逐拍估纵向速度（低通滤波），RELEASED 把速度投影成
 * "还要抛多少像素"，交给 watch_list_fling() 用 rxroller_scroll 走完并吸附。
 *
 * 三个数是怎么定的（410x502、行距 100px）：
 *   FLING_MIN_VEL 120 px/s —— 手指缓慢移动完松手不该抛；120px/s × 0.25s = 30px，
 *     不足行距的 1/3，本来就吸附回原行，设成阈值正好把"没意义的小抛"滤掉。
 *   FLING_SEC 0.25 —— 投影时长，相当于衰减常数的近似积分。0.25s 下
 *     一次正常快滑（800~1500 px/s）抛 200~375px = 2~3 行，符合手表的观感。
 *   FLING_MAX_PX 3 行 —— 上限，防止甩一下跨过半屏找不到位置。 */
#define FLING_MIN_VEL     120        /* px/s，低于它当普通松手不抛 */
#define FLING_SEC         250        /* 毫秒（用整数算，省得引浮点） */
#define FLING_MAX_PX      (ROW_PITCH * 3)
#define FLING_MAX_ROWS    3          /* 一次快滑最多跨几行（= FLING_MAX_PX / 行距） */
#define FLING_VEL_SMOOTH  8          /* 低通：新样本占 3/8，历史占 5/8 */
#define FLING_VEL_STALE_MS 80        /* 超过这么久没更新 ⇒ 手指已停，速度作废 */

static lv_point_t s_last_pt;
static uint32_t   s_last_t;
static int        s_vel;            /* px/s，纵向；正=手指向下 */

static void row_press_cb(lv_event_t *e)
{
    lv_indev_t *in = lv_indev_get_act();

    (void)e;
    s_press_valid = false;
    if (NULL != in) {
        lv_indev_get_point(in, &s_press_pt);
        s_press_travel = 0;
        s_last_pt = s_press_pt;
        s_last_t = lv_tick_get();
        s_vel = 0;
        s_press_valid = true;
    }
}

/* 抬手但没形成快滑（或手势被系统抢走）：把速度清掉，别让下一次松手误用 */
static void row_press_lost_cb(lv_event_t *e)
{
    (void)e;
    s_press_valid = false;
    s_vel = 0;
}

static void row_pressing_cb(lv_event_t *e)
{
    lv_indev_t *in = lv_indev_get_act();
    lv_point_t p;
    int dx, dy;

    (void)e;
    if (!s_press_valid || NULL == in) return;
    lv_indev_get_point(in, &p);
    dx = LV_ABS(p.x - s_press_pt.x);
    dy = LV_ABS(p.y - s_press_pt.y);
    if (dx > s_press_travel) s_press_travel = dx;
    if (dy > s_press_travel) s_press_travel = dy;

    /* 速度（px/s，纵向）：按拍差分 + 低通平滑，避免最后一拍抖动决定成败 */
    {
        uint32_t now = lv_tick_get();
        uint32_t dt = (uint32_t)lv_tick_elaps(s_last_t);

        if (dt > 0) {
            int inst;

            /* 手指停住超过 FLING_VEL_STALE_MS ⇒ 位置没变但时间变了，速度归零。
             * 不加这条，"慢慢拖到某行、停一下再松手"会按最后一次的残留速度抛出。 */
            if (dt > FLING_VEL_STALE_MS && p.y == s_last_pt.y) {
                s_vel = 0;
            } else {
                inst = (int)((p.y - s_last_pt.y) * 1000 / (int32_t)dt);
                s_vel = (s_vel * (FLING_VEL_SMOOTH - 3) + inst * 3) / FLING_VEL_SMOOTH;
            }
            s_last_pt = p;
            s_last_t = now;
        }
    }
}

/* 松手：把速度投影成"再抛多少像素"，交给 fling 去做。
 * 必须 lv_async_call 延一拍——上游也注册了 RELEASED（Rxroller.c:628）且它跑在我们之后，
 * 直接调 scroll 会被它那次 set_center 覆盖掉。 */
static void fling_async(void *user)
{
    watch_list_fling((int32_t)(intptr_t)user);
}

static void row_released_cb(lv_event_t *e)
{
    int32_t throw_px;

    (void)e;
    if (!s_press_valid) return;
    s_press_valid = false;

    /* 位移没超过"轻点"阈值 ⇒ 这是点击，不是快滑（哪怕瞬时速度采样偏高）。
     * 不挡这条的话，一次 10px 的轻扫会同时触发 CLICKED 和抛出。 */
    if (s_press_travel <= DRAG_CLICK_IGNORE_PX) { s_vel = 0; return; }

    if (s_vel > -FLING_MIN_VEL && s_vel < FLING_MIN_VEL) {   /* 慢速移动不算快滑 */
        s_vel = 0;
        return;
    }

    /* 屏幕内容跟手指同向走 ⇒ 手指向下(+vel)是看更早的行，行号减小 */
    throw_px = (int32_t)s_vel * FLING_SEC / 1000;
    if (throw_px >  FLING_MAX_PX) throw_px =  FLING_MAX_PX;
    if (throw_px < -FLING_MAX_PX) throw_px = -FLING_MAX_PX;
    printf("[FLING] vel=%d px/s -> throw=%d px\n", s_vel, (int)throw_px);
    s_vel = 0;
    lv_async_call(fling_async, (void *)(intptr_t)throw_px);
}

static void row_click_cb(lv_event_t *e);

/* 行内容：左圆图标 + 右中文名。★ 不能用容器 user_data 存下标——
 * Rxroller 自己占用了它（rx_init_item 里 lv_obj_set_user_data(item->obj, item)），
 * 所以点击时反查 rxroller_get_item_obj()。 */
static void row_create_cb(lv_obj_t *row, int32_t index, void *user_data)
{
    const watch_app_row_t *r = &WATCH_APP_ROWS[index];
    lv_obj_t *icon, *label;

    (void)user_data;

    icon = lv_image_create(row);
    lv_image_set_src(icon, r->icon);
    lv_obj_align(icon, LV_ALIGN_LEFT_MID, 12, 0);

    label = lv_label_create(row);
    lv_label_set_text(label, r->name);
    lv_obj_set_style_text_font(label, &ui_font_cn14, LV_PART_MAIN);
    lv_obj_set_style_text_color(label, lv_color_white(), LV_PART_MAIN);
    lv_obj_align(label, LV_ALIGN_LEFT_MID, 100, 0);

    lv_obj_add_flag(row, LV_OBJ_FLAG_CLICKABLE);
    /* 锁住手势目标：不锁的话 LVGL 每拍重搜按下对象，行会从手指底下溜走，
     * 于是一次拖动被记成"在好几行上按下"（详见上面 DRAG_CLICK_IGNORE_PX 的注释） */
    lv_obj_add_flag(row, LV_OBJ_FLAG_PRESS_LOCK);
    lv_obj_remove_flag(row, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_add_event_cb(row, row_press_cb, LV_EVENT_PRESSED, NULL);
    lv_obj_add_event_cb(row, row_pressing_cb, LV_EVENT_PRESSING, NULL);
    lv_obj_add_event_cb(row, row_released_cb, LV_EVENT_RELEASED, NULL);
    lv_obj_add_event_cb(row, row_press_lost_cb, LV_EVENT_PRESS_LOST, NULL);
    lv_obj_add_event_cb(row, row_click_cb, LV_EVENT_CLICKED, NULL);
}

static int row_index_of(lv_obj_t *obj)
{
    int32_t i, n = rxroller_get_count(s_wheel);

    for (i = 0; i < n; i++) {
        if (rxroller_get_item_obj(s_wheel, i) == obj) return (int)i;
    }
    return -1;
}

static void row_click_cb(lv_event_t *e)
{
    lv_obj_t *row = lv_event_get_target(e);
    int idx = row_index_of(row);

    if (idx < 0 || idx >= WATCH_APP_ROWS_COUNT || NULL == s_wheel) return;

    /* ★ 拖动时必须忽略这次"点击"：上游把行与滚轮根对象的 SCROLLABLE 都清了
     *   （Rxroller.c:578/835，它自己按距离做位移动画），于是 LVGL 的 indev
     *   永远不会置 scroll_obj（lv_indev.c:1211），松手时就直接发
     *   LV_EVENT_CLICKED（lv_indev.c:1368）——**不管拖了多远**。 */
    {
        int travel = s_press_travel;

        s_press_valid = false;
        s_press_travel = 0;
        if (travel > DRAG_CLICK_IGNORE_PX) {
            printf("[WHEEL] click ignored: travel=%dpx (>%d)\n",
                   travel, DRAG_CLICK_IGNORE_PX);
            return;
        }
    }

    /* 两段式点击（本轮只加"拖动忽略"，其余逻辑保持原样）：
     * 非中心行 → 先滚到中心；中心行 → 打开。 */
    if (idx != (int)rxroller_get_center(s_wheel)) {
        printf("[WHEEL] focus row %d -> %s\n", idx, WATCH_APP_ROWS[idx].id);
        watch_list_center(idx, true);
        return;
    }

    {
        char buf[64];

        printf("[WHEEL] open row %d -> %s\n", idx, WATCH_APP_ROWS[idx].id);
        if (s_status) {
            /* ★ "已打开" 三个汉字必须在字体子集内（preflight 第 3 组门禁扫这条） */
            snprintf(buf, sizeof(buf), "已打开: %s", WATCH_APP_ROWS[idx].name);
            lv_label_set_text(s_status, buf);
        }
    }
}

static void cull_timer_cb(lv_timer_t *t) { (void)t; watch_list_cull(); }

/* 屏外回收：上游只在"根对象很小、子行天然被裁"的前提下工作。
 * 我们把根撑满宿主以便 5 行都可见，代价是 22 行全部进入绘制/无效计算——
 * 实测 lv_snapshot_take 一次要 ~55 秒（关掉快照后同样时长能跑 9500 拍）。
 * 这里按真实手表列表的做法做屏外回收：|distance| 超过 CULL_PITCHES 个行距就隐藏。 */
#define CULL_PITCHES 4

void watch_list_cull(void)
{
    rxroller_item_t *items;
    int32_t i, n, center;
    int32_t limit = ROW_PITCH * CULL_PITCHES;

    if (NULL == s_wheel) return;
    items = rxroller_get_icons(s_wheel);
    if (NULL == items) return;
    n = rxroller_get_count(s_wheel);
    center = (int)rxroller_get_center(s_wheel);

    for (i = 0; i < n; i++) {
        lv_obj_t *o = rxroller_get_item_obj(s_wheel, i);
        int32_t d;
        if (NULL == o) continue;
        /* 用"离中心的行距"而不是 items[].distance：动画中 distance 会连续变化 */
        d = (int32_t)LV_ABS(items[i].distance);
        if (i != center && d > limit) lv_obj_add_flag(o, LV_OBJ_FLAG_HIDDEN);
        else lv_obj_remove_flag(o, LV_OBJ_FLAG_HIDDEN);
    }
}

void watch_list_create(lv_obj_t *host, lv_obj_t *status_label)
{
    rxroller_config_t cfg;

    memset(&cfg, 0, sizeof(cfg));
    s_status = status_label;

    cfg.icon_distance = ROW_PITCH;
    cfg.big_w = ROW_W;
    cfg.big_h = ROW_H;
    cfg.edge_scale = EDGE_SCALE;
    cfg.arrange = RXROLLER_ARRANGE_VERTICAL;
    /* 参考图（Design Watch 的 AppList）是**竖直一列**、只按距离缩放；
     * 上游的 ARC 模式让上下两侧都往 +x 漂（x=r*(1-cos)），观感偏"斜"。
     * 所以默认走 NONE（直列）。要看弧线把 curve_mode 改回 ARC 并调 CURVE_RADIUS。 */
    cfg.curve_mode = RXROLLER_CURVE_NONE;
    cfg.curve_radius = CURVE_RADIUS;
    cfg.curve_reverse = 0;
    cfg.anim_time = ANIM_TIME;
    cfg.icon_mode = RXROLLER_MODE_CONTAINER;   /* 容器模式：行里放图标+名称 */
    cfg.create_cb = row_create_cb;
    cfg.normal_font = &ui_font_cn14;
    cfg.text_color = lv_color_white();
    cfg.scale_mode = RXROLLER_SCALE_TRANSFORM; /* 变换缩放：不改布局尺寸 */
    cfg.inertia_divisor = 20;
    cfg.circular = 0;                          /* 线性列表，不循环 */

    s_wheel = rxroller_create(host, WATCH_APP_ROWS_COUNT, &cfg);
    if (NULL == s_wheel) {
        printf("[WHEEL] rxroller_create FAILED\n");
        return;
    }
    /* 点击 cb 在 row_create_cb 里逐行挂（要的是"哪一行被点"，挂在轮上拿不到行号） */
    /* 上游把根对象留成一个 130x130 的"锚"，行以它的内容原点为中心向正负两侧排。
     * LVGL 9.4 里子对象一律裁到父边界——`LV_OBJ_FLAG_OVERFLOW_VISIBLE` 只是
     * 按 ext_draw_size 放宽（src/core/lv_obj_pos.c:914），并不取消裁剪，
     * 所以实测 5 行位置都算对了（abs y=9..492）却只画出中心那一行。
     * 外壳级修法：把根对象撑满宿主 + 用 padding 把原锚点保住（不改它的坐标数学）。
     * 注意要先 lv_obj_update_layout()：EEZ 的宿主在此刻还没排版，量出来是 0。 */
    lv_obj_update_layout(s_wheel);
    {
        int ax = (int)lv_obj_get_x(s_wheel);
        int ay = (int)lv_obj_get_y(s_wheel);
        int hw = (int)lv_obj_get_width(host);
        int hh = (int)lv_obj_get_height(host);

        lv_obj_set_align(s_wheel, LV_ALIGN_TOP_LEFT);
        lv_obj_set_pos(s_wheel, 0, 0);
        lv_obj_set_size(s_wheel, hw, hh);
        lv_obj_set_style_pad_left(s_wheel, ax, LV_PART_MAIN);
        lv_obj_set_style_pad_top(s_wheel, ay, LV_PART_MAIN);
        printf("[WHEEL] anchor(%d,%d) kept, root=%dx%d\n", ax, ay, hw, hh);
    }

    lv_timer_create(cull_timer_cb, 60, NULL);

    printf("[WHEEL] created, rows=%d pitch=%d edge=%d/255 curve_r=%d\n",
           WATCH_APP_ROWS_COUNT, ROW_PITCH, EDGE_SCALE, CURVE_RADIUS);
}

/*---- 自证接口 ----*/

int watch_list_center_index(void)
{
    return s_wheel ? (int)rxroller_get_center(s_wheel) : -1;
}

bool watch_list_is_animating(void)
{
    return s_wheel ? (rxroller_is_animating(s_wheel) != 0) : false;
}

void watch_list_center(int index, bool anim)
{
    if (s_wheel) rxroller_set_center(s_wheel, index, anim ? LV_ANIM_ON : LV_ANIM_OFF);
}

/* 惯性抛出。px 带符号：正=手指往下划（看更早的行，行号减小）。
 *
 * 为什么不直接叫 rxroller_scroll(px)：上游动画分支里 offset 只参与算动画时长
 * （Rxroller.c:725），行的目标位置恒等于"当前最近行"——也就是永远只吸附、不位移。
 * 所以这里自己把抛距换算成行距增量，再让上游去做那段动画（多行、ease_out、
 * 落点严格对齐某一行），观感才和真手表一致。 */
void watch_list_fling(int32_t px)
{
    int32_t center, rows, target;

    if (NULL == s_wheel || 0 == px) return;

    /* 四舍五入到整行（+半行距再截断） */
    rows = (px + (px > 0 ? ROW_PITCH / 2 : -ROW_PITCH / 2)) / ROW_PITCH;
    if (rows >  FLING_MAX_ROWS) rows =  FLING_MAX_ROWS;
    if (rows < -FLING_MAX_ROWS) rows = -FLING_MAX_ROWS;
    if (rows == 0) return;              /* 抛距不足半行：交给上游的吸附就够了 */

    center = (int32_t)rxroller_get_center(s_wheel);
    target = center - rows;             /* 见上：手指向下 = 行号减小 */
    if (target < 0) target = 0;
    if (target > WATCH_APP_ROWS_COUNT - 1) target = WATCH_APP_ROWS_COUNT - 1;
    if (target == center) return;

    printf("[FLING] throw=%dpx rows=%d center=%d -> %d\n",
           (int)px, (int)rows, (int)center, (int)target);
    rxroller_set_center(s_wheel, target, LV_ANIM_ON);
}

int watch_list_row_scale(int index)
{
    rxroller_item_t *items;

    if (NULL == s_wheel || index < 0 || index >= WATCH_APP_ROWS_COUNT) return -1;
    items = rxroller_get_icons(s_wheel);
    return items ? (int)items[index].scale : -1;
}

void watch_list_dump(const char *tag)
{
    rxroller_item_t *items;
    int center, i;

    if (NULL == s_wheel) {
        printf("[WHEEL] %s 未创建\n", tag);
        return;
    }
    items = rxroller_get_icons(s_wheel);
    center = (int)rxroller_get_center(s_wheel);
    if (NULL == items) {
        printf("[WHEEL] %s items=NULL\n", tag);
        return;
    }
    printf("[WHEEL] %-8s center=%2d(%s) scale:", tag, center,
           WATCH_APP_ROWS[center].id);
    for (i = 0; i < WATCH_APP_ROWS_COUNT; i++) {
        if (i >= center - 3 && i <= center + 3) printf(" %3d", items[i].scale);
    }
    printf(" | dist(center)=%d\n", items[center].distance);

    /* 逐行几何诊断（排"只有一行可见"这类观感问题用）：坐标/尺寸/是否隐藏 */
    if (getenv("WATCH_ROWDEBUG")) {
        lv_area_t a;
        int lvl = 0;
        lv_obj_get_coords(s_wheel, &a);
        printf("[WHEEL obj] coords=(%d,%d)..(%d,%d) size=(%d,%d)\n",
               (int)a.x1, (int)a.y1, (int)a.x2, (int)a.y2,
               (int)lv_obj_get_width(s_wheel), (int)lv_obj_get_height(s_wheel));
        for (i = 0; i < WATCH_APP_ROWS_COUNT; i++) {
            lv_obj_t *o = rxroller_get_item_obj(s_wheel, i);
            if (NULL == o) continue;
            if (i < center - 4 || i > center + 4) continue;
            lv_obj_get_coords(o, &a);   /* 绝对坐标（相对显示器） */
            printf("[ROW %2d] dist=%5d scale=%3d abs=(%4d,%4d)..(%4d,%4d)"
                   " hidden=%d opa=%d\n",
                   i, items[i].distance, items[i].scale,
                   (int)a.x1, (int)a.y1, (int)a.x2, (int)a.y2,
                   (int)lv_obj_has_flag(o, LV_OBJ_FLAG_HIDDEN),
                   (int)lv_obj_get_style_opa(o, LV_PART_MAIN));
            if (i == center) {
                /* 谁在裁谁：把行内两个子对象的绝对坐标与行的裁剪祖先一起列出来 */
                uint32_t ci, cn = lv_obj_get_child_count(o);
                lv_obj_t *anc;
                printf("[  row children] count=%u\n", (unsigned)cn);
                for (ci = 0; ci < cn; ci++) {
                    lv_obj_t *ch = lv_obj_get_child(o, ci);
                    lv_obj_get_coords(ch, &a);
                    printf("[   child %u] abs=(%4d,%4d)..(%4d,%4d) hidden=%d\n",
                           (unsigned)ci, (int)a.x1, (int)a.y1, (int)a.x2, (int)a.y2,
                           (int)lv_obj_has_flag(ch, LV_OBJ_FLAG_HIDDEN));
                }
                for (anc = o; anc != NULL; anc = lv_obj_get_parent(anc)) {
                    lv_obj_get_coords(anc, &a);
                    printf("[   ancestor %d] abs=(%4d,%4d)..(%4d,%4d)"
                           " overflow=%d scroll=%d\n",
                           lvl++,
                           (int)a.x1, (int)a.y1, (int)a.x2, (int)a.y2,
                           (int)lv_obj_has_flag(anc, LV_OBJ_FLAG_OVERFLOW_VISIBLE),
                           (int)lv_obj_has_flag(anc, LV_OBJ_FLAG_SCROLLABLE));
                }
            }
        }
    }
}
