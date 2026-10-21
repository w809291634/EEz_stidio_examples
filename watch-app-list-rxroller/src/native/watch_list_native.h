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

/* 立刻做一次屏外回收（拍屏前调，保证快照只算可见行） */
void watch_list_cull(void);

/* 动画是否还在跑（等惯性收敛用） */
bool watch_list_is_animating(void);

/* 第 i 行当前的变换缩放（256 = 100%）；越界或未创建返回 -1 */
int watch_list_row_scale(int index);

#endif /* WATCH_LIST_NATIVE_H */
