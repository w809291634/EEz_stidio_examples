# widget-gallery —— 常用 LVGL 控件一屏览

> **演示点**：7 类常用控件（Button / Slider / Switch / Bar / Spinner / Checkbox / Panel）的
> **正确 JSON 形态** —— 全部复刻 EEZ Studio 0.29 调色板默认值，是"已知能构建"的稳妥写法。

## 演示点

1. 每种控件的 `widgetFlags` / 专属属性三件套（min/max/mode/value…）长什么样；
2. **Button 的子 Label**：`align: CENTER` + content 尺寸，由 LVGL button 的 flex 布局自动居中——不手摆像素（B9）；
3. **content 尺寸控件**（Checkbox）：`widthUnit/heightUnit = "content"`，宽高由内容撑开；
4. **初始选中态用属性不用事件**：Switch 的 `checkedState: true` 初始即选中态（P-0028 规则）；
5. **Panel 嵌套子控件**：子坐标相对父容器 + Panel MAIN padding 显式清零（B5 / P-0007 / 红线 6）。

## 工程结构

| 文件 | 说明 |
|---|---|
| `build_example.py` | ★ 唯一设计源；内含 `button()/slider()/bar()/checkbox()` 四个可复用构造助手 |
| `widget-gallery.eez-project` | 生成产物，EEZ Studio 可直接打开 |
| `src/ui/` | 构建产物（可再生产物，已 gitignore） |

## 依赖版本

EEZ Studio 0.29.0 · LVGL 9.4.0 · 480×320 深色主题 · 无自定义字体（文字走内置 Montserrat）。

## 踩过的坑

- ★★ **`widgetFlags` 漏 `CHECKABLE` → 控件变装饰件**：LVGL 9.4 的点击翻转写在
  `lv_obj.c` 的 `LV_EVENT_RELEASED` 分支里，**硬条件是 `LV_OBJ_FLAG_CHECKABLE`**
  （源码实证：`apl_lvgl_v9_4/src/core/lv_obj.c` ~L826）。widgetFlags 漏了它，EEZ 生成的
  `screens.c` 会 `lv_obj_remove_flag(obj, LV_OBJ_FLAG_CHECKABLE)`——Switch/Checkbox
  看着在、点了不翻。同款教训见经验库 `P-0004`（"界面开关是装饰容器，点了没反应"）。
  参考工程 Design Watch 的 checkbox 也漏了该标志（仅作显示用，状态由外部驱动）。
- ★ **没有字体条目的工程，中文必成豆腐块**：内置 Montserrat 无中文字形（`B1` / `P-0022`）。
  本示例因此全文用英文；中文字体的正确条目形态见同仓库 `font-entry-form`。
- Slider 的 **KNOB 直径 = 控件高度**（`P-0049`）：高度 10 的滑杆圆点只有 10px 几乎不可见，
  本示例用高 20 让圆点可见；要更细的轨道得用 MAIN `pad_top/pad_bottom` 收细，
  **不要**用 `transform_height` 负值（会把 INDICATOR 画成细线，`P-0084`）。
- Button 子 Label **不要手摆像素**：写 `align: CENTER` + content 尺寸即可，
  LVGL button 自带 flex 居中；手摆坐标遇舍入模式差异会偏 1px（`B9`）。
- Panel 的子控件坐标**相对父容器**且越界会被裁：子 Label 放 (12, 28) 而非绝对坐标（`B5` / `P-0007`）。

## 经验库对照

- `PLAYBOOK.md` §4.2（默认主题）/ §4.4（字体分离）/ §4.5（居中）/ §4.10（坐标系分层）
- `cases/B5`（嵌套容器二次偏移）、`cases/B9`（居中）、`intake/P-0004`、`P-0049`、`P-0084`
