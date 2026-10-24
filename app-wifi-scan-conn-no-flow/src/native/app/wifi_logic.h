/*
 * wifi_logic.h — 应用装配：初始化与每拍调度（main 循环调用）
 */
#pragma once
#ifdef __cplusplus
extern "C" {
#endif

void user_io_init(void);   /* 一次性初始化平台后端 */
void user_io_tick(void);   /* 排空命令环 → 推进平台 → 请求视图刷新 */

#ifdef __cplusplus
}
#endif
