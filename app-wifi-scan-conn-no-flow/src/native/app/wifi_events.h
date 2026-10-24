/*
 * wifi_events.h — 输入层：EEZ 动作回调 + 供 native 手势复用的"投递命令"入口
 *
 * 分层口径（kit reference/12）：本层是"输入 → 命令"的唯一出口，函数体只写
 * 选中项与 app_set_output()，不碰 objects.*、不碰硬件。
 * widgets/ 里的行手势也算输入，所以它调这里，而不是自己改 model。
 */
#pragma once
#include "lvgl.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ---- EEZ 生成的按钮/遮罩动作（src/ui/actions.h 声明，screens.c 挂接） ---- */
void action_scan_start(lv_event_t *e);
void action_wifi_connect(lv_event_t *e);
void action_pwd_cancel(lv_event_t *e);
void action_dlg_forget(lv_event_t *e);
void action_dlg_cancel(lv_event_t *e);

/* ---- native 手势复用入口 ---- */
void wifi_events_select(const char *ssid);      /* 记下本次操作针对哪个网络 */
void wifi_events_request_connect(void);         /* 投递「连接」命令 */

#ifdef __cplusplus
}
#endif
