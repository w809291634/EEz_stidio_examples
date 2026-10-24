/* watch_nav.cpp —— 第⑤步导航接线层（no flow：跳转全在 native，EEZ 只出控件）
 *
 * 口径（2026-10-22 用户定）：本层只保证"整体跳转+切换+每屏可达可回"，
 * 页面内细节功能（测量/播控/计时逻辑…）留第⑦步逐条立项。
 *
 * 跳转表与 designer/控件清单表.md 同源（改跳转先改清单表再改这里）：
 *   tab_main(tabview)：tab0=表盘 tab1=applist，左右滑=tabview 原生
 *   applist 滚轮行(本层建) → 14 个 app_* 页
 *   app_* 页 back → tab_main 且切到 applist tab
 *   app_alarm.al_add → alarm_editor；alarm_editor.back/ae_save → app_alarm
 *   app_settings 6 行点击区(本层盖) → set_* 页；set_*.back → app_settings
 *   set_facestyle.fs_apply → tab_main(tab0 表盘)
 * 显式 id 纪律：全部绑到 EEZ 生成的 objects.<identifier>，不新造控件句柄
 * （滚轮行与设置点击区是宿主内动态子件，属 native 内容，允许）。
 */
#include "lvgl.h"
#include "screens.h"
#include "images.h"
#include "fonts.h"   /* ui_font_cn26：滚轮行名称 */
#include "navigation/watch_nav.h"
#include "generated/app_rows.h"
#include "widgets/applist/watch_list_native.h"
#include "app/watch_logic.h"

extern objects_t objects;

/* ---- 跳转原语：三步等价 replacePageHook（NO_FLOW §1.2 正解） ---- */
static void go_screen(lv_obj_t *scr)
{
    if (lv_screen_active() != scr)
        lv_screen_load_anim(scr, LV_SCR_LOAD_ANIM_NONE, 0, 0, false);
}

static void go_applist(void)
{
    int center;

    go_screen(objects.tab_main);
    lv_tabview_set_active(objects.tv_main, 1, LV_ANIM_OFF);

    /* 点击首尾应用后的上游动画可能把它们暂时摆到中心；返回列表时同步
     * 经过 watch_list_center() 的边界钳位，保证可停中心范围始终一致。 */
    center = watch_list_center_index();
    if (center >= 0) watch_list_center(center, false);
}

/* ---- 路由事件：只决定目标页面，不修改 app/watch_model ---- */
static void back_cb(lv_event_t *e)
{
    lv_obj_t *target = (lv_obj_t *)lv_event_get_user_data(e);
    if (target == NULL) go_applist();          /* NULL=回 applist tab（非屏对象） */
    else go_screen(target);
}

static void row_cb(lv_event_t *e)
{
    lv_obj_t **scr = (lv_obj_t **)lv_event_get_user_data(e);
    go_screen(*scr);
}

static void applist_tab_cb(lv_event_t *e)   /* tab_main 上返回钮之外的 tab 切换 */
{
    (void)e;
}

/* ---- 设置页 6 行点击区（se_list 是纯展示 label，行点击区盖在宿主屏上） ---- */
static const struct { const char *name; lv_obj_t **scr; } SET_ROWS[] = {
    { "亮度",       &objects.set_brightness },
    { "声音与振动", &objects.set_sound },
    { "表盘样式",   &objects.set_facestyle },
    { "蓝牙连接",   &objects.set_bt },
    { "勿扰模式",   &objects.set_dnd },
    { "系统关于",   &objects.set_about },
};

static lv_obj_t *s_set_hits[6];

static void build_settings_hits(void)
{
    for (int i = 0; i < 6; i++) {
        lv_obj_t *hit = lv_obj_create(objects.app_settings);
        lv_obj_remove_style_all(hit);
        lv_obj_set_size(hit, 290, 44);
        lv_obj_set_pos(hit, (466 - 290) / 2, 150 + i * 46);
        lv_obj_add_flag(hit, LV_OBJ_FLAG_CLICKABLE);
        lv_obj_add_event_cb(hit, row_cb, LV_EVENT_CLICKED, (void *)SET_ROWS[i].scr);
        s_set_hits[i] = hit;
    }
}

/* ---- PC 无头回归的只读访问器；真机代码不应依赖它们 ---- */
lv_obj_t *watch_nav_app_screen(int i) { return *WATCH_APP_ROWS[i].screen; }
lv_obj_t *watch_nav_app_row(int i) { return watch_list_row_obj(i); }
lv_obj_t *watch_nav_set_screen(int i) { return *SET_ROWS[i].scr; }
lv_obj_t *watch_nav_set_hit(int i) { return s_set_hits[i]; }

/* ---- 绑定表：back 钮 → 目标（NULL=applist tab） ---- */
static void bind_back(lv_obj_t *btn, lv_obj_t *target)
{
    if (!btn) return;
    lv_obj_add_event_cb(btn, back_cb, LV_EVENT_CLICKED, target);
}

static void fs_apply_cb(lv_event_t *e)
{
    (void)e;
    go_screen(objects.tab_main);
    lv_tabview_set_active(objects.tv_main, 0, LV_ANIM_OFF);   /* 必须落回表盘 tab0 */
}

static void tab_changed_cb(lv_event_t *e)
{
    (void)e;
    watch_list_realign();
}

/* ---- 对外初始化：按“宿主先创建、再绑定回调”的顺序装配 ---- */
void watch_nav_init(void)
{
    lv_obj_add_event_cb(objects.tv_main, tab_changed_cb, LV_EVENT_VALUE_CHANGED, NULL);

    /* tab_main：tabview 原生左右滑（tab0 表盘 ↔ tab1 applist），无需绑事件 */

    /* applist 滚轮 */
    watch_list_create(objects.al_roller_host, NULL);

    /* 14 个 APP 页返回钮 → applist tab */
    bind_back(objects.app_sport_app_sport_back_b, NULL);
    bind_back(objects.app_hr_app_hr_back_b, NULL);
    bind_back(objects.app_sleep_app_sleep_back_b, NULL);
    bind_back(objects.app_spo2_app_spo2_back_b, NULL);
    bind_back(objects.app_weather_app_weather_back_b, NULL);
    bind_back(objects.app_msg_app_msg_back_b, NULL);
    bind_back(objects.app_music_app_music_back_b, NULL);
    bind_back(objects.app_alarm_app_alarm_back_b, NULL);
    bind_back(objects.app_stopwatch_app_stopwatch_back_b, NULL);
    bind_back(objects.app_timer_app_timer_back_b, NULL);
    bind_back(objects.app_calc_app_calc_back_b, NULL);
    bind_back(objects.app_compass_app_compass_back_b, NULL);
    bind_back(objects.app_findphone_app_findphone_back_b, NULL);
    bind_back(objects.app_settings_app_settings_back_b, NULL);

    /* 闹钟链：al_add → alarm_editor；editor back/save → app_alarm */
    bind_back(objects.app_alarm_app_alarm_al_add_b, objects.alarm_editor);
    bind_back(objects.alarm_editor_alarm_editor_back_b, objects.app_alarm);
    bind_back(objects.alarm_editor_alarm_editor_ae_save_b, objects.app_alarm);

    /* 设置子页：行点击区 + 各子页 back → app_settings */
    build_settings_hits();
    bind_back(objects.set_brightness_set_brightness_back_b, objects.app_settings);
    bind_back(objects.set_sound_set_sound_back_b, objects.app_settings);
    bind_back(objects.set_facestyle_set_facestyle_back_b, objects.app_settings);
    bind_back(objects.set_bt_set_bt_back_b, objects.app_settings);
    bind_back(objects.set_dnd_set_dnd_back_b, objects.app_settings);
    bind_back(objects.set_about_set_about_back_b, objects.app_settings);

    /* 表盘样式应用 → tab_main（tab0） */
    lv_obj_add_event_cb(objects.set_facestyle_set_facestyle_fs_apply_b, fs_apply_cb, LV_EVENT_CLICKED, NULL);

    /* 第⑦步页面内功能：在导航对象与动态点击区全部就绪后再绑定。 */
    watch_logic_init();
}
