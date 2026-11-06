# AGENTS.md — LVGL / EEZ UI 开发默认流程

**适用范围：本工程内所有 LVGL / EEZ Studio UI 开发任务，默认生效，无需每次点名。**
**任意 AI 快速起步的提示词卡**：`...\EEZ Studio_ui_debug_kit\QUICKSTART_PROMPTS.md`（不自动读本文件的 AI 贴卡 A 开场）。

## 流程唯一真值

本地经验库 kit 流程文件（本机路径，换机需重核），按方式二选一：

```
no flow 方式：C:\Users\yjt54\Desktop\local_knowledge_base\embedded\EEZ Studio_ui_debug_kit\EEZ_FIRST_WORKFLOW_NO_FLOW.md
flow   方式：C:\Users\yjt54\Desktop\local_knowledge_base\embedded\EEZ Studio_ui_debug_kit\EEZ_FIRST_WORKFLOW_FLOW.md
```

## no flow 方式：唯一流程 = 七步主线（NO_FLOW 文件 §2）

1. **设计图**：用户提供；没有则由 AI 生成——先写设计源，**设计图由独立的设计图脚本从同一设计源渲染**（与 EEZ 工程生成脚本分离，同源派生）；**必须经用户确认核对后才算数**，不满意改设计源重渲染。
2. **控件标注**：用户序号标注控件类型、跳转界面、控制硬件；说明页面关系（tabview、top bar / bottom bar）。
   标注落为控件清单表；**未标注作用＝纯展示、不接行为**。
   **②b H5 核验步（独立一步，见 kit NO_FLOW §2.0c）**：设计图本身就在 H5「高清设计图」页签确认（SVG 可选）；
   先出 H5 全览供确认，确认之后出页面连接 + AI 预估控件图；设计阶段的 UI 显示与跳转演示**以 H5 为主要载体**。
3. **框架确认**：确认走 no flow（选 flow 则转 FLOW 文件执行）。
4. **预生成全部界面**：EEZ 生成所有界面（含字体、图标）；**大图需用户确认是否走 TF 卡**。
5. **双核对**：先 EEZ 内部预览器核对与设计图完全一致，再用仿真器出图核对（**本步仿真默认跑**）。
6. **用户核对＋真机**：用户核对预生成界面，烧录硬件确认可显示、可调整。点头＝设计冻结。
7. **逐个补全功能**：每条按五元组立项，各走一轮内环：改设计源→生成→EEZ 构建→EEZ 画布/Run（静态主验收）→
   仿真（动态主验收）→门禁全绿→真机（点名）。

## flow 方式

无七步前置，直接走主链七步（FLOW 文件 §2）；判"EEZ 做不到"前四面对查＋报备；仿真点名才跑。

## 铁律摘要

0. **静动分界**：静态看 EEZ、动态看仿真、真机终验；设计载体不做过渡动效。
1. **EEZ 优先（分阶段）**：预生成阶段的设计控件必须 EEZ 生成，`src/ui` 不可手改。
2. **仿真时机**：设计核对默认跑，其余微调点名才跑（跳过要留"待同步"清单）。
3. **五元组**：每条需求写目标/口径/验收/约束/验证归档；观感词两轮对不上就出标注图。
4. **留痕**：提示词逐字进 kit `prompts/PROMPT_LOG.md`（PR-####），新问题进 `intake/`（P-####）
   并追 `intake/index.md`；查问题先看这张索引。
5. **收尾即清**：过程件只放工程 `tmp/` 且收尾删除，交付件只放正位；**构建/编译缓存 `tmp/sim_build_<工程名>`、`tmp/compile_cache` 保留**（用户令，避免下次全量重编；build 目录按工程命名，防多工程冲突）。
6. **载体与交付**：设计阶段以 H5 三视图为主；**高清设计图默认叠加全部控件标注（开关/滑条/按钮/输入/图表都要有号），可一键关**；**H5 批注**：右键右侧控件清单行/底部控件标签 → 删除/修改/加提示，右键效果图空白 → 落坐标标签，导出 `annotations.json` 给 AI 改设计源，浏览器不改工程；核对给 HTML 绝对路径、不内嵌、不出查看器页；改 H5 交互/实时效果要同步高清设计图。
7. **覆盖表只补真值**：例外/映射表不得推翻设计源行为字段，配 assert 门禁。
8. **控件只克隆 EEZ 拖拽样板**：新建控件从根目录 `eez-widget-templates/templates/` 克隆
   （模板来自 EEZ UI 拖拽创建并保存后的工程，`validate_templates.py` 逐字段校验）；
   生成器只改几何/identifier/文本/样式值，**禁止手写或新增字段**（A10 门禁逐控件核对）。
   `tools/eez_defaults.py` 只用于已有工程的自定义样板采样/对照，不再作为新建控件来源。
   按钮无 `text`（文字在子标签）；克隆后复位表达式型属性，否则会带入别工程的 `get_var_*`。
   生成器还有十条硬口径：页名 ASCII / identifier 按类别码命名 / 字号 ≤3 档令牌 / 替换字符进子集 /
   卡片只做底板 / 行式按钮 LEFT_MID+设计文案 / 颜色只收 `#RRGGBB` / 装饰容器去 CLICKABLE（只改 flags）/
   控件 JSON 只克隆拖拽样板（A10 字段集校验）——细则见 NO_FLOW §2.2。
   **设计标注的控件必须按类型真实建立**（开关→Switch、滑条→Slider、动作/跳转→Button、
   输入→Textarea、进度→Bar、图表→Chart）；大卡片用容器 + 卡内真控件；A12 硬门禁，禁止透明容器冒充。
   **Switch 样板必须带 `CHECKABLE`**（A13），否则点击不切换状态。
   **字段集必须等于 UI 拖拽保存语法**（A14）：不得按 classInfo/defaultValue 片段或拖动 payload 补字段。
   **新建控件唯一来源**：根目录 `eez-widget-templates/templates/`（kit `reference/eez_widget_syntax`），
   模板来自 EEZ UI 拖拽创建并保存后的工程，不允许临时去其他工程抓样板；不要用脚本生成/修改 `.eez-project`；
   不得带源工程配色/字体/尺寸；克隆后只改几何/identifier/文本/样式值。
   **设备读数也是控件**（温度/湿度/百分比/功率/电量/在线状态/日期时间等），按 value 类标注并生成 Label（`hr` 码）；
   随 UI 滑条/开关变化的值（含滑条/进度条旁的数值）自动归 `in_read`；标题、说明、按钮文案不算读数（标注范围见 NO_FLOW §2.1）。
9. **中文只在索引里出现**：`log_entry --json`、`design/texts.py` key、`lint_text.py` 门禁。
10. **字体 F1–F7**：三件套 / `lvglGlyphs.encodings` / 核 cmap / 多字号共用 TTF / headless 不烘 / 验收三连。
11. **交付必过 D1–D9**：`design/delivery_gate.py`，FAIL 不许交付；D5 每次生成后用
    `design/d5_pages.py` 打出**相似度百分比**（100−逐像素差异率）并留并排图。
    **D5 整轮只启动一次 EEZ，禁止反复开关/逐页重启**；多次改动先自检，最后合并跑一次全量。

12. **Wi-Fi 连接页先移植**：扫描/连接/密码/忘记网络一律按 kit `reference/15` 移植成熟结构（单页 + lv_list 动态行 + 密码半页 + 忘记框 + busy），不拆三屏、不自造交互。

13. **UI 内存按档位控制（字体/动图）**：**设计阶段（①）先问用户 UI 预算档位**（200K/500K/1M/2M/4M 或实际值）并落 `design/mem_budget.json`，未确认不进预生成；按档决定字号档数/bpp/动图规模，可读性优先、不压呈现质量；交付跑 D9 对档核账；**每次编译/测试打印资源树，默认用 IDF 工具链只编译估算**（`design/esp32_estimate.py`，目标架构、逐文件字节，Flash 偏高约17%；**默认优化 `-O2`（IDF 当前），并给 -O0/-O1/-O2/-O3/-Os 对比**），**PC 编译上限并列**；**只有用户点名“用 IDF 工程编译”时才跑 `design/esp32_size.py` 做最终链接**；无 IDF 时只报 PC 并标明上限（NO_FLOW §2.5）。

14. **字号 ≤3 档且共用**：设计源一套令牌全工程共用；**镜像字库只有 1 档带汉字（尽量小，如 12px）**，其余档只放 ASCII/数字；**SD 卡字库不受限**（保留镜像 1 档兜底）；设计阶段先确认字库存放位置（NO_FLOW §2.5/F4）。

> 细节只在对应文档里写一次：流程 = `EEZ_FIRST_WORKFLOW_NO_FLOW.md`；方法论 = `PLAYBOOK.md`；
> 字段级 = `reference/07`（工程 JSON / 字体）、`reference/14`（H5 评审页）、`reference/15`（Wi-Fi 连接页结构）。
> **新增规则只加两处**：这里一行（入口）+ 对应文档一节（细节）。别在第三处复述。

