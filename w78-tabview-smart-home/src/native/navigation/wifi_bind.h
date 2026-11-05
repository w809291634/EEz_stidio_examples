#ifndef WIFI_BIND_H
#define WIFI_BIND_H
#ifdef __cplusplus
extern "C" {
#endif
/* 把示例工程里由 EEZ action 挂的按钮，改在 native 侧统一挂（no-flow 不生成 action）。 */
void wifi_bind_init(void);
#ifdef __cplusplus
}
#endif
#endif
