/*
 * watch_list_config.h —— 应用列表**所有可调参数**的唯一出处
 *
 * 想改观感只改这个文件，不要再去翻 watch_list_native.c / Rxroller.c / gen_assets.py。
 * 三方都会读它：
 *   - src/native/watch_list_native.c  直接 include
 *   - design/gen_assets.py            正则读 ICON_PX（图标位图尺寸）
 *   - design/port_rxroller.py         正则读 SCALE_SPAN_PITCHES（烘进上游补丁）
 *   - design/preflight.py             读全部值做门禁，并反向检查这些名字没在别处定义
 *
 * 单位都标在行尾注释里，改完跑：
 *   python design\gen_assets.py && python design\port_rxroller.py
 *   python design\preflight.py
 */
#ifndef WATCH_LIST_CONFIG_H
#define WATCH_LIST_CONFIG_H

/*==== 1. 图标与行几何 =========================================================*/

/* 图标位图边长（px）。★ 中心行的"最大"就是 100% × 这个值；
 *   非中心行的"最小"由 SCALE_EDGE_PCT 决定，不是改这里。 */
#define ICON_PX              76

#define ROW_W               300     /* 行容器宽（上游 big_w） */
#define ROW_H               120     /* 行容器高（上游 big_h）。★ 必须 >= ICON_PX ×
                                       SCALE_CENTER_PCT/100，否则中心图标会顶到上下行
                                       （preflight 有这条几何门禁） */
#define ROW_PITCH           120     /* 相邻行中心距（上游 icon_distance）。同上约束 */
#define ROW_ICON_X           12     /* 图标在行内的左偏移 */
#define ROW_LABEL_X         100     /* 名称在行内的左偏移（要让开图标） */

/*==== 2. 缩放曲线：选中最大、未选中最小、过程线性 ==============================*/

/* 缩放曲线口径：**选中最大、未选中最小、中间线性插值**。
 *
 *   scale ┤ 255 ●  ← 正中 = 100%
 *         │      ╲ 100%
 *         │        ╲ 67%      ← d=1
 *         │          ╲ 33%    ← d=2
 *   EDGE  │- - - - - - ●- - - ← d=3 起到底（最小）
 *         └────┬───┬───┬───┬──── 离中心的行距
 *              0   1   2   3
 *
 * SPAN = "从最大走到最小要跨几行"。它决定中间档的比例：
 *   SPAN=1 → 紧邻行就到底（只有正中亮）
 *   SPAN=2 → 中间那行 = 50%
 *   SPAN=3 → 中间两行 = 67% / 33%   ← 2026-10-22 口径（0/33/66/100）
 *   SPAN=4 → 67/50/33… 依此类推，公式就是线性
 */
#define SCALE_SPAN_PITCHES     3    /* 从最大降到最小要跨几个行距 */

/* ★ 中心档（满档）= 位图原尺寸的百分之几。
 *   上游把中心档写死成 255 ⇒ 中心最多只等于 ICON_PX，**永远不可能比原图更大**。
 *   要"中心更突出"就调这个（由 port_rxroller.py 烘进上游补丁 RXROLLER_SCALE_MAX）。
 *   256 = LVGL transform_zoom 的 100%。 */
#define SCALE_CENTER_PCT     150    /* 150 ⇒ 中心图标 76×1.5 = 114px */
#define SCALE_MAX            (256 * SCALE_CENTER_PCT / 100)

#define SCALE_EDGE_PCT        59    /* ★ 最小档占**满档**的百分比（不是占 255）。
                                       对比要更强就调小。 */
#define EDGE_SCALE          (SCALE_MAX * SCALE_EDGE_PCT / 100)   /* 换算 */

/*---- 排布形状：一条竖线 还是 一条曲线 ----*/

/* 0 = 竖直一列；1 = 按半径弯成弧线（上游 ARC 模式）。
 * 弧线公式 x = R*(1 - cos(d/R)) 是**偶函数** ⇒ 上下两侧都朝同一侧鼓，
 * 形成"C"形（不是左右镜像的 S）。这正是侧看圆柱滚轮的样子。
 * 中心行 d=0 ⇒ x=0，所以**不影响中心行的横向落点**，只挪动上下那些行。 */
#define CURVE_ENABLE         1
#define CURVE_RADIUS       700     /* 弧度半径 px。★ 越小越弯、越大越平。
                                    *  行距 120 时"第 n 行相对中心行的横移"：
                                    *    420 → +17/+67/+145/+246（±1..±4 行，太鼓）
                                    *    700 → +10/+41/+91/+158  ← 当前
                                    *    900 → +8/+32/+71/+125
                                    *  半径还顺带管纵向疏密：y = R·sin(d/R)，
                                    *  420 时 ±4 行被压到 382px（挤 20%），
                                    *  700 时 443px（挤 8%）⇒ 收平=行距也更均匀。 */
#define ANIM_TIME            300    /* ms，一次定位动画基准时长 */

/*==== 3. 中心行的落点位置（一次性闭环标定，不写死 pad） =======================*/

/* ★ 口径：**屏幕上看到的位置**，不是布局坐标。上游把整行按行中心做 transform
 *   缩放，图标在轴心左侧 ⇒ 放大后往左漂（中心档 150% 时实测 42px），
 *   用布局坐标标会越放大越偏左。
 *   见 FIXLOG FX-024 / README §5.3。用百分比而不是 1/N：1/N 只能在
 *   50%(205) / 33%(136) / 25%(102) 之间跳，中间落点够不着。 */
#define CENTER_X_PCT          42    /* 水平：屏宽的 42% ⇒ 410 上 = 172px */
#define CENTER_Y_PCT          50    /* 垂直：屏高的 50%（正中） */
#define CENTER_TOL_PX          1    /* 标定收敛容差 */
#define CENTER_ITERS_MAX      12    /* 割线法最多迭代次数 */
#define CENTER_PROBE_PX       24    /* 第一步试探幅度，用来实测斜率 */

/*==== 4. 松手磁吸：拖动行程不限，落点弹回"第 n 个" =============================*/

#define EDGE_SNAP_TOP_ORDINAL     2   /* 拖到顶 → 弹回从上数第 2 个 */
#define EDGE_SNAP_BOTTOM_ORDINAL  2   /* 拖到底 → 弹回从下数第 2 个 */

/*==== 5. 快滑惯性 =============================================================*/

#define FLING_MIN_VEL        120    /* px/s，低于它当普通松手不抛 */
#define FLING_SEC            250    /* ms，速度→抛距 的投影时长 */
#define FLING_MAX_ROWS         3    /* 一次快滑最多跨几行 */
#define FLING_MAX_PX     (ROW_PITCH * FLING_MAX_ROWS)
#define FLING_VEL_SMOOTH       8    /* 低通：新样本 3/8、历史 5/8 */
#define FLING_VEL_STALE_MS    80    /* 停手超过它 ⇒ 速度作废 */

/*==== 6. 点击 / 拖动判定 =======================================================*/

#define DRAG_CLICK_IGNORE_PX  15    /* 位移超过它就忽略随之而来的 CLICKED */
#define CLICK_TRAVEL_MAX_PX   10    /* 上游侧阈值（被 port_rxroller.py 烘进补丁） */

/*==== 7. 屏外回收 =============================================================*/

#define CULL_PITCHES           4    /* 离中心超过 4 个行距就隐藏 */

#endif /* WATCH_LIST_CONFIG_H */
