# AGENTS.md — LVGL / EEZ UI 开发默认流程

**适用范围：本工程内所有 LVGL / EEZ Studio UI 开发任务，默认生效，无需每次点名。**

## 流程唯一真值

统一走本地经验库 kit 的流程文件（本机路径，换机需重核）：

```
C:\Users\yjt54\Desktop\local_knowledge_base\embedded\EEZ Studio_ui_debug_kit\EEZ_FIRST_WORKFLOW.md
```

同目录配套：`PLAYBOOK.md`（通用方法论）、`skills.md`（操作手册）、`INTAKE.md`（留痕规约）、
`tools/`（run_gate 等 kit 工具）、`EEZ-Studio-reference-guide.pdf`（官方手册存档）。

动手前先读 `EEZ_FIRST_WORKFLOW.md`，按其中**七步主链**执行：

① 改设计源 → ② 生成器出 EEZ 工程 → ③ EEZ 构建（GUI Build 或 headless）→
④ **EEZ 里看效果 = 主验收**（画布核视觉、Run 模式核交互）→ ⑤ 仿真辅助（仅点名时）→
⑥ 门禁全绿 → ⑦ 真机终验（仅点名时）。顺序纪律：④ 必须在 ⑤ 之前。

## 铁律摘要（详见流程文件 §0）

1. **EEZ 优先**：能在 EEZ 实现的必须在 EEZ 实现；`src/native` C 代码只允许用于控制外部硬件。
   判"EEZ 做不到"前必须四面对查（事件面/动作面/Loop+Delay 调度面/运行时源码面），
   查完仍不行须通知用户、取得同意才可出 EEZ。
2. **默认只跑 EEZ 侧闭环，仿真器与真机等用户点名**；跳过仿真时在注释留
   "下次跑仿真前需同步"清单，交付说明注明"本次未经仿真量化验证"。
3. **改动只落设计源/生成器/EEZ 工程**；`src/ui` 是覆盖式重写产物，永不手改。
4. **每条新需求按五元组提示词写**（目标/口径/验收/约束/验证与归档，见流程文件 §6）；
   缺项先补问再动手。观感类形容词两轮对不上就要求标注截图/数值目标，禁猜第三轮。
5. **留痕**：用户提示词逐字追加 `prompts/PROMPT_LOG.md`（PR-####），新问题登记 `intake/`（P-####）。
