/*
 * wifi_view.h — 状态 → objects.* 的单向投影（每拍由 wifi_logic 调用）
 */
#pragma once
#ifdef __cplusplus
extern "C" {
#endif

void wifi_view_sync(void);

/* 读半页密码框的当前内容，写进调用方给的缓冲。objects.* 只允许 view 层碰，
 * 所以 wifi_logic 要密码时走这里，不直接抓 pwd_ta。 返回值：缓冲本身。 */
const char *wifi_view_password(char *out, int out_sz);

#ifdef __cplusplus
}
#endif
