# flow-understanding —— EEZ Flow 理解专区

> **这个目录不是示例工程**，是**读手册 + 立口径**的地方：
> 把官方《EEZ Studio Reference Guide》里关于 Flow 的规则**逐条落到页码**，
> 再据此决定本仓库该补哪些示例工程（示例一律仍按仓库规矩放在根目录的独立子目录里）。
> 建这个目录的直接动因：`app-wifi-scan-flow` / `app-wifi-scan-flow-no-flow` 这对
> Flow on/off 对照工程暴露了一个问题——**我们对 Flow 的认知零散且部分来自猜测**
> （例如"事件 handler 依赖 flowSupport"曾被写进经验库，实测才发现只对 flow 件成立）。

## 目录结构

```
flow-understanding/
├── README.md                        ← 本文件（目的 / 读法 / 索引 / 规矩）
├── MANUAL_MAP.md                    ← 手册地图：章节 ↔ 页码 ↔ 本地全文行号（复查入口）
├── EXAMPLE_PLAN.md                  ← 该补哪些示例：23 个候选（四梯队 ①–㉓）+ 手册/面板/运行时三层证据 + 验收面
├── tools/
│   └── extract_studio_facts.py      ← ★ 从装机 app.asar 抽权威事实（面板可用性 + A43 注册表）
└── notes/                           ← 手册与装机包的结论蒸馏（每条都带锚点）
    ├── flow-execution-semantics.md  ← P6.1–P6.3 执行语义（队列/就绪/线型/四反例）
    ├── flow-variables-expressions.md← P8 变量·表达式·49 个函数·求值时机
    ├── flow-actions-lvgl.md         ← ★ 动作件 LVGL 清单（9 件被禁 / A43 有 65 子动作）
    ├── flow-timeline-animation.md   ← ★ 页面时间线机制（关键帧形态 / opacity 域 / 命中即 break）
    ├── _lvgl_palette_availability.txt        ← 脚本产物：件级可用性原始表
    ├── _lvgl_action_registry_extract.txt     ← 脚本产物：A43 子动作注册表原始 dump（65 项）
    └── _manual_vs_registry_diff.txt          ← 脚本产物：手册 ↔ 装机 差集（真缺 2 项：objGetDisplayX/Y）
```

## 三份资料的分工（别写串）

| 写什么 | 写在哪 |
|---|---|
| 手册**原文事实**（规则、属性、限制） | `flow-understanding/notes/`，必须带 `P6.2 · P.40` 这类双锚点 |
| **换个工程还成立**的踩坑结论 | 经验库 `EEZ Studio_ui_debug_kit/intake/P-01xx` |
| **只在该示例成立**的坑 | 那个示例子目录的 `README.md`（**Flow 机制类示例统一住 [`../flow-examples/`](../flow-examples/README.md)**） |
| 示例**该不该做、验收怎么判** | `EXAMPLE_PLAN.md`（本目录） |

## 读手册的硬规矩（本目录内适用）

1. **双锚点**：每条结论后面要能指出「章节号 + 页码」（本地全文有 `第 N 页 / 共 784 页` 标记，
   `MANUAL_MAP.md` 备好了行号）。给不出锚点的句子一律标 `（推断，待核）`；
2. **区分工程类型**：手册 92 个 Action 里大量属于 EEZ-GUI / Dashboard / EEZ BB3
   （Instrument / SCPI / Modbus / MQTT / Serial / TCP / File / Python / CSV…），
   **LVGL 工程用不到**。任何"Flow 能做 X"的结论，要先确认 X 在 LVGL 运行时存在；
3. **观测面分级**：队列/活跃 Flow/Watch 面板是 **GUI Debug 专属**，headless CLI 与 PC_SIM 都拿不到
   → 涉及执行顺序的验收必须写清是"GUI 看队列"还是"仿真看行为"。

## 与仓库既有铁律的关系

- `AGENTS.md` / 经验库 `EEZ_FIRST_WORKFLOW.md`：**能在 EEZ 实现必须在 EEZ 实现**。
  本目录的作用是把"EEZ 到底能实现什么"变成**有页码依据的清单**，而不是靠试错猜；
- no-flow 对照工程给出的边界：`app-wifi-scan-flow-no-flow/README.md`
  （结论：native 动作不依赖 Flow；表达式绑定 / flow 件 / `SetVariable` 依赖 Flow）。

## 读资料的第四条硬规矩（本次读手册读出来的教训）

4. **手册是二手证据**：判"LVGL 工程能不能做 X"要以**装机包里的注册表/谓词**为第一证据，
   实机 CLI 构建为第二证据。本轮实测已经抓到三处手册与产品不一致：
   - 手册 A43 列 **63** 个 LVGL 子动作，装机注册表是 **65** 个（多 `objGetDisplayX` / `objGetDisplayY`）；
   - 手册正文写了 `Animate`、`OnEvent`、`ShowKeyboard` 等件，但 **9 个件在 LVGL 面板里被禁用**
     （`OnEvent`/`ShowPage`/`ShowKeyboard`/`ShowKeypad`/`ShowMessageBox`/`OverrideStyle`/
     `SelectLanguage`/`SetPageDirection`/`SCPI`）——手册从没说它们不在 LVGL；
   - 手册说 `Id` 字段是 EEZ-GUI 专用、`Persistent` 仅 Dashboard，这类**逐件限制散落在正文各处**，
     没有汇总页。
   重跑取证：`python flow-understanding/tools/extract_studio_facts.py`（只读，不改装机件）。

## 索引 · 目前已确立的结论（详证见 notes）

| # | 结论 | 锚点 |
|---|---|---|
| 1 | 时序线与数据线**语义不同**：前者只传时机（"null data"），后者传数据且**同样触发执行** | P6.1 · P.39 |
| 2 | 就绪条件 = **所有数据输入都有值** 且 **至少一个时序输入收到过**（若存在时序输入）；**没连线终接的输入不参与判定** | P6.2 · P.40 |
| 3 | 件执行完：**时序输入被清除**、**数据输入保留旧值** → 后续仅凭时序线再触发会**复用旧数据** | P6.2 · P.40 |
| 4 | 无输入的件启动即执行（`Start`）；例外是 `CatchError` 与 `OnEvent` | P6.2 · P.41 |
| 5 | 所有活跃 Flow **共用一条执行队列** → `executionQueueSize` 是静态 RAM 的直接代价 | P6.2 · P.40 + P13.2 · P.100 |
| 6 | 编辑器**报错的 Flow 仍允许运行**（"画了不连"不会被构建挡住） | P6.3 · P.42 |
| 7 | 变量四件套：`Evaluate` / `Watch`（**启动即发一次当前值**）/ `SetVariable` / 分支件 | P8.1 · P.58 |
| 8 | Widget 属性可写成表达式，变量变化时属性自动更新 | P8.1 · P.58 |
| 9 | 表达式层**只有 49 个函数**；`LVGL` 命名空间只 1 个（且指向的 W33 是坏链）；**没有 `Array.sort` / `toUpperCase` / `trim` / `replace` / `sqrt` / 保留小数位的 round** | P8.3 · P.63–P.74 |
| 10 | **坐标类属性不是 Flow 表达式**：`Left/Top/Width/Height` 是 Number + 构建期四则运算（只 `+ - * /`），绑变量只会烘成死数字 | 各控件属性提示（如 raw 6693–6699） |
| 11 | `Array.*` 全是**纯函数**（返回新数组，"original array will not be modified"）→ 必须 `SetVariable` 写回 | P8.3.6 · 第 83–85 页 |
| 12 | **LVGL 没有任何内置持久化**：`Persistent` 与 `Read/WriteSetting` 都写明 Dashboard-only | P8 · 第 70 页；A61/A92 |
| 13 | JSON / Blob / Stream / Object 变量 = Dashboard-only；LVGL 要复合数据只能**结构体（需开 Flow）** | P8.2.2/2.4/2.6 · 第 71 页 |
| 14 | **9 个动作件在 LVGL 面板被禁用**（`OnEvent`/`ShowPage`/`ShowKeyboard`/`ShowKeypad`/`ShowMessageBox`/`OverrideStyle`/`SelectLanguage`/`SetPageDirection`/`SCPI`）；`LVGL`(A43) 是 LVGL 专属件 | 装机包 `enabledInComponentPalette`（`tools/`） |
| 15 | A43 实际有 **65** 个子动作（手册只 63，多 `objGetDisplayX/Y`），覆盖切屏/几何/样式/flag/state/**焦点组 7 项**/**动画 7 项**/控件专用 | 装机包 `registerAction`（`tools/`） |
| 16 | 官方 traits 允许 LVGL native 变量为 `enum/integer/float/double/boolean/string`——**与本仓库"只有 int/string 稳、布尔用 integer"的口径冲突，待实测裁决** | 装机包 `LVGLProjectTypeTraits` |
| 17 | 手册自身有缺陷可直接引用为"别照抄"：`<`/`>` 说明写反、`Array.append` 说明是 `String.split` 的复制粘贴、`Math.round(x,2)` 与函数表矛盾、`Date.getDay` 是**月内日不是星期** | raw 2893–2896、3441–3530、第 73 页 |
| 19 | **页面时间线是 Flow 原生能力、运行时已实现**：`Animate` 沿 `parentFlowState` 上溯写页面级 `timelinePosition`，插值在生成的 C 里；游标不变则整段不重算 ⇒ 倒放/跳帧可复现 | `notes/flow-timeline-animation.md`；`eez-flow.cpp:2650-2699` |
| 20 | ★ 手册未写的两条静默失效：关键帧 `opacity` 用 **0..1**（写 70 被夹成全不透明，构建仍 0 错 0 警）；**同一区间拆两帧无效**（codegen 命中第一个就 `break`） | 同上 §3；`screens.c:391,477` |
| 18 | 建 `flow-variables-basics` 实测补充 8 条（无 Flow 时 `defaultValue` 也禁用、`native` 勾选框只在开 Flow 时可切、件类型名=JS 类名、`Watch` 输出名是 `variable`、拼错变量名会被 Checks 拦…） | `notes/flow-variables-expressions.md` §11 |

（`notes/flow-execution-semantics.md` = 1–8 的推导；`notes/flow-variables-expressions.md` = 9–13、17；
`notes/flow-actions-lvgl.md` = 14–16；`EXAMPLE_PLAN.md` = 这些结论该变成哪些示例。）
