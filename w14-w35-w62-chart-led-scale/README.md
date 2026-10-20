# w14-w35-w62-chart-led-scale — 数据可视化与状态指示（A 级组合 2/5）

> 覆盖控件：**W14 Chart / W35 Led / W62 Scale**（W 号出处见
> [`../示例工程模板说明.md`](../示例工程模板说明.md)）。
> ★ 计划中的 Meter **仅 LVGL 8.x 可用**（EEZ 面板在 9.x 下不显示该控件），已剔除，
> 由 Scale 替代仪表职能。

## 演示点与属性覆盖

### W14 Chart —— EEZ 空壳，数据必须 C 喂

- EEZ 的 Chart 控件**零属性**（同 List，只生成 `lv_chart_create`）——
  series/类型/范围/数据全部在 `ui_init()` 之后用 C 补（本工程 `main.c`）：
  `lv_chart_set_type(LINE)` + `lv_chart_add_series` + 初始 30 点正弦 +
  `lv_timer` 每 200ms `lv_chart_set_next_value` 滚动推进（SHIFT 模式）。
- Chart 的 flags 用官方默认（含 SCROLLABLE，P-0150 勿裁）。

### W35 Led —— color / brightness 都是 integer expression

| Led | 属性绑定 | 效果 |
|---|---|---|
| led_color | `color = g_color`（expression） | 运行时可变色（g_color=65280=0x00FF00 绿） |
| led_bright | `brightness = g_bright`（expression） | 运行时可调亮度（手册：0 最暗 ~ 255 最亮） |

flow 变量改值 → LED 颜色/亮度实时变（在 EEZ 或运行时写 g_color/g_bright 即可）。

### W62 Scale —— EEZ 9.x 可配的刻度尺（替代 Meter）

关键属性全显式：`scaleMode:"HORIZONTAL_BOTTOM"`、`minValue/maxValue`(0/100)、
`angleRange:270`、`rotation:135`、`totalTickCount:31`、`majorTickEvery:5`、
`showLabels:true`、`sections:[]`。

## 工程结构

```
w14-w35-w62-chart-led-scale/
├── build_example.py          ← 唯一设计源
├── design/cli_build.py       ← EEZ CLI 构建
├── design/sim_cmake/         ← 三件套（main.c 含 Chart 的 C 喂数据）
└── src/ui/                   ← EEZ 生成（screens.c 含 lv_chart/led/scale 创建链）
```

## 构建与验收

```
python build_example.py && python design/cli_build.py
双击 design\sim_cmake\run_sim.bat
```

验收：Chart 内蓝色正弦波每 200ms 滚动一格；右侧绿 LED 常亮（color 绑定）、
黄绿 LED 中亮（brightness 绑定）；底部横排刻度尺（31 tick、每 5 一大格、带标签）。
CLI 0 错 0 警 + 仿真器编译链接 0 错（2026-10-19）。

## 踩过的坑

1. **★ Meter 仅 LVGL 8.x**：EEZ 面板 `enabledInComponentPalette` 要求
   `lvglVersion.startsWith("8.")`，**9.4 工程里没有 Meter**——仪表职能用
   Scale（W62，要求 9.x）或 Arc（W2）替代。
2. **★ Chart 是空壳**（零属性，仅 `lv_chart_create`）：series/数据必须
   `ui_init()` 后 C 补（`lv_chart_add_series` + `lv_chart_set_next_value`）；
   要动态曲线就沿用本工程 main.c 的 timer 喂点模式。
3. **Led 的 color/brightness 都是 integer expression**：可绑定 flow 变量做
   运行时变色/调光；literal 模式下 color 用 `"#RRGGBB"` 字符串。
4. **Scale 属性面很大但可选项极多**（`mainLineWidth` 等全部可 void）——
   只显式写要覆盖的键，其余留默认即可，别全量照抄。
5. **本工程 main.c 含 Chart 喂数据 C 段，不是干净模板**——新示例从
   `tabview-swipe-switch` 或 `w1-animation-image` 拷 main.c（见模板说明）。
