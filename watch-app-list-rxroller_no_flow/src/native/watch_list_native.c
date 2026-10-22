/*
 * watch_list_native.c —— 用 Rxroller 搭的 22 行应用列表（本工程界面主体）
 *
 * 分工（no-flow 口径）：
 *   EEZ 出：410x502 屏、宿主容器 objects.list_host、标题、状态行、中文字体条目；
 *   这里出：滚轮件本体（弧线排布 + 逐行按离中心距离缩放 + 惯性 + 点击）。
 *
 * 不走 EEZ Flow 的论证见 README §2；缺陷史与修复见 FIXLOG.md。
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "lvgl.h"
#include "watch_list_native.h"
#include "watch_list_config.h"   /* ★ 所有可调参数都在这一份头文件里 */
#include "app_rows.h"
#include "rxroller/Rxroller.h"
#include "fonts.h"          /* EEZ 生成：ui_font_cn14 */

/* 由 config 派生的量（口径见 watch_list_config.h） */
#define CENTER_MIN_INDEX   (EDGE_SNAP_TOP_ORDINAL - 1)
#define CENTER_MAX_INDEX   (WATCH_APP_ROWS_COUNT - EDGE_SNAP_BOTTOM_ORDINAL)

static lv_obj_t *s_wheel = NULL;
static lv_obj_t *s_status = NULL;

/* 拖动判定：按拍累计最大位移，超阈值就忽略随之而来的 CLICKED。
 * 必须"累计 + PRESS_LOCK"两道一起上的原因见 FIXLOG FX-003。 */
static lv_point_t s_press_pt;
static bool s_press_valid = false;
static int s_press_travel = 0;

/* 快滑惯性（上游没有，见 FIXLOG FX-007）。阈值推导见 README §5.2。 */
static lv_point_t s_last_pt;
static uint32_t   s_last_t;
static int        s_vel;            /* px/s，纵向；正=手指向下 */

/* 定义在本文件后半段，这里先声明给事件回调用 */
static void watch_list_align_center(lv_obj_t *host);
static int  center_clamp(int idx);
static void snap_edge_async(void *user);

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

            /* 停手超过 STALE_MS 且 y 未变 ⇒ 速度清零，否则残留速度会误抛 */
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

/* 松手：速度投影成抛距交给 fling。必须延一拍——上游的 RELEASED 跑在我们后面，
 * 同步调会被它那次 set_center 覆盖（见 FIXLOG FX-007 补充）。 */
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

    /* 位移未超阈值 = 轻点，不是拖动：否则一次 10px 轻扫会同时触发 CLICKED 和抛出 */
    if (s_press_travel <= DRAG_CLICK_IGNORE_PX) { s_vel = 0; return; }

    if (s_vel <= -FLING_MIN_VEL || s_vel >= FLING_MIN_VEL) {   /* 够快才算快滑 */
        /* 屏幕内容跟手指同向走 ⇒ 手指向下(+vel)是看更早的行，行号减小 */
        throw_px = (int32_t)s_vel * FLING_SEC / 1000;
        if (throw_px >  FLING_MAX_PX) throw_px =  FLING_MAX_PX;
        if (throw_px < -FLING_MAX_PX) throw_px = -FLING_MAX_PX;
        printf("[FLING] vel=%d px/s -> throw=%d px\n", s_vel, (int)throw_px);
        lv_async_call(fling_async, (void *)(intptr_t)throw_px);
    }
    s_vel = 0;

    /* 松手落点纠正。排在 fling 之后 => 快滑落点已定，这里只管"拖到端点慢慢松手" */
    lv_async_call(snap_edge_async, NULL);
}

static void row_click_cb(lv_event_t *e);

/* 行内容：左圆图标 + 右中文名。
 * ★ 容器 user_data 已被上游占用，行号要靠 rxroller_get_item_obj() 反查。 */
static void row_create_cb(lv_obj_t *row, int32_t index, void *user_data)
{
    const watch_app_row_t *r = &WATCH_APP_ROWS[index];
    lv_obj_t *icon, *label;

    (void)user_data;

    icon = lv_image_create(row);
    lv_image_set_src(icon, r->icon);
    lv_obj_align(icon, LV_ALIGN_LEFT_MID, ROW_ICON_X, 0);

    label = lv_label_create(row);
    lv_label_set_text(label, r->name);
    lv_obj_set_style_text_font(label, &ui_font_cn14, LV_PART_MAIN);
    lv_obj_set_style_text_color(label, lv_color_white(), LV_PART_MAIN);
    lv_obj_align(label, LV_ALIGN_LEFT_MID, ROW_LABEL_X, 0);

    lv_obj_add_flag(row, LV_OBJ_FLAG_CLICKABLE);
    /* 锁住手势目标，见 FIXLOG FX-003 */
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

    /* ★ 上游清了 SCROLLABLE ⇒ indev 永不置 scroll_obj ⇒ 松手无条件发 CLICKED，
     *   不管拖了多远。必须自己按位移挡掉，见 FIXLOG FX-001。 */
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

    /* 两段式点击：非中心行先滚到中心；中心行才打开 */
    if (idx != (int)rxroller_get_center(s_wheel)) {
        printf("[WHEEL] focus row %d -> %s\n", idx, WATCH_APP_ROWS[idx].id);
        watch_list_center(idx, true);
        return;
    }

    {
        char buf[64];

        printf("[WHEEL] open row %d -> %s\n", idx, WATCH_APP_ROWS[idx].id);
        if (s_status) {
            /* ★ 上屏中文必须在字体子集内（preflight 第 3 组反查产物） */
            snprintf(buf, sizeof(buf), "已打开: %s", WATCH_APP_ROWS[idx].name);
            lv_label_set_text(s_status, buf);
        }
    }
}

static void cull_timer_cb(lv_timer_t *t) { (void)t; watch_list_cull(); }

/* 屏外回收：|distance| 超过 CULL_PITCHES 个行距就隐藏。
 * 为什么必须做（以及它反过来引发的 FX-011）见 FIXLOG FX-005。 */

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
    /* 排布形状由 config 的 CURVE_ENABLE 决定（0=竖列，1=弧线，半径 CURVE_RADIUS）。
     * 弧线下上下两侧同向鼓出（x 是 |d| 的偶函数），中心行 d=0 不受影响。 */
    cfg.curve_mode = CURVE_ENABLE ? RXROLLER_CURVE_ARC : RXROLLER_CURVE_NONE;
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
    /* 根对象撑满宿主 + 用 padding 保住上游锚点（不改它的坐标数学）。
     * 为什么必须这样做：见 FIXLOG FX-004。 */

    /* ★ 手势回调必须同时挂行与滚轮根对象，只挂行会被 HIDDEN 静默吞掉：
     *   见 FIXLOG FX-011。两条路径都归到同一个 snap_edge_async。 */
    lv_obj_add_event_cb(s_wheel, row_press_cb, LV_EVENT_PRESSED, NULL);
    lv_obj_add_event_cb(s_wheel, row_pressing_cb, LV_EVENT_PRESSING, NULL);
    lv_obj_add_event_cb(s_wheel, row_released_cb, LV_EVENT_RELEASED, NULL);
    lv_obj_add_event_cb(s_wheel, row_press_lost_cb, LV_EVENT_PRESS_LOST, NULL);

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
    watch_list_align_center(host);
    /* 上游建轮时直接把中心摆成行 0，那是"不允许磁吸"的范围外 ⇒ 起步就落到行 1。
     * 用 ANIM_OFF：这是初始态，不该有一段开场动画。 */
    watch_list_center(CENTER_MIN_INDEX, false);

    lv_timer_create(cull_timer_cb, 60, NULL);

    printf("[WHEEL] created, rows=%d pitch=%d edge=%d/255 curve_r=%d\n",
           WATCH_APP_ROWS_COUNT, ROW_PITCH, EDGE_SCALE, CURVE_RADIUS);
}

/*---- 中心行的落点标定（横向 CENTER_X_PCT% + 垂直 CENTER_Y_PCT%）----*/

/* 一次性闭环标定：割线法**实测** pad→图标中心 的斜率，不假设 1/2。
 * 为什么不写死 pad：见 FIXLOG FX-010 / README §5.3。 */

/* 上游把**整行**（图标+文字）按行自己的 (big_w/2, big_h/2) 当轴心做 transform 缩放。
 * 图标在轴心左侧 ⇒ 放大后内容整体往轴心方向漂，`lv_obj_get_coords` 拿到的
 * "布局中心"并不是屏幕上看到的中心（中心档 150% 时实测往轴心侧偏 42px）。
 * 标定与断言一律换算成渲染后的坐标，缺陷史见 FIXLOG FX-024。 */
static void row_pivot(lv_obj_t *row, int *z, int *px, int *py)
{
    lv_area_t ra;

    lv_obj_get_coords(row, &ra);
    *z = (int)lv_obj_get_style_transform_scale_x(row, LV_PART_MAIN);
    if (*z <= 0) *z = 256;
    *px = (int)ra.x1 + (int)lv_obj_get_style_transform_pivot_x(row, LV_PART_MAIN);
    *py = (int)ra.y1 + (int)lv_obj_get_style_transform_pivot_y(row, LV_PART_MAIN);
}

static int zoom_about(int v, int pivot, int z)
{
    return pivot + (int)((int64_t)(v - pivot) * z / 256);
}

static lv_obj_t *center_row(void)
{
    int idx = (int)rxroller_get_center(s_wheel);

    if (NULL == s_wheel || idx < 0 || idx >= WATCH_APP_ROWS_COUNT) return NULL;
    return rxroller_get_item_obj(s_wheel, idx);
}

static bool center_icon_rect(int *cx, int *cy, int *w, bool on_screen)
{
    lv_obj_t *row = center_row(), *icon;
    lv_area_t a;
    int z, px, py;

    if (NULL == row || lv_obj_get_child_count(row) < 1) return false;
    icon = lv_obj_get_child(row, 0);          /* child 0 = row_create_cb 先建的图标 */
    if (NULL == icon) return false;
    lv_obj_get_coords(icon, &a);
    if (on_screen) {
        row_pivot(row, &z, &px, &py);
        a.x1 = zoom_about(a.x1, px, z);   a.x2 = zoom_about(a.x2, px, z);
        a.y1 = zoom_about(a.y1, py, z);   a.y2 = zoom_about(a.y2, py, z);
    }
    if (cx) *cx = ((int)a.x1 + (int)a.x2) / 2;
    if (cy) *cy = ((int)a.y1 + (int)a.y2) / 2;
    if (w)  *w  = (int)a.x2 - (int)a.x1 + 1;
    return true;
}

static int center_axis(bool is_x)
{
    int cx, cy;
    return center_icon_rect(&cx, &cy, NULL, true) ? (is_x ? cx : cy) : -1;
}

static int pad_of(bool is_x)
{
    return (int)(is_x ? lv_obj_get_style_pad_left(s_wheel, LV_PART_MAIN)
                      : lv_obj_get_style_pad_top(s_wheel, LV_PART_MAIN));
}

static void pad_set(bool is_x, int v)
{
    if (is_x) lv_obj_set_style_pad_left(s_wheel, v, LV_PART_MAIN);
    else      lv_obj_set_style_pad_top(s_wheel, v, LV_PART_MAIN);
}

static void align_center_axis(bool is_x, int target)
{
    int p0 = pad_of(is_x), c0 = center_axis(is_x);
    int p1, c1, i, next;

    if (c0 < 0) return;
    if (LV_ABS(c0 - target) <= CENTER_TOL_PX) {
        printf("[WHEEL] align-%c: 已达标 target=%d got=%d\n",
               is_x ? 'x' : 'y', target, c0);
        return;
    }
    p1 = p0 + CENTER_PROBE_PX;                /* 试探点：实测斜率 */
    pad_set(is_x, p1);
    lv_obj_update_layout(s_wheel);
    c1 = center_axis(is_x);
    if (c1 < 0) { pad_set(is_x, p0); return; }

    for (i = 0; i < CENTER_ITERS_MAX; i++) {
        if (LV_ABS(c1 - target) <= CENTER_TOL_PX) break;
        next = (c1 == c0) ? (p1 - (c1 - target))
                          : (p1 + (int)((int64_t)(target - c1) * (p1 - p0) / (c1 - c0)));
        p0 = p1; c0 = c1;                     /* 割线往前滚一格 */
        p1 = next;
        pad_set(is_x, p1);
        lv_obj_update_layout(s_wheel);
        c1 = center_axis(is_x);
        if (c1 < 0) break;
    }
    printf("[WHEEL] align-%c: target=%d got=%d pad %d->%d 步数=%d\n",
           is_x ? 'x' : 'y', target, c1, pad_of(is_x), p1, i + 2);
}

static void watch_list_align_center(lv_obj_t *host)
{
    align_center_axis(true, (int)lv_obj_get_width(host) * CENTER_X_PCT / 100);
    align_center_axis(false, (int)lv_obj_get_height(host) * CENTER_Y_PCT / 100);
    /* 布局中心与渲染中心差多少 = 上游整行缩放把图标往轴心拽了多少（FX-024 的量证） */
    printf("[WHEEL] center icon: 渲染=(%d,%d) 布局=(%d,%d) 差=(%d,%d)\n",
           center_axis(true), center_axis(false),
           watch_list_center_icon_layout_x(), watch_list_center_icon_layout_y(),
           center_axis(true) - watch_list_center_icon_layout_x(),
           center_axis(false) - watch_list_center_icon_layout_y());
}

/*---- 观测量（无头夹具核对用）----*/

int watch_list_center_icon_x(void) { return center_axis(true); }
int watch_list_center_icon_y(void) { return center_axis(false); }
int watch_list_center_icon_layout_x(void)
{
    int cx;
    return center_icon_rect(&cx, NULL, NULL, false) ? cx : -1;
}
int watch_list_center_icon_layout_y(void)
{
    int cy;
    return center_icon_rect(NULL, &cy, NULL, false) ? cy : -1;
}

/* 第 index 行"图标+文字"在屏幕上的真实包围盒（含整行 transform 缩放）。
 * 行不存在/已被回收（HIDDEN）返回 false。胶囊边界核对夹具用它。 */
bool watch_list_row_box(int index, int *x1, int *y1, int *x2, int *y2)
{
    int z, px, py, i, n;
    lv_obj_t *row, *ch;
    bool any = false;

    if (NULL == s_wheel || index < 0 || index >= WATCH_APP_ROWS_COUNT) return false;
    row = rxroller_get_item_obj(s_wheel, index);
    if (NULL == row || lv_obj_has_flag(row, LV_OBJ_FLAG_HIDDEN)) return false;
    row_pivot(row, &z, &px, &py);

    n = (int)lv_obj_get_child_count(row);
    for (i = 0; i < n; i++) {
        int cx1, cy1, cx2, cy2;
        lv_area_t a;

        ch = lv_obj_get_child(row, i);
        if (NULL == ch || lv_obj_has_flag(ch, LV_OBJ_FLAG_HIDDEN)) continue;
        lv_obj_get_coords(ch, &a);
        cx1 = zoom_about(a.x1, px, z);   cx2 = zoom_about(a.x2, px, z);
        cy1 = zoom_about(a.y1, py, z);   cy2 = zoom_about(a.y2, py, z);
        if (!any) {
            *x1 = cx1;  *y1 = cy1;  *x2 = cx2;  *y2 = cy2;
            any = true;
        } else {
            if (cx1 < *x1) *x1 = cx1;
            if (cy1 < *y1) *y1 = cy1;
            if (cx2 > *x2) *x2 = cx2;
            if (cy2 > *y2) *y2 = cy2;
        }
    }
    return any;
}

int watch_list_center_icon_w(void)
{
    int w;
    return center_icon_rect(NULL, NULL, &w, false) ? w : -1;
}

int watch_list_row_pitch(void) { return ROW_PITCH; }

/* 第 i 行当前离中心的带符号距离（px）。夹具用它验"过程线性"。 */
int watch_list_row_distance(int index)
{
    rxroller_item_t *items;

    if (NULL == s_wheel || index < 0 || index >= WATCH_APP_ROWS_COUNT) return -99999;
    items = rxroller_get_icons(s_wheel);
    return items ? (int)items[index].distance : -99999;
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

/*---- 允许磁吸到中心的行范围：[1, N-2]（宏在文件顶部）----*/

static int center_clamp(int idx)
{
    if (idx < CENTER_MIN_INDEX) return CENTER_MIN_INDEX;
    if (idx > CENTER_MAX_INDEX) return CENTER_MAX_INDEX;
    return idx;
}

/* 松手落点纠正：拖到最上/最下都允许，但松手后弹回"第 n 个"（宏在文件顶部）。
 * 必须延一拍——上游也在行上注册了 LV_EVENT_RELEASED（Rxroller.c:638，
 * 注册在我们的行 cb 之后），它那次吸附会覆盖掉我们同步发起的这次。 */
static void snap_edge_async(void *user)
{
    (void)user;
    watch_list_snap_edge();
}

void watch_list_snap_edge(void)
{
    int c, t;

    if (NULL == s_wheel) return;
    c = (int)rxroller_get_center(s_wheel);
    t = center_clamp(c);
    if (t == c) return;                       /* 落在正常区间，什么都不做 */
    printf("[WHEEL] 松手落点越界：中心=%d（第 %d 个）-> 弹回 %d（第 %d 个）\n",
           c, c + 1, t, t + 1);
    rxroller_set_center(s_wheel, t, LV_ANIM_ON);
}

void watch_list_center(int index, bool anim)
{
    if (s_wheel) rxroller_set_center(s_wheel, center_clamp(index),
                                     anim ? LV_ANIM_ON : LV_ANIM_OFF);
}

/* 探针：**绕过**本工程的 clamp，直接叫上游 API。
 * 夹具用它证明"首尾不许磁吸"是上游钳位（补丁 #15）在挡，而不是靠我们事后纠正。 */
void watch_list_center_no_clamp(int index, bool anim)
{
    if (s_wheel) rxroller_set_center(s_wheel, index, anim ? LV_ANIM_ON : LV_ANIM_OFF);
}

int watch_list_center_min(void) { return CENTER_MIN_INDEX; }
int watch_list_center_max(void) { return CENTER_MAX_INDEX; }

/* 惯性抛出。px 带符号：正=手指往下划（行号减小）。
 * 不能用 rxroller_scroll(px)：上游动画分支里 offset 只参与算时长，见 FIXLOG FX-007。 */
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
    target = center_clamp(center - rows);           /* 见上：手指向下 = 行号减小 */
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
