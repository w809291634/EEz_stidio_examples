# EEZ 控件语法模板（UI 拖拽创建）

本工程是在 **EEZ Studio 的 UI** 里新建的：

- 18 个画布（Pages），每页一个控件；
- 每个控件都是**从 Components Palette 拖到画布、松开稳定后保存**的；
- 没有用脚本生成/修改 `.eez-project`；
- `templates/*.json` 是从这份保存后的工程只读提取的语法。

## 文件

- `eez-widget-templates.eez-project`：UI 创建并保存的源工程（18 画布）。
- `templates/<Type>.json`：从各画布控件提取的语法模板（objID 已占位）。
- `defaults.json`：每类控件的页面、flags 与保存后的默认值（不含对象 ID/位置）。
- `manifest.json`：类型 → 页面/模板文件。
- `extract_templates.py`：**只读提取**，从保存后的工程重写 templates/defaults/manifest。
- `validate_templates.py`：只读校验，逐字段对比模板与 UI 工程保存的控件。

## 关键语法口径

这是“拖拽后保存”的语法，不是拖动中的临时 payload，也不是 classInfo 片段：

- `clickableFlag: true` 表示可点击，`widgetFlags` **不含 `CLICKABLE`**；
- 有 `flagScrollbarMode`、`flagScrollDirection`、`scrollSnapX/Y`、`group`；
- **没有** `hiddenFlag`、`checkedState`；
- `localStyles` 只有 `{objID}`，没有 `definition`；
- Keyboard **没有** `textarea`（绑定后才会出现）；
- Button 子 Label 是完整 Label 字段集。

## 使用

1. 克隆 `templates/<Type>.json`；
2. 换新 objID/style/localStyles objID 和 `identifier`；
3. 只改几何/文本/样式值，不增删字段；
4. Switch 保留 `CHECKABLE`；Button 保留唯一子 Label；
5. 改动 UI 工程后跑 `python extract_templates.py` 再提取，跑 `python validate_templates.py` 校验。

> Screen 是页面根节点，不是 Palette 拖拽控件；它的模板从页面根提取，`children` 清空。
