/*
 * wifi_eye.h — 密码框右端的「眼睛」：按住显示明文，松开恢复星号
 *
 * 为什么是原生控件：EEZ 侧没有能随按压切换密码模式的机制（不持变量、也无长按态
 * 的数据绑定），而且这是运行时交互，按 §2 口径动态内容可用原生实现。
 */
#pragma once
#include "lvgl.h"

#ifdef __cplusplus
extern "C" {
#endif

/* 幂等：在 objects.sheet 里建眼睛并给输入框留出右内边距；控件缺失时什么也不做。 */
void wifi_eye_init(void);
/* 夹具用：返回眼睛对象（未创建返回 NULL）。 */
lv_obj_t *wifi_eye_handle(void);

#ifdef __cplusplus
}
#endif
