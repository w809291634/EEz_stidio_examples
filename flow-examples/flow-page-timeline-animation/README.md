# flow-page-timeline-animation —— 页面动画时间线 + `Animate` 件（EXAMPLE_PLAN ⑮）

> **演示点**：EEZ Flow 的**页面时间线**这条动效主路——关键帧挂在控件上、页面只有一个游标、
> `Animate` 件推游标，倒放/跳帧/放完通知全都是游标语义的副产品。全程 EEZ 内实现，零 native C。
> 手册：P3 · P.24–25（Animation timeline editor）+ A2 Animate · P.13 + `Flow.pageTimelinePosition` · P.64。

## 1. 机制（三层证据，别当黑盒）

| 层 | 事实 | 出处 |
|---|---|---|
| 数据模型 | `timeline` 是**控件（Widget）级**数组，元素是关键帧 `{start,end,<属性>:{enabled,value,easingFunction}}`；页面级只有一个游标 | 装机包 `Widget.classInfo` + `TimelineKeyframe` 类字段 |
| 代码生成 | `lvglBuildPageTimeline()` 在页面 tick 里发一段：`float timeline_position = getTimelinePosition(flowState);`，**游标变了才重算**；插值一律**从控件创建时的 style 初值起算**（`obj_card_x_init_value = lv_obj_get_style_prop(...)`） | 装机包 codegen + 本工程 `src/ui/screens.c:381-407` |
| 运行时 | `Animate` 沿 `parentFlowState` **上溯到页面级** flowState 再写 `timelinePosition`；到 `To` 才 `propagateValueThroughSeqout` | `eez-flow.cpp:2650-2699` |

⇒ 因为"每帧从初值重放到当前游标"，**倒放、跳帧、来回拖都是确定可复现的**（也才敢做回归夹具）。

## 2. 屏上有什么

```
EEZ Flow - page animation timeline + Animate
g_status                                     ← 谁在报告进度
┌────┐                                       card：主角控件，4 段关键帧
      ░░░░░                                  shadow：进度条，共用同一游标
timeline cursor = <g_pos> s (range 0..3 s)
[播放][跳帧(speed=0)][倒放][读游标]
```

| 时间 | card 的关键帧 | 演的是 |
|---|---|---|
| 0 → 1.0s | `left→300 (easeInOutCubic)`、`top→60 (easeOutBack)` | 斜向上滑 + 缓动差异对比 |
| 1.0 → 2.0s | `rotate→45 (easeInOutSine)`、`opacity→0.27 (linear)` | 边转边淡出 |
| **2.0 → 2.0s** | `width→150` | ★ `start == end` ⇒ **"At 2s set ..."**，是设值不是动画 |
| 2.0 → 3.0s | `left→40`、`top→150` (easeInOutQuad) | 归位 |

`shadow` 一条 `0 → 3s` 把 `width 40 → 424` ⇒ 天然当**进度条**，证明"一条游标驱动多个控件"。

## 3. 四个按钮各验一条 Animate 语义

| 按钮 | 流图 | 验手册哪句 |
|---|---|---|
| 播放 | `Animate(from=Flow.pageTimelinePosition(), to=3, speed=1)` → `seqout` → `SetVariable(g_status="finished: seqout fired")` | 「`seqout` 在到达 To 时才激活」——**没放完就看不到这句话** |
| 跳帧(speed=0) | `Animate(from=3, to=3, speed=0)` → `SetVariable` | 「`Speed=0` 立即跳到 To，此时 From 无意义」 |
| 倒放 | `Animate(from=当前, to=0, speed=2)` → `SetVariable` | `to < from` 走反向分支（`currentTime = start - speed*Δt`），**倒放是真支持**，不是靠重置 |
| 读游标 | `Evaluate(Flow.pageTimelinePosition())` → `result` 数据线 → `SetVariable(g_pos=r)` | 游标可读；顺带再练一次"数据线要配自定义输入名" |

`f_start(Start) → SetVariable(g_status="ready")` 顺手演 P6.2 的"无输入件启动即执行"。

## 4. 工程结构 / 依赖

```
flow-page-timeline-animation/
├── build_example.py        ← 唯一设计源；★ 含 keyframe() 工厂 + 三类自检（关键帧/画布/字体覆盖）
├── fonts/simhei.ttf        ← 中文字体源（UI 有按钮文案 + g_status 取值是中文）
├── design/cli_build.py     ← EEZ CLI + flow 守卫
├── design/gen_font.py      ← 烘 src/ui/fonts/ui_font_cn14.c（CLI 不烘，P-0140）
├── design/audit_chars.py   ← 逐字审计：UI 文案字符 ⊆ 字体字符集
├── design/sim_cmake/       ← run_sim.bat + main.c（含 FLOW_AUTOTEST 无头自证）+ lv_conf.h
├── shots/                  ← 无头自证产物（6 张 PNG + 几何/游标读数）
└── src/ui/                 ← 生成产物；时间线块在 screens.c:381+
```
EEZ Studio 0.29 · LVGL 9.4 · 480×320 深色 · **中文 UI ⇒ 必挂字体条目**（`cn14`，
子集 = ASCII 可打印 + `UI_CJK` 那 10 个字，38 KB）· `flowSupport=true`。

```bat
python build_example.py            && rem 三类自检：非法关键帧/画布重叠/缺字都直接拒绝生成
python design\cli_build.py         && rem BUILD RESULT: ok
python design\gen_font.py          && rem ★ 必须在 cli_build 之后（孤儿清理会删字体 .c）
python design\audit_chars.py       && rem OK: 每一个文字都在字体字符集内
双击 design\sim_cmake\run_sim.bat  && rem 点四个按钮看动效
set FLOW_AUTOTEST=1 && set FLOW_AUTOEXIT=1 && main.exe   && rem 无头自证（下面那张贴图）
```

## 5. 实测状态（2026-10-21）

| 检查 | 结果 |
|---|---|
| 生成器自检负控（7 条） | opacity 越界 / rotate 越界 / 同区间拆两帧 / 非法缓动名 / 非法属性名 / 关键帧倒序 / 总长超 Animate —— **全部拦住 ✓**，正常工程 PASS |
| CLI 构建 | `BUILD RESULT: ok`，`No error and no warning detected` |
| ★ 字体链 | `gen_font.py` → `src/ui/fonts/ui_font_cn14.c` **38,189 B**；`fonts.h` 声明 `ui_font_cn14`；`screens.c` 引用 `&ui_font_cn14` **9 处**；`audit_chars.py` → OK |
| ★ 中文真的渲染出来了 | `shots/shot_after.png`：按钮 `播放/跳帧(speed=0)/倒放/读游标` + 状态行 `jumped (speed=0, From 无意义)` 全是汉字实形（不是豆腐块）。判据来自 `FLOW_AUTOTEST` 无头截图，不靠肉眼开窗口 |
| ★ 插值代码真发射 | `src/ui/screens.c:382` `getTimelinePosition(flowState)`；`:397-403` 抓 `X/Y/OPA/ROTATION/WIDTH` 初值；`:444` `opacity_value += eez_linear(t) * (0.27 - opacity_value)`；缓动实到 5 种：`eez_linear/easeInOutCubic/easeInOutQuad/easeInOutSine/easeOutBack` |
| ★ 行为自证（合成点击，无人参与） | 见下表 |
| 布局/画布自检 | 控件无重叠无越界；流组件按 24px 网格分列，`_check_flow_boxes` PASS |
| 验收面 | **动效必须 PC_SIM 看**（Run 预览时序不可信，P-0141）；`g_pos` 读数可在 Debug 的 Watch 面板对时 |

### 5.1 无头行为自证（`FLOW_AUTOTEST=1 FLOW_AUTOEXIT=1`，2026-10-21 19:44）

主循环每圈 `lv_tick_inc(2)`；触发/采样点按**拍数**固定（点击 30/250/400/550/700/1100/1160，
截图与读数 20/270/420/570/720/1120/1190，见 `design/sim_cmake/main.c:autotest_hooks()`），
"游标"一列是**工程自己的** `读游标` 按钮（Evaluate → `Flow.pageTimelinePosition()` → `g_pos`）
读出来的，不是外部猜测。下面是其中一次运行的读数；游标绝对值随机器负载有 ±0.1 s 抖动，
**不变的是区间关系**（每个中段采样都严格落在 0 与 3 之间、倒放终点与初始逐字段相同）。

| 触发（采样拍） | card x / y / w | opa | rot | shadow w | 游标 | g_status |
|---|---|---|---|---|---|---|
| 初始（20） | 24 / 120 / 96 | 255 | 0° | 40 | 0 s | `ready (cursor at 0)` |
| 点`播放`(30) 后（270） | 300 / 60 / 96 | **200** | **9°** | **184** | **1.191 s** | — |
| 中段（420） | 293 / 62 / **150** | **69** | **43°** | **357** | **2.008 s** | — |
| 接近终点（570） | 40 / 150 / 150 | 69 | 0° | 424 | 2.871 s | — |
| 点`倒放`(700) 中途（720） | 58 / 144 / 150 | 69 | 3° | 421 | 2.871 s | `finished: seqout fired` |
| 倒放回零（1120） | **24 / 120 / 96** | **255** | **0°** | **40** | **0 s** | `rewound to 0` |
| 点`跳帧`(1160, speed=0)（1190） | 40 / 150 / 150 | 69 | 0° | 424 | **3 s（一步到位）** | `jumped (speed=0, From 无意义)` |

- 中段采样点的 opa/rot/shadow **既不是初值也不是终值** ⇒ 插值成立（不是"到点一次性设值"）。
- 倒放终点与初始**逐字段相同** ⇒ 插值是"从初值重放到当前游标"的纯函数，可复现。
- `跳帧` 前游标已被倒放回 0，点完立刻是 3 ⇒ speed=0 真的一步到位，手册那句
  "此时 From 无意义"是真的（本例 `From` 故意填 3，与结果无关）。
- 截图 `shots/shot_*.png` 同时是**中文字体**的证据：按钮 `播放/跳帧/倒放/读游标`、
  状态行 `无意义` 都是实形汉字。

### 5.2 两个手册没写、必须记住的单位坑

| 属性 | 域 | 证据 |
|---|---|---|
| `opacity` 关键帧 | **0..1**（不是 0..255） | codegen 读初值 `.../255.0f`、写回 `*255.0f`（`screens.c:399/484`）。填 70 会被夹成"全不透明"，**构建照样 0 错** |
| `rotate` 关键帧 | **0.1°**（450 = 45°） | codegen 把值 `roundf` 后原样塞进 `LV_STYLE_TRANSFORM_ROTATION`（`screens.c:487`），LVGL 该属性单位是 0.1°。填 45 实测只有 4.5°（第一轮自证里 rot 打印 2°/4° 就是它） |

两条都已经变成生成器里的硬断言（越界直接拒绝生成），不靠记性。

## 6. 踩过的坑（全是这一例特有的）

- ★ **关键帧的 `opacity` 是 0..1，不是 0..255**：codegen 读初值 `LV_STYLE_OPA / 255.0f`、
  写回再 `* 255.0f`。我第一版写 `opacity=70`，结果是被夹成**全不透明**，动画"没反应"。
  已在 `build_example.py` 里做成自检（越界直接拒绝生成）。
- ★ **同一时间区间不能拆成两帧**：codegen 命中第一个满足 `start <= pos < end` 的帧就 `break`，
  所以同一时刻要一起动的属性**必须写进同一帧**，否则只有一半在动。
  自检里表现为"关键帧倒序/重叠"，但根因是这个 break，不是顺序问题。
- **`Start == End` 的帧是"设值"**（手册标签 `At X s set ...`）；它对该时刻**及其之后**都生效，
  不是只有一瞬——想让它只在瞬间生效，得靠后一帧再写回目标值。
- **游标只在"Animate 在跑"时才动**：没有 Animate 时页面停在 0，控件保持创建时的初值；
  别指望"打开工程就自动播"。要自动播就 `Start → Animate`。
- **`Animate` 驱动的是页面级游标**（运行时上溯 `parentFlowState`），所以 User Widget 内部再放
  Animate 会推到**宿主页面**的游标上——多实例复用时会互相带动画（与 `app-wifi-scan-flow` §9 P1#10
  的"共享全局变量互串"是同一类问题）。
- **`from` 是 Python 关键字**：生成器里不能写 `from=...`，只能 `**{"from": ...}`。
- ★ **中文没挂字体条目 = 屏上一片豆腐，而且构建 0 错**（本例就是这么被用户当场指出来的：
  "明显字体有问题，没有中文显示"）。修法三件齐全：`fonts[]` 条目 + 控件 `text_font` +
  `cli_build` 之后跑 `gen_font.py`；防回归靠 `_check_font_coverage()`（从工程 JSON 反查非 ASCII
  字符，缺字拒绝生成）。证据：`shots/shot_*.png` 里 `播放/跳帧/倒放/读游标/无意义` 是实形汉字。
- ★ **动画控件在 `children[]` 里要排在文字前面**（数组顺序 = 创建顺序 = z 序）。
  第一版 `card` 排在两条读数 Label 之后，播放中段就把 `timeline cursor = …` 整行盖住了；
  静态布局自检（只比创建位）看不见这种中途遮挡——因为卡片是**会动的**。

## 7. 相关

- 规划与选型对照：`../../flow-understanding/EXAMPLE_PLAN.md` ⑮（本例）与 ⑭（A43 `animY/animOpacity` 件级路子）；
- 机制取证脚本：`../../flow-understanding/tools/extract_studio_facts.py`（同法可复抽 codegen/运行时证据）；
- 执行语义基础：`../../flow-understanding/notes/flow-execution-semantics.md`（无输入件启动即执行、seqout 语义）。
