# flow-examples —— EEZ Flow 专题示例的家

> **为什么单独一个目录**：Flow 的学习型示例会一串接一串地长出来（执行语义、动作目录、
> 函数体检台、状态机、数组排序……见 `../flow-understanding/EXAMPLE_PLAN.md` 的 14 项）。
> 全堆在仓库根会把"一个示例=一个根目录"的索引冲垮，所以 **Flow 类示例统一进本目录**，
> 每个示例仍是**本目录下的一个独立子目录**，内部结构与仓库模板完全一致。

## 1. 归属判据（什么进这里，什么不进）

| 情况 | 放哪 |
|---|---|
| 演示点是**Flow 机制本身**（变量用法、执行队列、动作件、表达式、作用域、连线语义） | **本目录** |
| 演示点是**控件/样式/字体**等静态形态（W 号专题：Slider、Chart、Led…） | 仓库根（`w67-…`、`w14-…` 等，命名带手册 W 号） |
| 演示点是**完整应用/架构**（EEZ 外壳 + native 业务分层） | 仓库根（`app-wifi-scan-flow`、`app-wifi-scan-flow-no-flow`、`app-wifi-connect`） |
| 手册事实蒸馏、取证脚本、示例规划 | `../flow-understanding/`（**只放结论，不放工程**） |

判据冲突时问一句：**"这个示例的坑，是坑在 Flow 语义上，还是坑在控件形态上？"** 前者进这里。

## 2. 命名

`flow-<主题>[-<细分>]`，kebab-case，见名知意，**不带 W 号**（W 号规则只针对控件专题示例）：

```
flow-variables-basics/          变量使用方法（已建）
flow-execution-semantics/       执行队列与就绪语义（EXAMPLE_PLAN ①）
flow-expression-function-bank/  49 个表达式函数体检台（EXAMPLE_PLAN ②）
flow-lvgl-actions-catalog/      A43 的 65 个子动作目录（EXAMPLE_PLAN ③）
```

## 3. 每个示例子目录的骨架（与仓库模板一致，不得省略）

```
flow-examples/<flow-主题>/
├── build_example.py             ← 唯一设计源；产物 .eez-project 勿手改
├── <flow-主题>.eez-project
├── design/
│   ├── cli_build.py             ← 逐字拷贝，只改 1 处 PROJ 工程名
│   └── sim_cmake/               ← run_sim.bat + main.c + lv_conf.h（逐字拷贝）
└── src/ui/                      ← EEZ 生成产物（含 eez-flow.cpp/h）
```

拷贝源与五步流程照 [`../示例工程模板说明.md`](../示例工程模板说明.md)（根目录那份）；
★ **改名/换位置时必须删本工程 `design/sim_cmake/build_rel/` 全量重配**
（里面缓存的是旧绝对路径，不删会出现"编的是上一个工程"的假绿）。

## 4. 每个 Flow 示例的 README 必须回答的四件事

除模板要求的（演示点 / 工程结构 / 依赖版本 / 踩过的坑）之外，Flow 专题额外加两栏：

1. **手册锚点表**：每条演示点对应 `P6.2 · P.40` 这种页码，出处去
   `../flow-understanding/MANUAL_MAP.md` 查行号复查；
2. **面板/运行时证据**：用到哪个动作件，写清它属于
   `../flow-understanding/notes/flow-actions-lvgl.md` 的哪一档
   （LVGL 专属 / 面板允许 / **LVGL 禁用的 9 件**）——禁用件一旦出现在示例里就是设计错误。

## 5. 索引登记（三处，缺一处就是悬空）

1. 本文件下面的 §6 清单表；
2. 根 [`../README.md`](../README.md) 示例索引表（一行汇总，链接写 `flow-examples/<名>/`）；
3. 根 [`../CODE_WIKI.md`](../CODE_WIKI.md) §8 索引表。

## 6. 清单

| 目录 | 演示点 | 状态 |
|---|---|---|
| [`flow-variables-basics/`](flow-variables-basics/) | Flow 变量的使用方法：读（表达式/模板串/Bar 单向）· 写（Slider 回写、`SetVariable` 单条与批量、`Evaluate`→数据线→`SetVariable`）· 监听（`Watch`）· 分支（`Switch`）· 作用域（全局 vs 页面局部 `l_step`） | CLI `BUILD RESULT: ok`（0 错 0 警，assets 1,210 B）+ 产物对账 + PC_SIM `[537/537] build succeeded`；**从仓库根迁入本目录时已删 `build_rel` 全量重配并复验通过**；两个负控（写错变量名 / 画布重叠）均生效；★ **行为验收未做**（点按钮看变量动，需起仿真） |

## 7. 与 `flow-understanding/` 的分工（别写串）

- 这里放**能构建、能打开的工程**；那里放**读手册与装机包的结论**；
- 示例里踩到的**通用** Flow 坑（换个 Flow 工程还成立）→ 回写
  `../flow-understanding/notes/`（带页码），再回灌经验库 `intake/`；
- 只在该示例成立的坑 → 留在该示例自己的 `README.md`。
