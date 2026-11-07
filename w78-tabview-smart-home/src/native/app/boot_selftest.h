#ifndef BOOT_SELFTEST_H
#define BOOT_SELFTEST_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdbool.h>

/* 开机自检：进度条 + 单行动态字条；完成后（PC）播放 assets/boot.mp4。 */
void boot_selftest_start(void);
bool boot_selftest_active(void);
int boot_selftest_progress(void);

#ifdef __cplusplus
}
#endif

#endif
