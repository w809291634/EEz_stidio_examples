/*
 * wifi_nav.h — 页面去向：两个模态（连接半页 / 忘记对话框）的显隐与互斥
 *
 * 分层口径（kit reference/12）：本层只管"哪个界面在前台"，
 * 不碰业务真值（app/wifi_model）、不建行（widgets/wifi_list）、不接硬件。
 */
#pragma once
#include <stdbool.h>

/* 半页动效的编译期开关：1 = 入场/退场动画（默认）；0 = 直接显隐。
 * 只在编译命令行覆盖，别在 .c 里再定义一次：
 *   g++ -DWIFI_SHEET_ANIM=0 ...
 * 夹具（design/sim_cmake/main.c）用同一个宏决定要不要断言"动画在跑"。 */
#ifndef WIFI_SHEET_ANIM
#define WIFI_SHEET_ANIM 1
#endif
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
/* 半页入场动画是否还在跑（夹具靠它等动画结束再点，免得点偏） */
bool wifi_nav_animating(void);

#ifdef __cplusplus
}
#endif
