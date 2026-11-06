/* ui_behavior.c — 本地交互行为（⑦）
 *
 * 只接不需要硬件的 UI 行为：
 *   - 主控 4 个场景按钮：切换选中态
 *   - 窗帘详情 全开/半开/全关：设置滑条（读数由 value_bind 更新）
 *   - 空调详情 温度 −/＋、模式、风速：更新读数和选中态
 */
#include "lvgl.h"
#include "screens.h"
#include "ui_behavior.h"

#define COLOR_ACCENT 0xF2B45C
#define COLOR_CARD2  0x1C2430
#define COLOR_BG     0x05080F
#define COLOR_T1     0xF4F7FB

typedef enum {
    ACT_SCENE,
    ACT_CURTAIN,
    ACT_AC_TEMP,
    ACT_AC_MODE,
    ACT_AC_FAN
} act_type_t;

typedef struct {
    act_type_t type;
    int value;
    lv_obj_t **btn;
    lv_obj_t **lb;
} action_t;

static int g_scene = 0;
static int g_ac_temp = 235;      /* 23.5°C，单位 0.1°C */
static int g_ac_mode = 0;        /* 0 制冷 / 1 制热 / 2 送风 */
static int g_fan = 1;            /* 0 低 / 1 中 / 2 高 */

static const action_t ACTIONS[] = {
    { ACT_SCENE,    0, &objects.main_hw01, &objects.main_hw01_lb },
    { ACT_SCENE,    1, &objects.main_hw02, &objects.main_hw02_lb },
    { ACT_SCENE,    2, &objects.main_hw03, &objects.main_hw03_lb },
    { ACT_SCENE,    3, &objects.main_hw04, &objects.main_hw04_lb },

    { ACT_CURTAIN, 100, &objects.detail_curtain_hw02, &objects.detail_curtain_hw02_lb },
    { ACT_CURTAIN,  50, &objects.detail_curtain_hw03, &objects.detail_curtain_hw03_lb },
    { ACT_CURTAIN,   0, &objects.detail_curtain_hw04, &objects.detail_curtain_hw04_lb },

    { ACT_AC_TEMP,  -1, &objects.detail_ac_hw01, &objects.detail_ac_hw01_lb },
    { ACT_AC_TEMP,   1, &objects.detail_ac_hw02, &objects.detail_ac_hw02_lb },
    { ACT_AC_MODE,   0, &objects.detail_ac_hw03, &objects.detail_ac_hw03_lb },
    { ACT_AC_MODE,   1, &objects.detail_ac_hw04, &objects.detail_ac_hw04_lb },
    { ACT_AC_MODE,   2, &objects.detail_ac_hw05, &objects.detail_ac_hw05_lb },
    { ACT_AC_FAN,    0, &objects.detail_ac_hw06, &objects.detail_ac_hw06_lb },
    { ACT_AC_FAN,    1, &objects.detail_ac_hw07, &objects.detail_ac_hw07_lb },
    { ACT_AC_FAN,    2, &objects.detail_ac_hw08, &objects.detail_ac_hw08_lb },
};

#define ACTIONS_COUNT ((int)(sizeof(ACTIONS) / sizeof(ACTIONS[0])))

static void set_active(lv_obj_t *btn, lv_obj_t *lb, int active)
{
    if (!btn) return;
    lv_obj_set_style_bg_color(btn, lv_color_hex(active ? COLOR_ACCENT : COLOR_CARD2),
                              LV_PART_MAIN | LV_STATE_DEFAULT);
    if (lb)
        lv_obj_set_style_text_color(lb, lv_color_hex(active ? COLOR_BG : COLOR_T1),
                                    LV_PART_MAIN | LV_STATE_DEFAULT);
}

static void sync_scene(void)
{
    set_active(objects.main_hw01, objects.main_hw01_lb, g_scene == 0);
    set_active(objects.main_hw02, objects.main_hw02_lb, g_scene == 1);
    set_active(objects.main_hw03, objects.main_hw03_lb, g_scene == 2);
    set_active(objects.main_hw04, objects.main_hw04_lb, g_scene == 3);
}

static void sync_ac_mode(void)
{
    set_active(objects.detail_ac_hw03, objects.detail_ac_hw03_lb, g_ac_mode == 0);
    set_active(objects.detail_ac_hw04, objects.detail_ac_hw04_lb, g_ac_mode == 1);
    set_active(objects.detail_ac_hw05, objects.detail_ac_hw05_lb, g_ac_mode == 2);
}

static void sync_fan(void)
{
    set_active(objects.detail_ac_hw06, objects.detail_ac_hw06_lb, g_fan == 0);
    set_active(objects.detail_ac_hw07, objects.detail_ac_hw07_lb, g_fan == 1);
    set_active(objects.detail_ac_hw08, objects.detail_ac_hw08_lb, g_fan == 2);
}

static void update_ac_header(void)
{
    static const char *modes[] = { "制冷", "制热", "送风" };
    if (objects.detail_ac_hr01)
        lv_label_set_text_fmt(objects.detail_ac_hr01, "客厅 · %s中 · %d.%d°C",
                              modes[g_ac_mode], g_ac_temp / 10, g_ac_temp % 10);
    if (objects.detail_ac_hr02)
        lv_label_set_text_fmt(objects.detail_ac_hr02, "%d.%d°",
                              g_ac_temp / 10, g_ac_temp % 10);
}

static void action_cb(lv_event_t *e)
{
    const action_t *a = (const action_t *)lv_event_get_user_data(e);
    if (!a) return;
    switch (a->type) {
    case ACT_SCENE:
        g_scene = a->value;
        sync_scene();
        break;
    case ACT_CURTAIN:
        if (objects.detail_curtain_hw01_sl) {
            lv_slider_set_value(objects.detail_curtain_hw01_sl, a->value, LV_ANIM_OFF);
            /* 程序赋值不会自动发 VALUE_CHANGED；补发一次，value_bind 才会刷新读数 */
            lv_obj_send_event(objects.detail_curtain_hw01_sl,
                              LV_EVENT_VALUE_CHANGED, NULL);
        }
        break;
    case ACT_AC_TEMP:
        g_ac_temp += a->value * 5;
        if (g_ac_temp < 160) g_ac_temp = 160;
        if (g_ac_temp > 300) g_ac_temp = 300;
        update_ac_header();
        break;
    case ACT_AC_MODE:
        g_ac_mode = a->value;
        sync_ac_mode();
        update_ac_header();
        break;
    case ACT_AC_FAN:
        g_fan = a->value;
        sync_fan();
        break;
    }
}

void ui_behavior_init(void)
{
    int i;
    for (i = 0; i < ACTIONS_COUNT; i++) {
        if (ACTIONS[i].btn && *ACTIONS[i].btn)
            lv_obj_add_event_cb(*ACTIONS[i].btn, action_cb,
                                LV_EVENT_CLICKED, (void *)&ACTIONS[i]);
    }
    sync_scene();
    sync_ac_mode();
    sync_fan();
    update_ac_header();
}

int ui_behavior_scene(void) { return g_scene; }
int ui_behavior_ac_temp(void) { return g_ac_temp; }
int ui_behavior_ac_mode(void) { return g_ac_mode; }
int ui_behavior_fan(void) { return g_fan; }
