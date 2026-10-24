#pragma once
#include <stdbool.h>
#ifdef __cplusplus
extern "C" {
#endif

void wifi_ui_sync(void);

/* ---- 模态显隐（⑦-1 导航闭环：只负责"进得去、退得出"，不含连接后端） ----
 * 打开走 native（列表行是 native 建的，EEZ 侧没有可挂的控件）；
 * 关闭走 EEZ 生成的 action（pwd_cancel / dlg_cancel 投递 APP_OUT_* 命令），
 * 由 user_io_tick 排空时回调下面两个 close。 */
void wifi_ui_open_sheet(const char *ssid);
void wifi_ui_close_sheet(void);
void wifi_ui_open_dialog(const char *ssid);
void wifi_ui_close_dialog(void);
bool wifi_ui_sheet_open(void);
bool wifi_ui_dialog_open(void);

#ifdef __cplusplus
}
#endif
