# PORTLOG —— 上游开源件 Rxroller 的修改记录

> 这份文件是**唯一权威账单**。任何对本目录上游件的改动都必须先落到
> `design/port_rxroller.py`，再在这里记账；`preflight.py` 第 4 组会逐字节比对
> "脚本重放结果 vs 磁盘产物"，绕过本流程的手改会当场 FAIL。

## 1. 上游身份（可核对）

| 项 | 值 |
|---|---|
| 仓库 | https://github.com/rxwind7/Rxroller |
| 分支 / commit | `master` @ **`8928104b2aa7961e2d2d44cd50f01cb3a1747088`**（`git ls-remote` 取得） |
| 许可 | **MIT**（`LICENSE` 随库入库，blob 见下） |
| 获取时间 | 2026-10-21 |
| 标称 LVGL 版本 | v8（本工程跑到 9.4） |
| 上游文件形态 | `Rxroller.c` 1204 行 + `Rxroller.h`，单文件、无第三方依赖 |

## 2. 入库文件的 SHA256（改一个字节就能查出来）

```
3a364084ef499629d97185ba800336c836187087c0337026db7af1741f97e146  src/native/rxroller/Rxroller.c.orig   ← 上游原文，逐字未改
9ffe79f8de34478791ee57c95921603287e841708765bf75a0f255e809971bd3  src/native/rxroller/Rxroller.h         ← 上游原文，未改
5ee83fa2c52beb32c6bd27b3dc01b33be72075b514b1359667a32b16957080c9  src/native/rxroller/LICENSE            ← 上游原文
26732cd3eda6…（重算见 §5 命令；每次改补丁都要回来更新这一行）  src/native/rxroller/Rxroller.c         ← 补丁产物（由脚本生成）
```

★ 为什么上游原文改名成 `.orig`：PC_SIM 的 CMake 用 `GLOB_RECURSE src/native/*.c` 收源码，
两个 `.c` 会重复定义符号。`.orig` 不被收集，又能就地做 diff。

## 3. 修改账单（补丁产物 vs 上游原文）

```
diff -u Rxroller.c.orig Rxroller.c   →   14 hunks, +49 / -16
```

| # | 上游位置 | 类别 | 改了什么 | 为什么 |
|---|---|---|---|---|
| 1 | 文件头 | 记录 | 插入生成说明横幅（指回本 PORTLOG 与 port 脚本） | 产物必须自带来源，翻到文件就知道去哪核对 |
| 2 | `#include "Rxroller.h"` 之后 | 版本适配 | 加 `lv_mem_alloc→lv_malloc`、`lv_mem_free→lv_free` 别名宏 | LVGL 9 改了名（`src/stdlib/lv_mem.h:69/97`）；不补只报"隐式声明"，**链接期才炸**，最难查 |
| 3 | `rx_get_ctx()` | 版本适配 | `wheel->user_data` 读 → `lv_obj_get_user_data(wheel)`（含判空那处） | v9 把 `lv_obj_t` 变不透明类型，直接摸字段编不过 |
| 4 | `rx_cleanup_internal()` | 版本适配 | `ctx->screen->user_data = NULL` → `lv_obj_set_user_data(...)` | 同上 |
| 5 | `rx_update_item_scale()` | **能力补丁** | 衰减窗口 `icon_distance` → `icon_distance * RX_SCALE_SPAN_PITCHES`（本工程 3） | 上游只放大中心行，相邻行直接落到 `edge_scale`；参考图要连续渐变。**取 1 即完全恢复上游行为** |
| 6-10 | `rx_item_event_cb` / `rx_event_pressing` 等 7 处 | 版本适配 | `parent->user_data`、`icon_obj->user_data`、`item->obj->user_data=`、`e->user_data` → 对应访问器 | 同 #3，合计 12 个 `user_data` 站点 |
| 7 | `rx_event_pressing` + `rx_event_released` + ctx 结构体 | **上游真 bug（RX-PORT-FIX）** | 新增 `ctx->drag_travel` 按拍累计位移；`is_click` 从 `offset == 0` 改成 `drag_travel <= RXROLLER_CLICK_TRAVEL_MAX(10px)` | 上游 `offset` 是**单拍增量**（`point1` 随即跟进），用它判点击 ⇒ 松手前只要停顿一拍，整段拖动被判成点击，上游自己把列表动画切到松手那一行 = 用户报的“拖完自动回弹/滑不到底” | 

**没有改的**：滚轮布局数学、缩放曲线、动画与惯性参数、吸附算法、数据结构。
**改过的行为**：只有 #5（缩放衰减窗口）与 #7（点击/拖动判定）两处，其余逐字保留。

## 4. 撤回记录（重要，别删）

移植过程中我一度判定"**上游有 bug**：`rx_calc_curve_pos()` 的 `CURVE_NONE + VERTICAL`
分支漏赋 `*x`（未初始化）"，并据此打了 `RX-PORT-FIX` 补丁、还写进了 README 与根索引。

**核对上游原文后确认该判定是错的**：`Rxroller.c.orig:171-173` 开头就是

```c
if (!x || !y) return;
*x = 0;
*y = 0;
```

两个出参都清零了。补丁已撤销，撤销后重跑：`10 hunks / +38 / -15` 不变、
三条行为断言仍 3/3 PASS、两张取证图照常产出。

真正的"卡死"现象来自环境：刚链接完立刻 exec 会瞬时失败（`rc=127`，日志只剩 3 行
LVGL warning），与代码无关——重试即恢复。

★ 留这条记录的理由：**"能解释现象的补丁"不等于"正确的补丁"**。当时 `*x=0` 打上之后
卡死确实消失了，但那是重试生效，不是补丁生效；只有回头核对原文才拆得穿。

## 5. 复核方法（三条命令）

```bash
# ① 看账单
diff -u src/native/rxroller/Rxroller.c.orig src/native/rxroller/Rxroller.c

# ② 确认产物确实是脚本生成的（被手改过就会 FAIL）
python design/port_rxroller.py && python design/preflight.py

# ③ 确认上游原文没被动过
sha256sum src/native/rxroller/Rxroller.c.orig
# 期望 3a364084ef499629d97185ba800336c836187087c0337026db7af1741f97e146
```

## 6. 回同步上游时怎么做

1. 拉新 commit，覆盖 `Rxroller.c.orig`（保持逐字原样）；
2. 跑 `python design/port_rxroller.py` —— **锚点命中数不对会直接退出并点名是哪条**，
   这就是"上游动了我们依赖的那几行"的报警器；
3. 逐条复核失败的锚点，改脚本而不是改产物；
4. 更新本文件 §1 的 commit、§2 的哈希、§3 的账单数字。
