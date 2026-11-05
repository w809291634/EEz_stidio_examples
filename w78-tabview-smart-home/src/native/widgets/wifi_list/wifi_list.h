/*
 * wifi_list.h — 专用动态控件：Wi-Fi 结果列表（行创建、行内几何、手势）
 *
 * 分层口径（kit reference/12）：父对象（lv_list）由 EEZ 画，行由本层动态创建；
 * 手势只决定"去哪个界面"，显隐交给 navigation/wifi_nav。
 */
#pragma once
#ifdef __cplusplus
extern "C" {
#endif

/* 按 io 当前列表重建所有行（state==2 才有行；state 由调用方传入以保持单向） */
void wifi_list_rebuild(int state);

#ifdef __cplusplus
}
#endif
