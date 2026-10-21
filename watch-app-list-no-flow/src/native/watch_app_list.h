/*
 * watch_app_list.h —— 移植件对外接口（只暴露三个入口，内部状态不外泄）
 */
#ifndef WATCH_APP_LIST_H
#define WATCH_APP_LIST_H

#include "lvgl.h"

/* 建表：host = EEZ 生成的整屏宿主；status_label = EEZ 生成的状态行 */
void watch_app_list_create(lv_obj_t *host, lv_obj_t *status_label);

/* 自证钩子：打印 [LIST] 行（visible / scale 区间 / 中心项） */
void watch_app_list_dump(const char *tag);

/* 给验收夹具拿可滚动的页面对象（合成滑动用），运行时未创建则 NULL */
lv_obj_t *watch_app_list_page(void);

#endif /* WATCH_APP_LIST_H */
