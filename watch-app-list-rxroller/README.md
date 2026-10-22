# watch-app-list-rxroller —— 手表纵向滚轮应用列表（移植 rxwind7/Rxroller）

一句话：把开源 LVGL 滚轮件 **Rxroller** 搬到本仓库的 LVGL 9.4 上，做出参考图
（桌面 Design Watch 工程的 AppList）那种**纵向一列、中心行最大、上下按距离渐变、
能甩动能吸附**的应用列表；EEZ 只画外壳，列表本体是 native C，**全程零 Flow**。

与 `watch-app-list-no-flow/`（蜂窝穹顶，SiFli 主菜单）的关系：**两种形态各一个工程**，
不是替代关系。选型见 §6。

## 1. 上游与许可

| 项 | 值 |
|---|---|
| 上游 | https://github.com/rxwind7/Rxroller `master` |
| 许可 | **MIT**（`src/native/rxroller/LICENSE` 随库入库，可粘代码） |
| 体量 | `Rxroller.c` 1204 行 + `Rxroller.h` 4.2KB，单文件、无依赖扩展 |
| 标称版本 | LVGL **v8**（本工程把它跑到 **9.4**） |
| 上游成熟度 | ★ 诚实口径：**0 star、单人维护、无 CI 无测试**。形态成熟（滚轮该有的都有），工程不成熟 ⇒ 所以本工程的验收全靠行为断言兜（见 §5） |

上游原文**逐字保留**在 `src/native/rxroller/Rxroller.c.orig`（`.orig` 不被 CMake 的
`*.c` glob 收，不会重复定义符号）；`Rxroller.c` 由 `design/port_rxroller.py` 生成。
`diff Rxroller.c.orig Rxroller.c` 就是完整的移植账单。

## 2. no-flow 口径与"为什么主体不在 EEZ 里"

```
settings.general.flowSupport = False
settings.build.generateSourceCodeForEezFramework = False
变量表 gvs = []（no-flow 下 EEZ 变量必须 native，而状态文本由 native 直接写 label）
屏幕 410 x 502（与 Design Watch 参考工程同口径）
```

★ **出 EEZ 的判断依据**（不是"我更喜欢 C"）：
- `scroll_snap` 轴：asar 实测 `scroll_snap` 只出现在 WASM 符号表与 LVGL 常量字符串表里，
  **没有 widget 属性定义** ⇒ EEZ 侧设不了 snap；
- 逐子项 `transform_scale`：同理不在属性面内。
参照工程（Design Watch）用 Flow 做到了，代价是 **97 个 action 写 / 15ms（66fps）**；
这里 native 一次遍历解决，实测 **79 FPS、1% CPU、3 ms/帧**（截图右下角的 sysmon 读数）。

## 3. 移植账单（补丁全部在 `design/port_rxroller.py`，可重放）

| 类别 | 内容 |
|---|---|
| 版本适配 | 12 处 `obj->user_data` / `e->user_data` → `lv_obj_get_user_data()` / `lv_obj_set_user_data()` / `lv_event_get_user_data()`（v9 把 `lv_obj_t` 变不透明） |
| 版本适配 | `lv_mem_alloc` / `lv_mem_free` → `lv_malloc` / `lv_free` 别名宏（9.4 改名，`src/stdlib/lv_mem.h:69/97`；不补只报"隐式声明"，链接期才炸） |
| **上游真 bug（已修）** | `rx_event_released` 用 `ctx->offset == 0` 判点击，而 `offset` 是**单拍增量** ⇒ 松手前停顿一拍就把整段拖动判成点击并回弹。修法见 `PORTLOG.md` §3 #7。|
| 撤回一条误判 | 中途我曾判"`rx_calc_curve_pos` 的 `NONE+VERTICAL` 分支漏赋 `*x`（未初始化）"并打了 `RX-PORT-FIX` 补丁。**核对原文后确认是错的**：上游函数开头就有 `*x = 0; *y = 0;`（`Rxroller.c.orig:172-173`）。真正的"卡死"是刚链接完立刻 exec 的瞬时失败（`rc=127`、日志只剩 3 行 warning），与代码无关。该补丁已撤销，撤销后重跑：10 hunks、+37/−15，三条断言仍 3/3 PASS、两张图照常出。**留这条撤回记录，是因为它说明"能解释现象的补丁"不等于"正确的补丁"** |
| **能力补丁** | `rx_update_item_scale()` 的衰减窗口上游写死 **1 个行距**（只有中心行放大，相邻行直接落到 `edge_scale`）。参考图是好几行连续渐变 ⇒ 窗口参数化为 `RX_SCALE_SPAN_PITCHES`（本工程 3；取 1 即恢复上游行为）。实测剖面：`150 185 220 255 220 185 150` |

其余上游代码一行未动。`preflight.py` 第 4 组用**逐字节重放比对**守住这条：
产物 ≠ 脚本重放结果 ⇒ 直接 FAIL 并指出第几行，杜绝"绕过脚本手改上游件"。

## 4. 工程结构 / 怎么跑

```
watch-app-list-rxroller/
├── FIXLOG.md                        ← ★ 错误修复记录（19 条：现象/根因/修复/证据/防再犯）
├── PORTLOG.md                       ← ★ 上游件改动账单
├── build_example.py                 ← EEZ 外壳设计源（410x502 + 字体条目 + 覆盖自检）
├── design/
│   ├── apps.py                      ← ★ 22 行应用表的唯一事实源
│   ├── gen_assets.py                ← 由表生成 22 个图标 .c + app_rows.{c,h}
│   ├── port_rxroller.py             ← 上游 v8 -> 9.4 补丁（可重放，preflight 比对它）
│   ├── compare_upstream.py          ← ★ 拿 upstream_Rxroller/ 整仓对账 + 逐字节核原文
│   ├── cli_build.py / gen_font.py / audit_chars.py / preflight.py
│   └── sim_cmake/                   ← main.c（含 WATCH_AUTOTEST 取证）+ lv_conf.h(SNAPSHOT=1)
├── upstream_Rxroller/               ← ★ 上游仓库完整克隆（6 文件 + .git 全历史），不编译、不入库
├── src/native/
│   ├── rxroller/{Rxroller.c.orig,Rxroller.c,Rxroller.h,LICENSE}
│   │        ├── README.md           ← ★ 就地说明：这是谁的上游件、改了哪 14 处、怎么复核
│   │        └── Rxroller_port.diff  ← ★ 就地对照件：.orig -> Rxroller.c 的逐字 diff
│   ├── watch_list_native.{c,h}      ← 接线：配置 + 行内容 + 点击 + 快滑惯性 + 屏外回收 + 自证口
│   ├── app_rows.{c,h} + icons/      ← 生成的表与图标
└── src/ui/                          ← EEZ 产物（★ 没有 eez-flow.*，这正是判据）
```

```bat
python build_example.py            && rem UI_CJK 由 design/apps.py 算，改应用名不会漏字
python design\cli_build.py         && rem EEZ CLI 构建
python design\port_rxroller.py     && rem 从上游原文重放补丁
python design\gen_assets.py        && rem 22 个图标 + app_rows
python design\gen_font.py          && rem ★ 必须在 cli_build 之后（P-0140）
python design\audit_chars.py       && rem EEZ 侧逐字审计
python design\preflight.py         && rem ★ 六组硬门禁
python design\compare_upstream.py --diff   && rem ★ 与 upstream_Rxroller/ 整仓对账
双击 design\sim_cmake\run_sim.bat  && rem 起窗口，鼠标拖动/点击
```

★ **在 EEZ Studio GUI 里点 Build 也算一步生成链**：GUI 会**自己烘字体**（CLI 不会，见 P-0140），
所以 GUI 构建后 `src/ui/fonts/ui_font_cn14.c` 会变成 EEZ 那份 `--range` 配方的产物。
两份配方目前覆盖完全相同（155 码点），但**别靠记忆认定它们一致** ——
preflight 第 3 组会解析字体文件头部的 `Opts:` 行反查真实覆盖，被换掉时会当场 FAIL。

无头自证：`set WATCH_AUTOTEST=1 && set WATCH_AUTOEXIT=1 && main.exe`
真 indev 合成拖动（走 SDL 事件队列 → LVGL indev → 行/根回调）：`set WATCH_DRAGTEST=1 && main.exe`
（辅助开关：`WATCH_NOSHOT=1` 跳拍屏、`WATCH_TICKTRACE=1` 打节拍、`WATCH_ROWDEBUG=1` 打逐行坐标、
`WATCH_ALLOWMOUSE=1` 把真鼠标接回来——默认自证模式下鼠标是被摘掉的，见 §5.1）

## 5. 实测状态（2026-10-22）

| 检查 | 结果 |
|---|---|
| EEZ CLI 构建 | `Build successfully finished`，`No error and no warning detected` |
| no-flow 判据 | `src/ui/` 无 `eez-flow.*`；`ui.c` 走 `create_screens()`；`objects.list_host/lbl_status/lbl_title` 在位 ✓ |
| 分辨率对齐 | EEZ 410×502 == `SIM_W/SIM_H` ✓ |
| 字体链 | `ui_font_cn14.c` 70,917 B（子集 155 字 = ASCII + 44 汉字）；native 上屏用字 54 个全在子集内 ✓ |
| 上游件可审计 | 产物 == `port_rxroller.py` 重放结果（逐字节一致）✓ |
| 表 × 图标 | 22 项、22 个图标、`app_rows.c` 与表同步 ✓ |
| PC_SIM 编译链接 | `build succeeded`（含 22 个图标编译单元）✓ |
| ★ 行为断言（无头，11 条行级 + 2 条真拖动 = 13/13 PASS） | 基线：`中心行=10`、`中心行缩放最大`(255>220)、`离中心越远单调衰减`(220>185>150)；惯性：`快滑一次跨多行并吸附到整行`(10→13，抛 250px)、`末尾快滑钳住不越界`(20→20)；真 indev 合成拖动：`真拖动到顶/到底：松手弹回第 n 个`(→1、→20)；样式：`中心图标落在横向 1/3`(x=136=410/3)、`起步不吸在首行`(=1)；磁吸落点：`首行/末行可以拖到正中（行程不限）`(→0、→21)、`松手弹回顶部第 n 个`(0→1)、`松手弹回底部倒数第 n 个`(21→20) |
| ★ 剖面 | `[WHEEL] center10 scale: 150 185 220 255 220 185 150`（对称渐变 = 滚轮观感来源） |
| ★ 截图 | `shots/shot_init.png` / `shot_center10.png` / `shot_round.png`：竖直一列、圆角图标 + 中文名、中心最大、**主屏胶囊遮罩生效**；sysmon 读数 82 FPS / 2% CPU / 2 ms |
| ★ 表盘外形 | 主屏 `radius=LV_RADIUS_CIRCLE` + `clip_corner=true` **由 EEZ 生成**（screens.c 可反查），native 零改动；410×502 ⇒ 胶囊（左右半圆 + 上下 92px 直边），非正圆 |
### 5.1 踩过的坑

**全部挪到 [`FIXLOG.md`](FIXLOG.md)** —— 那才是记这个的地方，源码注释里只留
`见 FIXLOG FX-###` 一行指路。取证链相关的几条：

| 编号 | 一句话 |
|---|---|
| FX-005 | 快照不返回 → 改读活动绘制缓冲；且禁止先调 `lv_refr_now()` |
| FX-012 | 合成 SDL 拖动：上游 `SDL_MOUSEBUTTONDOWN` 读的是 `motion.x/y` 不是 `button.x/y` |
| FX-013 | 无头自证必须摘掉真鼠标，否则一次手滑就把观测量歪 |
| FX-016 | 字体覆盖门禁要比产物、不比声明（EEZ GUI 会自己烘字体） |
| FX-017 | 改宏后必须 `touch` 源文件，否则 ccache 让 ninja 只重链不重编 |
| FX-018 | `.orig` 与上游哈希对不上是 CRLF/LF，不是被改过 |

### 5.2 快滑惯性（本工程加，上游没有）

上游其实**没有惯性**：`rxroller_config_t.inertia_divisor` 是死字段——`Rxroller.c` 只在
配置兜底里写过一次 `if (ctx->config.inertia_divisor <= 0) ... = 20;`，全文再无第二处读取
（`grep -n inertia_divisor Rxroller.c` 只命中这一行）。松手时 `rx_event_released` 走的是
`rx_set_center_internal(best, 1)`，`best` 就是"当前最近行" ⇒ 永远只吸附、不抛出。
所以惯性整套做在我们自己的 `watch_list_native.c` 里，**上游补丁账单不变（仍 14 hunks）**。

三段：

| 环节 | 做法 | 为什么这么写 |
|---|---|---|
| 测速 | `LV_EVENT_PRESSING` 逐拍差分 `dy/dt`，低通 3/8；停手超过 80 ms 且 y 没变 ⇒ 速度清零 | 只看最后一拍会被抖动支配；不清零则"拖到位、停一下再松手"会按残留速度乱抛 |
| 判抛 | `|v| < 120 px/s` 不抛 | 120×0.25s=30px，不足 1/3 行距，本来就吸附回原行，留着只会误抛 |
| 抛出 | `v×0.25s` 投影成 px，钳在 ±3 行；换算成整行增量后 `rxroller_set_center(anim)` | 不能用 `rxroller_scroll(px)`：上游动画分支里 offset 只参与算时长（`Rxroller.c:725`），目标位置恒等于当前最近行 |

★ 抛出必须 `lv_async_call` 延一拍。上游也在行上注册了 `LV_EVENT_RELEASED`
（`Rxroller.c:638`，注册在 `create_cb` 之后 ⇒ 它的 cb 跑在我们的后面），同步调
`set_center` 会被它随后那次"吸附"覆盖掉。

符号约定：`watch_list_fling(px)` 的 px 与手指同向，**正=往下划=看更早的行=行号减小**
（`rx_event_pressing` 是 `distance += offset`，行号小的 distance 为负，所以正向把中心往小行拉）。

### 5.3 两条样式规则（横向 1/3 + 松手弹回第 n 个）

| 规则 | 落点 | 实测 |
|---|---|---|
| 中心行的图标放在**屏宽 1/3** 处（口径已确认是横向） | `watch_list_align_center_x()` | 图标中心 x=**136** = 410/3；`pad_left` 由 140 标定到 **48** |
| **允许一路拖到最上/最下，松手后弹回"第 n 个"**（顶部第 n 个 / 底部倒数第 n 个，序号从 1 起） | 宏 `EDGE_SNAP_TOP_ORDINAL` / `EDGE_SNAP_BOTTOM_ORDINAL`（当前都是 2）+ `watch_list_snap_edge()` | 行程真的放开：能停在行 0 / 行 21；松手弹回 **1 / 20**（= 第 2 个 / 倒数第 2 个） |

★ 1/3 定位用**一次性闭环标定**（割线法，实测斜率，最多 12 次 `lv_obj_update_layout`），
不是写死一个 `pad_left`：行是在"扣掉左内边距后的内容框"里居中的，还叠着边框固定偏差
（实测锚点 140 却量出行左缘 117，差 8px），写死值一改 `ROW_W` 或图标行内偏移就会飘。
只在建轮时跑，**不是逐拍轮询**。

★ 为什么"弹回第 n 个"落在 native 而不是上游钳位：口径要求**拖动行程放开**。
上一版改过上游 `rx_clamp_distance` 的钳位范围（补丁 #15），实测确实挡得住首尾行，
但那**同时把拖动行程也锁死了** —— 与"允许拖到顶"直接冲突，所以整条补丁已撤销，
上游账单回到 14 hunks（见 [`PORTLOG.md` §3](PORTLOG.md) 末段）。
现在只有松手那一次纠正：行 `RELEASED` → `lv_async_call` 延一拍，避开上游随后那次吸附。

★ 手势回调**同时挂在行和滚轮根对象上**。只挂行会静默失效：屏外回收把远处行置了
`HIDDEN`，LVGL 跳过隐藏对象 ⇒ 手指按在"隐藏行/空白"上时目标是根对象，行回调一次都不跑。
用户报的"滑到最上面不返回"就是这个（`shot_drag_top.png` 是同一条夹具的取证图）。

★ 判据仍按"绕过我的兜底还能过"来设计，只是这次绕的是**上游**：
夹具先 `watch_list_center_no_clamp(0 / 21)` 断言行程真的放开（能停在行 0 / 行 21），
再 `watch_list_snap_edge()` 断言弹回第 n 个。单变量把 `EDGE_SNAP_TOP_ORDINAL` 改成 3
⇒ 落点从"第 2 个"变"第 3 个"、区间变 `[2,20]`，证明是**宏驱动**不是写死。

★ 改宏后**必须 `touch` 源文件再构建**：实测 ccache + mtime 会让 ninja 只重链不重编，
第一遍单变量测试因此读了旧二进制、假复现成"宏没生效"。

### 5.4 表盘外形：胶囊圆角，**全部在 EEZ 属性面**

口径：EEZ 是窗口框架，外形必须由 EEZ 生成、仿真器只靠 `ui_init()` 就生效，native 一行都不加。

| 层 | 做了什么 | 证据 |
|---|---|---|
| EEZ 设计源 | 主屏 style `radius = LV_RADIUS_CIRCLE(32767)` + `clip_corner = true`（[build_example.py](build_example.py) 的 `SCREEN_RADIUS`） | 生成产物 `src/ui/screens.c`：`lv_obj_set_style_radius(obj, 32767, …)` + `lv_obj_set_style_clip_corner(obj, true, …)` |
| native | **零改动** | 门禁 `native 侧没有偷偷补 radius/clip_corner` |
| 仿真器 | 照旧 `ui_init()` / `ui_tick()` | main.c:223 / 232 |

★ 两个必须记住的事实：

1. **`settings.general.circularDisplay` 不生成任何代码**。在 EEZ Studio 的 `app.asar` 里这个字段
   8 处命中全在 React 预览渲染层（给预览 DOM 加 CSS `border-radius`），代码生成器 0 处
   ⇒ 只勾它，仿真器永远是方的。控件级 `radius` + `clip_corner` 才是真的（属性定义在
   MISCELLANEOUS 样式组，`description: "Enable to clip the overflowed content on the rounded corner"`）。
   只有 `radius` 没有 `clip_corner` 也不行 —— 那只会把背景画圆，子对象照样糊到角外。
2. **410×502 上 `LV_RADIUS_CIRCLE` 出来的是胶囊，不是正圆**：半径被钳到短边一半 205，
   左右两端成半圆、上下各留 `502-410 = 92px` 直边（用 canvas 采样验证过）。要正圆得用方形分辨率。

★ 加了圆角后**标题和状态行会被整个裁掉**（它们原本贴在直角上 `(0,8)`）。外壳元素的落点
按胶囊弧算：半宽 `h` 处需要的深度 `d = R - sqrt(R² - h²)`，取 `h=140` ⇒ `d≈56`，
于是标题 `(65,56)`、状态行 `(65,428)`。这条算式在 `build_example.py` 里，
preflight 第 1 组会拿它反查每个标签的左上/右上角是否真在弧内。

取证：`shots/shot_round.png` —— 四角已被裁掉、标题与状态行完整可见、中心图标仍在 1/3 处。

### 5.5 结论撤回记录

本工程有两条"先下结论、后被推翻"的记录，都已归档：

- **误判上游 `rx_calc_curve_pos` 漏初始化 `*x`** → 见 [`FIXLOG.md`](FIXLOG.md) FX-006
  与 [`PORTLOG.md` §4](PORTLOG.md)（含"为什么当时看起来修好了"）。
- **误判"EEZ 属性面出不了 `clip_corner`"** → 见 FX-014 / §5.4；
  错因是只 grep 了驼峰 `clipCorner`，实际属性名是 snake_case。

## 6. 两种形态怎么选

| | 本工程（纵向滚轮） | `watch-app-list-no-flow/`（蜂窝穹顶） |
|---|---|---|
| 观感 | 一列图标+名称，中心放大 | 六边形蜂窝，穹顶挤压 |
| 来源 | rxwind7/Rxroller（MIT，有源码） | SiFli SDK `watch_v9/app_mainmenu.c`（Apache-2.0） |
| 屏 | 410×502（方形表） | 368×448（SiFli 长表） |
| 适合 | 应用多于 ~8 个、要读名字 | 图标少、要"表盘式"密度 |

## 7. 已知差异 / 未做

- ★ **行缩放往中线收**（和 1/3 定位叠加后更明显）：上游把 transform 轴心设在 `big_w/2`
  （行宽一半），所以离中心越远的行不仅变小、图标还向水平中线漂 —— 实测第 3 外的行
  （`呼`）图标中心比中心行（`天`）偏右 ~75px。参考图是"图标列基本对齐"。
  要贴平得把轴心改成行左缘（需要再打一条 `RX-PORT-FEAT`，或改用 SIZE 缩放模式）。
- **半验**：真实鼠标快滑的手感（速度阈值 120 px/s、投影 0.25 s、上限 3 行这几个数）
  只验到了"链路通"——自证模式下真鼠标被摘掉，抛距→行数的换算与落点吸附是用
  `watch_list_fling()` 直接喂 -250 px 断言的；真手滑的**观感**轻重还得人上手调。
  首尾磁吸同理：无头是"请求行 0/21 看有没有被拉回"，真正拖到头的跟手感觉要人试。
  真机（SiFli 面板）编译未做。
- **未做**：图标自身动画（自转/心跳/步态那套 66fps 参数通道，Design Watch 有）。

## 8. 相关

- 值得回报给上游的有两条：**缩放衰减窗口写死 1 个行距**（`rx_update_item_scale`），
  想要"多行连续渐变"就得改；**`inertia_divisor` 是死字段**（只被兜底赋值、从不被读），
  配置它没有任何效果，文档却列在惯性参数里。
  其余是 v8→v9 的适配，不是 bug。
  （我曾报过第三条"`rx_calc_curve_pos` 漏初始化 `*x`"——核对原文后撤回，见 §3 末行。）
- 中文字体铁律：`示例工程模板说明.md` 坑表 + `flow-examples/README.md` §3
- no-flow 口径的由来：`app-wifi-scan-flow-no-flow/README.md`
