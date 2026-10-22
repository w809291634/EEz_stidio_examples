#ifndef RXROLLER_H
#define RXROLLER_H

#include "lvgl.h"
#include "stdint.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ==================== 调试开关 ==================== */
#ifndef SW_DEBUG_ENABLE
#define SW_DEBUG_ENABLE 0
#endif

#if SW_DEBUG_ENABLE
#define SW_LOG_ERROR(fmt, ...) printf("[SW:ERROR] %s:%d " fmt "\n", __func__, __LINE__, ##__VA_ARGS__)
#define SW_LOG_WARN(fmt, ...)  printf("[SW:WARN]  %s:%d " fmt "\n", __func__, __LINE__, ##__VA_ARGS__)
#define SW_LOG_INFO(fmt, ...)  printf("[SW:INFO]  %s:%d " fmt "\n", __func__, __LINE__, ##__VA_ARGS__)
#else
#define SW_LOG_ERROR(fmt, ...) ((void)0)
#define SW_LOG_WARN(fmt, ...)  ((void)0)
#define SW_LOG_INFO(fmt, ...)  ((void)0)
#endif

/* ==================== 模式枚举 ==================== */
#define RXROLLER_MODE_CONTAINER  0
#define RXROLLER_MODE_IMAGE      1

/* ==================== 排列方向 ==================== */
#define RXROLLER_ARRANGE_HORIZONTAL  0
#define RXROLLER_ARRANGE_VERTICAL    1

/* ==================== 缩放模式 ==================== */
#define RXROLLER_SCALE_SIZE      0
#define RXROLLER_SCALE_TRANSFORM 1

/* ==================== 曲线模式 ==================== */
#define RXROLLER_CURVE_NONE   0
#define RXROLLER_CURVE_ARC    1

/* ==================== 前向声明 ==================== */
typedef struct rxroller_item_t rxroller_item_t;

/* ==================== 容器模式元素创建回调 ==================== */
typedef void (*rxroller_item_create_cb_t)(lv_obj_t *container, int32_t index, void *user_data);

/* ==================== 滚动元素结构体 ==================== */
struct rxroller_item_t {
    lv_obj_t *obj;
    lv_obj_t *label_obj;
    int32_t   distance;
    uint16_t  scale;
    void     *user_data;
};

/* ==================== 配置结构体 ==================== */
typedef struct {
    uint32_t icon_distance;
    uint32_t big_w;
    uint32_t big_h;
    uint16_t edge_scale;
    uint8_t  arrange;
    uint8_t  curve_mode;
    int32_t  curve_radius;
    uint8_t  curve_reverse;
    uint32_t anim_time;
    uint8_t  icon_mode;
    const void **icon_path;
    const char **text_array;
    const lv_font_t *normal_font;
    lv_color_t text_color;
    uint8_t  scale_mode;

    uint32_t anim_time_factor;
    rxroller_item_create_cb_t create_cb;
    void *create_user_data;
    int32_t  inertia_divisor;
    uint8_t  circular;
} rxroller_config_t;

/* ==================== 创建 & 销毁 ==================== */
lv_obj_t *rxroller_create(lv_obj_t *parent, int32_t icon_max,
                              const rxroller_config_t *config);
void rxroller_delete(lv_obj_t *wheel);

/* ==================== 控制接口 ==================== */
void rxroller_set_center(lv_obj_t *wheel, int32_t index, uint8_t anim_en);
void rxroller_set_center_manual(lv_obj_t *ui_obj, int32_t icon_id, uint8_t anim_en);
void rxroller_switch_next(lv_obj_t *wheel);
void rxroller_switch_prev(lv_obj_t *wheel);
void rxroller_scroll(lv_obj_t *wheel, int32_t distance);

/* ==================== 查询接口 ==================== */
uint32_t rxroller_get_center(lv_obj_t *wheel);
uint8_t  rxroller_is_touched(lv_obj_t *wheel);
uint8_t  rxroller_get_touch_state(lv_obj_t *ui_obj);
uint8_t  rxroller_is_animating(lv_obj_t *wheel);
int32_t  rxroller_get_count(lv_obj_t *wheel);

/* ==================== 确认选择 API ==================== */
int32_t rxroller_confirm_selection(lv_obj_t *wheel, uint32_t anim_time);
void rxroller_cancel_selection(lv_obj_t *wheel, uint32_t anim_time);
uint8_t rxroller_is_confirmed(lv_obj_t *wheel);
int32_t rxroller_get_confirmed_index(lv_obj_t *wheel);

/* ==================== 数据接口 ==================== */
rxroller_item_t *rxroller_get_icons(lv_obj_t *wheel);
const rxroller_item_t *rxroller_get_center_item(lv_obj_t *wheel);
lv_obj_t *rxroller_get_item_obj(lv_obj_t *wheel, int32_t index);
void  rxroller_set_item_user_data(lv_obj_t *wheel, int32_t index, void *data);
void *rxroller_get_item_user_data(lv_obj_t *wheel, int32_t index);
void  rxroller_set_user_data(lv_obj_t *wheel, void *data);
void *rxroller_get_user_data(lv_obj_t *wheel);

/* ==================== 兼容旧API ==================== */
void rxroller_switch_center(lv_obj_t *ui_obj, int32_t direction);

#ifdef __cplusplus
}
#endif

#endif