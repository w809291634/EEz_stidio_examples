# flow-variables-basics —— EEZ Flow「变量的使用方法」示例（纯 EEZ，零 native C）

> 本例住在 **`flow-examples/`**（Flow 机制类示例的容器，规则见
> [`../README.md`](../README.md)）；相对路径都按这一层写（`../../flow-understanding/…`）。


> **演示点**：Flow 打开时，变量到底**怎么读、怎么写、活在哪一层**。
> 一个页面把四条读法、四条写法、两种作用域全部摆出来，每条都标了手册页码；
> 配套理论见 `../../flow-understanding/notes/flow-variables-expressions.md`。

## 0. 先回答"变量区分不区分 flow"

**变量表只有一张，不分裂成"flow 变量"和"UI 变量"两种。**
决定用法的是**两条独立的轴**：

| 轴 | 取值 | 后果（谁持有值） |
|---|---|---|
| 工程 `settings.general.flowSupport` | `true` | 值可以活在 **Flow 引擎**里；能用表达式属性、`SetVariable`/`Watch`/`Evaluate`/`Switch` |
| | `false` | **只能有全局变量，而且必须 native**（手册 P8 · P.57 原话），值活在 C++ 里，EEZ 侧没有 Flow 可用 |
| 变量自身 `native` 标志 | `false` | EEZ 持有值（本示例四个 `g_*` 全是这种） |
| | `true` | C++ 持有值，EEZ 生成 `get_var_xxx/set_var_xxx` 声明，**必须自己实现桥**（P-0153），Flow 仍可读写它 |

两轴交叉出三种真实形态，本示例覆盖第 1、3 种，第 2 种在姊妹工程里：

1. **Flow 开 + `native:false`** → 本示例：变量完全由 EEZ 管，零 C 代码；
2. **Flow 开 + `native:true`** → 见 `app-wifi-connect` 系列（`src/native` 里实现 `set_var_*`）；
3. **Flow 关** → 见 `../../app-wifi-scan-flow-no-flow/`：所有全局变量被迫 native。

★ 另外两个只有 LVGL 工程吃得到的限制（装机包里逐条验证过）：
`persistent` 复选框在 LVGL **禁用**（手册 P.58 写"仅 Dashboard"），
所以 LVGL 想掉电保存只能自己写 NVS；
`defaultValue` 在 LVGL **未开 Flow 时也禁用**——因为那时 EEZ 根本不负责初始化值。

## 1. 演示矩阵（页面上每一行对应一条）

| 编号 | 用法 | 页面元素 | 手册锚点 |
|---|---|---|---|
| 读① | 控件属性 = 变量表达式 | `val_count` 的 `text = g_count` | P8.1 · P.58 |
| 读② | 模板字符串插值 | `val_tpl = ` `` `count=${g_count} double=${g_double} flag=${g_flag}` `` | P8.2.8 · P.60 |
| 读③ | 单向跟随（input 型属性） | `bar_count.value = g_count`，**拖不动它** | W 属性表 |
| 写④ | 双向回写（assignable） | `sld_count.value = g_count`，拖动即改变量 | P8.2.7 |
| 写⑤ | `SetVariable` 单条 | 按钮 `+1` → `g_count = g_count + 1` | A73 · P.188 |
| 写⑤′ | `SetVariable` **批量** | 按钮 `批量写` → 一次写 5 个变量 | P8.1 "Multiple entries are allowed" |
| 写⑥ | `Evaluate` → **数据线** → `SetVariable` | `expression = g_count * 2`，`result` 线接到目标件的自定义输入 `r`，再 `g_double = r` | A21 · P.53 + P8.2.7 |
| 监听⑦ | `Watch` 监听变量，变化即触发下游 | 无按钮：`Watch(g_count)` → `variable`(changed) 线 → `g_flag = v > 3`、`g_status = ${v} is watched` | A91 + P8.1（**启动时必发一次**） |
| 分支⑧ | `Switch` 判变量值 | `+1` 之后串一条：`g_count >= 10` → 写 `g_branch` | A81/A8 · P.308 |
| 作用域⑨ | 全局变量 `g_*` | 所有 Flow 都看得见 | P8 · P.57 |
| 作用域⑩ | **页面局部变量 `l_step`** | 按钮 `+l_step` → `g_count = g_count + l_step`，只在定义它的这条 Flow 内可见 | P8 · P.57 |

★ 为什么分支特意写 `g_branch` 而不是 `g_status`：
`Watch` 链也在写 `g_status`。两个 writer 抢同一变量时，演示结论会取决于队列顺序而变得含糊——
**故意分开**，才能一眼看出"哪条链真的跑了"。

## 2. 工程结构

```
flow-variables-basics/
├── build_example.py                 ← 唯一设计源（改 UI/改流图都改它）
├── flow-variables-basics.eez-project ← 生成产物，EEZ Studio 可直接打开看流图
├── fonts/simhei.ttf                 ← 中文字体源（按钮文案有中文）
├── design/
│   ├── cli_build.py                 ← EEZ headless CLI 构建 + flow 错误守卫
│   ├── gen_font.py                  ← 烘 src/ui/fonts/ui_font_cn14.c（CLI 不烘，P-0140）
│   ├── audit_chars.py               ← 逐字审计（屏上字符 ⊆ 字体字符集）
│   └── sim_cmake/                   ← run_sim.bat + main.c + lv_conf.h（从 tabview 干净拷贝）
└── src/ui/                          ← EEZ 生成（禁手改）；★ 有 eez-flow.cpp/h（Flow 在跑）
```

**没有 `src/native/`**：本示例的全部逻辑在 EEZ 的流图里，一行 C 都不写——这是它与
`app-wifi-scan-flow*` 系列的根本区别，也是"EEZ 优先"铁律的正例。

## 3. 依赖版本

| 项 | 值 |
|---|---|
| EEZ Studio | 0.29.0（`projectVersion=v3`，`projectType=lvgl`） |
| LVGL | 9.4.0（PC 仿真宿主 9.5） |
| 屏幕 | 480×320，深色，16bpp |
| 字体 | **`cn14`（simhei 子集 98 字 = ASCII 可打印 + `批量写`）**——UI 上有中文就必须挂字体条目，见 §4 |
| flowSupport | `true`；`generateSourceCodeForEezFramework=true` |

## 4. 怎么用

```bat
python build_example.py            rem 生成 .eez-project；★ 内含字体覆盖自检（缺字拒绝生成）
python design\cli_build.py         rem 判据：BUILD RESULT: ok + 产物对账（见 §5）
python design\gen_font.py          rem ★ 必须在 cli_build 之后（CLI 不烘字体 .c，P-0140；
                                   rem    且孤儿清理会把先烘出来的字体 .c 删掉）
python design\audit_chars.py       rem 逐字审计：屏上会出现的字符 ⊆ 字体字符集
双击 design\sim_cmake\run_sim.bat  rem 编译 + 起窗口，点四个按钮看变量动
```

★ **为什么一个"讲变量"的示例要带字体链**：按钮文案 `批量写` 是中文。EEZ 的 LVGL 工程
只要屏上有非 ASCII 字符，就必须 ①在工程里挂字体条目、②生成后烘 `.c`、③把控件的
`text_font` 指过去——三件缺一件就是**一片豆腐，而且构建 0 错 0 警**（本轮就是这么翻车的：
README 原先写"文字全 ASCII"，实际有中文，Run 预览里直接露馅）。所以生成器里加了
`_check_font_coverage()`：它从**生成的工程 JSON** 里扫非 ASCII 字符（`description` 是编辑器
注释、不上屏，排除），缺字直接拒绝生成，不靠人记。

想看流图：EEZ Studio 打开 `.eez-project` → Page `Main` 的 **Flow 画布**，
9 个件 + 10 条连线（4 条事件线、2 条数据线、时序线）都在里面。

## 5. 本轮实测状态（2026-10-21）

| 检查 | 命令 | 结果 |
|---|---|---|
| CLI 构建 | `python design\cli_build.py` | `BUILD RESULT: ok`，`No error and no warning detected` + `EEZ Flow engine built`，assets **3,212 B** ✓（挂字体前是 1,210 B，多的 2 KB 就是字体条目进 `assets[]` 的物证：`ui.c:8 const uint8_t assets[3212]`） |
| ★ 中文字体链 | `gen_font.py` → `audit_chars.py` → `grep` | `src/ui/fonts/ui_font_cn14.c` **32,572 B**；`fonts.h:10 extern const lv_font_t ui_font_cn14`；`screens.c` 里引用 `&ui_font_cn14` **16 处**；审计 `UI 非 ASCII 字符数: 3 / OK` ✓ |
| 产物对账 | `ls src/ui` | 12 模板文件 + **`eez-flow.cpp`(9,923 行) + `eez-flow.h`** ✓（Flow 在跑的物证） |
| 变量入码 | `grep` `src/ui/vars.h` | `FLOW_GLOBAL_VARIABLE_G_COUNT/G_DOUBLE/G_FLAG/G_STATUS/G_BRANCH` 五个枚举项 ✓（`native` 区为空——本示例没有 native 变量） |
| 流引擎在位 | `nm ..\..\PC_SIM\lv_port_pc_vscode_v9.5\bin\main.exe \| grep -c "_ZN3eez4flow"` | **541** 个 `eez::flow` mangled 符号（含 `setGlobalVariable`/`eez_flow_tick`；对照 `app-wifi-scan-flow-no-flow` = **0**）✓ |
| ★ 局部变量在哪里 | 生成码里**没有** `l_step` 的 C 符号 | 局部变量不进 `vars.h`，它编译进 `assets` 的流定义里 → 所以**不能靠 grep 证明它生效**，用下面的负控证明 |
| 回写入码 | `grep assignIntegerProperty src/ui/screens.c` | **只有 Slider**（`Failed to assign Value in Slider widget`），Bar 没有 → 印证"Slider/Arc 双向、Bar 单向" ✓ |
| 事件入流 | `grep flowPropagateValueLVGLEvent src/ui/screens.c` | 4 处（= 4 个按钮）✓ |
| ★ 负控 A（局部变量真实性） | 把 `l_step` 改成 `l_bogus` 重新构建 | `FLOW-ERR: identifier 'l_bogus' is neither input or local or global variable` → **2 errors**；改回即 0 错 → 证明 Checks **确实**在校验标识符、`l_step` 确实按**局部变量**解析 ✓ |
| ★ 负控 B（画布重叠守卫） | 内存里把最后两件挪到同一坐标再调 `_assert_flow_boxes()` | `流组件画布重叠：分支⑧：Switch 判 g_count × 分支⑧'：命中后写 g_branch`，退出码 1；正常坐标 PASS ✓ |
| 布局自检 | 顶层 17 个控件逐个比矩形 | 无重叠、无越界 ✓ |
| PC_SIM 编译链接 | `run_sim.bat build` | `[8/8] Linking ... build succeeded` ✓（挂字体后增量重编：`ui_font_cn14.c` 作为一个编译单元进 `main.exe`，链接期没有 `undefined reference: ui_font_cn14` ⇒ 字体真的在二进制里） |
| ★ 迁移后重验 | 从仓库根搬进 `flow-examples/` 时**删了 `design/sim_cmake/build_rel/`** 再全量重配 | 重编 `[537/537]` 通过、`main.exe` 已刷新（16:15）、`nm` 仍有 541 个 flow 符号 ✓<br>（不删缓存会拿旧绝对路径去编上一个位置的工程——这就是容器规则里"迁移必删 build_rel"的原因） |


**未做**：行为验收（点按钮看 `val_count` 变化、`Watch` 是否启动即发一次）。
按仓库口径仿真默认不擅自跑（`EEZ_FIRST_WORKFLOW` / 默认 EEZ 闭环，仿真等点名）。
要验的话：`WIFI`-无关，直接起窗口点 `+1` 四次 → `flag` 应从 `false` 变 `true`
（`Watch` 判 `v > 3`，注意是"大于"，第 4 次 `g_count=4` 才成立）。

## 6. 踩过的坑

- ★ **Flow 件的 JSON `type` 名 = Studio 里的类名**，不能猜：`SetVariableActionComponent` /
  `WatchVariableActionComponent` / `EvalExprActionComponent` / `SwitchActionComponent`；
  属性键也是类里的名字（`entries` / `variable` / `expression` / `tests`）。
  取法（可复现）：从装机 `app.asar` 里抽 `ActionComponent.classInfo`，
  见 `../../flow-understanding/tools/extract_studio_facts.py` 同源做法。
- ★ **`SetVariable.entries` 的键是 `variable` + `value`**（不是 `name`/`expression`）：
  `{"variable": "g_count", "value": "g_count + 1"}`，`variable` 侧是**可赋值表达式**。
- ★ **`Watch` 的输出名是 `variable`，displayName 才叫 changed**：连线时
  `"output": "variable"`；写成 `"changed"` 会报未连接。它的属性名也叫 `variable`
  （表达式），两处同名不同义，别混。
- ★ **`Evaluate` 的 `result` 是数据线**：目标件必须**自己加自定义输入**（`customInputs:[{name:"r",type:"any"}]`）
  并在表达式里**用名字 `r` 取值**；只连数据线不连时序线会被"至少一条时序输入"卡死（P6.2 就绪判定）。
  自定义输入的 `type` 必须显式给（这里给 `"any"`），否则 Checks 面板一直转圈（P-0146 同款）。
- ★ **事件进 Flow 用 `handlerType:"flow"`**，连线源就是控件的 `objID`、输出名 = 事件名（`CLICKED`）。
  与 `app-wifi-scan-flow` 的 `handlerType:"action"`（走 native 动作）是两条不同的路——
  这正是"EEZ 内实现"和"甩给 C"的分界。
- **`Switch` 没有兜底分支就什么都不发生**：`tests` 里只写 `g_count >= 10`，
  不满足时它不输出任何东西（手册 A81 建议放一条 `When = true` 兜底）。
- **流图画布也会"叠件"**：`build_example.py` 的 `main()` 里有 `_assert_flow_boxes()`，
  两件重叠直接退出。负控实测（把 `f_full` 从 `(240,390)` 挪到 `(240,300)`）：
  `流组件画布重叠：监听⑦'：变化结果写回 × 分支⑧'：命中后写 g_branch`，退出码 1。
  首版就踩过这个——9 个件里有 8 个坐标互相压着，Studio 里打开会糊成一团（控件层另有一套
  矩形自检，见 §5 的"布局自检"行）。
- **不要建 `src/native/`**：本示例的价值就在于证明"变量用法一行 C 都不用写"。
  一旦加 native 就变成第二个 `app-wifi-scan-flow`，演示点消失。

## 7. 相关

- 理论/取证：`../../flow-understanding/notes/flow-variables-expressions.md`（变量·表达式·49 函数）、
  `../../flow-understanding/notes/flow-execution-semantics.md`（为什么数据线+时序线要成对连）
- 对照工程：`../../app-wifi-scan-flow/`（Flow 开但**零变量**、逻辑在 native）·
  `../../app-wifi-scan-flow-no-flow/`（Flow 关）——三个工程合起来是变量归属的完整光谱
- 双向回写控件的完整属性面：`../../w67-w3-w2-slider-arc-bar/`
