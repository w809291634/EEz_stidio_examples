/* ui_bg.c — 固定背景图（运行期从文件系统读取，不烧进固件）
 *
 * 半分辨率解码 + 拉伸铺满：
 *   PNG 是 400×240，LVGL 解码缓冲 400*240*4 ≈ 384KB；
 *   用 LV_IMAGE_ALIGN_STRETCH 放大到 800×480，避免 1.5MB 的整屏解码。
 *
 * 路径：
 *   - PC 仿真：A: 由 sim_fs 接管 → 工程根 assets/ui_bg.png
 *   - 真机：同路径，由 FATFS/LittleFS 注册 A:（或 -DUI_BG_PATH 改路径）
 */
#include "ui_bg.h"

#include "lvgl.h"
#include "screens.h"
#include "nav_bind_table.h"

#ifndef UI_BG_PATH
#define UI_BG_PATH "A:/assets/ui_bg.png"
#endif

#define UI_BG_SCREEN_W 800
#define UI_BG_SCREEN_H 480

static bool s_applied;

void ui_bg_apply(void)
{
    lv_obj_t *scr;
    lv_obj_t *img;

    if (s_applied) return;
    s_applied = true;

#define APPLY_BG(sid, field)                                        \
    do {                                                            \
        scr = objects.field;                                        \
        if (scr) {                                                  \
            img = lv_image_create(scr);                             \
            lv_image_set_src(img, UI_BG_PATH);                      \
            lv_obj_set_pos(img, 0, 0);                              \
            lv_obj_set_size(img, UI_BG_SCREEN_W, UI_BG_SCREEN_H);   \
            /* STRETCH：按控件尺寸自动算缩放（400×240 → 800×480）， */ \
            /* 比手算 scale 稳，且不受 set_size/scale 调用顺序影响 */   \
            lv_image_set_inner_align(img, LV_IMAGE_ALIGN_STRETCH);  \
            lv_obj_clear_flag(img, LV_OBJ_FLAG_CLICKABLE |          \
                                   LV_OBJ_FLAG_SCROLLABLE);         \
            lv_obj_move_to_index(img, 0);   /* 最底层，别盖住内容 */ \
        }                                                           \
    } while (0);

    NAV_PAGE_LIST(APPLY_BG)
#undef APPLY_BG
}
