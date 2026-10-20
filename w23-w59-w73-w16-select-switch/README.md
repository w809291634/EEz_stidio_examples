# w23-w59-w73-w16-select-switch — 选择与开关：Tabview 4 页 + 联动（A 级组合 3/5）

> 覆盖控件：**W23 Dropdown / W59 Roller / W73 Switch / W16 Checkbox**
> （原计划的 W85 ToggleButton 已剔除，见坑 1）。tabview 写法遵循 KB P-0150
> （Tab 直挂配置 1、flags 只裁 SCROLLABLE；本例 tab 栏**可见** size=30 供切页）。

## 结构：可见页签 Tabview 承载 4 个分页

| 页签 | 控件 | 演示内容 |
|---|---|---|
| Drop | Dropdown W23 | `options`（换行分隔多选项）+ `selected` **assignable 双向绑定 g_sel** + `direction:"bottom"` |
| Roll | Roller W59 | 同一组 options + `selected` 绑 **同一个 g_sel** + `mode:"NORMAL"` |
| Sw | Switch W73 ×2 | `checkedState` false/true 两种初始态 + CHECKED 样式态（绿轨） |
| Chk | Checkbox W16 ×2 | `text` 文本 + checkedState false/true |

**★ 联动主线**：Dropdown 与 Roller 的 `selected` 绑**同一个 g_sel**（两处都是
assignable）——改任一处，另一处自动同步到相同索引（ VALUE_CHANGED 写回 +
tick 反向同步，纯绑定零 flow 图零 C，机制同 w67-w3-w2）。每页有
`"selected index = " + g_sel` 实时回显。

## 工程结构

```
w23-w59-w73-w16-select-switch/
├── build_example.py          ← 唯一设计源
├── design/cli_build.py       ← 支持argv指定工程文件（bisect 用）
├── design/sim_cmake/         ← 干净三件套（无 C 扩展）
└── src/ui/                   ← 生成产物（screens.c 含 5 处控件创建 + g_sel 绑定）
```

## 构建与验收

```
python build_example.py && python design/cli_build.py
双击 design\sim_cmake\run_sim.bat
```

验收：点页签切页；Drop 页下拉选 Blue(2) → 切到 Roll 页滚轮已同步到 Blue；
Roll 改索引 → Drop 跟随；Sw/Chk 页点按出 CHECKED 视觉态。

## 踩过的坑

1. **★ ToggleButton（W85）不能直接用于 LVGL 工程**：其 EEZ 类是
   `ToggleButtonWidget`（继承 EEZ-GUI Widget 基类，必填 `data/text1/text2`，
   **无 LVGL codegen**）——塞进 LVGL 工程构建必报
   `t.lvglBuild is not a function`。LVGL 等价物 = CHECKABLE Button
   （widget-gallery 已覆盖）。注意它的类名没有 LVGL 前缀，别猜成
   `LVGLToggleButtonWidget`。
2. **★ 排障方法：per-tab bisect**：把页签 children 逐一过滤成单 tab 工程
   （`_bisect_<名>.eez-project`）+ `cli_build.py` 支持argv 指定工程文件——
   本例靠它证明 4 个控件各自构建 OK，从而锁定罪魁是 ToggleButton。
3. **Switch/Checkbox 在 EEZ 中没有数据绑定属性**（defaultValue 只有几何 +
   checkedState）——状态联动需要 flow 事件线（VALUE_CHANGED → SetVariable），
   本例只演示形态与 CHECKED 样式；Dropdown/Roller 的 `selected` 才是
   assignable 可绑定属性。
4. **改名/换目录后必须删 sim_cmake 的 build_rel**：CMakeCache 记录旧路径，
   configure 直接失败（lv_conf.h "not found" 指向旧目录）。
5. 排障期间若 EEZ Studio 进程残留（单实例锁），先
   `taskkill /F /IM "EEZ Studio.exe"` 再构建。

## 依赖版本

EEZ Studio 0.29（projectVersion=v3）· LVGL 9.4 · 480x320 · PC_SIM 仿真验证
（CLI 0 错 0 警 + 仿真器编译链接 0 错，2026-10-20）。
