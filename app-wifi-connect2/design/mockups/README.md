# 设计图目录（mockups）

> **编号是稳定 ID，不复用**：删掉的图不会再补号，所以编号不连续是正常的。
> 规则：**只保留与当前定稿一致的图**；一个过程只留一张，旧的直接删，不做累计。

全部由 `design/mockup_gen.py` 用同一套网格常量生成；浏览器直接打开 SVG 查看（矢量无损）。

## 一、列表组件（扫描结果）

| 文件 | 状态 | 关键点 |
|---|---|---|
| `mockup_01_list.svg` | 列表主态 | 分组置顶（已连接 · 已保存 / 可用网络）；行内 7 项：信号图示·名称·类型·强度·频段·锁·状态 |
| `mockup_02_scanning.svg` | 扫描中 | 4 行骨架占位（行位与主态一致，不跳动）+ 刷新转圈 |
| `mockup_03_empty.svg` | 无网络 | 空态图标 + 引导 + 「重新扫描」 |
| `mockup_06_connecting.svg` | 连接中 | 目标行蓝描边 + 「连接中」胶囊；半页按钮禁用并显示进度 |
| `mockup_07_failed.svg` | 连接失败 | 目标行红描边 + 「连接失败」胶囊；错误就地显示在半页标题行 |
| `mockup_08_forget_confirm.svg` | 忘记确认 | 长按已保存网络 → 遮罩 + 确认卡（忘记=危险色） |
| `mockup_09_embedded.svg` | 组件内嵌 | 同一组件放进设置页卡片，行宽/字号随容器自适应 |

## 二、方案图

| 文件 | 说明 |
|---|---|
| `mockup_15_subcontainer_sheet.svg` | **定稿方案 C**：列表在宿主子容器（424×192）→ 点行 → 遮罩 + 半页 224 上滑（密码框 + 连接 + 全宽键盘 42.8）；附高度预算与 z 序规则 |

## 三、架构图

| 文件 | 说明 |
|---|---|
| `mockup_17_flow_arch.svg` | 五层：EEZ 工程 → 生成源码 `src/ui` → Flow 运行时 → native 薄层 → 硬件；含 90/10 代码占比与三条目标保障 |
| `mockup_18_scan_to_ui.svg` | 扫描回流 9 步：点击 → actions → 命令 → native 泵 → 扫描 → SCAN_DONE → 投影 → `eez_flow_tick` → LVGL |
| `mockup_19_password_flow.svg` | 密码下行 5 步（输入→action→命令槽→校验→join） + 上行 5 步（事件→结果结构→pump→Flow→UI）+ reason→文案映射 |

## 已删除（避免再次生成或引用）

| 原图 | 删除原因 |
|---|---|
| `mockup_04_password` / `05_password_keyboard` | 整页密码页，与定稿「半页 224」冲突 |
| `mockup_10_page_layers` | 「整页覆盖」层级图，被 15 的 z 序规则取代 |
| `mockup_12_explain_keyboard` | 结论是「必须整页」，与方案 C 矛盾 |
| `mockup_13_popup_forms` | 半页按 200 算（实为 224），两种形态并列造成歧义 |
| `mockup_14_arch_flow` | 四层扁平变量架构，已被 Flow 架构（17）推翻 |
| `mockup_16_scan_binding` | 37 个扁平变量，与 Flow「3 个变量」冲突 |
| `mockup_list` | 旧基准版，`mockup_01_list` 已含分组 |

## 修改方式

**不要手改 SVG。** 改 `design/mockup_gen.py` 里的网格常量（行高/基线/右缘/锁位/半页高度），
重新生成即全图自动对齐；脚本带断言（胶囊右缘一致、锁居中 ≤1.5px、列表不溢出）。
