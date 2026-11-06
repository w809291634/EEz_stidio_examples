/* value_bind.c — 滑条值与界面读数标签联动（in_read）
 *
 * 接“UI 自己控制”的数值：亮度百分比、窗帘开合、色温、自动锁屏秒数。
 * 初始化即按控件实际值刷新一次，避免"滑条在这里、读数还是设计稿文字"。
 */
#include "lvgl.h"
#include "screens.h"
#include "value_bind.h"

typedef struct {
    lv_obj_t **slider;
    lv_obj_t **label;
    const char *fmt;
    int (*map)(int);
} value_bind_t;

int value_bind_cct(int v)          /* 45%（设计稿位置）=3000K，100%=6500K */
{
    int k = (v <= 45) ? 3000 : 3000 + (v - 45) * 64;
    return (k / 50) * 50;
}

static const value_bind_t BINDS[] = {
    { &objects.living_hw03_sl,          &objects.living_r01,          "开合 %d%%", NULL },
    { &objects.master_hw03_sl,          &objects.master_r02,          "开合 %d%%", NULL },
    { &objects.detail_curtain_hw01_sl,  &objects.detail_curtain_r01,  "客厅 · 南向 · 开合 %d%%", NULL },
    { &objects.detail_curtain_hw01_sl,  &objects.detail_curtain_r02,  "%d%%", NULL },
    { &objects.detail_light_hw02_sl,    &objects.detail_light_r01,    "%d%%", NULL },
    { &objects.detail_light_hw03_sl,    &objects.detail_light_r02,    "%dK", value_bind_cct },
    { &objects.settings_w03_sl,         &objects.settings_r01,        "无操作后 %d 秒", NULL },
};

#define VALUE_BIND_COUNT ((int)(sizeof(BINDS) / sizeof(BINDS[0])))

static void apply(const value_bind_t *b)
{
    int v;
    if (!b || !b->slider || !*b->slider || !b->label || !*b->label) return;
    v = lv_slider_get_value(*b->slider);
    if (b->map) v = b->map(v);
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
        apply(&BINDS[i]);            /* 初始值也要对上，别留设计稿文字 */
    }
}

