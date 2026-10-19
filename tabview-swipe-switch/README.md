# tabview-swipe-switch — Tabview 隐藏 tab 栏 + 原生滑动切页

## 演示点

单 screen + `lv_tabview` 两页，**`tabviewSize=0` 隐藏 tab 栏**，页间切换只靠**跟手滑动**
（拖一半松手自动吸附）——与 [`gesture-page-switch`](../gesture-page-switch/)（GESTURE 离散切屏）
互补：要"跟手拖动、可半途弹回"用本例，要"整页离散翻页、跨屏跳转"用手势版。

- **滑动切换是 tabview 原生行为，零流组件、零连线**：内容区自带 `SCROLL_SNAP_CENTER`
  横向吸附（apl_lvgl `lv_tabview.c:190`）+ `LV_EVENT_SCROLL_END` 自动吸附最近页
  （`lv_tabview.c:344-373`）。不需要画任何 Switch/Action 判定链。
- **隐藏 tab 栏 = `lv_tabview_set_tab_bar_size(tv, 0)`**：内核实现就是把 bar 高度直接
  置 0（`lv_tabview.c:224`），bar 里的页按钮仍在但不可见；EEZ 侧只需把 Tabview 控件的
  **Size 属性填 0**。
- Tab 控件直接作 Tabview 子控件（EEZ"配置 1"，`watch.eez-project` 同款实测形态）。

## 工程结构

```
tabview-swipe-switch/
├── build_example.py          ← 唯一设计源，重新生成 .eez-project
├── tabview-swipe-switch.eez-project
├── design/
│   ├── cli_build.py          ← EEZ 无头 CLI 构建校验（headless 不烘字体，本例无字体）
│   └── sim_cmake/            ← PC_SIM 仿真器三件套（run_sim.bat / main.c / lv_conf.h）
└── src/ui/                   ← EEZ 生成产物（screens.c 含 tabview 调用链）
```

关键产物（`src/ui/screens.c`，由本工程自动生成）：

```c
lv_obj_t *obj = lv_tabview_create(parent_obj);
lv_tabview_set_tab_bar_position(obj, LV_DIR_TOP);
lv_tabview_set_tab_bar_size(obj, 0);          // ★ 隐藏 tab 栏
lv_obj_t *obj = lv_tabview_add_tab(parent_obj, "p1");
lv_obj_t *obj = lv_tabview_add_tab(parent_obj, "p2");
```

## 依赖版本

EEZ Studio 0.29（projectVersion=v3）· LVGL 9.4 · 480x320 · PC_SIM 仿真验证。

## 验收

```
双击 design\sim_cmake\run_sim.bat        → 编译并弹仿真器窗口
```

**鼠标按住页面拖动**（模拟手指）即可在 PAGE 1（蓝）/ PAGE 2（绿）间跟手滑动；
拖过半屏松手自动翻页，拖不足半屏弹回。CLI 构建产物对账 0 错 0 警；
仿真器编译链接 0 错（2026-10-19）。

## 踩过的坑

1. **Tab 控件的 widgetFlags 裁掉了滚动族**（`SCROLLABLE/SCROLL_ELASTIC/SCROLL_MOMENTUM/
   SCROLL_WITH_ARROW/SNAPPABLE` 不保留）：页内容自身若可滚，会跟页切换抢手势；
   `watch.eez-project` 同款裁剪。Tabview 本体保留完整默认 flags（含 SCROLLABLE+SNAPPABLE）。
2. **tabName 用 ASCII**：EEZ 的 tabName 不进字形收集（KB P-0022），中文 tab 名会豆腐；
   本例 tab 栏虽隐藏（tabName 不可见），仍取 `p1/p2` 稳妥。
3. **tabview 背景要透明**（MAIN `bg_opa=0`），页底色在 Tab 控件上着——否则 tabview
   自身背景盖住页配色（KB P-0021 主题发白问题的本例变体）。
4. **EEZ 无头 CLI 不烘字体**（KB P-0140）：本例刻意只用默认字体 + ASCII，无字体条目，
   CLI 产物即完整；若要加中文，参考 `font-entry-form` 的 lv_font_conv 离线链路。
5. **不要在 tabview 外再套 changeScreen 翻页**：`changeScreen fadeMode` 动画与 tabview
   的 SCROLL_END 吸附有竞态（KB P-0029），本例单屏、原生吸附，从结构上绕开。
