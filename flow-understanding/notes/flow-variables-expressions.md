# 变量 · 表达式 · 函数（P8 · 手册 P.57–P.74 / 第 69–86 页）

> 复查锚点见 `../MANUAL_MAP.md`（raw 行 2343–3599 = 整个 P8 章）。
> 本篇口径：**手册明说的**才写"规则"；手册没写的标 `手册未说明`；
> 与本仓库实测冲突的，两条都列并标"待裁决"。
> 本仓库场景固定为 `projectType:"lvgl"` + EEZ Studio 0.29 + LVGL 9.4。

## 1. 作用域与存在性（P8 开篇 · 第 69 页）

| 事实 | 原文要点 | 对本仓库的意义 |
|---|---|---|
| 开 Flow 的工程 | 可有**全局 + 局部**变量；"全局对所有 Flow 可见，**局部只在定义它的那条 Flow 内可见**" | 局部变量是 per-Flow-实例 的状态，不是 per-page |
| **不开 Flow 的工程** | "**只能有全局变量，而且必须是 Native**（由 C++ 代码管理）" | ★ 这正是 `app-wifi-scan-flow-no-flow` 的合法能力面：想要变量就得自己实现 `get_var_*/set_var_*` |
| 变量属性表 | 对话框只问 **Name / Type / Default value**，其余在 Properties 面板改 | — |
| 命名规则 | 字母或下划线开头，后接字母/数字/下划线，**禁空格** | 生成器里变量名要 assert 一遍 |
| `Id` 字段 | "**EEZ-GUI 工程专用**" | LVGL 工程别指望稳定 Id |
| `Default value list` | "仅支持**未启用 Flow 的 EEZ-GUI 工程**" | LVGL 不可用 |
| **Persistent** | "把最后一次值存进 `.eez-runtime-settings`……**仅 Dashboard 工程支持**" | ★ **LVGL 没有任何内置持久化**（详见 §6） |

## 2. 类型清单与 LVGL 可用性（P8.2.1–P8.2.6 · 第 71 页）

| 类型 | 手册定义 | LVGL |
|---|---|---|
| Integer | 有符号 32 位 | ✅ |
| Float / Double | IEEE 4 / 8 字节 | ✅ |
| Boolean | true/false | ✅（但见下方"本仓库实测"） |
| String | 字符序列 | ✅ |
| Date | **就是 Unix 时间戳** | ✅ |
| Any | 可装任意类型 | ✅ |
| Blob / Stream | "仅 Dashboard" | ❌ |
| Object | "仅 Dashboard"（Instrument/PostgreSQL 连接那类） | ❌ |
| **JSON 变量** | "**for now, JSON is only supported in Dashboard projects**"（第 71 页 / raw 2472） | ❌ → LVGL 里要用**结构体**（运行时不可加字段），JSON 只在**表达式层**出现（`json\`…\`` 字面量、`JSON.get`） |
| Structures | "**只能在启用 EEZ Flow 的工程使用**" | ✅ 仅 Flow 版 |
| Enums | 底层是整数，取值受限集合 | ✅ |
| Arrays | 手册全文只有一句"数组变量存多个值" | ⚠ 元素类型/上限/多维**手册未说明** |

> **本仓库实测补充（与手册不冲突但手册没写）**：native 全局变量走 `get_var_*/set_var_*` 桥时，
> 稳定可用的类型只有 **integer / string**，布尔请用 integer 0/1（经验库 P8 节口径 / `07_project_json_schema.md` §3）。
> 手册对 LVGL 的 native 变量工作流**完全没写**（它的交叉引用是坏链 "Chapter XX"）。
> ★ **但装机包 traits 认为 LVGL native 变量支持 `enum/integer/float/double/boolean/string`**
> ——与本仓库口径直接冲突，判据与结案计划见 `flow-actions-lvgl.md` §5 与 `EXAMPLE_PLAN.md` 示例 ⑬。
> **在实测出结论前，写代码仍按仓库旧口径（int/string）走，别拿 traits 当保证。**

## 3. 表达式语法（P8.2.7 · 第 71–72 页）

合法标识符**只有两类**：变量名、**数据输入名**（"用输入的名字取该输入里存的数据"）。

| 元素 | 手册例 |
|---|---|
| 字面量 | `42` `"Hello"` `true` |
| 变量 | `my_var` |
| 输入 | `input_name` |
| 二元/逻辑/一元/三元 | `my_integer_var + 1`、`< 10`、`-x`、`x == 1 ? true : false` |
| 函数 | `String.length(my_string_var)` |
| 括号 | `"Counter: " + (a + 1)` |
| 成员访问 | `my_struct_var.member1` |
| 下标 | `my_array_var[3]`、`my_array_var[index]`（**下标本身可以是变量**） |
| 枚举 | `MyEnumTypeName.Member1` |

字面量细则（P8.2.8 · 第 72–73 页）：

- **模板串**：反引号包裹，支持多行 + `${复杂表达式}`；
- **翻译串**：`T"资源ID"`，**T 前缀必须有**，等价 `Flow.translate("资源ID")`；
- **JSON 字面量**：`` json`{ "a": 1, "arr": [1,2,3] }` ``。

★ **几何属性不是 Flow 表达式**（每个控件的 `Left/Top/Width/Height` 都写着同一段提示）：
类型是 **Number**，"输入表达式回车后**当场求值并把结果固化为属性值**，只允许 `+ - * /` 和括号"
（例：`18 + 36`、`(100 - 32) / 2`）。→ **别想把坐标绑到变量上**，绑了也只会烘成一个死数字。
本仓库"控件树 8 坑"里"声明坐标 == 渲染坐标"的红线就是它的应用面。

## 4. 运算符与类型提升（P8.2.9–P8.2.12 · 第 73–75 页）

- `+` 是唯一有文字规则的运算符：**任一侧是字符串 → 结果是字符串**（`voltage + " V"` → `"1.5 V"`）；
  否则按 double > float > integer 提升；
- `- * %`：布尔被提升成**整数**；
- `/`：**整数 ÷ 整数 = 整数**（截断风险）；布尔参与除法提升为 double；
- 位移/位与或异或：**只接受整数与布尔**，其它组合手册直接标 `err`；
- 一元：`-` 取负、`~` 按位取反、`!` 逻辑非；三元是"唯一三操作元运算符"。

★ **手册自身两处缺陷，引用时别照抄**（我已逐字核过）：

1. P8.2.10 的表把 **`<` 写成 "Greater than"、`>` 写成 "Less than"**（raw 行 2893–2896）；
2. 第 73 页的示例出现 `Math.round(factor, 2)`——而函数表里 `Math.round` **只有一个参数**，
   手册**没有任何"保留 N 位小数"的函数**（无 `sqrt/exp/tan/mod`，也无 π/E 常量）。
   → 需要四舍五入到小数位时，**必须实测**，不能引用手册那行。

## 5. 函数全集（P8.3 · 第 75–86 页，**49 个条目**）

> 这是判"EEZ 能不能实现 X"的**唯一依据**（铁律：EEZ 优先，先查再下结论）。
> 手册分类与逐个签名都在这页，抄录如下；**未列出的就是手册没有**。

| 分类 | 函数 |
|---|---|
| **System**(1) | `System.getTick`（自**本 Flow 启动**起毫秒数） |
| **Flow**(10) | `index`（List/Grid 当前项序号，嵌套时 0=最内层）· `isPageActive` · `pageTimelinePosition` · `makeValue`（造 Struct 值）· `makeArrayValue` · `languages` → `Array:string` · `translate` · `parseInteger` · `parseFloat` · `parseDouble` |
| **Date**(12) | `now` · `toString` · `toLocaleString` · `fromString` · `getYear` · `getMonth`（1–12）· **`getDay` = 月内日 1–31（不是星期！）** · `getHours` · `getMinutes` · `getSeconds` · `getMilliseconds` · `make(y,m,d,h,mi,s,ms)` |
| **Math**(11) | `sin` `cos`（**弧度**）· `pow` · `log` `log10` · `abs` · `floor` · `ceil` · `round`（最近整数）· `min` `max`（**零个或多个**参数） |
| **String**(5) | `length` · `substring(s,start[,end])`（**end 不含**，省略到末尾）· `find`（首个匹配下标，找不到 **−1**）· `padStart(len,pad)`（左补；`pad` 过长会**从尾部截断**）· `split(sep)` → `Array:string` |
| **Array**(7) | `length`(`Array\|json`) · `slice` · `allocate(size)` · `append(array,value)` · `insert(array,pos,value)` · `remove(array,pos)` · `clone`（**深拷贝**） |
| **JSON**(2) | `get(json,"users.3.name")`（点/下标路径）· `clone` |
| **LVGL**(1) | `LVGL.MeterTickIndex`（手册说"见 Meter 控件 W33"——**坏链**：W33 是 `InstrumentTerminal`，Meter 实为 W47，且 W47 里查不到该函数） |

★ 三条可直接指导写法的结论：

1. **Array 函数全是纯函数**：`slice/insert/remove/append` 都返回**新数组**，
   手册反复写 "The original array will not be modified" → 想更新变量必须**把返回值写回**（`SetVariable`），
   原地调用等于什么都没发生。（手册自己的错字也顺手记一下：`Array.append` 的说明是 `String.split` 的复制粘贴，
   `Array.allocate` 的 `size` 类型印成 `Array`。）
2. **没有 `Array.sort`**：排序只能上 `A79 SortArray` **动作件**（见 §7）或交给 native C；
   也**没有** `toUpperCase/trim/replace/concat` → "SSID 大小写/去空格"这类需求手册层面**做不到**，
   要么实测出隐藏函数，要么落 native（`ARCHITECTURE.md` §9 P1 #11 的口径由此可判）。
3. **LVGL 命名空间只有 1 个函数且文档是坏的** → 表达式层基本是"平台无关的那套"，
   别指望有 LVGL 专属 helper。

## 6. 持久化：LVGL 一条都没有（★ 对本仓库最重要的缺口）

- 变量的 **Persistent** 勾选：手册明写 "**Supported only in Dashboard projects**"（第 70 页 / raw 2407）；
- `A61 ReadSetting` / `A92 WriteSetting` 读写 `.eez-project-runtime-settings`，
  手册注释同样把用途限定为 "**survive the Dashboard project restart**"，还说"用持久化变量更方便"
  ——而持久化变量 LVGL 又没有；
- 结论：**LVGL 工程的"记住密码/掉电恢复"必须完全由 native 实现**（NVS / 文件），
  EEZ 侧最多暴露一个 native 变量当门面。
  → `ARCHITECTURE.md` §9 P1 #6（开机恢复路径）不是"待补的设计"，是**框架不给的能力**。

## 7. 求值时机（谁在什么时候被重算）

| 场景 | 手册规则 | 锚点 |
|---|---|---|
| 控件的表达式属性 | "**变量一改，属性就更新**"（Label 绑变量即随变随刷） | P8.1 第 70 页 |
| `Watch` 动作件 | **整条 Flow 期间后台持续求值**；**Flow 启动时必发一次当前值**，之后**只在结果变化时**发 | P8.1 + A91.1 第 329 页 |
| 动作件属性（`Evaluate`/`Compare` A·B·C/`IsTrue`/`SwitchCase` 各 case/`SetVariable` 各项/`Loop` from-to-step） | **该件轮到执行时**求值一次 | P8.1、A73、A81 |
| 件能否被执行 | 见 `flow-execution-semantics.md` §2（数据输入齐 + 至少一条时序输入到过） | P6.2 第 54 页 |
| `System.getTick` | 运行时相对时间（不是编译期常量） | P8.3.1 |

手册**没有说**：表达式是否惰性/记忆化、依赖如何追踪、有无环保护、不加 Flow 时怎么求值 → `手册未说明`。
**Expression Builder**（P8.4 · 第 86 页）全部内容只有三句话：Action 与 Widget 都支持表达式；
**每个可被表达式求值的属性都有一个 `...` 图标**打开编辑器；可手输也可用编辑器。
→ 实用推论：**看属性右侧有没有 `...` 图标，就能判断它能不能绑表达式**（比猜属性类型可靠）。

## 8. 属性方向：读 / 写 的三种写法（手册没有总纲，逐件标注）

| 记法 | 含义 | 手册实例 |
|---|---|---|
| `EXPRESSION (类型)` | **只读**：属性的值由表达式算出 | `A21 Expression`、`W57 Label`、`A92 Value` |
| `ASSIGNABLE EXPRESSION (类型)` | **写目标**：表达式必须解析成一个可写位置，件把值**写进去** | `A42 Loop.Variable`、`A88 TestAndSet.Variable`、`W57 Radio.Group variable` |
| `<某属性>` + `<某属性> type` = Enum(**Literal / Assignable**) | LVGL 控件的**双向回写开关**：选 Assignable 时该字段就变成"存用户输入的变量" | `W24 Dropdown.Selected`、`W69 Spinbox.Value/Step`、`W78 Tabview.Active tab`、`W2 Arc.Checked/Disabled` |

→ **`w67`（Slider/Arc 双向、Bar 单向）和 `w23`（Dropdown+Roller 同绑）实测到的行为，
   在手册里就是这张表**；反过来，`Switch/Checkbox` 无绑定属性这点也对得上（它没有 Assignable 字段）。

★ 手册还给了一个**避免破坏性写回**的技巧（重复出现在动作件说明里，如 A91.2.3/2.4）：
"可以把 **输出名** 填进 `Variable` 这类属性，而不是变量名——这样该件**不再改写变量**，
只把当前值从那个输出送出去"（Loop 的说明就是原文举的例子）。

## 9. 与执行语义联动的坑（可直接写成示例的反例）

1. `Watch` 启动即发一次 → 页面一进去就可能触发一串动作（**不是 bug**，别在它下游放幂等性差的命令）；
2. 数据输入保留旧值 + 时序输入被清除（`flow-execution-semantics.md` §2 第 5 条）
   → "第二次点击复用了上一次的数据"这类现象有手册依据；
3. `Constant`（A10）的表达式**禁止引用变量**（第 137 页原文 "must not use variables"）；
4. 坐标类属性是**构建期四则运算**，不会随变量变（§3）；
5. Array 纯函数不写回就等于没做（§5 第 1 条）；
6. `+` 的字符串吞噬（`"1" + 2` → `"12"` 型语义，§4）；整数除法截断（§4）；
7. 手册的 `<`/`>` 标签反了（§4）→ **教学材料里不要复制那张表**。

## 10. 观测面（别在 headless 里找）

Debug 模式面板清单（P4.4 · 第 46 页）：**Active Flows / Watch / Queue / Breakpoints / Logs**
（Logs 分 Fatal·Error·Warning·Info·Debug·SCPI，可过滤）。
Watch 面板同时给：全局变量值 + **当前活跃 Flow 的局部变量** + **下一个待执行件的输入状态**（P6.2 第 53 页）。
Flow 名后面的括号数字 = 该 Flow 状态的**内存地址**。
→ 手册**没说** LVGL 工程是否享有同一套 Debug 面板 → `手册未说明`，
   涉及"顺序/队列"的验收必须现场开 GUI 确认（见 `EXAMPLE_PLAN.md` 的 GUI-only 标注）。
