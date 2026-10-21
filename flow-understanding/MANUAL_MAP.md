# 手册地图 · EEZ Studio Reference Guide（本地全文锚点）

> **为什么要这张表**：手册正文 784 页，靠翻 PDF 找一条执行语义规则要几分钟；
> 本仓库已有一份**提取全文**，任何结论都能用「行号 + 页码」双锚点秒级复查。
> 本文件只做**地图**，结论写在 `notes/` 各篇里，每条结论都回指这里的锚点。

## 资料位置（★ 本机路径，换机器需重新确认）

| 件 | 路径 | 说明 |
|---|---|---|
| 英文提取全文 | `C:\Users\yjt54\Desktop\local_knowledge_base\embedded\EEZ Studio_ui_debug_kit\reference_guide_raw.txt` | **28,653 行**，含 `========== 第 N 页 / 共 784 页 ==========` 分页标记 |
| 英文原 PDF | 同目录 `EEZ-Studio-reference-guide.pdf` | 原始件 |
| 中文全译版 | `C:\Users\yjt54\Desktop\AI临时回话\output\pdf\EEZ-Studio-参考指南-中文全译版.pdf` | 文本重排（阅读用） |
| 中文原版式 | 同目录 `EEZ-Studio-参考指南-中文原版式-784页.pdf` | 页码与英文版一一对应，**引用页码时以这版为准** |

复查命令示例（在经验库目录下）：

```bash
grep -n "^P6\.2\. Flow execution" reference_guide_raw.txt      # 定位章节
sed -n '1889,1980p' reference_guide_raw.txt                    # 读该节全文
awk 'NR>=1889 && /第 [0-9]+ 页/' reference_guide_raw.txt        # 找页码标记
```

## 正文章节锚点（P 系列）

| 章节 | 手册页 | raw 行 | 与本仓库的关系 |
|---|---|---|---|
| P1 Home page project sections | P.7 | 1016 | 工程类型（EEZ-GUI / Dashboard / **LVGL**）差异的入口 |
| P5.1.2 User Actions | P.34 | 1757 | `actions[]` 段（native / flow 两种实现） |
| P5.1.3 User Widgets | P.34 | 1767 | `userWidgets[]` 段 |
| P5.2.1 Page viewer | P.37 | — | Run 预览的行为边界（P-0141：预览不产生 GESTURE） |
| **P6.1 Flow basic concepts** | **P.39** | **1834** | 五种基本元素：Widget / User Widget / Action / User Action / **两条线** |
| **P6.2 Flow execution** | **P.40** | **1889** | ★ 执行队列与就绪判定、sequence/data 输入的清除与保留规则 |
| **P6.3 Flow examples** | **P.42** | **1959** | 4 个连线正/反例（含"编辑器报错但允许运行"） |
| P7.1.1 Connecting Flow components | P.46 | 2100 | 连线规则 |
| P7.2.2 Creating a User Widget | P.50 | 2200 | 复用片段 |
| P7.3.2 Creating a User Action | P.53 | 2321 | 复用逻辑 |
| **P8.1 Variables usage（启用 Flow）** | **P.58** | **2408** | ★ 变量四件套：Evaluate / Watch / SetVariable / 分支件 |
| P8.2 Variable types | P.59 | 2434 | 基本类型 / 结构体 / 枚举 / 对象 / 数组 / JSON / 表达式 / 字面量 |
| P8.2.9–8.2.12 运算符 | P.61-63 | — | 二进制/逻辑/一元/三元 |
| **P8.3 Functions（函数表）** | **P.63-74** | **2918** | ★ 表达式能调用的全部函数，8 个分类；**LVGL 分类只有 1 个** |
| P8.4 Expression Builder | P.74 | 3594 | GUI 里的表达式助手 |
| P9.5.3 LVGL project（样式属性） | P.82 | 3875 | LVGL 工程的样式属性面 |
| P10.x Bitmaps | P.85 | — | 图片（本仓库 P-0140：CLI 不产图片 .c） |
| P11.2 LVGL project fonts | P.91 | 4167 | 字体条目（对应 `font-entry-form` 示例） |
| P12.x Texts / XLIFF | P.95 | 4225 | 多语言（i18n） |
| **P13.2 Build** | **P.100** | **4360** | ★ 影响 flash/RAM 的三个选项（queue/压缩/求值栈） |

## 动作附录锚点（A 系列，共 92 件）

TOC 清单在 raw 行 **4482–4586**（`A1. AddToInstrumentHistory … A92. WriteSetting`），
附录正文从 **4586** 起。**每件动作用 `grep -n "^A<编号>\. <名字>"` 定位。**

| 编号 | 名字 | raw 行 | 备注 |
|---|---|---|---|
| A2 | Animate | 4737 | 动效 |
| A15 | Delay | — | 非阻塞延时（内部状态件） |
| A21 | Evaluate | — | 表达式求值 → `result` 数据线 |
| A28 | FocusWidget | — | 焦点/键盘组 |
| A32 / A54 | Input / Output | — | User Widget / User Action 的边界件 |
| A36 | IsTrue | — | 分支 |
| A41 | Log | — | 开发期可见性 |
| A42 | Loop | — | 循环（内部状态件） |
| **A43** | **LVGL** | **7300** | ★ LVGL 专属子动作大清单（切屏/对象几何/样式/旗标/状态…） |
| A53 | OnEvent | 8543 | 页面 open/close 等事件 |
| A55 | OverrideStyle | — | 运行时改样式 |
| A72 | SetPageDirection | — | 页面方向 |
| A73 | SetVariable | — | 批量赋值 |
| A75 / A76 | ShowKeyboard / ShowKeypad | 9974 | 软键盘 |
| A77 | ShowMessageBox | — | 消息框 |
| A78 | ShowPage | — | 显示页面 |
| A79 | SortArray | 10259 | 数组排序 |
| A81 | SwitchCase | — | 多路分支 |
| A88 | TestAndSet | — | 原子测试置位 |
| A91 | Watch | 11056 | ★ 变量监听（启动即发一次） |
| A92 | ReadSetting | — | 持久化读（`WriteSetting` 同名 A 件） |

> **注意**：附录里大量件（`Instrument*` / `SCPI` / `Modbus` / `MQTT*` / `Serial*` / `TCP*` / `UDP*` /
> `File*` / `Python*` / `CSV*` / `JSON*` / `PrintToPDF` / `TabulatorAction`）属于
> EEZ-GUI / Dashboard / EEZ BB3 运行时，**LVGL 工程用不到**——别照它们设计示例。

## 第二份证据源：装机 Studio（手册只是第一份）

手册对 **LVGL 工程能用哪些动作**只给了一张图（P7.3 · Fig.78，第 65 页），没有文字清单——
所以动作可用性必须以装机包为准，用脚本抽：

```bash
python flow-understanding/tools/extract_studio_facts.py [app.asar] [手册全文txt]
```

产物三份（都在 `notes/`，可复查）：`_lvgl_palette_availability.txt`（件级可用性）、
`_lvgl_action_registry_extract.txt`（A43 注册表 65 项）、`_manual_vs_registry_diff.txt`（手册差集）。

默认路径（★ 每机不同，换机器务必传参）：

| 件 | 路径 |
|---|---|
| Studio 包 | `C:\Users\yjt54\AppData\Local\Programs\eezstudio\resources\app.asar` |
| 手册全文 | `C:\Users\yjt54\Desktop\local_knowledge_base\embedded\EEZ Studio_ui_debug_kit\reference_guide_raw.txt` |

> 脚本只读，不改装机件；判读口径写在脚本 docstring 里
> （**"面板允许"≠"生成的 C++ 里有实现"**，后者要靠示例②③实测）。

## 与经验库的分工

- 手册**事实**（这一篇）：只在 `flow-understanding/` 里沉淀，带页码；
- 踩坑**结论**（换个工程还成立）：回灌经验库 `EEZ Studio_ui_debug_kit/intake/P-01xx`；
- 只在某个示例成立：写进那个示例的 `README.md`。
