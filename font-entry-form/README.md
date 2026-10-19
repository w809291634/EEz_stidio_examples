# font-entry-form —— 中文字体条目的正确形态

> **演示点**：EEZ Studio 0.29 里中文字体条目到底怎么写才不会变豆腐块。
> 结论来自经验库 `P-0125` 的 A/B/C 对照实测：**决定性变量是「条目形态」，不是字体文件**。

## 演示点

1. **正确形态四要点**（缺一不可，`build_example.py` 的 `font_entry()` 逐条注释）：
   - `renderingEngine: "LVGL"` —— 缺了 → 画布/Run 中文豆腐块 + 点 Fonts 面板崩；
   - **中文码位进 `lvglRanges`（数字表字符串）** + `lvglGlyphs.encodings`（`{from,to}` 数字表）；
   - `glyphs: []`（旧形态字段，留空）；
   - `source.filePath` 存**相对工程目录**的路径（`P-0035`：EEZ 用原文拼 opts_string，不相对化）。
2. **同一字体文件两个字号条目**（cn20 / cn14）：条目按"文件+字号"为单位，不是按文件；
3. **字符集白名单**：`FONT_CHARS` 声明 UI 用到的每个码位，与 `lvglRanges` 同源生成——
   渲染/校验共用一份清单（PLAYBOOK §4.4 断言思路）。

## 工程结构

| 文件 | 说明 |
|---|---|
| `build_example.py` | ★ 唯一设计源；`font_entry()` 可直接抄进自己的生成器 |
| `font-entry-form.eez-project` | 生成产物，EEZ Studio 可直接打开 |
| `fonts/simhei-subset.ttf` | 示例字体资产：从 `C:\Windows\Fonts\simhei.ttf` 子集化（159 字形 / 23.8KB，fonttools） |
| `src/ui/` | 构建产物（可再生产物，已 gitignore） |

## 依赖版本

EEZ Studio 0.29.0 · LVGL 9.4.0 · 480×320 深色主题 · 字体 4bpp / threshold 128。

## 怎么用

```bash
python build_example.py      # 生成 font-entry-form.eez-project
```

构建后**还必须做一次 GUI 字体提取**（CLI 不产字体 .c，见下）：

```bash
# 1) CLI 构建（校验工程结构 + 写 fonts.h 声明）
"EEZ Studio.exe" --build-project font-entry-form.eez-project --no-sandbox --disable-gpu --enable-unsafe-swiftshader --disable-dev-shm-usage

# 2) GUI 补字体：EEZ Studio 打开工程 → 工具栏 Build（扳手）一次
#    产物：src/ui/fonts/ui_font_cn20.c、ui_font_cn14.c
# 3) 目检：编辑器画布 / Run 模式 —— 七行中文应正常渲染，无豆腐块
```

> 本示例的自动化验证到 CLI 构建 + `fonts.h` 声明核对为止（均通过）；
> 字体 .c 提取与中文目检需要 GUI 会话（单实例限制，见下），为待人工步骤。

## 踩过的坑

- ★★ **CLI 构建不产字体 .c**（`P-0140`）：CLI 只写 `fonts.h` 声明；`ui_font_*.c` 由
  **GUI 的 Build**（会话内字体提取）产出，且 CLI 的孤儿清理会把与旧定义不匹配的字体 .c
  **删掉却不重建**——改字形集后必须再跑一次 GUI Build，否则 MCU 编译缺符号。
- ★ **错误形态对照**（`P-0125` A/B/C 实测，别试，会崩）：
  | 错误写法 | 后果 |
  |---|---|
  | 缺 `renderingEngine: "LVGL"` | 画布/Run 中文豆腐块；点 Fonts 面板直接崩 |
  | 中文码位只写在旧 `glyphs` 列表 | 不收字形 → 豆腐（换字体文件也没用） |
  | 只换字体文件不改条目形态 | **无效**——形态才是决定性变量 |
- **tabName 不进字形收集**（`P-0022`）：tabview 的 tab 标签中文要单独喂码位，
  本示例无 tabview；用到 tabview 时注意这条。
- **运行时字符串也要补字形**（`P-0051`）：native/io 侧的中文字面量不在 DSL 里，
  不会自动进白名单——本示例文字全在 DSL 内，暂无此坑。
- 子集字体用 fonttools 从系统 simhei 裁到 159 字形（23.8KB）：**不要**把 9.7MB
  的全量 TTF 塞进示例仓库；自家工程同理，按白名单子集化。

## 经验库对照

- `intake/P-0125`（形态定论 + A/B/C 实测）、`P-0035`（相对路径）、
  `P-0140`（CLI 不烘字体）、`P-0022`（tabName 字形）、`P-0051`（运行时字形）
- `PLAYBOOK.md` §4.4（图标/特殊字体分离 + 码位断言）
