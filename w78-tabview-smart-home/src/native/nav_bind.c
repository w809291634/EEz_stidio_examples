/*
 * nav_bind.c — no-flow 工程的导航接线（native 层）
 *
 * 数据来自 src/native/nav_bind_table.h（design/nav_bind_gen.py 生成）：
 * 每条 = 控件对象 + 源屏 + 目标屏（或"返回来路"）。EEZ 工程里不放 action，
 * 点击回调在这里统一挂，避免 23 屏 × 69 条边散落手写。
 */
#include "lvgl.h"
#include "screens.h"
#include "ui.h"
#include "nav_bind.h"
#include "nav_bind_table.h"

static int s_cur = SCREEN_ID_MAIN;
static int s_hist[64];
static int s_hist_n = 0;

lv_obj_t *nav_screen_obj(int id)
{
    switch (id) {
#define NAV_CASE(sid, field) case sid: return objects.field;
        NAV_PAGE_LIST(NAV_CASE)
#undef NAV_CASE
    default:
        return NULL;
    }
}

static void nav_click(lv_event_t *e)
{
    const nav_bind_entry_t *b = (const nav_bind_entry_t *)lv_event_get_user_data(e);
    int dst;
    if (!b) return;
    if (b->back) {
        if (s_hist_n <= 0) return;
        dst = s_hist[--s_hist_n];
    } else {
        if (s_hist_n < (int)(sizeof(s_hist) / sizeof(s_hist[0]))) {
            s_hist[s_hist_n++] = s_cur;
        }
        dst = b->dst;
    }
    loadScreen((enum ScreensEnum)dst);
    s_cur = dst;
}

void nav_bind_init(void)
{
    int i;
    s_cur = SCREEN_ID_MAIN;
    s_hist_n = 0;
    for (i = 0; i < NAV_BIND_COUNT; i++) {
        lv_obj_t *obj = *NAV_BIND[i].obj;
        if (obj) {
            lv_obj_add_event_cb(obj, nav_click, LV_EVENT_CLICKED, (void *)&NAV_BIND[i]);
        }
    }
}

int nav_bind_current(void)
{
    return s_cur;
}

void nav_bind_goto(int id)
{
    lv_obj_t *scr;
    if (id <= 0) return;
    /* 状态机跳转必须立即生效：EEZ 的 loadScreen() 带 200ms 淡入，
     * 连着跳两次时第二次会被动画吃掉（实测停在连接中页）。 */
    scr = nav_screen_obj(id);
    if (scr) lv_screen_load(scr);
    s_cur = id;
}

void nav_bind_seed(int cur, int back)
{
    s_cur = cur;
    s_hist_n = 0;
    if (back) {
        s_hist[s_hist_n++] = back;
    }
}
