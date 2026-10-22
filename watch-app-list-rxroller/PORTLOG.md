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

### 2.1 本地对照库：**整个上游工程**都在 `upstream_Rxroller/`

上游仓库一共 6 个文件、3 个 commit、无 tag、无 release（`git ls-remote --tags` 空 +
`releases.atom`/`tags.atom` 各 0 条 entry，2026-10-22 查）。整仓已克隆进本工程：

```
watch-app-list-rxroller/upstream_Rxroller/     ← git clone 原件，含 .git 全历史
├── Rxroller.c  41339 B  ← 上游是 CRLF
├── Rxroller.h   4249 B
├── LICENSE      1080 B
├── README.md    6077 B   ← 未取用（上游自己的说明）
├── CMakeLists.txt 110 B  ← 未取用
└── .gitignore   305 B    ← 未取用
```

它**不参与编译**：CMake 只 `GLOB` `src/native/*.c`，`build.ninja` 里 `upstream_Rxroller`
出现 0 次、Rxroller 编译单元只有 `src/native/rxroller/Rxroller.c.obj` 一个（已实测）。
因为带 `.git` 是嵌套仓库，根 `.gitignore` 里把整个目录排除了，不入库。

重新拉取：

```bash
git clone https://github.com/rxwind7/Rxroller.git watch-app-list-rxroller/upstream_Rxroller
```

### 2.2 ★ 行尾：入库原文是 LF，上游仓库是 CRLF（哈希对不上是这个原因）

直接 `sha256sum` 拿我们的 `.orig` 去比 `upstream_Rxroller/Rxroller.c` **是对不上的**：

```
对照库 Rxroller.c   166b648076f665bd…   （CRLF，41339 B）
入库 Rxroller.c.orig 3a364084ef499629…   （LF， 40135 B）
```

差的 1204 个字节正好等于行数 ⇒ 就是行尾。**把行尾归一化成 LF 之后两者逐字节一致**
（归一化后的上游哈希同样是 `3a364084ef49…`）。`Rxroller.h`、`LICENSE` 同理。

所以别用"哈希不等"当"改过"的证据，用脚本 —— 它还会做**整仓对账**
（上游每个文件必须有归属，出现没记账的文件就 FAIL）：

```bash
python watch-app-list-rxroller/design/compare_upstream.py --diff
```

实测输出（2026-10-22）：`上游仓库共 6 个文件`、3 条取用件全 `OK 逐字节一致`、
3 条未取用件点名、账单 `14 hunks / +49 / -16`、结论"入库原文与上游一致"。

## 3. 修改账单（补丁产物 vs 上游原文）

```
diff -u Rxroller.c.orig Rxroller.c   →   14 hunks, +49 / -16
```

机器导出的完整 diff 已入库，**放在上游件同一个目录**：
[`src/native/rxroller/Rxroller_port.diff`](src/native/rxroller/Rxroller_port.diff)（178 行，含上下文）。
同目录还有一份 [`src/native/rxroller/README.md`](src/native/rxroller/README.md)——
打开那个目录就能看到"这是谁的上游件、改了哪 14 处、怎么复核"，不用先知道本文件在哪。
下表按 `diff -u` 的 14 个 hunk 逐条对号，"上游位置"就是 hunk 头里的 `-行,数`，
可以直接 `sed -n '490,520p' Rxroller.c.orig` 跳过去看原文。

| # | 上游位置（hunk 头） | 所在函数 | 类别 | 改了什么 |
|---|---|---|---|---|
| 1 | `-1,5 +1,30` | 文件头 | 记录 + 常量 | 插入生成说明横幅；其后加三条宏：`RXROLLER_CLICK_TRAVEL_MAX 10`（#11 用）、`lv_mem_alloc/free → lv_malloc/free` 别名、`RX_SCALE_SPAN_PITCHES 3`（#5 用） |
| 2 | `-16,6 +41,7` | `rxroller_ctx_t` | 上游真 bug | 结构体加 `int32_t drag_travel` |
| 3 | `-90,11 +116,11` | `rx_get_ctx()` | 版本适配 | `wheel->user_data` 读 → `lv_obj_get_user_data()`（判空 + 返回，2 站点） |
| 4 | `-118,7 +144,7` | `rx_cleanup_internal()` | 版本适配 | `ctx->screen->user_data = NULL` → `lv_obj_set_user_data()` |
| 5 | `-202,15 +228,17` | `rx_update_item_scale()` | **能力补丁** | 衰减窗口 `icon_distance` → `× RX_SCALE_SPAN_PITCHES`（本工程 3）；**取 1 即逐字恢复上游行为** |
| 6 | `-269,13 +297,13` | `rx_anim_exec_cb()` | 版本适配 | `parent->user_data`、`icon_obj->user_data` → 访问器（2 站点） |
| 7 | `-319,8 +347,8` | `rx_dismiss_ready_cb()` | 版本适配 | `parent->user_data` 判空 + 读 → 访问器（2 站点） |
| 8 | `-368,8 +396,8` | `rx_restore_ready_cb()` | 版本适配 | 同上（2 站点） |
| 9 | `-469,6 +497,7` | `rx_event_pressing()` | 上游真 bug | 新手势分支里 `ctx->drag_travel = 0` |
| 10 | `-481,6 +510,7` | `rx_event_pressing()` | 上游真 bug | 每拍 `ctx->drag_travel += LV_ABS(ctx->offset)` |
| 11 | `-508,7 +538,10` | `rx_event_released()` | 上游真 bug | `is_click` 从 `offset == 0` 改成 `drag_travel <= 10px` |
| 12 | `-590,7 +623,7` | `rx_init_item()` | 版本适配 | `item->obj->user_data = item` → `lv_obj_set_user_data()` |
| 13 | `-704,7 +737,7` | `rx_event_delete()` | 版本适配 | `e->user_data` → `lv_event_get_user_data(e)` |
| 14 | `-810,7 +843,7` | `rxroller_create()` | 版本适配 | `ctx->screen->user_data = ctx` → `lv_obj_set_user_data()` |

**类别汇总**：版本适配（v8→9.4 不透明 `lv_obj_t` / 内存改名）= #3,4,6,7,8,12,13,14 共 8 个 hunk、
12 个 `user_data` 站点 + 2 个别名宏；能力补丁 = #5 一处；上游真 bug = #2,9,10,11 四处（同一件事）；
说明横幅 = #1。

**为什么 #2/9/10/11 算 bug 而不是适配**：上游 `offset` 是**单拍增量**（`touch_point1` 随即跟进），
`rx_event_released` 却拿它判"是不是点击" ⇒ 松手前只要停顿一拍，整段拖动就被判成点击，
上游自己再把列表动画切回松手那一行 = 用户报的"拖完自动回弹 / 滑不到底"。

**没有改的**：滚轮布局数学、弧线坐标、动画与惯性参数、吸附算法、数据结构（除新增一个字段）。
**改过运行时行为的**：只有 #5（缩放衰减窗口）与 #2/9/10/11（点击/拖动判定）两组，其余逐字保留。

### 3.1 快滑惯性：**没有**新增上游补丁（账单仍 14 hunks）

2026-10-22 加"快滑惯性"时先查过上游：`inertia_divisor` 只在配置兜底里被写了一次
（`if (ctx->config.inertia_divisor <= 0) ctx->config.inertia_divisor = 20;`），
**全文再无第二处读取** ⇒ 上游根本没有惯性，那个字段是死的；松手路径
`rx_event_released` 也只会 `rx_set_center_internal(best, 1)` 吸附到最近行。
所以整套惯性做在**本工程自己的** `src/native/watch_list_native.c`
（测速 → `row_released_cb` → `watch_list_fling()`），一行上游代码都没动。
`preflight.py` 第 4 组的"产物 == 脚本重放结果（逐字节一致）"仍然 OK，就是这条的自证。

## 4. 撤回记录（重要，别删）

移植过程中我一度判定"**上游有 bug**：`rx_calc_curve_pos()` 的 `CURVE_NONE + VERTICAL`
分支漏赋 `*x`（未初始化）"，并据此打了 `RX-PORT-FIX` 补丁、还写进了 README 与根索引。

**核对上游原文后确认该判定是错的**：`Rxroller.c.orig:171-173` 开头就是

```c
if (!x || !y) return;
*x = 0;
*y = 0;
```

两个出参都清零了。补丁已撤销，撤销当时重跑：`10 个 hunk / +38 / -15`（那是撤销后的历史数字，
**不是现在的账单**——之后又为"拖完回弹"补了 #2/9/10/11 四处，才变成当前的 `14 hunks / +49 / -16`）、
行为断言照常 PASS、两张取证图照常产出。

真正的"卡死"现象来自环境：刚链接完立刻 exec 会瞬时失败（`rc=127`，日志只剩 3 行
LVGL warning），与代码无关——重试即恢复。

★ 留这条记录的理由：**"能解释现象的补丁"不等于"正确的补丁"**。当时 `*x=0` 打上之后
卡死确实消失了，但那是重试生效，不是补丁生效；只有回头核对原文才拆得穿。

## 5. 复核方法（四条命令）

```bash
# ① 看账单
diff -u src/native/rxroller/Rxroller.c.orig src/native/rxroller/Rxroller.c
#   同一份 diff 已导出成文件，不用自己跑：src/native/rxroller/Rxroller_port.diff（178 行）

# ② 确认产物确实是脚本生成的（被手改过就会 FAIL）
python design/port_rxroller.py && python design/preflight.py

# ③ 确认上游原文没被动过
sha256sum src/native/rxroller/Rxroller.c.orig
# 期望 3a364084ef499629d97185ba800336c836187087c0337026db7af1741f97e146

# ④ 越过我们自己，直接跟**上游仓库**对（整仓 6 个文件逐个核 + 查 commit 身份）
python design/compare_upstream.py --diff
```

## 6. 回同步上游时怎么做

1. 拉新 commit，覆盖 `Rxroller.c.orig`（保持逐字原样）；
2. 跑 `python design/port_rxroller.py` —— **锚点命中数不对会直接退出并点名是哪条**，
   这就是"上游动了我们依赖的那几行"的报警器；
3. 逐条复核失败的锚点，改脚本而不是改产物；
4. 更新本文件 §1 的 commit、§2 的哈希、§3 的账单数字。
