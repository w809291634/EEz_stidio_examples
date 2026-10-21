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
├── notes/                           ← 手册结论蒸馏（每条都带 P/A 锚点）
│   └── flow-execution-semantics.md  ← ★ P6.1–P6.3 执行语义（队列/就绪/线型/四反例）
└── EXAMPLE_PLAN.md                  ← 该补哪些示例：候选清单 + 手册出处 + 验收判据
```

## 三份资料的分工（别写串）

| 写什么 | 写在哪 |
|---|---|
| 手册**原文事实**（规则、属性、限制） | `flow-understanding/notes/`，必须带 `P6.2 · P.40` 这类双锚点 |
| **换个工程还成立**的踩坑结论 | 经验库 `EEZ Studio_ui_debug_kit/intake/P-01xx` |
| **只在该示例成立**的坑 | 那个示例子目录的 `README.md` |
| 示例**该不该做、验收怎么判** | `EXAMPLE_PLAN.md`（本目录） |

## 读手册的三条硬规矩（本目录内适用）

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

（`notes/flow-execution-semantics.md` 是第 1–8 条的完整推导；函数表与 A43 LVGL 子动作清单待补。）
