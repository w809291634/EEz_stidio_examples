# EEZ 控件模板采集工程（eez-widget-templates）

用途：把**真实拖拽创建**的 EEZ 控件保存为模板语法，供后续工程新建控件时克隆。
**不要手写控件 JSON，不要从别的工程随手抓一个就用**；模板必须来自本工程提取流程。

## 采集方式（核对结论）

- 本工程**不模拟拖拽手势**：它从真实工程取控件字段集，再把属性值复位为
  EEZ `classInfo.defaultValue/defaultFlags`（见 `defaults.json`）。
- EEZ 工程 JSON 不记录“是否拖拽过”；判断是否标准只看四项：字段集、默认值、标志、localStyles。
  这四项已对 19 类逐项校验，`validate_templates.py` PASS。
- 因此模板内容等同“在 EEZ 里新建控件”，但采集动作是“提取 + 复位”，不是在本工程里现拖。

## 内容

- `templates/<Type>.json`：每种控件的初始模板（字段集 + 默认样式 + 子结构）。
  - objID 是占位符 `__OBJID__/__STYLE_OBJID__/__LOCAL_STYLE_OBJID__`，克隆时必须换新 UUID。
  - 事件/时间线已清空；表达式字段已改为 literal，并给默认值。
  - **所有属性值已复位为 EEZ 新建控件的标准默认值**（几何、标志、文本、选项、值域、localStyles）。
- `defaults.json`：标准默认值真值表，取自 EEZ Studio `classInfo.defaultValue/defaultFlags`。
- 所有模板含基础字段 `hiddenFlagType: literal` / `hiddenFlag: false`；隐藏控件只改值，不删字段。
  `defaults.json` 只列 classInfo 默认值，不含这个基础字段。
- `manifest.json`：类型 → 源工程、源 identifier、备注（源工程只提供字段集）。
- `eez-widget-templates.eez-project`：18 页 gallery，每页一个控件，用于 EEZ 构建验证。
- `build_templates_project.py`：重新提取模板 + 生成工程 + EEZ 无头构建。
- `src/ui/`：EEZ 构建产物（验证用，不是模板真值）。

## 重新生成/验证

```bat
python validate_templates.py
python build_templates_project.py
```

`build_templates_project.py` 构建完会自动跑一次 `validate_templates.py`，校验失败即非零退出。
换控件样板：只改脚本里的 `SOURCES`，重新提取并构建；不要手改 `templates/*.json`。
`validate_templates.py` 会逐项对照 `defaults.json`：几何、单位、标志、文本、选项、值域、
`localStyles` 必须与 EEZ 新建控件一致；Button 子 Label 也必须标准。

> Screen 是页面，不是拖拽控件：模板按 classInfo 默认 100×50；建页时由工程分辨率覆盖。

## 已覆盖

Label / Button / Container / Panel / Switch / Slider / Bar / Arc / Chart / Scale / Led /
Checkbox / Dropdown / Roller / Textarea / Keyboard / List / Spinner（Screen 模板也提供，但不单独成页）。

## 硬规则

- **Switch 必须带 `CHECKABLE`**（否则点击不切换；A13）。
- **Button 必须恰一个子 Label**，文字在子 Label，按钮自身无 `text`（A4）。
- 模板字段集不得增删；克隆只改 identifier/几何/文本/样式值（A10）。
- 表达式字段克隆后复位为 literal（本工程已处理模板，克隆时还要再检查）。
