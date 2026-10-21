/*
 * watch_icon_transform.c —— get_icon_transform_param 的复算实现
 *
 * 背景：SiFli SDK 里 `middleware/cell_transform/` 只有 cell_transform.h +
 * 预编译库（libcell_transform_gcc.a / *_msvc.lib / *_rvds.lib），**没有 .c**。
 * 移植件唯一的调用点在 watch_app_list.c 的 layout_icon_transform()，
 * 所以这里按 SDK 同目录的 `mainmenu.py`（生成 r→m / r→d 定点表的脚本）
 * 把那条曲线用浮点重写一遍。
 *
 * ★ 口径：这是**复算**，不声称与原库逐位一致。可核对的判据只有两条单调性
 *   （design/preflight.py 会跑）：
 *     - 缩放 m(r) 随离屏心距离 r 单调不增，且 m(0)=1；
 *     - 径向压缩 d(r) 随 r 单调不增，且 d(0)=1。
 *   也就是"中间大、两边小；越靠边挤得越紧"——手表穹顶列表的观感来源。
 *
 * 曲线出处（mainmenu.py，s 固定 1.8）：
 *   u = r*120/rw,  k = s*120
 *   m = 1.11111 * (u - 0.04342944819*k*10^(u/k) + 0.043429*k) / u,  m(0)=1
 *   d = (7/22 - (7/220)*10^(r/(rw*s))) / (63/220),                  d(0)=1
 */
#include <math.h>
#include <stdbool.h>

#include "sifli_compat.h"

#define TR_S           1.8f                 /* mainmenu.py 里的 s */
#define TR_LOG10_E_10  0.04342944819f       /* 0.4342944819E-1 */
#define TR_LOG10_E_10b 0.043429f            /* 脚本里截断的同一个常数 */
#define TR_K           (TR_S * 120.0f)      /* 216 */

/* rw：曲线自变量归一化用的半径。SDK 是脚本参数，本工程取短边半径，
 * 与 ICON_OUTER_RADIUS / LIMIT_ROUND_RADIUS 的口径一致。 */
#define TR_RW          ((WATCH_HOR_RES < WATCH_VER_RES ? WATCH_HOR_RES : WATCH_VER_RES) / 2)

/* 离屏心 r 像素处的图标缩放（1.0 = 原始大小） */
static float magnification(float r)
{
    float u = r * 120.0f / (float)TR_RW;

    if (u < 1e-4f) return 1.0f;             /* 0/0 极限，脚本里特判成 4096>>12 */

    return 1.11111f * (u - TR_LOG10_E_10 * TR_K * powf(10.0f, u / TR_K)
                       + TR_LOG10_E_10b * TR_K) / u;
}

/* 离屏心 r 像素处的径向压缩系数（1.0 = 不压缩） */
static float radial_factor(float r)
{
    float dp = (7.0f / 22.0f
                - (7.0f / 220.0f) * powf(10.0f, r / ((float)TR_RW * TR_S)))
               / (63.0f / 220.0f);

    if (dp < 0.0f) dp = 0.0f;               /* 超出 rw*s 后曲线为负，夹到 0 */
    return dp;
}

/*
 * 原型与 cell_transform.h 逐字一致：
 *   int get_icon_transform_param(float x, float y, float icon_r,
 *        float *p_x, float *p_y, float *p_icon_r, float *p_pivot_r,
 *        float scr_width, float scr_height)
 * 返回 0 表示"这项不该画"（调用方把 icon_r 归零并隐藏控件）。
 */
int get_icon_transform_param(float x, float y, float icon_r,
                             float *p_float_x, float *p_float_y,
                             float *p_float_icon_r, float *p_float_pivot_r,
                             float scr_width, float scr_height)
{
    float cx = scr_width / 2.0f;
    float cy = scr_height / 2.0f;
    float dx = x - cx;
    float dy = y - cy;
    float r  = sqrtf(dx * dx + dy * dy);
    float m  = magnification(r);
    float d  = radial_factor(r);

    /* pivot_r 语义：图标到屏心的距离。调用方用它挑"离中心最近的图标"，
     * 也用它做 limit_round2/limit_square 的裁剪判定。 */
    *p_float_pivot_r = r;

    /* 位置沿径向压缩，尺寸按 m 缩放——两者都以屏心为不动点 */
    *p_float_x = cx + dx * d;
    *p_float_y = cy + dy * d;
    *p_float_icon_r = icon_r * m;

    return (*p_float_icon_r > 0.0f) ? 1 : 0;
}
