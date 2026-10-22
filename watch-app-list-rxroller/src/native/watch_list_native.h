/*
 * watch_list_native.h —— 本工程 native 侧对外接口（EEZ 只出外壳，列表在这里）
 */
#ifndef WATCH_LIST_NATIVE_H
#define WATCH_LIST_NATIVE_H

#include "lvgl.h"

/* 在 EEZ 生成的宿主容器里建 Rxroller 应用列表；status_label 用于点击回显 */
void watch_list_create(lv_obj_t *host, lv_obj_t *status_label);

/* 自证钩子：打印 [WHEEL] 行（中心项 / 各行缩放），preflight 与夹具都读它 */
void watch_list_dump(const char *tag);

/* 给无头夹具用的控制口：把第 i 行滚到中心；anim=true 走惯性/动画 */
void watch_list_center(int index, bool anim);

/* 当前中心行下标（未创建返回 -1） */
int watch_list_center_index(void);

/* 惯性抛出：px 带符号（正=手指向下划，看更早的行），内部换算成整行后做动画。
 * 手指快滑由 row_released_cb 调用；夹具也可以直接调它做无头断言。 */
void watch_list_fling(int32_t px);

/* 立刻做一次屏外回收（拍屏前调，保证快照只算可见行） */
void watch_list_cull(void);

/* 动画是否还在跑（等惯性收敛用） */
bool watch_list_is_animating(void);

/* 第 i 行当前的变换缩放（256 = 100%）；越界或未创建返回 -1 */
int watch_list_row_scale(int index);

/* 中心行图标的绝对 x 中心（px）——"横向 1/3 定位"的观测量，preflight/夹具用它核对 */
int watch_list_center_icon_x(void);

/* 允许磁吸到中心的行下标区间（首尾行不许）。夹具用它做边界断言。 */
int watch_list_center_min(void);
int watch_list_center_max(void);

/* 探针：绕过本工程的 clamp 直接叫上游 API，用来验证"首尾不许磁吸"是上游钳位在挡 */
void watch_list_center_no_clamp(int index, bool anim);

/* 松手落点纠正：把中心弹回允许范围（顶部第 n 个 / 底部倒数第 n 个，宏在 .c 里）。
 * 真机上由行 RELEASED 自动调；夹具也可以直接调它做无头断言。 */
void watch_list_snap_edge(void);

#endif /* WATCH_LIST_NATIVE_H */
