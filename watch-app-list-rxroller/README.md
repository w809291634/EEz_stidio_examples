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

无头自证：`set WATCH_AUTOTEST=1 && set WATCH_AUTOEXIT=1 && main.exe`
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
| ★ 行为断言（无头） | `惯性收敛后中心行 = 10` **PASS**；`中心行缩放最大` **PASS**（255 vs 220）；`离中心越远单调衰减` **PASS**（220 > 185 > 150）；`快滑一次跨多行并吸附到整行` **PASS**（10 → 13，抛 250px）；`末尾快滑钳在最后一行` **PASS**（21 → 21，不越界） |
| ★ 剖面 | `[WHEEL] center10 scale: 150 185 220 255 220 185 150`（对称渐变 = 滚轮观感来源） |
| ★ 截图 | `shots/shot_init.png` / `shot_center10.png`：竖直一列、圆角图标 + 中文名、中心最大；sysmon 读数 79 FPS / 1% CPU / 3 ms |

### 5.1 取证链上的两个坑（都实测过）

- **`lv_snapshot_take` 在这棵树上不返回**（200 s 内连计时都没打出来），而同一棵树正常渲染
  是 210 拍/秒 ⇒ 卡的是快照路径。改成读显示的活动绘制缓冲 `lv_display_get_buf_active()`。
- **不要在拍屏前调 `lv_refr_now()`**：它强制整屏重绘，实测带着它取帧同样在 200 s 窗口内
  没出图（未单独计时，不下"多少秒"的结论）；正常循环只刷无效区，所以是 210 拍/秒。
  去掉它、直接拿当前活动缓冲就正常出图。
- 上游**不做屏外回收**：根对象撑满宿主后 22 行全部进入绘制计算 ⇒ 本工程在
  `watch_list_native.c` 里加了 `CULL_PITCHES=4` 的隐藏回收（真手表列表也是这么做的）。
- **无头跑会被人手污染**：`WATCH_AUTOTEST` 并不挡住 SDL 真鼠标。实测一次夹定要判
  `10 -> 13`，中途一次真实拖动把中心行改成了 11，结果量成 `11 -> 15` ⇒ FAIL。
  现在 `hal_init()` 在自证模式下 `lv_indev_delete(mouse)` 把鼠标摘掉（`WATCH_ALLOWMOUSE=1` 可恢复）。
  顺带这条也证明了测速链是通的：那次污染日志里就是 `[FLING] vel=-1292 px/s -> throw=-300 px`。

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

## 6. 两种形态怎么选

| | 本工程（纵向滚轮） | `watch-app-list-no-flow/`（蜂窝穹顶） |
|---|---|---|
| 观感 | 一列图标+名称，中心放大 | 六边形蜂窝，穹顶挤压 |
| 来源 | rxwind7/Rxroller（MIT，有源码） | SiFli SDK `watch_v9/app_mainmenu.c`（Apache-2.0） |
| 屏 | 410×502（方形表） | 368×448（SiFli 长表） |
| 适合 | 应用多于 ~8 个、要读名字 | 图标少、要"表盘式"密度 |

## 7. 已知差异 / 未做

- ★ **行缩放往中线收**：上游把 transform 轴心设在 `big_w/2`（行宽一半），所以离中心越远
  的行不仅变小、图标还向水平中线漂（截图里 `呼` 比 `天` 偏右 ~100px）。参考图是"图标列
  基本对齐"。要贴平得把轴心改成行左缘（需要再打一条 `RX-PORT-FEAT`，或改用 SIZE 缩放模式）。
- **半验**：真实鼠标快滑的手感（速度阈值 120 px/s、投影 0.25 s、上限 3 行这几个数）
  只验到了"链路通"——自证模式下真鼠标被摘掉，抛距→行数的换算与落点吸附是用
  `watch_list_fling()` 直接喂 -250 px 断言的；真手滑的**观感**轻重还得人上手调。
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
