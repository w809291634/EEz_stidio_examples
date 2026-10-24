/*
 * wifi_view.h — 状态 → objects.* 的单向投影（每拍由 wifi_logic 调用）
 */
#pragma once
#ifdef __cplusplus
extern "C" {
#endif

void wifi_view_sync(void);

#ifdef __cplusplus
}
#endif
