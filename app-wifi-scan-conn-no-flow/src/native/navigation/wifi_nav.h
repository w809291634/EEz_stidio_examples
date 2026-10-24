/*
 * wifi_nav.h — 页面去向：两个模态（连接半页 / 忘记对话框）的显隐与互斥
 *
 * 分层口径（kit reference/12）：本层只管"哪个界面在前台"，
 * 不碰业务真值（app/wifi_model）、不建行（widgets/wifi_list）、不接硬件。
 */
#pragma once
#include <stdbool.h>
#ifdef __cplusplus
extern "C" {
#endif

/* 打开由 widgets/wifi_list 的行手势调用；关闭由 EEZ 生成的 action
 * （× / 遮罩 / 取消按钮）投递 APP_OUT_* 命令，wifi_logic 排空时回调 close。
 * 参数 ssid 只用于填界面标题；"这条命令针对哪个网络"记在 model 的
 * APP_IN_SEL_SSID，不由本层保管。 */
void wifi_nav_open_sheet(const char *ssid);
void wifi_nav_close_sheet(void);
void wifi_nav_open_dialog(const char *ssid);
void wifi_nav_close_dialog(void);
bool wifi_nav_sheet_open(void);
bool wifi_nav_dialog_open(void);

#ifdef __cplusplus
}
#endif
