/*
 * sifli_compat.h —— SiFli 手表主菜单移植件的"依赖替身"层
 *
 * 被移植的算法本体在 watch_app_list.c（逐字来自 SiFli SDK
 * example/multimedia/lvgl/watch_v9/src/gui_apps/main/app_mainmenu.c，
 * SPDX-License-Identifier: Apache-2.0）。它原本编译在 RT-Thread + SiFli GUI
 * 框架里，本文件把那些依赖在本工程（PC_SIM / LVGL 9.4）下补齐，
 * **只补接口，不改算法**。
 *
 * 三条硬约束（都是实测出来的，别"顺手改漂亮"）：
 *  1) 分辨率必须是**编译期常量**：原文件在 `#if (LV_VER_RES_MAX > LV_HOR_RES_MAX)`
 *     里拿它做预处理算术（ICON_OUTER_RADIUS / LIMIT_* 都由它推），
 *     换成 lv_display_get_*() 运行期调用会直接编不过。
 *  2) 这里刻意 include 了 LVGL 的 *_private.h：原文件直接摸 obj->flags、
 *     img->scale_x、indev->scroll_limit 这些内部字段（见 watch_app_list.c 顶部注释）。
 *  3) get_icon_transform_param 在 SDK 里是**预编译库**（middleware/cell_transform
 *     只有头 + .a），本工程用 watch_icon_transform.c 按 mainmenu.py 的曲线**复算**，
 *     不声称与原库逐位一致，只在 README 里给出行为对照判据。
 */
#ifndef WATCH_SIFLI_COMPAT_H
#define WATCH_SIFLI_COMPAT_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "lvgl.h"
/* 原文件直接访问内部结构体/字段，这三个头是必需的，不是"顺手多包一层" */
#include "src/core/lv_obj_private.h"
#include "src/core/lv_obj_scroll_private.h"
#include "src/widgets/image/lv_image_private.h"
#include "src/draw/lv_draw_image_private.h"
#include "src/indev/lv_indev_private.h"

/*---- 1. 面板（与 EEZ 工程 displayWidth/Height 必须一致，见 design/preflight.py）----*/
#define WATCH_HOR_RES 368
#define WATCH_VER_RES 448

/* LVGL 9.4 自己把 LV_HOR_RES/LV_VER_RES 定义成 lv_display_get_*() **运行期调用**
 * （src/display/lv_display.h:683/690）。移植件在 `#if (LV_VER_RES_MAX > LV_HOR_RES_MAX)`
 * 里拿它们做预处理算术（ICON_OUTER_RADIUS / LIMIT_* 都由它推），运行期表达式编不过，
 * 所以这里必须 #undef 之后换成编译期常量。视口 = 面板，本来就是本工程的事实。 */
#undef LV_HOR_RES
#undef LV_VER_RES
#define LV_HOR_RES_MAX WATCH_HOR_RES
#define LV_VER_RES_MAX WATCH_VER_RES
#define LV_HOR_RES     WATCH_HOR_RES
#define LV_VER_RES     WATCH_VER_RES
/* SiFli 局刷行数；PC 是全帧缓冲，取 0 ⇒ 原文件走"on_start 里就重绘"那条分支 */
#define LV_FB_LINE_NUM 0

/*---- 2. RT-Thread 替身 ----*/
typedef int rt_err_t;
#define RT_EOK    0
#define RT_EEMPTY (-1)
#define RT_ASSERT(expr)                                              \
    do {                                                             \
        if (!(expr)) {                                               \
            printf("[FATAL] %s:%d assert(%s)\n",                     \
                   __FILE__, __LINE__, #expr);                       \
            abort();                                                 \
        }                                                            \
    } while (0)

#define rt_kprintf printf
static inline void *rt_calloc(size_t n, size_t s) { return calloc(n, s); }
static inline void *rt_malloc(size_t n) { return malloc(n); }
static inline void  rt_free(void *p) { free(p); }
/* 原文件里 rt_hw_interrupt_disable/enable 已被注释掉，这里就不提供假临界区 */

/*---- 3. 日志 ----*/
#define DBG_LEVEL 0
#define LOG_I(...) printf(__VA_ARGS__)
#define LOG_E(...) printf(__VA_ARGS__)

/*---- 4. LVGL 版本差（SiFli 分支有、9.4 上游没有的名字）----*/
#define LV_COLOR_BLACK lv_color_black()
#define LV_COLOR_WHITE lv_color_white()
/* LV_IMG_DECLARE 由 LVGL 自己的 src/lv_api_map_v8.h:318 提供，别再定义一遍 */
/* 资源管理器取图：本工程图标是普通 lv_image_dsc_t，直接取地址 */
#define LV_EXT_IMG_GET(id) (&id)
/* v8 名字：_lv_obj_scroll_by_raw → 9.4 去掉了下划线 */
#define _lv_obj_scroll_by_raw lv_obj_scroll_by_raw
/* v8 名字：lv_disp_* → 9.4 改名 lv_display_*（原文件在 set_zoom 里用它关/开
 * 无效化，避免 refresh_ext_draw_size 把整块区域刷一遍） */
#define lv_disp_enable_invalidation lv_display_enable_invalidation
/* LVGL 9 取消了"输入设备独立读周期"，只有全局刷新周期；原文件用它估算
 * 甩动动画时长（每多滚一个读周期加 4 倍时间），量纲不变即可 */
#define LV_INDEV_DEF_READ_PERIOD LV_DEF_REFR_PERIOD
/* SiFli 按键扩展的返回值，9.4 上游没有这两个名字 */
#define LV_BLOCK_EVENT 0
#define LV_POST_EVENT  1

/*---- 5. SiFli 按键扩展（PC 上无键盘后端，注册即空操作）----*/
typedef int32_t (*watch_keypad_handler_t)(lv_key_t key, lv_indev_state_t event);
static inline void keypad_handler_register(watch_keypad_handler_t h) { (void)h; }

/*---- 6. 应用表（替 gui_builtin_app_list_*，数据在 sifli_compat.c）----*/
typedef struct {
    const char *id;
    const void *icon;
} builtin_app_desc_t;

const builtin_app_desc_t *gui_builtin_app_list_open(void);
const builtin_app_desc_t *gui_builtin_app_list_get_next(const builtin_app_desc_t *cur);
void gui_builtin_app_list_close(const builtin_app_desc_t *cur);
/* 点中图标时由移植件调用；本工程只把它写到状态行上 */
void gui_app_run(const char *cmd);
/* 状态行由 EEZ 生成，创建移植件时注入 */
void watch_app_list_bind_status(lv_obj_t *status_label);

/*---- 7. cell_transform 的复算实现（watch_icon_transform.c）----*/
int get_icon_transform_param(float x, float y, float icon_r,
                             float *p_float_x, float *p_float_y,
                             float *p_float_icon_r, float *p_float_pivot_r,
                             float scr_width, float scr_height);

/*---- 8. 移植件对外入口（watch_app_list.h 里也有，这里给 C++ 侧留个方便）----*/
void watch_app_list_create(lv_obj_t *host, lv_obj_t *status_label);
void watch_app_list_dump(const char *tag);   /* 自证用：打印中心项与各图标缩放 */

#endif /* WATCH_SIFLI_COMPAT_H */
