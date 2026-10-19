# two-state-styles —— DEFAULT / CHECKED 两态样式

> **演示点**：Switch / Checkbox / Button 三类控件的两态样式写法，
> 以及两个最常踩的坑：**两态不写全**（P-0048）与 **toggle 控件漏 CHECKABLE**。

## 演示点

1. **两态样式写全**：`localStyles.definition` 按 `部件(MAIN/INDICATOR/KNOB) × 状态(DEFAULT/CHECKED)`
   组织；本示例三个控件都是 DEFAULT/CHECKED 两态都写（P-0048 教训：只写默认态会被主题盖住）；
2. **初始选中态用属性**：`checkedState: true/false` + `checkedStateType: "literal"`——
   初始态是属性不是事件（P-0028 场景E 规则 2）；
3. **toggle 按钮显式加 CHECKABLE**：palette 默认 flags 没有它，不加就是"看着像按钮、
   点了不翻"的装饰件（见下）；
4. **子元素颜色走继承**：Button 的子 Label **不写 text_color**，只在父控件 MAIN 写两态色，
   选中态一变整项自动跟随（P-0028 场景E 规则 2）。

## 工程结构

| 文件 | 说明 |
|---|---|
| `build_example.py` | ★ 唯一设计源；`two_state_switch/checkbox/button()` 三个构造助手可直接抄 |
| `two-state-styles.eez-project` | 生成产物，EEZ Studio 可直接打开 |
| `src/ui/` | 构建产物（可再生产物，已 gitignore） |

## 依赖版本

EEZ Studio 0.29.0 · LVGL 9.4.0 · 480×320 深色主题 · 无自定义字体（文案用英文，原因见坑 4）。

## 怎么用

```bash
python build_example.py      # 生成 two-state-styles.eez-project
"EEZ Studio.exe" --build-project two-state-styles.eez-project --no-sandbox --disable-gpu --enable-unsafe-swiftshader --disable-dev-shm-usage
```

目检：编辑器画布看初始态（Switch 绿 / Checkbox 空 / Button 蓝底亮字）；
**Run 模式（F5）**分别点三个控件，验证翻转与文字色跟随。

## 踩过的坑

- ★★ **toggle 控件必须显式 `CHECKABLE`**：EEZ Button 的 palette 默认 flags 里**没有**
  CHECKABLE；LVGL 9.4 的点击翻转写在 `lv_obj.c` 的 `LV_EVENT_RELEASED` 分支，
  **硬条件就是 `LV_OBJ_FLAG_CHECKABLE`**（源码实证）。漏了它 → 生成代码里控件不带该标志 →
  点击无翻转。Switch/Checkbox 的 palette 默认自带（lv_switch/lv_checkbox 构造函数里 add），
  **Button/Container 没有，要自己加**（参考工程 Design Watch 导航项同款写法）。
- ★ **两态都要写全**（P-0048）：主题通常给 CHECKED 态定义过样式，只写 DEFAULT 态
  会被主题盖住——现象是"点了没变化"。修法不是反向补偿，是两个状态都显式写。
- ★ **初始选中态用 `checkedState` 属性，不靠事件**（P-0028）：事件驱动的初态会在
  页面加载时序上出竞态；属性初值在 `create_screen` 里一步到位。
- **LVGL 9.4 翻转发生在 `LV_EVENT_RELEASED` 而非 `LV_EVENT_CLICKED`**（P-0046）：
  写冒烟/自动化测试模拟点击时必须发 RELEASED，发 CLICKED 不翻状态。
- **KNOB 直径 = 控件高度**（P-0049）：想要细轨道用 MAIN `pad_top/pad_bottom` 收细，
  **不要**用负 `transform_height`（会把 INDICATOR 画成细线，P-0084）。
- 本示例**不含字体条目**，中文文案会变豆腐块（B1/P-0022）——故全文英文；
  中文字体正确形态见同仓库 `font-entry-form`。

## 经验库对照

- `intake/P-0046`（RELEASED 翻转）、`P-0048`（两态写全）、`P-0028`（checkedState 初态 +
  场景E 高亮跟随规则）、`P-0049`/`P-0084`（KNOB/轨道几何）
- `PLAYBOOK.md` §4.2（默认主题覆盖手写值）
