/* 自动生成：design/gen_assets.py（事实源 design/apps.py）——勿手改 */
#ifndef WATCH_APP_ROWS_H
#define WATCH_APP_ROWS_H

typedef struct {
    const char *id;      /* 目标页 id（ASCII，不上屏） */
    const char *name;    /* 中文名，上屏 ⇒ 必须在字体子集内 */
    const void *icon;    /* lv_image_dsc_t* */
} watch_app_row_t;

extern const watch_app_row_t WATCH_APP_ROWS[];
extern const int WATCH_APP_ROWS_COUNT;

#endif
