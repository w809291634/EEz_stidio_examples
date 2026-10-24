/*
 * watch_list_config.h —— applist 滚轮所有可调参数的唯一出处
 *
 * 三方都读它：src/native/widgets/applist/watch_list_native.c（直接 include）、
 * design/port_rxroller.py（正则读 SCALE_SPAN_PITCHES / SCALE_MAX / CLICK_TRAVEL_MAX_PX）、
 * design/design_source.py（经 wconfig 读，用来算设计图剖面与宿主几何）。
 * 本工程屏=圆形 466×466；EEZ 导出的图标位图就是 90×90，所以中心档取 100%（1:1 不糊）。
 */
#ifndef WATCH_LIST_CONFIG_H
#define WATCH_LIST_CONFIG_H

/*==== 1. 图标与行几何 =========================================================*/
#define ICON_PX              90
#define ROW_W               300
#define ROW_H                92     /* 必须 >= ICON_PX × SCALE_CENTER_PCT/100 = 90 */
#define ROW_PITCH            92     /* = 设计源 ROLLER.pitch */
#define ROW_ICON_X            0
#define ROW_LABEL_X         110     /* 让开 90px 图标 + 20px 间距 */

/*==== 2. 缩放曲线 =============================================================*/
#define SCALE_SPAN_PITCHES     3    /* 剖面 0/33/66/100 */
#define SCALE_CENTER_PCT     100    /* 中心档=位图原尺寸 */
#define SCALE_MAX            (256 * SCALE_CENTER_PCT / 100)
#define SCALE_EDGE_PCT        59    /* 90×0.59 ≈ 53px */
#define EDGE_SCALE          (SCALE_MAX * SCALE_EDGE_PCT / 100)

#define CURVE_ENABLE         1
#define CURVE_RADIUS       700      /* x=R*(1-cos(d/R)) 偶函数 ⇒ C 形 */
#define ANIM_TIME            300

/*==== 3. 中心行落点（屏幕坐标，非布局坐标；FIXLOG FX-024） ======================*/
/* 设计源 ROLLER：icon cx=175 → 38%、cy=195 → 42% */
#define CENTER_X_PCT          38
#define CENTER_Y_PCT          42
#define CENTER_TOL_PX          1
/* pad→落点斜率倒数：实测 pad Δ-254 ⇒ 落点 Δ-127（斜率 0.5），所以 pad 走 2×误差 */
#define PAD_SLOPE_INV          2

/*==== 4. 松手磁吸 ==============================================================*/
/* 首项/末项可被拖过中心，但松手后分别弹回第 2 项/倒数第 2 项。
 * 与 watch-app-list-rxroller_no_flow_2 的交互口径一致。 */
#define EDGE_SNAP_TOP_ORDINAL     2
#define EDGE_SNAP_BOTTOM_ORDINAL  2

/*==== 5. 快滑惯性 ==============================================================*/
#define FLING_MIN_VEL        120
#define FLING_SEC            250
#define FLING_MAX_ROWS         3
#define FLING_MAX_PX     (ROW_PITCH * FLING_MAX_ROWS)
#define FLING_VEL_SMOOTH       8
#define FLING_VEL_STALE_MS    80

/*==== 6. 点击 / 拖动判定 =======================================================*/
#define DRAG_CLICK_IGNORE_PX  15
#define CLICK_TRAVEL_MAX_PX   10

/*==== 7. 屏外回收 =============================================================*/
#define CULL_PITCHES           4

#endif /* WATCH_LIST_CONFIG_H */
