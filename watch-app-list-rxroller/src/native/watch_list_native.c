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
#include <stdio.h>
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
    lv_obj_remove_flag(row, LV_OBJ_FLAG_SCROLLABLE);
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
    char buf[64];

    if (idx < 0 || idx >= WATCH_APP_ROWS_COUNT || NULL == s_wheel) return;

    /* 两段式点击（也顺手避开"拖动结束误触发打开"）：
     * 非中心行 → 先滚到中心；中心行 → 打开。 */
    if (idx != (int)rxroller_get_center(s_wheel)) {
        printf("[WHEEL] focus row %d -> %s\n", idx, WATCH_APP_ROWS[idx].id);
        rxroller_set_center(s_wheel, idx, LV_ANIM_ON);
        return;
    }

    printf("[WHEEL] open row %d -> %s\n", idx, WATCH_APP_ROWS[idx].id);
    if (s_status) {
        /* ★ "已打开" 三个汉字必须在字体子集内（preflight 第 3 组门禁扫这条） */
        snprintf(buf, sizeof(buf), "已打开: %s", WATCH_APP_ROWS[idx].name);
        lv_label_set_text(s_status, buf);
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
