# EEZ_stidio_examples — EEZ Studio 示例工程库

> 本仓库收 **EEZ Studio 示例工程**：一个工程一个独立子目录，每个工程演示一类用法、提供一份可拷走复用的实例。
> 使用经验与方法论的沉淀在本地经验库 `C:\Users\yjt54\Desktop\local_knowledge_base`（下称「经验库」）。
> 最后更新：2026-10-19。

---

## 1. 怎么获取 EEZ Studio 的使用经验

按优先级四条途径（详细说明见经验库
`embedded/EEZ_Studio_examples/README.md`）：

1. **先查经验库已有积累**（最快）—— `local_knowledge_base/embedded/EEZ Studio_ui_debug_kit/`：
   - `PLAYBOOK.md`：通用方法论（三层图策略 / 差异量化四步法 / 组件树 8 个通用坑 / 十条红线）
   - `skills.md`：操作手册（自动设计 → 对照查验 → 仿真器真点击）
   - `EEZ_FIRST_WORKFLOW.md`：EEZ 为主、仿真为辅的栈专属流程（验证优先级金字塔 / 七步主链）
   - `cases/`、`intake/`、`prompts/`：历史案例、问题登记、提示词留痕
2. **官方渠道** —— <https://github.com/eez-open/studio>（`docs/` 有使用文档）；
   新建工程向导里的 **Templates / Examples** 是最直接的写法参照；issues 区搜报错关键字。
3. **做示例工程积累** —— 每学会一类用法，就在本仓库落一个最小示例工程（见第 2 节），
   踩的坑写进该工程的 `README.md`，通用结论回灌经验库。
4. **AI 协作留痕** —— 让 AI 改 EEZ 工程时，用 ui_debug_kit 的
   `log_entry.py` 把提示词与新问题追加进经验库记录区（规约见其 `INTAKE.md`）。

---

## 2. 怎么建子目录保存工程文件夹

**一个示例工程 = 一个独立子目录**，目录名即示例主题（kebab-case，见名知意）：

```
EEZ_stidio_examples/
├── README.md              ← 本文件
├── <示例主题>/             ← 每个工程一个独立文件夹
│   ├── README.md          ← ★ 必备（写什么见下）
│   ├── <工程名>.eez-project
│   └── ...
└── ...
```

### 新建一个示例工程的固定动作

1. 在本仓库根新建 `<示例主题>/` 子目录；
2. 拷入 EEZ 工程文件（`.eez-project`、`.ei`、`vars/` 等），
   **剔除可再生产物**：`build/`、`generated/`、SDK 拷贝、大体积缓存；
3. 为该工程写 `README.md`，最少写清四件事：
   - **演示点**：这个示例演示什么用法；
   - **工程结构**：关键文件各自是什么；
   - **依赖版本**：EEZ Studio 版本、LVGL 版本、目标平台；
   - **踩过的坑**：症状 / 根因 / 修法（严重坑在标题加 ★）；
4. 在本文件第 3 节索引表加一行。

### 与经验库的分流

- **只在本示例工程成立** → 写进该工程子目录的 `README.md`；
- **换一个 EEZ 工程还成立**（组件树通用坑、对照查验方法、工具用法）→
  回灌经验库 `embedded/EEZ Studio_ui_debug_kit/` 记录区（`intake/` / `skills.md`）；
- **机器相关路径**（每台电脑不同的 B 类路径）不当事实写死，一律按 `{占位符}` 处理。

---

## 3. 示例工程索引

| 目录 | 演示什么 | 一句话 / 关键坑 |
|---|---|---|
| （暂无；新增示例后在此加行） | | |
