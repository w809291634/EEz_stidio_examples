#ifndef NAV_BIND_H
#define NAV_BIND_H

#include "lvgl.h"

#ifdef __cplusplus
extern "C" {
#endif

/* 把 nav_bind_table.h 的边挂到控件上；ui_init() 之后调用。 */
void nav_bind_init(void);

/* 当前屏与来路栈（返回键用）。 */
int nav_bind_current(void);
void nav_bind_seed(int cur, int back);   /* 测试用：设当前屏 + 一条来路 */
lv_obj_t *nav_screen_obj(int id);        /* 屏 id → 根对象（测试断言用） */

#ifdef __cplusplus
}
#endif

#endif
