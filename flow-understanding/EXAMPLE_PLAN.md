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
下面 14 项补的是引擎层（执行语义、动作目录、函数体检台）。


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
- 解锁：WiFi「待做」第 1 条的**EEZ 优先**正解（现行 native 直写控件的写法是被 Flow 缺失逼出来的，
  如果 A43 走得通就该收回 EEZ）；同时给出"EEZ 版 vs native 版"对照，接 `perf-tabview-native-vs-eez` 的口径。


---

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
```

> ①②⑬ 三件做完，"EEZ 能不能做 X"从此有**手册 + 面板谓词 + 实测**三层证据；
> ③⑭ 做完，`app-wifi-scan-flow` 的三条「待做」（密码半页、真后端、记住密码）
> 就能按"EEZ 优先"落地，而不是默认甩给 native。
