#ifndef BOOT_ANIM_H
#define BOOT_ANIM_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdbool.h>

/* 开机动画：按 boot_frames.h 的帧序列在顶层播放，播完自动移除。
 * 帧路径走 LVGL FS（A:/assets/boot/...）；FS 不可用时直接跳过。 */
void boot_anim_play(void);
bool boot_anim_active(void);
int boot_anim_frames_played(void);

#ifdef __cplusplus
}
#endif

#endif
