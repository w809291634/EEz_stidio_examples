/*
 * app_rows.h —— applist 行数据表（由 design/build_watch_ui.py 从 design_source.APPS 生成）
 * 不要手改 app_rows.c：改应用集合请改 design/design_source.py 的 APPS。
 */
#ifndef APP_ROWS_H
#define APP_ROWS_H

#include "lvgl.h"

typedef struct {
    const char *id;        /* 页面名，如 "app_sport" */
    const char *name;      /* 中文名 */
    const void *icon;      /* &img_ic_N */
    lv_obj_t **screen;     /* &objects.app_xxx */
} watch_app_row_t;

extern const watch_app_row_t WATCH_APP_ROWS[];
extern const int WATCH_APP_ROWS_COUNT;

#endif /* APP_ROWS_H */
