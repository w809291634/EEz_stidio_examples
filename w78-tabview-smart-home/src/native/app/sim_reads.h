#ifndef SIM_READS_H
#define SIM_READS_H

#ifdef __cplusplus
extern "C" {
#endif

/* PC 仿真专用：外部读动态模拟 + 开关派生状态；ESP32 上是空实现。 */
void sim_reads_init(void);
void sim_reads_tick(void);

#ifdef __cplusplus
}
#endif

#endif
