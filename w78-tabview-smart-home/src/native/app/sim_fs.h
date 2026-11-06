#ifndef SIM_FS_H
#define SIM_FS_H

#ifdef __cplusplus
extern "C" {
#endif

/* PC 仿真文件系统：A: → <工程根>/；ESP32 上是空实现（真机换 FATFS/LittleFS）。 */
void sim_fs_init(void);

#ifdef __cplusplus
}
#endif

#endif
