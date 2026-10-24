/* watch_nav.h —— 第⑤步导航接线层（no flow：跳转全在 native，EEZ 只出控件）
 *
 * 口径（2026-10-22 用户定）：本层只保证"整体跳转+切换+每屏可达可回"，
 * 页面内细节功能（测量/播控/计时逻辑…）留第⑦步逐条立项。
 */
#ifndef WATCH_NAV_H
#define WATCH_NAV_H

#include "lvgl.h"

#if defined(__cplusplus)
extern "C" {
#endif

/* ui_init() 之后调用：建滚轮行、绑全部跳转事件、盖设置行点击区。 */
void watch_nav_init(void);

/* ---- 导航自证访问器（sim main 的 AUTOTEST 走路脚本用；真机不用） ---- */
lv_obj_t *watch_nav_app_screen(int i);   /* 第 i 个 APP 的屏（i<14） */
lv_obj_t *watch_nav_app_row(int i);      /* applist 滚轮第 i 行（可点） */
lv_obj_t *watch_nav_set_screen(int i);   /* 第 i 个设置子页屏（i<6） */
lv_obj_t *watch_nav_set_hit(int i);      /* app_settings 第 i 行点击区 */

#if defined(__cplusplus)
}
#endif

#endif /* WATCH_NAV_H */
