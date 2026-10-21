/*
 * sifli_compat.c —— 依赖替身层的实现部分（应用表 + 状态回写）
 *
 * 只放"本工程的环境"该有的东西；算法在 watch_app_list.c。
 */
#include "sifli_compat.h"

/* 图标由 design/gen_icons.py 自绘生成到 src/native/icons/（占位风格：
 * 纯色圆底 + 首字母），每个都是 lv_image_dsc_t，尺寸 98x98。 */
#define ICON_DECL(id) LV_IMG_DECLARE(img_app_##id)
ICON_DECL(clock);
ICON_DECL(activity);
ICON_DECL(alarm);
ICON_DECL(calendar);
ICON_DECL(camera);
ICON_DECL(health);
ICON_DECL(mail);
ICON_DECL(maps);
ICON_DECL(music);
ICON_DECL(phone);
ICON_DECL(photos);
ICON_DECL(remote);
ICON_DECL(settings);
ICON_DECL(stocks);
ICON_DECL(stopwatch);
ICON_DECL(workout);
#undef ICON_DECL

#define ICON_PTR(id) (&img_app_##id)

/* 20 项里放 16 个真应用：蜂窝布局第 0 位固定留给 clock（原文件的
 * mainmenu_cell_reorder_wf_icon 就是这个规则），其余按表顺序螺旋排布。 */
static const builtin_app_desc_t APP_TABLE[] = {
    {"clock",     ICON_PTR(clock)},
    {"activity",  ICON_PTR(activity)},
    {"alarm",     ICON_PTR(alarm)},
    {"calendar",  ICON_PTR(calendar)},
    {"camera",    ICON_PTR(camera)},
    {"health",    ICON_PTR(health)},
    {"mail",      ICON_PTR(mail)},
    {"maps",      ICON_PTR(maps)},
    {"music",     ICON_PTR(music)},
    {"phone",     ICON_PTR(phone)},
    {"photos",    ICON_PTR(photos)},
    {"remote",    ICON_PTR(remote)},
    {"settings",  ICON_PTR(settings)},
    {"stocks",    ICON_PTR(stocks)},
    {"stopwatch", ICON_PTR(stopwatch)},
    {"workout",   ICON_PTR(workout)},
};
#define APP_COUNT (sizeof(APP_TABLE) / sizeof(APP_TABLE[0]))

const builtin_app_desc_t *gui_builtin_app_list_open(void)
{
    return &APP_TABLE[0];
}

const builtin_app_desc_t *gui_builtin_app_list_get_next(const builtin_app_desc_t *cur)
{
    if (NULL == cur) return NULL;
    if ((cur + 1) >= &APP_TABLE[APP_COUNT]) return NULL;
    return cur + 1;
}

void gui_builtin_app_list_close(const builtin_app_desc_t *cur)
{
    (void)cur;   /* 表是静态的，没有要释放的东西 */
}

/*---- 状态回写：真机上这里是切应用，本工程只在状态行上留痕----*/
static lv_obj_t *s_status_label = NULL;

/* ★ 这行中文必须出现在屏上字体子集里 —— design/preflight.py 会拿
 *   src/native/*.c 的非 ASCII 字符去比对 EEZ 字体条目，缺字即 FAIL。 */
#define WATCH_STATUS_FMT "已打开: %s"

void watch_app_list_bind_status(lv_obj_t *status_label)
{
    s_status_label = status_label;
}

void gui_app_run(const char *cmd)
{
    printf("[APP] gui_app_run(\"%s\")\n", cmd ? cmd : "(null)");
    if (s_status_label && cmd) {
        char buf[64];
        snprintf(buf, sizeof(buf), WATCH_STATUS_FMT, cmd);
        lv_label_set_text(s_status_label, buf);
    }
}
