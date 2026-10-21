# 示例规划 —— Flow 该补哪些工程（手册出处 + 验收判据）

> 回答的问题：**读完官方手册后，本仓库还缺哪些能"把 Flow 讲清楚"的示例。**
> 每条都带手册锚点（`P6.x` / `Axx` / `Wxx`，页码复查见 `MANUAL_MAP.md`），
> 并标出它**解锁了哪个产品需求**（多数是 `app-wifi-scan-flow` 的「待做」项）。
> 立项前请先读 `notes/flow-execution-semantics.md` 与 `notes/flow-variables-expressions.md`。

## 0. 先盘家底：Flow 已经被覆盖到哪了

> **★ 本规划已按装机事实修订**（判据见 `notes/flow-actions-lvgl.md`：
> 从本机 EEZ Studio 0.29 包里抽出的 `enabledInComponentPalette` 谓词）：
> **`OnEvent`、`ShowPage`、`ShowKeyboard`、`ShowKeypad`、`ShowMessageBox`、`OverrideStyle`、
> `SelectLanguage`、`SetPageDirection`、`SCPI` 这 9 件在 LVGL 工程面板里被禁用**——
> 手册里读到的这些能力**不能当可行性依据**，下面原 ⑦/⑨/⑪ 三条已改写或删除。

| 已覆盖能力 | 现有示例 | 手册锚点 |
|---|---|---|
| 一个变量驱动多控件（读） | `w67-w3-w2-slider-arc-bar` | P8.1 第 70 页 |
| assignable 双向回写（`…type` 开关） | 同上 + `w23-w59-w73-w16-select-switch` | W24/W69/W78 属性表 |
| 表达式绑样式/可见性 | `two-state-styles`、`w14-w35-w62-chart-led-scale` | P9.5.3 第 94 页 |
| 事件 → Switch → 切屏 | `gesture-page-switch`、`one-way-gesture-switch` | A43 Change Screen |
| Tabview 原生滑动（**绕开** Flow） | `tabview-swipe-switch` | — |
| Flow on/off 成本与能力对照 | `app-wifi-scan-flow` / `app-wifi-scan-flow-no-flow` | P13.2、P6.2 |
| 引擎体积优化 | `perf-tabview-native-vs-eez` + 经验库 P-0157 | P13.2 第 112 页 |
| Flow 变量用法全家（读 3 路 / 写 4 路 / `Watch` 监听 / `Switch` 分支 / 全局 vs 页面局部） | **`flow-examples/flow-variables-basics/`（已建，2026-10-21）** —— 纯 EEZ 零 native C，含"写错变量名会被 Checks 拦"的负控证据 | P8.1 · P.58、A73/A91/A21/A81 |

**结论**：绑定类（读/写/样式）已经够用了；缺的是**执行语义类**和**动作件能力类**——
也就是"Flow 作为逻辑引擎"的那一半。上面这条 `flow-variables-basics` 补的是"变量怎么用"的入门层，
下面 23 项（四梯队 ①–㉓）补的是引擎层：执行语义、动作目录、函数体检台、时间线动效、结构体记录、并行与互斥、错误与账单。


---

## 第一梯队 · 消除不确定性（做完这三项，后面所有 Flow 决策都不用再猜）

### ① `flow-execution-semantics` —— 队列与就绪语义实验台 ★首推

| 项 | 内容 |
|---|---|
| 演示点 | 手册 P6.3 的 4 个连线案例 1:1 复刻（Start 使时序输入变必需 / 不连→不执行 / 无 Start→启动即执行），再加两条：`Watch` **启动即发一次**、**数据输入保留旧值**导致"第二次点复用旧数据" |
| 手册出处 | P6.1–P6.3（P.39–P.42）、P8.1（P.58）、A91 Watch（第 329 页） |
| 为什么缺 | 仓库里三个反复踩的坑（P-0146 Checks 空转、"画了不连"、绑定不刷新）**根因全在这里**，但从没被做成可运行的对照实验 |
| 验收 | 4 个 Label 分别对应 4 个 case，进入页面即知谁执行了；GUI Debug 看 Queue 面板（**GUI-only**），仿真看最终文本；`preflight` + `ui_check` 对照 |
| 成本 | 低（单页、0 图片字体），但**必须开 GUI Debug** 才算验完 |

### ② `flow-expression-function-bank` —— 49 个函数逐个实测的"体检台" ★性价比之王

| 项 | 内容 |
|---|---|
| 演示点 | 一屏一分类，把 `System/Flow/Date/Math/String/Array/JSON/LVGL` **每个函数各跑一条表达式**并把结果显示在 Label 上 |
| 手册出处 | P8.3 全部（P.63–P.74，第 75–86 页） |
| 为什么缺 | 手册有**已知缺陷**必须实测才能用：① `Math.round(x,2)` 出现在示例里但函数表**只有一个参数**（无保留小数位的函数）；② `<`/`>` 的说明**写反**；③ `Array.append` 的描述是 `String.split` 的复制粘贴；④ `Date.getDay` 是**月内日不是星期**且无 weekday 函数；⑤ `LVGL.MeterTickIndex` 指向的 W33 是坏链（Meter 实为 W47）；⑥ 无 `sqrt/tan/exp/mod/π`、无 `toUpperCase/trim/replace`、**无 `Array.sort`** |
| 验收 | 产出一张**能力矩阵**（函数 × 手册签名 × 实测结果 × 差异），归档进 `flow-understanding/notes/`；缺函数一律标"手册无→落 native"，**不许再靠猜下"EEZ 做不到"的结论** |
| 直接收益 | `ARCHITECTURE.md` §9 P1 #11（长 SSID 截断/大小写/格式化的能力边界）当场结案：`String.substring`+`String.length` 有，**大小写转换没有** → 必须 native |

### ③ `flow-lvgl-actions-catalog` —— A43 LVGL 子动作全清单示例 ★补上产品缺的那一半

| 项 | 内容 |
|---|---|
| 演示点 | 把 A43 的**每个子动作各来一发**（装机注册表实测 **65 项**，手册只写 63，**多出的 `objGetDisplayX` / `objGetDisplayY` 手册根本没提**）：`changeScreen`（含 Fade/Speed/Delay/**useStack**）、`changeToPreviousScreen`、`create/delete/isScreenCreated`（需 `screensLifetimeSupport`）、`objSet/Get X·Y·Width·Height`、`objStyleSetProperty`、`objSet/GetStyleOpa`、`objAdd/RemoveStyle`、`objSetFlagHidden`、`objAdd/Clear/HasFlag`、`objSetStateChecked/Disabled`、`objAdd/Clear/HasState`、`groupFocus*`/`groupSetWrap`/`groupSetEditing`、`animX/Y/Width/Height/Opacity/ImageZoom/ImageAngle`、控件专用（`arcSetValue`/`arcRotateObjToAngle`/`barSetValue`/`sliderSetValue*`/`sliderSetRange`/`dropdownSetSelected`/`rollerSetSelected`/`tabviewSetActive|GetActiveTab`/`labelSetText`/`imageSetSrc|Angle|Zoom`/`keyboardSetTextarea`/`qrCodeUpdate`/`calendar*`/`buttonMatrix*Ctrl`） |
| 手册出处 | A43（第 213–217 页起，raw 行 7300+）；`Create/Delete Screen` 需 P13.2 Build 的 **Screens lifetime support** |
| 为什么缺 | WiFi 应用的「待做」第 1 条（**密码半页弹层**）正解就是这条能力：显隐用 `Obj Set Flag Hidden`、位移用 `Obj Set Y`、透明度用 `Obj Set Style Opa`——**全都在 Flow 里可做**，不必再回到 native 自绘；`no-flow` 变体做不到这些，正好构成第二组 on/off 对照 |
| 验收 | 每种子动作一个可点开的演示页；产物对账 + GUI 行为；`nav_audit` 门禁保证每屏能进能回（对应导航铁律） |

---

## 第二梯队 · 逻辑编排能力（产品状态机要用）

### ④ `flow-branching-state-machine`（SetVariable + SwitchCase + Compare + IsTrue）
- 演示点：**三值状态机**（0 空闲/1 进行/2 失败）纯 Flow 实现，含 `SetVariable` **一次写多个变量**、`SwitchCase` 逐条求值取第一个真、`Compare` 的 A/B/C 输入用法。
- 手册：P8.1（P.58）、A73（第 288 页）、A81（第 314 页）、A8/A36。
- 解锁：`ARCHITECTURE.md` §5 稳定性机制 #4（"点了没反应"）从 native 侧搬到 EEZ 侧的可行性判据。

### ⑤ `flow-loop-delay-counter`（Loop + Delay + Counter + 输出名技巧）
- 演示点：`Loop` 的 Variable/From/To/Step + **把输出名填进 Variable 属性从而不改写变量**（手册 A91.2.3 明确给的技巧）+ `Delay` 非阻塞 + 内部状态件"自我重新排队"（P6.2 第 54 页）。
- 解锁：轮播/进度提示/分步引导，不用写 LVGL 定时器。
- 关键坑：数组是**定长**的（经验库 P-0165 已推翻"可变长"），Loop 越界=直接错，示例里要演一次"越界会怎样"。

### ⑥ `flow-array-and-sort`（Array 函数 + A79 SortArray + makeArrayValue）
- 演示点：`Array.allocate/append/insert/remove/slice/clone` **纯函数必须写回**（§5 第 1 条），
  以及 **A79 SortArray 按结构体字段排序**（手册明写：允许 `array:integer/float/double/**struct**`，
  struct 时要给 `Structure name` + `Structure field name`，另有 `Ascending` / `Ignore case`；
  并强调 "**it does not do in-place sorting**"）。
- 解锁：WiFi 的 **RSSI 降序**到底能不能纯 Flow 做——手册说能（`array:ap_info` 按 `rssi` 字段排），
  但 Flow 里装结构体数组受定长限制（经验库 P-0165），做出来就是"Flow 排序 vs native 排序"的结案证据。
- 注意：表达式层**没有 `Array.sort` 函数**，排序只有 A79 这条动作件路子（`SortArray` 面板允许，③待实测）。


### ⑦ `flow-lvgl-navigation-vs-onevent` —— 页面生命周期在 LVGL 里只能怎么办 ★已由禁用清单改写
- **原提案作废**：`OnEvent` / `ShowPage` 在 LVGL 面板被禁用（`notes/flow-actions-lvgl.md` §2.1），
  "页面 open/close 事件流"**在 LVGL 工程里做不到**。
- 新演示点（三条路子对照，做成一页对照 + 结论）：
  1. `changeScreen.useStack` + `changeToPreviousScreen` 的进入/返回行为（**栈语义手册只有一句，实测**）；
  2. `Flow.isPageActive` 表达式属性做"只有当前屏才刷新"的判据；
  3. native 侧 `ui_tick` 里比对 `g_currentScreen` / 屏幕创建时机 —— 即 `app-wifi-scan-flow` 现在的做法。
- 解锁：`ARCHITECTURE.md` §9 P1 #6 开机恢复、`EEZ_WORKFLOW.md` 里 `demo_timer` 的替换方案能否成立。

### ⑧ `flow-navigation-stack`（Use stack + Previous Screen）
- 演示点：**导航闭环**用 Flow 实现（进得去也回得来，含 Fade/Speed/Delay），
  对齐仓库"每屏必须能返回"的铁律，并让 `nav_audit` 门禁能验 Flow 版。
- ★ 必须实测的两条未文档化行为：栈深上限、`useStack` 时旧屏是否被销毁（配合 `screensLifetimeSupport`）。
- **`SetPageDirection` 属 LVGL 禁用件**，本示例不做 LTR/RTL。

---

## 第三梯队 · 输入/错误/多语言（产品化必备）

### ⑨ `flow-lvgl-keyboard-and-group-focus` —— 软键盘与焦点组（LVGL 正道）★已由禁用清单改写
- **原提案作废**：`ShowKeyboard` / `ShowKeypad` / `ShowMessageBox` 在 LVGL 面板被禁用
  （它们依赖"键盘页 ID=2 / 小键盘页 ID=3"的 GUI 页机制）。
- 新演示点：真 `lv_keyboard` 控件 + A43 `keyboardSetTextarea` 绑定目标 textarea，
  配 `groupFocusObj` / `groupFocusNext` / `groupSetWrap` / `groupSetEditing` / `groupFocusFreeze`
  与工程 JSON 的 `lvglGroups` 段做**焦点环**（编码器/旋钮导航同一套机制）。
- 解锁：WiFi 待做第 1 条（密码输入）+ 医疗器械物理编码器场景。
- ★ 顺带验：**没有消息框件**，弹层必须自建容器（`objSetFlagHidden` + `animOpacity`）。

### ⑩ `flow-error-visibility`（`Catch error` 属性 + `@Error` 输出 + `Error(A19)`）
- 解锁：`ARCHITECTURE.md` §9 P1 #13"表达式写错通常静默"——手册其实给了机制：件属性 **Catch error（Boolean）打开后会出现 `@Error` 数据输出**，输出内容是**错误的文字描述**（A91.2.5、A63.2.3 都这么写）。这条**从来没被验证过**，做出来就是调试利器。
- `CatchError` / `Error` 面板允许（`notes/flow-actions-lvgl.md` §2.3），属③待实测项。

### ⑪ `flow-i18n-boundary` —— LVGL 多语言到底能到哪一步 ★边界示例（结论可能是"做不到"）
- **`SelectLanguage` 件在 LVGL 禁用**；`Flow.languages` / `Flow.translate` / `T"ID"` 是**表达式层**能力，
  手册 P12 的 XLIFF 流程整章是 GUI/Dashboard 口径。
- 演示点：只用表达式层的 `T"..."` + `Flow.translate` 能不能出中文/切语言；
  配 `font-entry-form` 的字库预算（中文字形进 assets 的 flash 代价）。
- 价值：把"多语言"从 `ARCHITECTURE.md` §9 P2 的悬案变成**有实测结论的边界**（能/不能/半能）。

### ⑫ `flow-user-widget-reuse`（User Widget/Action + 多实例状态互串）
- 演示点：把"设置项/状态卡"封装成 User Widget，**放两个实例**验证 `ARCHITECTURE.md` §9 P1 #10（共享全局变量导致状态互串）到底会不会发生、如何隔离。
- 手册：P6.1（半圆=输入输出）、P7.2.2（P.50）、P7.3.2（P.53）。
- 装机依据：LVGL 有 `COMPONENT_TYPE_LVGL_USER_WIDGET`（面板组 `!1Basic`，谓词 `"lvgl"===e`），**这条路是官方给 LVGL 的**。

### ⑬ `flow-native-variable-type-matrix` —— native 变量类型实测 ★由装机 traits 冲突引出
- 起因：装机包里 LVGL 的 `isVariableTypeSupportedAsNative` **允许 enum/integer/float/double/boolean/string**，
  而本仓库现在的口径是"只有 integer/string 稳，**布尔要用 integer 0/1**"（`07_project_json_schema.md` §3）。
- 演示点：同一工程里各建一个 native 变量（含 `boolean`、`float`、`double`、`enum:`），
  看 CLI 生成的 `get_var_*/set_var_*` 签名、是否编译通过、桥实现怎么写才不炸。
- 产出：**结案冲突**，据此改经验库与 `07_project_json_schema.md` 那句话（谁错改谁）。

### ⑭ `flow-popup-sheet-with-lvgl-actions` —— 用 A43 做"密码半页"（产品向收口）
- 演示点：`objSetFlagHidden` + `animY`/`animOpacity` + `objSetStyleOpa`（遮罩）+ `keyboardSetTextarea`
  + `labelSetText` 组合出一个可复用的**半页上滑弹层**，全程 EEZ 内实现、零 native 画界面。
- ★ **动效另有主路**：页面动画时间线 + `Animate` 件（⑮ 已建成，机制见 `notes/flow-timeline-animation.md`）。本例走件级 `anim*`（可参数化），
  ⑮ 走 GUI 拖关键帧（可读性好）——两条都要做，产出的是**选型对照**，不是先验拍板。
- 解锁：WiFi「待做」第 1 条的**EEZ 优先**正解（现行 native 直写控件的写法是被 Flow 缺失逼出来的，
  如果 A43 走得通就该收回 EEZ）；同时给出"EEZ 版 vs native 版"对照，接 `perf-tabview-native-vs-eez` 的口径。


---

## 第四梯队 · 手册里剩下的 Flow 能力（⑮–㉓，2026-10-21 二次通读补）

> 落地位置一律 `flow-examples/<名>`（容器规则见 [`../flow-examples/README.md`](../flow-examples/README.md)）；
> 每条都标**验收面**：Run（看结果）/ Debug（看队列与变量值）/ PC_SIM（看真实输入行为）。
> ★ 本梯队里 ⑮⑯⑳ 三件的成立条件我已经在**运行时源码**里核过（不只是手册措辞），出处见各行证据。

### ⑮ `flow-page-timeline-animation` —— 页面动画时间线 + `Animate` 件　★**已建成**（2026-10-21）

> 建成后经逆向取证，机制已单独沉淀：[`notes/flow-timeline-animation.md`](notes/flow-timeline-animation.md)（关键帧 JSON 形态、31 个缓动名白名单、三条手册没写的失效条件、与 ⑭ 的选型表）。
- **为什么单列**：我之前把动效只挂在 A43 的 `animX/animY` 子动作上（③⑭），
  漏了手册明写的主路——**"EEZ Flow supports animation of page content, for which the Animation
  timeline editor is used"**（P3 · P.24–25，Fig.35），且它**只要求工程启用 Flow**，不是 Dashboard 专属。
- **三层证据都齐**：
  - 手册：P3 · P.24–25；A2 Animate · P.13（From/To 单位**秒**、`Speed=0` 即跳帧、`seqout` 在**放到 To 才发**）；`Flow.pageTimelinePosition` · P.64；
  - 装机包：`AnimateActionComponent` 谓词 `"eez-gui-lite"!==e` ⇒ **LVGL 面板可拖**；控件 JSON 里那个 `timeline: []` 字段的 typeClass 是 `TimelineKeyframe`；
  - **运行时源码**（最硬）：`eez-flow.cpp:2650-2672` —— `Animate` 沿 `parentFlowState` 上溯到**页面级 flowState** 再写 `timelinePosition`，
    5807/6963/7690 三处实现 `Flow.pageTimelinePosition()`，9303 处在流启动时把位置清 0。**这条不是"手册写着待实测"，是实现已在我们要编译进去的那份 cpp 里。**
- 演示点：①给页面打 3–4 个关键帧（位移/透明度）；②`Animate(From=当前, To=终点, Speed=1)` 播完整段；
  ③`Speed=0` 直接跳帧（验证手册那句"此时 From 无意义"）；④用 `pageTimelinePosition()` 把进度回显成百分比；
  ⑤`seqout` 到底是不是放完才发（用 `Watch` 或第二个 `Animate` 串起来验）。
- 与 ⑭ 的对照关系：**同一个"半页上滑"用两条路各做一遍**——页面时间线（EEZ 原生、GUI 里拖关键帧）
  vs A43 `animY/animOpacity`（件级、可参数化）。产出选型结论，不是二选一先验拍板。
- 验收面：动效**必须 PC_SIM 看**（Run 预览的时序与真 indev/tick 不同，P-0141 教训）；数值进度可在 Debug 的 Watch 面板读 `timelinePosition` 对应表达式。

### ⑯ `flow-regexp-multimatch` —— `Regexp` 件的多匹配状态机（A62 · P.162–163）
- 演示点：`Pattern`/`Text`/`Global`/`Case insensitive` 四属性；
  ★ 它的**三个时序输入**是这套机制的教科书样本：`seqin`（手册原话"needs to be used once at the beginning"）、
  `next`（"get the next match"）、`stop`（中止后立刻从 `done` 继续）——**跨多次调用保持匹配进度**；
  输出是**结构体** `match{index, texts[], indices[]}`：`texts[0]` 整体匹配、其后各捕获组；
  `indices[k] = [start, end]`。做"从扫描到的 beacon 字符串里抽 SSID/信道/加密"这种真实解析。
- 为什么值得：这是手册里**唯一自带"迭代器语义"的数据件**，正好把 P6.2 的
  "件可自己清除某个数据输入"那句例外规则演实（`A42 Loop` 是同族，但 Regexp 带结构体输出）。
- 预判坑：`Global=false` 时只有一次匹配；`texts` 是 `array:string` ⇒ 取用要走 `[i]` 下标（P8.2.7）；
  手册该节 `done` 输出编号印错成 "A1.1.1."（引用时别照抄）。
- 验收面：Run 看解析结果文本；PC_SIM 不用（无输入依赖）。

### ⑰ `flow-parallel-flows-and-mutex` —— 并行 Flow 与 `TestAndSet` 临界段（P6.2 · P.40；A88 · P.224）
- 演示点：两条并行 Flow（一条按钮驱动、一条 `Watch` 自驱）共用**一条执行队列**（手册原话），
  各自持有**自己的局部变量与件内部状态**（`Loop` 记得自己转了几圈）；
  再用 `TestAndSet` 做互斥：为 false → 置 true 并放行；为 true → **"被放回执行队列直到变量变 false"**（非阻塞、原子）。
  临界段末尾用 `SetVariable` 复位。手册举的例子是 Tetris 的 `busy`。
- 为什么值得：这是 `ARCHITECTURE.md` §9 **P0 #1（线程边界）** 的 EEZ 侧答案——
  引擎本来就是协作式排队，我们的 `io_win` 回调只要不直接碰 LVGL 就不会竞态；
  而且它给"连接中禁止重复点击"这类需求一个**不写 C 的做法**。
- 预判坑：`TestAndSet` 死等会**占住队列**（并行≠抢占），所以临界段里绝不能有 `Delay` 长等待；
  `Variable` 属性是 **ASSIGNABLE EXPRESSION (boolean)** —— 布尔在 Flow 里是合法类型（≠ native 变量那套限制）。
- 验收面：**必须 Debug 面板**（Active Flows + Queue）才看得出"谁在队列里"，Run 只看结果会误判。

### ⑱ `flow-user-action-contract` —— User Action 的输入输出契约与"同流跳转"（A32/A54/A39/A40/A17）
- 演示点（四件事，全都在一条流图里）：
  1. `Input`/`Output` 件给 User Action / User Widget 加数据口（属性只有 `Name`+`Type`，
     **名字就是表达式里的标识符**，`Type` 是给 Checks 用来判数据线能不能连——P-0146 那条老坑的官方出处）；
  2. `Label OUT → Label IN` 做**同一条流内的跳转**（省掉一屏交叉线），
     ★ 手册硬约束：只在 **同一 flow（Page 或 User Action）内**有效，**不能跨流**；
     同名可多个 OUT，但 **IN 只能有一个**；
  3. `DynamicCallAction` 运行期按变量里的名字调 User Action，
     ★ 手册硬约束：被调件**只能有 Start/End，不能有 Input/Output**；
  4. `NoOp` + `Comment` 当占位/注释件（A7 在手册里**只有 Description 一节**，无属性无端口）。
- 为什么值得：现在仓库里 User Widget 只有一个"组件复用"的说法（⑫），**没人验证过端口类型和连线检查的关系**；
  而 Label IN/OUT 是画大图（A43 那 65 项、状态机图）唯一能救可读性的手段。
- 验收面：Run 看结果；连错类型时**编辑器 Checks 的报错文案**才是这例的产出物（截图进 notes）。

### ⑲ `flow-enum-state-machine` —— 枚举变量 + 点号成员比较（P8.2.3 · P.59；P8.2.7 例 · P.72）
- 演示点：`enum` 类型变量（面板里 Enums 段定义成员与整数值）；表达式
  `var == State.START || var == State.EMPTY`（手册给的正是这个形态）；
  `SwitchCase` 按枚举分支；生成码侧看 `vars.h` 的 `FLOW_ENUMS` 段是否真枚举化。
- 为什么值得：`app-wifi-scan-flow` 系列把状态全放 native 契约（`APP_IN_SCAN_STATE` 整数），
  枚举这条路**从没在 LVGL 工程里验过**；验通就能把"扫描态/连接态"做成 EEZ 里可读的具名分支，
  而不是满屏魔数。另外 native 变量支持枚举已由 traits 证明（⑬），两侧可以一起结案。
- 预判坑：`vars.h` 模板里 `// enum declarations` 段与 `FLOW_ENUMS` 占位符是否真被填（本仓库模板已带该占位符）。
- 验收面：Run 看分支文案；产物对账看 `vars.h` 枚举项。

### ⑳ `flow-struct-array-records` —— 结构体 + `array:struct` + 下标变量（P8.2.2/2.5；P8.3.2）
- 演示点：定义 `ap_info`（7 字段，对应 `io_iface.h` 的 `wifi_ap_t`）→
  默认值 JSON `[{"ssid":"A","rssi":-40}, ...]`；表达式 `` `ap[i].ssid` ``（**下标本身是变量**，手册 P.72 的写法）；
  `Flow.makeValue("ap_info", json\`{...}\`)` 造结构体值；`Flow.makeArrayValue` 造数组；
  `SetVariable` 改单个字段；★ 与 ⑥(`SortArray` 按结构体字段排序) 配对。
- 成立条件已核：运行时 `structs.h` 模板的 `EEZ_FOR_LVGL` 分支 + `FLOW_STRUCTS`/`FLOW_STRUCT_VALUES`
  占位符在我们自己的 `BUILD_TEMPLATES` 里就有；**数组定长**已由 P-0165 实测（`ArrayValue{arraySize, arrayType, values[1]}`，`makeArrayRef` 创建）。
- 为什么值得：这是"WiFi 列表数据要不要进 EEZ"的**唯一未验分支**——
  v3 试过（P-0167 翻车）、v4 整族撤到 native。做出来就是**结案**：定长 + 每轮重建的堆抖动，
  到底能不能撑住 5 行固定槽；撑不住就把"列表归 native"写成有证据的结论而不是习惯。
- 预判坑：手册对数组**只有一句话**（元素类型/上限/多维全未说明）⇒ 三条都得实测；越界下标行为要记录。
- 验收面：PC_SIM（列表渲染真实）+ Debug 的 Watch 面板（看数组变量当前值）。

### ㉑ `flow-date-and-clock` —— `DateNow` + Date 函数族（A14 · P.42；P8.3.3 · P.66）
- 演示点：`Date.now` → `Date.toString/toLocaleString` → `getHours/getMinutes`（0–23 / 0–59）
  → `Date.make(y,m,d,h,mi,s,ms)` 造时间；`String.padStart(2,"0")` 补零拼时钟文本（**手册没有格式化函数，只能自己拼**）。
- ★ 这例的价值一半在踩手册的坑：`Date.getDay` 是**月内日 1–31，不是星期**（手册无 weekday 函数）；
  `Date.now` 的返回类型印成 "Now"；小数/秒对齐要 `Math.round` 时**手册函数表只有一个参数**，
  而 P.60 示例里出现 `Math.round(x, 2)` ⇒ 以函数表为准，实测出"保留两位"到底行不行。
- 为什么值得：医疗器械与产品 UI 迟早要显示时间；而且 `Date` 底层就是 **Unix 时间戳**（P8.2.1）——
  正好和"时间谁提供"（native RTC / SNTP）这条边界画清楚：EEZ 只做格式化，取值仍归 native。
- 验收面：Run 即可（无输入依赖）。

### ㉒ `flow-cost-switches` —— P13.2 三个内存开关的固件级 A/B（P13.2 · P.102–103）
- 演示点：同一份流工程，只改 `Compress flow definition` / `Execution queue size` /
  `Expression evaluator stack size` 三个 Build 选项，跑 2×2×2 的 flash/RAM 账单矩阵；
  并验手册那句**"若流执行开始出错，说明队列/栈调太小了"**——即"出错"是可复现判据，不是玄学。
- 现状差：经验库 P-0157 有真机数字（queue 1000→128 省 10,464 B RAM 等），
  但**仓库里没有能一键复跑的示例**；本例把结论变成 `parse_map.py` + 脚本产出的表。
- 预判坑：LZ4 连带开销可能吃掉压缩收益（本地实测过一次）；`compressFlowDefinition` 改的是**发射的 assets 形态**，
  产物文件会多出 `eez-flow-lz4.*` —— 产物对账清单要跟着变（写进判据，别当异常）。
- 验收面：编译器/map（不是 Run 也不是仿真）。

### ㉓ `flow-log-and-error-visibility`（⑩ 的扩展） —— `Log` 件与异常可见性（A41 · P.104；P4.4 · P.31）
- 演示点：`Log` 件的输出到底出现在哪——手册只说"显示在 Studio 的 **Logs 面板**"（面板支持
  Fatal/Error/Warning/Info/Debug/SCPI 过滤），**真机上是否有出口手册未说明**；
  再演表达式异常的可见文本：数组越界下标、除 0、`Constant` 里引用变量（手册明禁）——
  每种都开 `Catch error` 看 `@Error` 送出的**文字**长什么样。
- 为什么值得：`ARCHITECTURE.md` §9 P1 #13"Flow 表达式写错通常静默"是目前调试成本的头号的坑，
  手册其实给了机制但**仓库从没验过一次**；验完就有了"开发期怎么让 Flow 报错可见"的标准做法。
- 验收面：Debug 面板（Logs）+ PC_SIM 串口/控制台（真机侧有无输出属**待实测**，结论要写清哪一面看到的）。

### 边界补充（写进 notes / 手册对照，**不做成能跑的示例**）

| 条目 | 手册与包内证据 | 为什么不做示例 |
|---|---|---|
| **Configurations / `Used in`** | P13.2.1 原文 "**only available for EEZ-GUI projects**"；装机包 `usedIn` 属性对 `isLVGLProject` 直接 disabled | "一份工程分别出板子/仿真器构建文件"在 LVGL 走不通，只能靠构建脚本或 `#if` 排除（native 侧已有先例） |
| **跨工程复制粘贴 Flow 片段** | P7.1.2 · P.48（要开两个 Studio 窗口 `CTRL+SHIFT+N`） | 纯 GUI 操作技巧 → 进经验库 `skills.md`，不是工程 |
| **看线色判数据线/时序线** | P6.1 · P.39（时序线青绿、数据线灰） | 同上，属观测技巧 |
| **断点** | 面板清单里有 Breakpoints（P4.1/P4.4），但手册**从不说明怎么打断点** | 机制未文档化 → 先实测再决定，不预设 |
| **Debug 面板对 LVGL 是否齐全** | 手册只在 Dashboard 语境展示 Fig.56/57，未说明 LVGL | ⑰㉓ 会顺带把这条验成事实 |

## 明确**不建议**立项的（省时间）

| 候选 | 不做的理由（**装机包面板谓词 + 手册双重依据**） |
|---|---|
| `ShowKeyboard` / `ShowKeypad` / `ShowMessageBox` 直接照手册做 | **LVGL 面板禁用**（谓词含 `"lvgl"!==e`）；它们依赖"键盘页 ID=2 / 小键盘页 ID=3"的 GUI 页机制 → 改走 ⑨ |
| `OnEvent` / `ShowPage` / `SetPageDirection` / `OverrideStyle` / `SelectLanguage` / `SCPI` 类示例 | **LVGL 面板禁用**（同上，共 9 件，见 `notes/flow-actions-lvgl.md` §2.1） |
| MQTT / Serial / TCP / UDP / HTTP / Modbus / File / Python / EvalJS / Instrument / SCPI 动作 | 面板没挡，但属性依赖 `object:` 变量类型，而 **`object` 变量是 Dashboard 专属**（手册 P8.2.4）→ LVGL 里喂不进输入，**视同不可用** |
| 持久化变量 / `ReadSetting` / `WriteSetting` 示例 | **Persistent 与这套文件明确 "Supported only in Dashboard projects"**（第 70 页 / raw 2407）→ LVGL 没有这能力，只能 native 写 NVS，做成 EEZ 示例是误导 |
| JSON 变量示例 | 手册："for now, JSON is **only supported in Dashboard projects**"（raw 2472）→ LVGL 用结构体 |
| Blob / Stream / Object 变量 | 同上，均标 Dashboard-only |
| `Default value list` | 仅"未启用 Flow 的 EEZ-GUI 工程" |
| 把控件坐标绑到变量 | 坐标属性是 **Number + 构建期四则运算**（只允许 `+ - * /`），绑变量只会烘成死数字（§3 ★ 条） |

---

## 立项规矩（沿用仓库现有铁律）

0. **落地位置统一：本文所有 `flow-*` 示例都建在 [`flow-examples/`](../flow-examples/README.md) 下**（Flow 机制类示例的容器，判据/命名/登记规则见该目录 README），不再是仓库根；


1. 一个示例 = 根目录一个独立子目录，照 `示例工程模板说明.md` 五步流程；
2. **唯一设计源** `build_example.py`，产物 `.eez-project` 勿手改；
3. 验收链：`preflight.py --with-sim` 全绿 → 产物清单对账 → 行为类必须仿真/真机（P-0141）；
4. **观测类结论要标观测面**：Queue/Active Flows/Watch 是 **GUI Debug 专属**，
   CLI 与 PC_SIM 拿不到（手册没说 LVGL 是否有同一套面板 → 现场确认）；
5. 每个示例的 `README.md` 写"演示点/结构/依赖/踩过的坑"，
   **手册事实**回写 `flow-understanding/notes/`（带页码），**通用坑**回灌经验库 `intake/`；
6. 新示例的"能不能做"结论，必须先查 `notes/flow-expression-function-bank` 与 A43 清单，
   再动手——**不许用"框架大概做不到"当结论**。

## 建议实施顺序

```
① 执行语义 → ② 函数体检台 → ③ A43 动作目录      （第一梯队：把"能做什么"钉死）
        ↓
⑬ native 变量类型矩阵（结案与经验库的冲突）
        ↓
④ 状态机 → ⑤ Loop/Delay → ⑥ 数组与排序 → ⑦ 生命周期替代法 → ⑧ 导航栈
        ↓
⑨ 键盘与焦点组 → ⑩ 错误可见性 → ⑭ 半页弹层（产品收口）→ ⑪ 多语言边界 → ⑫ User Widget 复用
        ↓
第四梯队（手册二次通读的增量，按产品价值排序）：
⑮ 页面时间线动效 → ⑳ 结构体数组记录（结案"列表归谁"）→ ⑲ 枚举状态机
        → ⑯ Regexp 多匹配 → ⑰ 并行与互斥 → ⑱ User Action 契约
        → ㉑ 时钟与 Date → ㉓ 错误可见性 → ㉒ 三个内存开关 A/B
```

> ①②⑬ 三件做完，"EEZ 能不能做 X"从此有**手册 + 面板谓词 + 实测**三层证据；
> ③⑭ 做完，`app-wifi-scan-flow` 的三条「待做」（密码半页、真后端、记住密码）
> 就能按"EEZ 优先"落地，而不是默认甩给 native。
