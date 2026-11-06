#ifndef SIM_VIDEO_H
#define SIM_VIDEO_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdbool.h>

/* PC 仿真专用：用 ffmpeg 直接解码真实 MP4，逐帧画到 LVGL canvas。
 * 不预转帧、不做动图；ESP32 上为空实现（真机需硬件解码或帧序列资源包）。 */
bool sim_video_play_boot(void);      /* 播放 <工程根>/assets/boot.mp4 */
bool sim_video_active(void);
int sim_video_frames(void);

#ifdef __cplusplus
}
#endif

#endif
