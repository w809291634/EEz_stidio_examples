# 本目录 = 上游开源件 Rxroller 的落地点

> **一句话**：这里 5 个文件，只有 `Rxroller.c` 被改过，改了什么全在下面那张表里，
> 逐字对照件是同目录的 [`Rxroller_port.diff`](Rxroller_port.diff)。
> 权威台账在工程根 [`PORTLOG.md`](../../../../PORTLOG.md)，整仓上游克隆在
> [`upstream_Rxroller/`](../../../../upstream_Rxroller/)。

## 上游身份

| 项 | 值 |
|---|---|
| 仓库 | https://github.com/rxwind7/Rxroller （MIT） |
| commit | `8928104b2aa7961e2d2d44cd50f01cb3a1747088` = `master` 顶点 |
| 上游形态 | 标称 LVGL **v8**；本工程编到 **9.4** |
| tag / release | **无**（整仓只有 3 个 commit，全在 2026-06-09）⇒ 只能按 SHA 钉版本 |

## 本目录 5 个文件各自的身份

| 文件 | 身份 | 哈希（SHA256 前 12） |
|---|---|---|
| `Rxroller.c.orig` | **上游原文，逐字未改**（行尾归一成 LF，见下） | `3a364084ef49` |
| `Rxroller.h` | **上游原文，未改一个字节** | `9ffe79f8de34` |
| `LICENSE` | 上游原文（MIT 要求随库保留） | `5ee83fa2c52b` |
| `Rxroller.c` | ★ **补丁产物 = `.orig` + 14 hunks**，由 [`design/port_rxroller.py`](../../../../design/port_rxroller.py) 生成，**勿手改** | `48a297ccd7f2` |
| `Rxroller_port.diff` | 上面那条 diff 的导出件（191 行），给人眼看 | —— |

★ 为什么原文改名 `.orig`：PC_SIM 的 CMake 用 `GLOB_RECURSE src/native/*.c` 收源码，
两个 `.c` 会重复定义符号。`.orig` 不被收集，又能就地 diff。

## 改了什么：14 个 hunk 逐条（`diff -u Rxroller.c.orig Rxroller.c` = 14 hunks / +61 / −18）

"上游行"就是 hunk 头里的 `-行`，可以直接 `sed -n '180,195p' Rxroller.c.orig` 跳过去看原文。

| # | 上游行 → 新行 | 所在函数 | 类别 | 改了什么 |
|---|---|---|---|---|
| 1 | 1 → 1–39 | 文件头 | 记录+常量 | 生成说明横幅；另加 4 条宏：`RXROLLER_CLICK_TRAVEL_MAX 10`、`lv_mem_alloc/free→lv_malloc/free` 别名、`RX_SCALE_SPAN_PITCHES 3`、`RXROLLER_SCALE_MAX 384` |
| 2 | 16 → 50 | `rxroller_ctx_t` | 🐞 上游真 bug | 结构体新增 `int32_t drag_travel` |
| 3 | 90 → 125 | `rx_get_ctx` | 版本适配 | `wheel->user_data` 读 → `lv_obj_get_user_data()`（2 站点） |
| 4 | 118 → 153 | `rx_cleanup_internal` | 版本适配 | `ctx->screen->user_data = NULL` → `lv_obj_set_user_data()` |
| 5 | 202 → 237–255 | `rx_update_item_scale` | ⭐ 能力补丁 | ① 衰减窗口 `icon_distance` → `× RX_SCALE_SPAN_PITCHES(3)`；② 两处写死的 `255` → `RXROLLER_SCALE_MAX(384)`。**取 1 / 255 即逐字恢复上游行为**，两半的值都来自 `watch_list_config.h` |
| 6 | 269 → 307 | `rx_anim_exec_cb` | 版本适配 | `parent->user_data`、`icon_obj->user_data` → 访问器（2 站点） |
| 7 | 319 → 357 | `rx_dismiss_ready_cb` | 版本适配 | `parent->user_data` 判空 + 读 → 访问器（2 站点） |
| 8 | 368 → 406 | `rx_restore_ready_cb` | 版本适配 | 同上（2 站点） |
| 9 | 469 → 507 | `rx_event_pressing` | 🐞 上游真 bug | 新手势分支里 `ctx->drag_travel = 0` |
| 10 | 481 → 520 | `rx_event_pressing` | 🐞 上游真 bug | 每拍 `ctx->drag_travel += LV_ABS(ctx->offset)` |
| 11 | 508 → 548–557 | `rx_event_released` | 🐞 上游真 bug | `is_click` 从 `offset == 0` 改成 `drag_travel <= 10px` |
| 12 | 590 → 633 | `rx_init_item` | 版本适配 | `item->obj->user_data = item` → `lv_obj_set_user_data()` |
| 13 | 704 → 747 | `rx_event_delete` | 版本适配 | `e->user_data` → `lv_event_get_user_data(e)` |
| 14 | 810 → 853 | `rxroller_create` | 版本适配 | `ctx->screen->user_data = ctx` → `lv_obj_set_user_data()` |

**分类合计**：版本适配 8 处（12 个 `user_data` 站点 + 2 个别名宏）· 能力补丁 1 处（#5，两半都在同一个函数）·
上游真 bug 4 处（#2/9/10/11 是同一件事的 4 个落点）· 说明横幅+常量 1 处。

**没动的**：滚轮布局数学、弧线坐标、动画/惯性参数、吸附算法、数据结构（除新增一个字段）。
改动占比 `61 / 1247 ≈ 4.9%`。

### 🐞 #2/9/10/11 为什么算上游 bug 而不是适配

上游 `offset` 是**单拍增量**（`touch_point1` 随即跟进），`rx_event_released` 却拿它判
"是不是点击" ⇒ 松手前只要停顿一拍，整段拖动就被判成点击，上游自己再把列表动画切回
松手那一行 = 现象上的"拖完自动回弹 / 滑不到底"。

### ⭐ 首尾行磁吸落点**没有**做成上游补丁（本目录账单因此保持 14 个 hunk）

需求是"允许一路拖到最上/最下，松手后弹回第 n 个"。若照上一版去改
`rx_clamp_distance` 的钳位范围，拖动行程就被一起锁死了 —— 与需求相反。
所以落点纠正放在本目录之外的 `watch_list_snap_edge()`（行 RELEASED 触发一次），
**本目录一行都没为它改**。

### ⭐ 上游没有惯性（本工程要惯性所以自己做）

`rxroller_config_t.inertia_divisor` 是**死字段**：全文只有配置兜底那一次赋值
（`if (ctx->config.inertia_divisor <= 0) ... = 20;`），再无第二处读取。
松手路径也只 `rx_set_center_internal(best, 1)` 吸附到最近行。
⇒ 快滑惯性整套做在**本目录之外**的
[`../../widgets/applist/watch_list_native.c`](../../widgets/applist/watch_list_native.c)（测速 → `row_released_cb` → `watch_list_fling()`），
**本目录的上游账单没有因此变化（当时仍是 14 个 hunk）**。

## 自己核对（三条，任选）

```bash
# ① 就地看改了什么
diff -u src/native/third_party/rxroller/Rxroller.c.orig src/native/third_party/rxroller/Rxroller.c
#   或直接打开同目录的 Rxroller_port.diff

# ② 确认产物确实是脚本生成的（被手改过就 FAIL）
python design/port_rxroller.py
design/sim_cmake/run_sim.bat build

# ③ 越过我们自己，直接跟上游整仓对（归一化行尾后逐字节）
python design/compare_upstream.py --diff
```

★ **别用 `sha256sum` 直接比**：上游仓库是 **CRLF**（`Rxroller.c` 41339 B / `166b6480…`），
本目录 `.orig` 归一成了 **LF**（40135 B / `3a364084…`），差的 1204 字节正好等于行数。
归一化行尾后两者逐字节一致。详见 [`PORTLOG.md` §2.2](../../../../PORTLOG.md)。

## 撤回记录（别删）

曾判定"上游 `rx_calc_curve_pos()` 的 `CURVE_NONE + VERTICAL` 分支漏赋 `*x`"并据此打了补丁，
核对上游原文（`Rxroller.c.orig:171-173` 开头就 `*x = 0; *y = 0;`）后确认**判定是错的**，
补丁已撤销。当时的"卡死"是刚链接完立刻 exec 的瞬时失败（`rc=127`），与代码无关。
完整经过见 [`PORTLOG.md` §4](../../PORTLOG.md)。
