/*
 * watch-app-list-no-flow 的 PC 仿真入口（design/sim_cmake/main.c）
 * ---------------------------------------------------------------------------
 * 与仓库通用模板的差别（本工程是 **no-flow + native 移植件**）：
 *  - 分辨率 368x448（SiFli 表形面板口径），必须与 EEZ 工程 displayWidth/Height
 *    和 src/native/sifli_compat.h 的 WATCH_HOR_RES/VER_RES 三处一致——
 *    design/preflight.py 会把这条对齐检查当硬判据。
 *  - flowSupport=false ⇒ EEZ 不发射 eez-flow.h/cpp，ui_init() 走的是
 *    `create_screens()` 那条分支（ui.c 的 #else），没有 eez_flow_tick。
 *    所以**界面主体不在 EEZ 里**：EEZ 只出整屏宿主 + 标题 + 状态行，
 *    蜂窝缩放列表由 native 移植件在 ui_init() 之后挂上 objects.list_host。
 *  - 滚动/缩放/吸附是 native C（从 SiFli watch_v9 app_mainmenu.c 移植），
 *    不依赖 EEZ Flow，也不依赖 RT-Thread（依赖替身见 sifli_compat.h）。
 *
 * WATCH_AUTOTEST=1 时无头自证：合成拖动 → 逐点 dump → 拍两张图。
 * 需要本工程 lv_conf.h 里 LV_USE_SNAPSHOT 1（偏离通用模板，preflight 会核对）。
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include "lvgl.h"
#include "SDL2/SDL.h"
#include "lv_sdl_window.h"   /* lv_sdl_window_get_window：真鼠标事件要拿 SDL_Window* 换 windowID */
#include "ui.h"              /* EEZ 生成：ui_init / ui_tick（C 安全，不引入额外 C++ 头） */
#include "screens.h"         /* objects_t：EEZ 生成的控件句柄（no-flow 下 ui.h 不带出来） */
#include "watch_app_list.h"  /* 移植件入口：create / dump / page */
#include "src/others/snapshot/lv_snapshot.h"

extern void ui_init(void);
extern void ui_tick(void);

#define SIM_W 368
#define SIM_H 448

/* ---- WATCH_AUTOTEST=1：无头自证（合成拖动 + dump + 拍屏），不需要人点鼠标 ----
 * 判据形态是"关系"而不是绝对值：
 *   ① 同屏图标的 scale 有区间（max > min）⇒ 穹顶缩放生效（中间大两边小）；
 *   ② 拖动后中心项（center）变了 ⇒ 吸附到了另一项；
 *   ③ 拖动后 visible 数量级不变 ⇒ 没有把整屏拖成空白。
 * 具体数字见 [LIST] 行，由 design/preflight.py 里同一套断言复核。 */
static void take_shot(const char *path)
{
    lv_draw_buf_t *buf = lv_snapshot_take(lv_screen_active(), LV_COLOR_FORMAT_XRGB8888);
    if (!buf) { printf("[SHOT] snapshot failed\n"); return; }
    int w = (int)buf->header.w, h = (int)buf->header.h;
    int stride = (int)buf->header.stride;
    unsigned char *src = (unsigned char *)buf->data;
    FILE *fp = fopen(path, "wb");
    if (fp) {
        int row = w * 4, data = row * h;
        unsigned char hd[54] = { 'B','M' };
        *(int *)(hd + 2) = 54 + data;
        *(int *)(hd + 10) = 54;
        *(int *)(hd + 14) = 40;
        *(int *)(hd + 18) = w;
        *(int *)(hd + 22) = -h;          /* 自顶向下，PIL 直接读 */
        *(short *)(hd + 26) = 1;
        *(short *)(hd + 28) = 32;
        fwrite(hd, 1, 54, fp);
        for (int y = 0; y < h; y++) fwrite(src + y * stride, 1, row, fp);
        fclose(fp);
        printf("[SHOT] saved %s\n", path);
    }
    lv_draw_buf_destroy(buf);
}

static void autotest_hooks(void)
{
    static int ticks = 0;
    lv_obj_t *page;

    if (!getenv("WATCH_AUTOTEST")) return;
    ticks++;
    page = watch_app_list_page();
    if (NULL == page) return;

    if (ticks == 30) {
        watch_app_list_dump("init");
        take_shot("shot_init.bmp");
    }
    if (ticks == 60) {
        /* 沿蜂窝斜轴拖一格：ICON_OUTER_DIAMETER=80，拖 (80, 80) 就换中心项 */
        lv_obj_scroll_by(page, 80, 80, LV_ANIM_OFF);
    }
    if (ticks == 80) {
        watch_app_list_dump("drag+80");
        take_shot("shot_drag.bmp");
        if (getenv("WATCH_AUTOEXIT")) exit(0);
    }
}

static lv_display_t * hal_init(int32_t w, int32_t h)
{    lv_group_set_default(lv_group_create());

    lv_display_t * disp = lv_sdl_window_create(w, h);

    lv_indev_t * mouse = lv_sdl_mouse_create();
    lv_indev_set_group(mouse, lv_group_get_default());
    lv_indev_set_display(mouse, disp);
    lv_display_set_default(disp);

    LV_IMAGE_DECLARE(mouse_cursor_icon);   /* 仿真器自带光标位图（main/src/mouse_cursor_icon.c） */
    lv_obj_t * cursor_obj = lv_image_create(lv_screen_active());
    lv_image_set_src(cursor_obj, &mouse_cursor_icon);
    lv_indev_set_cursor(mouse, cursor_obj);

    lv_indev_t * mousewheel = lv_sdl_mousewheel_create();
    lv_indev_set_display(mousewheel, disp);
    lv_indev_set_group(mousewheel, lv_group_get_default());

    lv_indev_t * kb = lv_sdl_keyboard_create();
    lv_indev_set_display(kb, disp);
    lv_indev_set_group(kb, lv_group_get_default());

    return disp;
}

int main(int argc, char **argv)
{
    (void)argc;
    (void)argv;

    lv_init();
    hal_init(SIM_W, SIM_H);

    ui_init();

    /* EEZ 外壳建好后，把 native 的蜂窝列表挂到整屏宿主上。
     * 顺序不能反：objects.* 是 create_screens() 里才有的句柄。 */
    watch_app_list_create(objects.list_host, objects.lbl_status);

    while (1) {
        lv_tick_inc(2);
        lv_timer_handler();
        ui_tick();
        autotest_hooks();
        usleep(4000);
    }

    return 0;
}
