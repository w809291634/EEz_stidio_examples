/* value_bind.c — 滑条值与界面读数标签联动（in_read）
 *
 * 只接“UI 自己控制”的数值：亮度百分比、窗帘开合、自动锁屏秒数。
 * 色温等需要值域映射的暂不接，留⑦逐个补。
 */
#include "lvgl.h"
#include "screens.h"
#include "value_bind.h"

typedef struct {
    lv_obj_t **slider;
    lv_obj_t **label;
    const char *fmt;
} value_bind_t;

static const value_bind_t BINDS[] = {
    { &objects.living_hw03_sl,          &objects.living_r01,          "开合 %d%%" },
    { &objects.master_hw03_sl,          &objects.master_r01,          "开合 %d%%" },
    { &objects.detail_curtain_hw01_sl,  &objects.detail_curtain_r01,  "客厅 · 南向 · 开合 %d%%" },
    { &objects.detail_curtain_hw01_sl,  &objects.detail_curtain_r02,  "%d%%" },
    { &objects.detail_light_hw02_sl,    &objects.detail_light_r01,    "%d%%" },
    { &objects.settings_w03_sl,         &objects.settings_r01,        "无操作后 %d 秒" },
};

#define VALUE_BIND_COUNT ((int)(sizeof(BINDS) / sizeof(BINDS[0])))

static void apply(const value_bind_t *b)
{
    int v;
    if (!b || !b->slider || !*b->slider || !b->label || !*b->label) return;
    v = lv_slider_get_value(*b->slider);
    lv_label_set_text_fmt(*b->label, b->fmt, v);
}

static void value_changed(lv_event_t *e)
{
    apply((const value_bind_t *)lv_event_get_user_data(e));
}

void value_bind_init(void)
{
    int i;
    for (i = 0; i < VALUE_BIND_COUNT; i++) {
        if (BINDS[i].slider && *BINDS[i].slider) {
            lv_obj_add_event_cb(*BINDS[i].slider, value_changed,
                                LV_EVENT_VALUE_CHANGED, (void *)&BINDS[i]);
        }
    }
}

