/*
 * wifi_busy.h — 「连接中」全屏遮罩 + 转圈（期间挡住一切操作）
 *
 * 为什么在 widgets 而不是 EEZ：这是运行时的过程态，控件树里本来就没有它；
 * EEZ 侧不持有任何变量，也没法用一个表达式驱动显隐（同 wifi_list 的口径）。
 */
#pragma once
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* 盖上整屏并开始转圈；txt 是圈下方那行字（可为 NULL 用默认「连接中…」）。
 * 遮罩是 CLICKABLE 的，所以期间列表、半页、对话框都点不到。 */
void wifi_busy_show(const char *txt);
void wifi_busy_hide(void);
bool wifi_busy_visible(void);

#ifdef __cplusplus
}
#endif
