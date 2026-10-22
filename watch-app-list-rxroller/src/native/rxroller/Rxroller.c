/*
 * Rxroller.c —— 由 design/port_rxroller.py 从上游 Rxroller.c.orig 生成，勿手改。
 * 上游 https://github.com/rxwind7/Rxroller (MIT)；改动 = LVGL v8 -> 9.4 的
 * user_data 访问器化（12 处，逐条见 diff）+ 内存 API 别名 + 一条缩放窗口参数化。
 * 完整账单与复核方法见工程根目录 PORTLOG.md。
 * 与上游的 diff 就是移植账单：diff Rxroller.c.orig Rxroller.c
 */
// Rxroller.c
#include "Rxroller.h"
/* RX-PORT-FIX: 累计位移 <= 该值才算点击（px）。行距 100px，轻点抖动远小于它 */
#ifndef RXROLLER_CLICK_TRAVEL_MAX
#  define RXROLLER_CLICK_TRAVEL_MAX 10
#endif
/* RX-PORT: LVGL 9 内存 API 改名（lv_mem_alloc->lv_malloc, lv_mem_free->lv_free）*/
#ifndef lv_mem_alloc
#  define lv_mem_alloc(sz) lv_malloc(sz)
#endif
#ifndef lv_mem_free
#  define lv_mem_free(p)   lv_free(p)
#endif
/* RX-PORT-FEAT: 缩放衰减窗口，单位=行距。上游写死 1 ⇒ 只有正中那行是大的，
 *  紧邻行立刻落到 edge_scale（= "未选中就是最小"的口径）。
 *  调大它才有"上下几行连续渐变"。值来自 watch_list_config.h 的
 *  SCALE_SPAN_PITCHES，取 1 时与上游行为完全一致。
 *  这是**能力补丁**不是版本适配，diff 里单列一条。 */
#ifndef RX_SCALE_SPAN_PITCHES
#  define RX_SCALE_SPAN_PITCHES 3
#endif
#include "string.h"
#include "limits.h"
#include "math.h"
#include "stdlib.h"

/* ==================== 内部结构定义 ==================== */
typedef struct {
    lv_obj_t       *screen;
    rxroller_item_t   *items;
    int32_t         item_count;
    int32_t         center_idx;

    uint8_t         touched;
    lv_point_t      touch_point1;
    lv_point_t      touch_point2;
    int32_t         offset;
    int32_t         drag_travel;  /* RX-PORT-FIX: 整段手势累计位移 */

    uint8_t         is_animating;

    rxroller_config_t config;

    void           *user_data;

    uint8_t         is_confirmed;
    int32_t         confirmed_index;
    int32_t         pending_anim_count;
} rxroller_ctx_t;

/* ==================== 内部函数声明 ==================== */
static void rx_anim_exec_cb(void *var, int32_t v);
static void rx_anim_ready_cb(lv_anim_t *a);
static void rx_create_animation(lv_obj_t *obj, int32_t start, int32_t end,
                                uint32_t time, rxroller_ctx_t *ctx);
static void rx_event_pressing(lv_event_t *e);
static void rx_event_released(lv_event_t *e);
static void rx_event_delete(lv_event_t *e);
static void rx_event_screen_unload(lv_event_t *e);
static void rx_update_item_scale(rxroller_ctx_t *ctx, rxroller_item_t *item);
static void rx_update_item_size(rxroller_ctx_t *ctx, rxroller_item_t *item);
static void rx_calc_curve_pos(const rxroller_ctx_t *ctx, int32_t distance,
                              int32_t *x, int32_t *y);
static void rx_normalize_distance(const rxroller_ctx_t *ctx, int32_t *distance);
static void rx_clamp_distance(const rxroller_ctx_t *ctx, int32_t index, int32_t *distance);
static void rx_set_center_internal(rxroller_ctx_t *ctx, int32_t icon_id, uint8_t anim_en);
static rxroller_ctx_t *rx_get_ctx(lv_obj_t *wheel);
static lv_obj_t *rx_create_item_obj(rxroller_ctx_t *ctx, int32_t index);
static void rx_init_item(rxroller_ctx_t *ctx, int32_t index);
static void rx_cleanup_internal(rxroller_ctx_t *ctx, uint8_t delete_screen);
static void rx_dismiss_exec_cb(void *var, int32_t v);
static void rx_dismiss_ready_cb(lv_anim_t *a);
static void rx_restore_exec_cb(void *var, int32_t v);
static void rx_restore_ready_cb(lv_anim_t *a);

/* 计算相对索引（支持循环） */
static int32_t calc_relative_index(const rxroller_ctx_t *ctx, int32_t i, int32_t center)
{
    if (!ctx->config.circular) return i - center;
    int32_t diff = i - center;
    int32_t half = ctx->item_count / 2;
    if (diff > half) diff -= ctx->item_count;
    else if (diff < -half) diff += ctx->item_count;
    return diff;
}

/* 获取目标距离 */
static int32_t get_target_distance(const rxroller_ctx_t *ctx, int32_t i, int32_t target_center)
{
    int32_t rel = calc_relative_index(ctx, i, target_center);
    return rel * (int32_t)ctx->config.icon_distance;
}

/* 循环模式下调整起始位置（最短路径） */
static void adjust_start_shortest(const rxroller_ctx_t *ctx, int32_t *start, int32_t target)
{
    if (!ctx->config.circular) return;
    int32_t range = ctx->item_count * (int32_t)ctx->config.icon_distance;
    int32_t diff = target - *start;
    if (LV_ABS(diff) > range / 2) {
        if (diff > 0) *start += range;
        else *start -= range;
    }
}

/* ==================== 上下文获取 ==================== */
static rxroller_ctx_t *rx_get_ctx(lv_obj_t *wheel)
{
    if (!wheel || !lv_obj_is_valid(wheel)) {
        SW_LOG_ERROR("wheel is NULL or invalid");
        return NULL;
    }
    if (!lv_obj_get_user_data(wheel)) {   /* RX-PORT: v8 直接摸 obj->user_data */
        SW_LOG_ERROR("wheel->user_data is NULL");
        return NULL;
    }
    return (rxroller_ctx_t *)lv_obj_get_user_data(wheel);
}

/* ==================== 清理内部资源 ==================== */
static void rx_cleanup_internal(rxroller_ctx_t *ctx, uint8_t delete_screen)
{
    if (!ctx) return;
    SW_LOG_INFO("cleanup: items=%ld, delete_screen=%u", (long)ctx->item_count, delete_screen);

    for (int32_t i = 0; i < ctx->item_count; i++) {
        if (ctx->items[i].obj && lv_obj_is_valid(ctx->items[i].obj)) {
            lv_anim_del(ctx->items[i].obj, rx_anim_exec_cb);
            lv_anim_del(ctx->items[i].obj, rx_dismiss_exec_cb);
            lv_anim_del(ctx->items[i].obj, rx_restore_exec_cb);
        }
    }

    if (ctx->screen && lv_obj_is_valid(ctx->screen)) {
        lv_obj_remove_event_cb(ctx->screen, rx_event_pressing);
        lv_obj_remove_event_cb(ctx->screen, rx_event_released);
        lv_obj_remove_event_cb(ctx->screen, rx_event_delete);
        lv_obj_remove_event_cb(ctx->screen, rx_event_screen_unload);

        if (delete_screen) {
            lv_obj_set_user_data(ctx->screen, NULL);
            lv_obj_del_async(ctx->screen);
        }
        ctx->screen = NULL;
    }

    if (ctx->items) {
        lv_mem_free(ctx->items);
        ctx->items = NULL;
    }

    ctx->item_count = 0;
    ctx->user_data = NULL;
    lv_mem_free(ctx);

    SW_LOG_INFO("cleanup complete");
}

/* ==================== 距离标准化与钳位 ==================== */
static void rx_normalize_distance(const rxroller_ctx_t *ctx, int32_t *distance)
{
    if (!ctx || !distance) return;
    if (!ctx->config.circular || ctx->item_count <= 1) return;

    int32_t range = ctx->item_count * (int32_t)ctx->config.icon_distance;
    int32_t half_range = (ctx->item_count / 2) * (int32_t)ctx->config.icon_distance;
    *distance = ((*distance + half_range) % range + range) % range - half_range;
}

static void rx_clamp_distance(const rxroller_ctx_t *ctx, int32_t index, int32_t *distance)
{
    if (!ctx || !distance) return;
    if (ctx->config.circular) return;

    int32_t min_dist = -(ctx->item_count - 1 - index) * (int32_t)ctx->config.icon_distance;
    int32_t max_dist = index * (int32_t)ctx->config.icon_distance;

    if (*distance < min_dist) {
        SW_LOG_INFO("clamp item[%ld]: %ld -> %ld (hit left bound)", (long)index, (long)*distance, (long)min_dist);
        *distance = min_dist;
    }
    if (*distance > max_dist) {
        SW_LOG_INFO("clamp item[%ld]: %ld -> %ld (hit right bound)", (long)index, (long)*distance, (long)max_dist);
        *distance = max_dist;
    }
}

static void rx_calc_curve_pos(const rxroller_ctx_t *ctx, int32_t distance,
                              int32_t *x, int32_t *y)
{
    if (!x || !y) return;
    *x = 0;
    *y = 0;
    if (!ctx) return;

    if (ctx->config.curve_mode == RXROLLER_CURVE_NONE || ctx->config.curve_radius == 0) {
        if (ctx->config.arrange == RXROLLER_ARRANGE_HORIZONTAL) {
            *x = distance;
        } else {
            *y = distance;
        }
        return;
    }

    int32_t radius = ctx->config.curve_radius;
    if (ctx->config.curve_reverse) radius = -radius;

    float angle = (float)distance / (float)radius;

    if (ctx->config.arrange == RXROLLER_ARRANGE_HORIZONTAL) {
        *x = (int32_t)(radius * sinf(angle));
        *y = (int32_t)(radius * (1.0f - cosf(angle)));
    } else {
        *x = (int32_t)(radius * (1.0f - cosf(angle)));
        *y = (int32_t)(radius * sinf(angle));
    }
}

/* ==================== 缩放与尺寸更新 ==================== */
static void rx_update_item_scale(rxroller_ctx_t *ctx, rxroller_item_t *item)
{
    if (!ctx || !item) return;

    int32_t distance = LV_ABS(item->distance);
    /* RX-PORT-FEAT: 衰减窗口从 1 个行距放宽到 RX_SCALE_SPAN_PITCHES 个 */
    int32_t span = (int32_t)ctx->config.icon_distance * RX_SCALE_SPAN_PITCHES;
    uint16_t scale;

    if (distance == 0) {
        scale = 255;
    } else if (distance >= span) {
        scale = ctx->config.edge_scale;
    } else {
        int32_t v_data = (int32_t)((float)(span - distance)
                         / (float)span
                         * (float)(255 - ctx->config.edge_scale));
        scale = (uint16_t)(ctx->config.edge_scale + v_data);
    }

    item->scale = scale;
    rx_update_item_size(ctx, item);
}

static void rx_update_item_size(rxroller_ctx_t *ctx, rxroller_item_t *item)
{
    if (!ctx || !item) return;
    if (!item->obj || !lv_obj_is_valid(item->obj)) return;

    uint16_t scale = item->scale;
    if (scale < 1) scale = 1;

    if (ctx->config.scale_mode == RXROLLER_SCALE_SIZE) {
        if (ctx->config.icon_mode == RXROLLER_MODE_IMAGE) {
            lv_img_set_zoom(item->obj, scale);
        } else {
            lv_obj_set_size(item->obj,
                ctx->config.big_w * scale / 255,
                ctx->config.big_h * scale / 255);
        }
    } else {
        /* SCALE_TRANSFORM: 使用 config 尺寸设置 pivot，避免动画期间调用 layout 导致崩溃 */
        if (ctx->config.icon_mode == RXROLLER_MODE_IMAGE) {
            lv_obj_update_layout(item->obj);
            lv_obj_set_style_transform_pivot_x(item->obj,
                lv_obj_get_width(item->obj) / 2, LV_PART_MAIN);
            lv_obj_set_style_transform_pivot_y(item->obj,
                lv_obj_get_height(item->obj) / 2, LV_PART_MAIN);
        } else {
            lv_obj_set_style_transform_pivot_x(item->obj,
                ctx->config.big_w / 2, LV_PART_MAIN);
            lv_obj_set_style_transform_pivot_y(item->obj,
                ctx->config.big_h / 2, LV_PART_MAIN);
        }
        lv_obj_set_style_transform_zoom(item->obj, scale, LV_PART_MAIN);
    }
}

/* ==================== 动画回调 ==================== */
static void rx_anim_exec_cb(void *var, int32_t v)
{
    lv_obj_t *icon_obj = (lv_obj_t *)var;

    if (!icon_obj || !lv_obj_is_valid(icon_obj)) {
        SW_LOG_ERROR("anim exec: obj invalid");
        return;
    }

    lv_obj_t *parent = lv_obj_get_parent(icon_obj);
    if (!parent || !lv_obj_is_valid(parent)) {
        SW_LOG_ERROR("anim exec: parent invalid");
        return;
    }

    rxroller_ctx_t *ctx = (rxroller_ctx_t *)lv_obj_get_user_data(parent);
    if (!ctx) {
        SW_LOG_ERROR("anim exec: ctx is NULL");
        return;
    }

    rxroller_item_t *item = (rxroller_item_t *)lv_obj_get_user_data(icon_obj);
    if (!item) {
        SW_LOG_ERROR("anim exec: item is NULL");
        return;
    }

    /* 计算新位置 */
    int32_t pos_x, pos_y;
    rx_calc_curve_pos(ctx, v, &pos_x, &pos_y);
    lv_obj_set_pos(icon_obj, pos_x, pos_y);

    item->distance = v;
    rx_update_item_scale(ctx, item);
}

static void rx_anim_ready_cb(lv_anim_t *a)
{
    if (!a) {
        SW_LOG_ERROR("anim ready: anim is NULL");
        return;
    }

    rxroller_ctx_t *ctx = (rxroller_ctx_t *)a->user_data;
    if (!ctx) {
        SW_LOG_ERROR("anim ready: ctx is NULL");
        return;
    }

    if (ctx->pending_anim_count > 0) ctx->pending_anim_count--;
}

/* ==================== 确认/取消动画回调 ==================== */
static void rx_dismiss_exec_cb(void *var, int32_t v)
{
    lv_obj_t *obj = (lv_obj_t *)var;
    if (!obj || !lv_obj_is_valid(obj)) {
        SW_LOG_ERROR("dismiss exec: obj invalid");
        return;
    }
    lv_opa_t opa = (lv_opa_t)(v > 255 ? 255 : (v < 0 ? 0 : v));
    lv_obj_set_style_opa(obj, opa, LV_PART_MAIN);

    /* 根据 scale_mode 选择 fade-out 的缩放方式 */
    lv_obj_t *parent = lv_obj_get_parent(obj);
    if (parent && lv_obj_is_valid(parent) && lv_obj_get_user_data(parent)) {
        rxroller_ctx_t *ctx = (rxroller_ctx_t *)lv_obj_get_user_data(parent);
        if (ctx->config.scale_mode == RXROLLER_SCALE_TRANSFORM) {
            lv_obj_set_style_transform_zoom(obj, (uint16_t)opa, LV_PART_MAIN);
        } else {
            if (ctx->config.icon_mode == RXROLLER_MODE_IMAGE) {
                lv_img_set_zoom(obj, (uint16_t)opa);
            } else {
                lv_obj_set_size(obj,
                    ctx->config.big_w * opa / 255,
                    ctx->config.big_h * opa / 255);
            }
        }
    }
}

static void rx_dismiss_ready_cb(lv_anim_t *a)
{
    if (!a) return;
    lv_obj_t *obj = (lv_obj_t *)a->var;
    rxroller_ctx_t *ctx = (rxroller_ctx_t *)a->user_data;

    if (obj && lv_obj_is_valid(obj)) {
        lv_obj_add_flag(obj, LV_OBJ_FLAG_HIDDEN);
    }

    if (ctx) {
        ctx->pending_anim_count--;
        SW_LOG_INFO("dismiss ready: remaining=%ld", (long)ctx->pending_anim_count);
        if (ctx->pending_anim_count <= 0) {
            ctx->is_confirmed = 1;
            SW_LOG_INFO("confirm selection done, center=%ld", (long)ctx->confirmed_index);
        }
    }
}

/* ==================== 恢复动画回调 ==================== */
static void rx_restore_exec_cb(void *var, int32_t v)
{
    lv_obj_t *obj = (lv_obj_t *)var;
    if (!obj || !lv_obj_is_valid(obj)) {
        SW_LOG_ERROR("restore exec: obj invalid");
        return;
    }
    lv_opa_t opa = (lv_opa_t)(v > 255 ? 255 : (v < 0 ? 0 : v));
    lv_obj_set_style_opa(obj, opa, LV_PART_MAIN);

    /* 根据 scale_mode 选择 restore 的缩放方式 */
    lv_obj_t *parent = lv_obj_get_parent(obj);
    if (parent && lv_obj_is_valid(parent) && lv_obj_get_user_data(parent)) {
        rxroller_ctx_t *ctx = (rxroller_ctx_t *)lv_obj_get_user_data(parent);
        if (ctx->config.scale_mode == RXROLLER_SCALE_TRANSFORM) {
            lv_obj_set_style_transform_zoom(obj, (uint16_t)opa, LV_PART_MAIN);
        } else {
            if (ctx->config.icon_mode == RXROLLER_MODE_IMAGE) {
                lv_img_set_zoom(obj, (uint16_t)opa);
            } else {
                lv_obj_set_size(obj,
                    ctx->config.big_w * opa / 255,
                    ctx->config.big_h * opa / 255);
            }
        }
    }
}

static void rx_restore_ready_cb(lv_anim_t *a)
{
    if (!a) return;
    lv_obj_t *obj = (lv_obj_t *)a->var;
    rxroller_ctx_t *ctx = (rxroller_ctx_t *)a->user_data;

    if (obj && lv_obj_is_valid(obj)) {
        lv_obj_clear_flag(obj, LV_OBJ_FLAG_HIDDEN);
        lv_obj_set_style_opa(obj, LV_OPA_COVER, LV_PART_MAIN);
    }

    if (ctx) {
        ctx->pending_anim_count--;
        SW_LOG_INFO("restore ready: remaining=%ld", (long)ctx->pending_anim_count);
        if (ctx->pending_anim_count <= 0) {
            ctx->is_confirmed = 0;
            ctx->confirmed_index = -1;
            SW_LOG_INFO("restore done");
        }
    }
}

static void rx_create_animation(lv_obj_t *obj, int32_t start, int32_t end,
                                uint32_t time, rxroller_ctx_t *ctx)
{
    if (!obj || !lv_obj_is_valid(obj)) {
        SW_LOG_ERROR("create_anim: obj invalid");
        return;
    }
    if (!ctx) {
        SW_LOG_ERROR("create_anim: ctx is NULL");
        return;
    }

    if (start == end) {
        lv_anim_del(obj, rx_anim_exec_cb);
        return;
    }

    ctx->pending_anim_count++;

    lv_anim_t anim;
    lv_anim_init(&anim);
    lv_anim_set_var(&anim, obj);
    lv_anim_set_exec_cb(&anim, rx_anim_exec_cb);
    lv_anim_set_values(&anim, start, end);
    lv_anim_set_time(&anim, time);
    lv_anim_set_path_cb(&anim, lv_anim_path_ease_out);
    lv_anim_set_ready_cb(&anim, rx_anim_ready_cb);
    lv_anim_set_user_data(&anim, ctx);
    lv_anim_start(&anim);
}

/* ==================== 触摸事件处理 ==================== */
static void rx_event_pressing(lv_event_t *e)
{
    lv_obj_t *target = lv_event_get_target(e);
    rxroller_ctx_t *ctx = (rxroller_ctx_t *)lv_event_get_user_data(e);

    if (!ctx) {
        SW_LOG_ERROR("pressing: ctx is NULL");
        return;
    }
    if (!ctx->screen || !lv_obj_is_valid(ctx->screen)) {
        SW_LOG_ERROR("pressing: screen invalid");
        return;
    }

    if (ctx->is_confirmed) {
        SW_LOG_INFO("pressing: wheel is confirmed, ignoring");
        return;
    }

    if (!ctx->touched) {
        for (int32_t i = 0; i < ctx->item_count; i++) {
            if (ctx->items[i].obj && lv_obj_is_valid(ctx->items[i].obj)) {
                lv_anim_del(ctx->items[i].obj, rx_anim_exec_cb);
                lv_anim_del(ctx->items[i].obj, rx_dismiss_exec_cb);
                lv_anim_del(ctx->items[i].obj, rx_restore_exec_cb);
            }
        }
        lv_indev_get_point(lv_indev_get_act(), &ctx->touch_point1);
        ctx->touched = 1;
        ctx->pending_anim_count = 0;
        ctx->offset = 0;
        ctx->drag_travel = 0;      /* RX-PORT-FIX: 新手势清零 */
        return;
    }

    lv_indev_get_point(lv_indev_get_act(), &ctx->touch_point2);

    if (ctx->config.arrange == RXROLLER_ARRANGE_HORIZONTAL) {
        ctx->offset = ctx->touch_point2.x - ctx->touch_point1.x;
        ctx->touch_point1.x = ctx->touch_point2.x;
    } else {
        ctx->offset = ctx->touch_point2.y - ctx->touch_point1.y;
        ctx->touch_point1.y = ctx->touch_point2.y;
    }
    ctx->drag_travel += LV_ABS(ctx->offset);   /* RX-PORT-FIX: 累计位移 */

    rx_set_center_internal(ctx, ctx->item_count, 0);
}

static void rx_event_released(lv_event_t *e)
{
    lv_obj_t *target = lv_event_get_target(e);
    rxroller_ctx_t *ctx = (rxroller_ctx_t *)lv_event_get_user_data(e);

    if (!ctx) {
        SW_LOG_ERROR("released: ctx is NULL");
        return;
    }
    if (!ctx->screen || !lv_obj_is_valid(ctx->screen)) {
        SW_LOG_ERROR("released: screen invalid");
        ctx->touched = 0;
        return;
    }

    if (ctx->is_confirmed) {
        ctx->touched = 0;
        ctx->offset = 0;
        SW_LOG_INFO("released: wheel is confirmed, ignoring");
        return;
    }

    /* 判断是否为点击 */
    /* RX-PORT-FIX: 原来用单拍 offset 判点击 ⇒ 松手前停一下就误判成点击，
     *   列表被动画切回松手那一行（现象=拖完自动回弹）。改按累计位移判。 */
    uint8_t is_click = (ctx->drag_travel <= RXROLLER_CLICK_TRAVEL_MAX
                        && ctx->pending_anim_count == 0 && target != ctx->screen);
    ctx->touched = 0;

    if (is_click) {
        int32_t click_id = lv_obj_get_index(target);
        if (click_id >= 0 && click_id < ctx->item_count) {
            int32_t cur_center = (int32_t)rxroller_get_center(ctx->screen);
            if (click_id != cur_center) {
                if (!ctx->config.circular) {
                    if (click_id < cur_center && cur_center <= 0) return;
                    if (click_id > cur_center && cur_center >= ctx->item_count - 1) return;
                }
                ctx->offset = 0;
                rx_set_center_internal(ctx, click_id, 1); /* 动画切换 */
                return;
            }
        }
        ctx->offset = 0;
        return;
    }

    /* 触摸滑动结束：计算最近中心 */
    int32_t best = (int32_t)rxroller_get_center(ctx->screen);
    rx_set_center_internal(ctx, best, 1);
    ctx->offset = 0;
}

/* ==================== 创建元素对象 ==================== */
static lv_obj_t *rx_create_item_obj(rxroller_ctx_t *ctx, int32_t index)
{
    if (!ctx) return NULL;

    lv_obj_t *obj = NULL;

    if (ctx->config.icon_mode == RXROLLER_MODE_IMAGE) {
        obj = lv_img_create(ctx->screen);
        if (!obj) return NULL;
        if (ctx->config.icon_path && ctx->config.icon_path[index]) {
            lv_img_set_src(obj, ctx->config.icon_path[index]);
        }
        lv_obj_set_size(obj, LV_SIZE_CONTENT, LV_SIZE_CONTENT);
    } else {
        obj = lv_obj_create(ctx->screen);
        if (!obj) return NULL;
        lv_obj_clear_flag(obj, LV_OBJ_FLAG_SCROLLABLE);
        lv_obj_set_style_bg_opa(obj, 0, LV_PART_MAIN);
        lv_obj_set_style_border_width(obj, 0, LV_PART_MAIN);
        lv_obj_set_style_clip_corner(obj, false, LV_PART_MAIN);
        lv_obj_set_size(obj, ctx->config.big_w, ctx->config.big_h);

        if (ctx->config.create_cb) {
            ctx->config.create_cb(obj, index, ctx->config.create_user_data);
        }
    }

    return obj;
}

static void rx_init_item(rxroller_ctx_t *ctx, int32_t index)
{
    if (!ctx || index < 0 || index >= ctx->item_count) return;

    rxroller_item_t *item = &ctx->items[index];

    if (!ctx->config.circular) {
        item->distance = index * (int32_t)ctx->config.icon_distance;
    } else {
        int32_t half = (ctx->item_count - 1) / 2;
        if (index <= half) {
            item->distance = index * (int32_t)ctx->config.icon_distance;
        } else {
            item->distance = -(ctx->item_count - index) * (int32_t)ctx->config.icon_distance;
        }
    }

    if (item->obj && lv_obj_is_valid(item->obj)) {
        if (ctx->config.icon_mode == RXROLLER_MODE_IMAGE) {
            lv_obj_set_size(item->obj, LV_SIZE_CONTENT, LV_SIZE_CONTENT);
        } else {
            lv_obj_set_size(item->obj, ctx->config.big_w, ctx->config.big_h);
        }
        lv_obj_center(item->obj);
        lv_obj_set_user_data(item->obj, item);
    }

    int32_t pos_x, pos_y;
    rx_calc_curve_pos(ctx, item->distance, &pos_x, &pos_y);
    if (item->obj && lv_obj_is_valid(item->obj)) {
        lv_obj_set_pos(item->obj, pos_x, pos_y);
    }

    if (item->obj && lv_obj_is_valid(item->obj)) {
        lv_obj_add_flag(item->obj, LV_OBJ_FLAG_CLICKABLE);
        lv_obj_add_event_cb(item->obj, rx_event_pressing, LV_EVENT_PRESSING, ctx);
        lv_obj_add_event_cb(item->obj, rx_event_released, LV_EVENT_RELEASED, ctx);
        /* 关闭所有子对象的 clip_corner，防止 LVGL 为每个 label 创建 draw layer */
        lv_obj_set_style_clip_corner(item->obj, false, LV_PART_MAIN);
        for (uint32_t _c = 0; _c < lv_obj_get_child_cnt(item->obj); _c++) {
            lv_obj_t *_ch = lv_obj_get_child(item->obj, _c);
            lv_obj_set_style_clip_corner(_ch, false, LV_PART_MAIN);
        }
    }
}

/* ==================== 设置中心位置（内部实现） ==================== */
static void rx_set_center_internal(rxroller_ctx_t *ctx, int32_t icon_id, uint8_t anim_en)
{
    if (!ctx) return;

    /* 无动画模式 */
    if (anim_en == 0) {
        int32_t center_id = rxroller_get_center(ctx->screen);
        int32_t t = 0;

        if (icon_id < ctx->item_count && icon_id >= 0) {
            for (t = 0; t <= ctx->item_count; t++) {
                if ((center_id + t) % ctx->item_count == icon_id) break;
            }
        }

        for (int32_t i = 0; i < ctx->item_count; i++) {
            if (icon_id < ctx->item_count && icon_id >= 0) {
                ctx->items[i].distance -= t * (int32_t)ctx->config.icon_distance;
            } else {
                ctx->items[i].distance += ctx->offset;
            }
            rx_normalize_distance(ctx, &ctx->items[i].distance);
            rx_clamp_distance(ctx, i, &ctx->items[i].distance);

            if (ctx->items[i].obj && lv_obj_is_valid(ctx->items[i].obj)) {
                int32_t px, py;
                rx_calc_curve_pos(ctx, ctx->items[i].distance, &px, &py);
                lv_obj_set_pos(ctx->items[i].obj, px, py);
            }
            rx_update_item_scale(ctx, &ctx->items[i]);
        }
        ctx->center_idx = (icon_id < ctx->item_count && icon_id >= 0)
                          ? icon_id : rxroller_get_center(ctx->screen);
        return;
    }

    /* 动画模式 */
    /* 无条件取消旧动画，使用 pending_anim_count 计数器代替 is_animating */
    if (ctx->pending_anim_count > 0) {
        SW_LOG_INFO("set_center: interrupting current animation");
    }
    for (int32_t i = 0; i < ctx->item_count; i++) {
        if (ctx->items[i].obj && lv_obj_is_valid(ctx->items[i].obj)) {
            lv_anim_del(ctx->items[i].obj, rx_anim_exec_cb);
            lv_anim_del(ctx->items[i].obj, rx_dismiss_exec_cb);
            lv_anim_del(ctx->items[i].obj, rx_restore_exec_cb);
        }
    }
    ctx->pending_anim_count = 0;

    /* 确定目标中心 */
    int32_t target_center;
    if (icon_id < ctx->item_count && icon_id >= 0) {
        target_center = icon_id;
    } else {
        /* 根据滑动偏移计算当前中心 */
        target_center = (int32_t)rxroller_get_center(ctx->screen);
    }

    for (int32_t i = 0; i < ctx->item_count; i++) {
        if (!ctx->items[i].obj || !lv_obj_is_valid(ctx->items[i].obj)) {
            SW_LOG_WARN("set_center: item[%ld] obj invalid, skip", (long)i);
            continue;
        }

        int32_t target = get_target_distance(ctx, i, target_center);
        int32_t start = ctx->items[i].distance;

        /* 循环模式下调整起始位置以走最短路径 */
        adjust_start_shortest(ctx, &start, target);

        /* 非循环模式下钳位距离，防止越界 */
        rx_clamp_distance(ctx, i, &target);
        rx_clamp_distance(ctx, i, &start);

        uint32_t anim_time = ctx->config.anim_time;
        if (ctx->offset != 0) {
            anim_time += (uint32_t)(LV_ABS(ctx->offset) * ctx->config.anim_time_factor);
        }

        rx_create_animation(ctx->items[i].obj, start, target, anim_time, ctx);
        ctx->items[i].distance = target; /* 立即更新存储的距离 */
    }

    ctx->center_idx = target_center;
    ctx->offset = 0;
}

/* ==================== LV_EVENT_DELETE 事件处理 ==================== */
static void rx_event_delete(lv_event_t *e)
{
    rxroller_ctx_t *ctx = (rxroller_ctx_t *)lv_event_get_user_data(e);
    if (!ctx) {
        SW_LOG_ERROR("delete event: ctx is NULL");
        return;
    }
    SW_LOG_INFO("LV_EVENT_DELETE triggered, cleaning up");

    rx_cleanup_internal(ctx, 0);
}

/* ==================== LV_EVENT_SCREEN_UNLOADED 事件处理 ==================== */
static void rx_event_screen_unload(lv_event_t *e)
{
    rxroller_ctx_t *ctx = (rxroller_ctx_t *)lv_event_get_user_data(e);
    if (!ctx) {
        SW_LOG_ERROR("screen_unload: ctx is NULL");
        return;
    }

    SW_LOG_INFO("screen unloading, stopping animations");

    for (int32_t i = 0; i < ctx->item_count; i++) {
        if (ctx->items[i].obj && lv_obj_is_valid(ctx->items[i].obj)) {
            lv_anim_del(ctx->items[i].obj, rx_anim_exec_cb);
            lv_anim_del(ctx->items[i].obj, rx_dismiss_exec_cb);
            lv_anim_del(ctx->items[i].obj, rx_restore_exec_cb);
        }
    }

    ctx->pending_anim_count = 0;
    ctx->touched = 0;
    ctx->screen = NULL;
}

/* ==================== 公共 API 实现 ==================== */

lv_obj_t *rxroller_create(lv_obj_t *parent, int32_t icon_max,
                              const rxroller_config_t *config)
{
    if (!parent || !lv_obj_is_valid(parent)) {
        SW_LOG_ERROR("create: parent invalid");
        return NULL;
    }
    if (icon_max <= 0 || icon_max > 255) {
        SW_LOG_ERROR("create: icon_max=%ld (1~255)", (long)icon_max);
        return NULL;
    }
    if (!config) {
        SW_LOG_ERROR("create: config is NULL");
        return NULL;
    }
    if (config->icon_distance <= 0) {
        SW_LOG_ERROR("create: icon_distance must > 0");
        return NULL;
    }
    if (config->icon_mode == RXROLLER_MODE_IMAGE && !config->icon_path) {
        SW_LOG_ERROR("create: image mode requires icon_path");
        return NULL;
    }
    if (config->icon_mode == RXROLLER_MODE_CONTAINER && !config->create_cb) {
        SW_LOG_WARN("create: container mode without create_cb, items will be empty");
    }
    if (config->edge_scale > 255) {
        SW_LOG_ERROR("create: edge_scale=%u > 255", config->edge_scale);
        return NULL;
    }

    rxroller_ctx_t *ctx = lv_mem_alloc(sizeof(rxroller_ctx_t));
    if (!ctx) {
        SW_LOG_ERROR("create: alloc ctx failed");
        return NULL;
    }
    lv_memset(ctx, 0, sizeof(rxroller_ctx_t));

    ctx->items = lv_mem_alloc(sizeof(rxroller_item_t) * icon_max);
    if (!ctx->items) {
        SW_LOG_ERROR("create: alloc items failed");
        lv_mem_free(ctx);
        return NULL;
    }
    lv_memset(ctx->items, 0, sizeof(rxroller_item_t) * icon_max);

    ctx->item_count = icon_max;
    lv_memcpy(&ctx->config, config, sizeof(rxroller_config_t));

    if (ctx->config.anim_time == 0) ctx->config.anim_time = 300;
    if (ctx->config.anim_time_factor == 0) ctx->config.anim_time_factor = 5;
    if (ctx->config.inertia_divisor <= 0) ctx->config.inertia_divisor = 20;
    if (ctx->config.big_w <= 0) ctx->config.big_w = 100;
    if (ctx->config.big_h <= 0) ctx->config.big_h = 100;
    if (ctx->config.edge_scale == 0) ctx->config.edge_scale = 128;
    if (ctx->config.curve_mode > 1) ctx->config.curve_mode = RXROLLER_CURVE_NONE;

    ctx->screen = lv_obj_create(parent);
    if (!ctx->screen) {
        SW_LOG_ERROR("create: screen obj failed");
        lv_mem_free(ctx->items);
        lv_mem_free(ctx);
        return NULL;
    }

    lv_obj_set_align(ctx->screen, LV_ALIGN_CENTER);
    lv_obj_set_style_bg_opa(ctx->screen, 0, LV_PART_MAIN);
    lv_obj_set_style_border_width(ctx->screen, 0, LV_PART_MAIN);
    lv_obj_set_style_clip_corner(ctx->screen, false, LV_PART_MAIN);
    lv_obj_clear_flag(ctx->screen, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_user_data(ctx->screen, ctx);

    lv_obj_add_event_cb(ctx->screen, rx_event_pressing, LV_EVENT_PRESSING, ctx);
    lv_obj_add_event_cb(ctx->screen, rx_event_released, LV_EVENT_RELEASED, ctx);
    lv_obj_add_event_cb(ctx->screen, rx_event_delete, LV_EVENT_DELETE, ctx);
    lv_obj_add_event_cb(ctx->screen, rx_event_screen_unload, LV_EVENT_SCREEN_UNLOADED, ctx);

    for (int32_t i = 0; i < icon_max; i++) {
        ctx->items[i].obj = rx_create_item_obj(ctx, i);
        if (!ctx->items[i].obj) {
            SW_LOG_ERROR("create: item[%ld] failed", (long)i);
            rx_cleanup_internal(ctx, 1);
            return NULL;
        }
        rx_init_item(ctx, i);
    }

    if (icon_max <= 1) {
        lv_obj_clear_flag(ctx->screen, LV_OBJ_FLAG_CLICKABLE);
    }

    rx_set_center_internal(ctx, 0, 0);

    SW_LOG_INFO("created: items=%ld mode=%u arrange=%u",
                (long)icon_max, ctx->config.icon_mode, ctx->config.arrange);
    return ctx->screen;
}

void rxroller_delete(lv_obj_t *wheel)
{
    rxroller_ctx_t *ctx = rx_get_ctx(wheel);
    if (!ctx) {
        SW_LOG_ERROR("delete: invalid wheel");
        return;
    }
    SW_LOG_INFO("manual delete requested");
    rx_cleanup_internal(ctx, 1);
}

void rxroller_set_center(lv_obj_t *wheel, int32_t index, uint8_t anim_en)
{
    rxroller_ctx_t *ctx = rx_get_ctx(wheel);
    if (!ctx) return;
    if (ctx->is_confirmed) {
        SW_LOG_WARN("set_center: wheel is confirmed, ignoring");
        return;
    }
    if (index < 0 || index >= ctx->item_count) {
        SW_LOG_ERROR("set_center: index=%ld OOB [0,%ld)", (long)index, (long)ctx->item_count);
        return;
    }
    ctx->offset = 0;
    rx_set_center_internal(ctx, index, anim_en);
}

void rxroller_set_center_manual(lv_obj_t *ui_obj, int32_t icon_id, uint8_t anim_en)
{
    rxroller_ctx_t *ctx = rx_get_ctx(ui_obj);
    if (!ctx) return;
    if (ctx->pending_anim_count > 0) return;
    if (ctx->is_confirmed) {
        SW_LOG_WARN("set_center_manual: wheel is confirmed, ignoring");
        return;
    }
    ctx->offset = 0;
    rx_set_center_internal(ctx, icon_id, anim_en);
}

void rxroller_switch_next(lv_obj_t *wheel)
{
    rxroller_ctx_t *ctx = rx_get_ctx(wheel);
    if (!ctx) return;
    int32_t c = rxroller_get_center(wheel);
    if (c < 0) return;
    if (!ctx->config.circular && c >= ctx->item_count - 1) {
        SW_LOG_INFO("switch_next: hit right bound (center=%ld)", (long)c);
        return;
    }
    int32_t next = ctx->config.circular ? ((c + 1) % ctx->item_count) : (c + 1);
    rxroller_set_center(wheel, next, 1);
}

void rxroller_switch_prev(lv_obj_t *wheel)
{
    rxroller_ctx_t *ctx = rx_get_ctx(wheel);
    if (!ctx) return;
    int32_t c = rxroller_get_center(wheel);
    if (c < 0) return;
    if (!ctx->config.circular && c <= 0) {
        SW_LOG_INFO("switch_prev: hit left bound (center=%ld)", (long)c);
        return;
    }
    int32_t prev = ctx->config.circular
                   ? ((c == 0) ? (ctx->item_count - 1) : (c - 1))
                   : (c - 1);
    rxroller_set_center(wheel, prev, 2);
}

void rxroller_scroll(lv_obj_t *wheel, int32_t distance)
{
    rxroller_ctx_t *ctx = rx_get_ctx(wheel);
    if (!ctx) return;
    ctx->offset = distance;
    rx_set_center_internal(ctx, ctx->item_count, 1);
}

uint32_t rxroller_get_center(lv_obj_t *wheel)
{
    rxroller_ctx_t *ctx = rx_get_ctx(wheel);
    if (!ctx) return 0;

    int32_t min_d = INT32_MAX;
    int32_t best = 0;
    int32_t dir = ctx->offset;

    for (int32_t i = 0; i < ctx->item_count; i++) {
        int32_t d = LV_ABS(ctx->items[i].distance);
        if (d < min_d) {
            min_d = d;
            best = i;
        } else if (d == min_d) {
            if ((dir > 0 && i > best) || (dir < 0 && i < best)) {
                best = i;
            }
        }
    }
    ctx->center_idx = best;
    return (uint32_t)best;
}

uint8_t rxroller_is_touched(lv_obj_t *wheel)
{
    rxroller_ctx_t *ctx = rx_get_ctx(wheel);
    if (!ctx) return 0;
    return ctx->touched;
}

uint8_t rxroller_get_touch_state(lv_obj_t *ui_obj)
{
    return rxroller_is_touched(ui_obj);
}

uint8_t rxroller_is_animating(lv_obj_t *wheel)
{
    rxroller_ctx_t *ctx = rx_get_ctx(wheel);
    if (!ctx) return 0;
    return (ctx->pending_anim_count > 0) ? 1 : 0;
}

int32_t rxroller_get_count(lv_obj_t *wheel)
{
    rxroller_ctx_t *ctx = rx_get_ctx(wheel);
    if (!ctx) return 0;
    return ctx->item_count;
}

/* ==================== 确认选择 API ==================== */

int32_t rxroller_confirm_selection(lv_obj_t *wheel, uint32_t anim_time)
{
    rxroller_ctx_t *ctx = rx_get_ctx(wheel);
    if (!ctx) return -1;

    if (ctx->is_confirmed || ctx->pending_anim_count > 0) {
        SW_LOG_INFO("confirm_selection: already confirmed or in progress (confirmed=%u pending=%ld)",
                    ctx->is_confirmed, (long)ctx->pending_anim_count);
        return ctx->confirmed_index;
    }

    if (ctx->item_count <= 1) {
        ctx->is_confirmed = 1;
        ctx->confirmed_index = 0;
        ctx->pending_anim_count = 0;
        SW_LOG_INFO("confirm_selection: single item, index=0");
        return 0;
    }

    int32_t center = (int32_t)rxroller_get_center(wheel);
    if (center < 0) {
        SW_LOG_ERROR("confirm_selection: failed to get center");
        return -1;
    }

    for (int32_t i = 0; i < ctx->item_count; i++) {
        if (ctx->items[i].obj && lv_obj_is_valid(ctx->items[i].obj)) {
            lv_anim_del(ctx->items[i].obj, rx_anim_exec_cb);
        }
    }
    ctx->pending_anim_count = 0;

    ctx->confirmed_index = center;
    ctx->pending_anim_count = 0;

    SW_LOG_INFO("confirm_selection: center=%ld, anim_time=%lu ms", (long)center, (unsigned long)anim_time);

    for (int32_t i = 0; i < ctx->item_count; i++) {
        if (i == center) continue;

        lv_obj_t *obj = ctx->items[i].obj;
        if (!obj || !lv_obj_is_valid(obj)) {
            SW_LOG_WARN("confirm_selection: item[%ld] obj invalid, skip", (long)i);
            continue;
        }

        if (ctx->config.scale_mode == RXROLLER_SCALE_TRANSFORM) {
            if (ctx->config.icon_mode == RXROLLER_MODE_IMAGE) {
                lv_obj_update_layout(obj);
                lv_obj_set_style_transform_pivot_x(obj, lv_obj_get_width(obj) / 2, LV_PART_MAIN);
                lv_obj_set_style_transform_pivot_y(obj, lv_obj_get_height(obj) / 2, LV_PART_MAIN);
            } else {
                lv_obj_set_style_transform_pivot_x(obj, ctx->config.big_w / 2, LV_PART_MAIN);
                lv_obj_set_style_transform_pivot_y(obj, ctx->config.big_h / 2, LV_PART_MAIN);
            }
        }

        if (anim_time == 0) {
            lv_obj_add_flag(obj, LV_OBJ_FLAG_HIDDEN);
            lv_obj_set_style_opa(obj, LV_OPA_TRANSP, LV_PART_MAIN);
        } else {
            lv_anim_t a;
            lv_anim_init(&a);
            lv_anim_set_var(&a, obj);
            lv_anim_set_exec_cb(&a, rx_dismiss_exec_cb);
            lv_anim_set_values(&a, 255, 0);
            lv_anim_set_time(&a, anim_time);
            lv_anim_set_path_cb(&a, lv_anim_path_ease_in);
            lv_anim_set_ready_cb(&a, rx_dismiss_ready_cb);
            lv_anim_set_user_data(&a, ctx);
            lv_anim_start(&a);
            ctx->pending_anim_count++;
        }
    }

    if (ctx->pending_anim_count == 0) {
        ctx->is_confirmed = 1;
        SW_LOG_INFO("confirm_selection: instant (no animations), index=%ld", (long)center);
    }

    return center;
}

void rxroller_cancel_selection(lv_obj_t *wheel, uint32_t anim_time)
{
    rxroller_ctx_t *ctx = rx_get_ctx(wheel);
    if (!ctx) return;

    if (!ctx->is_confirmed) {
        SW_LOG_INFO("cancel_selection: not confirmed, nothing to cancel");
        return;
    }

    for (int32_t i = 0; i < ctx->item_count; i++) {
        if (ctx->items[i].obj && lv_obj_is_valid(ctx->items[i].obj)) {
            lv_anim_del(ctx->items[i].obj, rx_dismiss_exec_cb);
            lv_anim_del(ctx->items[i].obj, rx_restore_exec_cb);
        }
    }

    ctx->pending_anim_count = 0;

    SW_LOG_INFO("cancel_selection: anim_time=%lu ms", (unsigned long)anim_time);

    for (int32_t i = 0; i < ctx->item_count; i++) {
        if (i == ctx->confirmed_index) continue;

        lv_obj_t *obj = ctx->items[i].obj;
        if (!obj || !lv_obj_is_valid(obj)) {
            SW_LOG_WARN("cancel_selection: item[%ld] obj invalid, skip", (long)i);
            continue;
        }

        if (ctx->config.scale_mode == RXROLLER_SCALE_TRANSFORM) {
            if (ctx->config.icon_mode == RXROLLER_MODE_IMAGE) {
                lv_obj_update_layout(obj);
                lv_obj_set_style_transform_pivot_x(obj, lv_obj_get_width(obj) / 2, LV_PART_MAIN);
                lv_obj_set_style_transform_pivot_y(obj, lv_obj_get_height(obj) / 2, LV_PART_MAIN);
            } else {
                lv_obj_set_style_transform_pivot_x(obj, ctx->config.big_w / 2, LV_PART_MAIN);
                lv_obj_set_style_transform_pivot_y(obj, ctx->config.big_h / 2, LV_PART_MAIN);
            }
        }

        lv_obj_clear_flag(obj, LV_OBJ_FLAG_HIDDEN);

        if (anim_time == 0) {
            lv_obj_set_style_opa(obj, LV_OPA_COVER, LV_PART_MAIN);
            if (ctx->config.scale_mode == RXROLLER_SCALE_TRANSFORM) {
                lv_obj_set_style_transform_zoom(obj, 256, LV_PART_MAIN);
            }
        } else {
            lv_anim_t a;
            lv_anim_init(&a);
            lv_anim_set_var(&a, obj);
            lv_anim_set_exec_cb(&a, rx_restore_exec_cb);
            lv_anim_set_values(&a, 0, 255);
            lv_anim_set_time(&a, anim_time);
            lv_anim_set_path_cb(&a, lv_anim_path_ease_out);
            lv_anim_set_ready_cb(&a, rx_restore_ready_cb);
            lv_anim_set_user_data(&a, ctx);
            lv_anim_start(&a);
            ctx->pending_anim_count++;
        }
    }

    if (ctx->pending_anim_count == 0) {
        ctx->is_confirmed = 0;
        ctx->confirmed_index = -1;
        SW_LOG_INFO("cancel_selection: instant restore");
    }
}

uint8_t rxroller_is_confirmed(lv_obj_t *wheel)
{
    rxroller_ctx_t *ctx = rx_get_ctx(wheel);
    if (!ctx) return 0;
    return ctx->is_confirmed;
}

int32_t rxroller_get_confirmed_index(lv_obj_t *wheel)
{
    rxroller_ctx_t *ctx = rx_get_ctx(wheel);
    if (!ctx) return -1;
    if (!ctx->is_confirmed) return -1;
    return ctx->confirmed_index;
}

/* ==================== 数据接口 ==================== */

rxroller_item_t *rxroller_get_icons(lv_obj_t *wheel)
{
    rxroller_ctx_t *ctx = rx_get_ctx(wheel);
    if (!ctx) return NULL;
    return ctx->items;
}

const rxroller_item_t *rxroller_get_center_item(lv_obj_t *wheel)
{
    rxroller_ctx_t *ctx = rx_get_ctx(wheel);
    if (!ctx) return NULL;
    int32_t c = (int32_t)rxroller_get_center(wheel);
    if (c < 0 || c >= ctx->item_count) return NULL;
    return &ctx->items[c];
}

lv_obj_t *rxroller_get_item_obj(lv_obj_t *wheel, int32_t index)
{
    rxroller_ctx_t *ctx = rx_get_ctx(wheel);
    if (!ctx) return NULL;
    if (index < 0 || index >= ctx->item_count) return NULL;
    if (!ctx->items[index].obj || !lv_obj_is_valid(ctx->items[index].obj)) return NULL;
    return ctx->items[index].obj;
}

void rxroller_set_item_user_data(lv_obj_t *wheel, int32_t index, void *data)
{
    rxroller_ctx_t *ctx = rx_get_ctx(wheel);
    if (!ctx) return;
    if (index < 0 || index >= ctx->item_count) return;
    ctx->items[index].user_data = data;
}

void *rxroller_get_item_user_data(lv_obj_t *wheel, int32_t index)
{
    rxroller_ctx_t *ctx = rx_get_ctx(wheel);
    if (!ctx) return NULL;
    if (index < 0 || index >= ctx->item_count) return NULL;
    return ctx->items[index].user_data;
}

void rxroller_set_user_data(lv_obj_t *wheel, void *data)
{
    rxroller_ctx_t *ctx = rx_get_ctx(wheel);
    if (!ctx) return;
    ctx->user_data = data;
}

void *rxroller_get_user_data(lv_obj_t *wheel)
{
    rxroller_ctx_t *ctx = rx_get_ctx(wheel);
    if (!ctx) return NULL;
    return ctx->user_data;
}

/* ==================== 旧的中心项选择 ==================== */

void rxroller_switch_center(lv_obj_t *ui_obj, int32_t direction)
{
    if (direction > 0) {
        rxroller_switch_next(ui_obj);
    } else {
        rxroller_switch_prev(ui_obj);
    }
}