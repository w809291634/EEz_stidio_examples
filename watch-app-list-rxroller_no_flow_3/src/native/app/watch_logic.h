#ifndef WATCH_LOGIC_H
#define WATCH_LOGIC_H

#ifdef __cplusplus
extern "C" {
#endif

/* 在 UI 与导航对象创建完成后调用一次：委托 events 绑定控件并创建 100ms 调度器。 */
void watch_logic_init(void);

#ifdef __cplusplus
}
#endif

#endif /* WATCH_LOGIC_H */
