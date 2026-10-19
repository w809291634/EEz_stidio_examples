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

1. **★ Tabview 里必须放 Tab 控件（EEZ 手册"配置 1"）**：控件面板里 `Tabview` 与 `Tab`
   是两个控件——Tabview 只是骨架，**把 Tab 控件直接放进 Tabview 才会生成页**
   （发射 `lv_tabview_add_tab`）。EEZ Studio 内置手册明示两种形态：① Tab 直接放
   Tabview 下（本例）；② Tabview 下放两个容器（第一个当 tab Bar、第二个当 Content，
   Tab 放 Content 里）。
2. **★ Tab（页）必须保留 `SNAPPABLE`——"无法滑动"的真正根因**：内容区是
   `SNAP_CENTER` 吸附滚动模式，内核拖动判定不走普通溢出，而是
   `has_more_snap_points()`（lv_indev_scroll.c:353-360）数**带 SNAPPABLE 标志的子对象**
   当吸附点；页被裁掉 SNAPPABLE → 零吸附点 → 内容区被判"该方向不可滚" → 拖动全程
   只有 PRESSING、零 SCROLL（注入实测 97 次 PRESSING / 0 次 SCROLL 实锤）。
   旧结论"裁掉滚动族防抢手势"（watch 裁法）是错的，watch 版滑不动同源。
   **正确形态（eez-test 实测可滑同款）：Tabview 与 Tab 都只裁 `SCROLLABLE`**，
   生成产物里只有一条 `lv_obj_remove_flag(obj, LV_OBJ_FLAG_SCROLLABLE)`。
3. **label 保留 `SCROLL_CHAIN_HOR/VER`**：label 不可点击、拖动落点一般是 PAGE，
   但保留链标志可让任何起点的拖动都传导到内容区（防御性，零成本）。
4. **tabName 用 ASCII**：EEZ 的 tabName 不进字形收集（KB P-0022），中文 tab 名会豆腐；
   本例 tab 栏虽隐藏（tabName 不可见），仍取 `p1/p2` 稳妥。
5. **tabview 背景要透明**（MAIN `bg_opa=0`），页底色在 Tab 控件上着——否则 tabview
   自身背景盖住页配色（KB P-0021 主题发白问题的本例变体）。
6. **EEZ 无头 CLI 不烘字体**（KB P-0140）：本例刻意只用默认字体 + ASCII，无字体条目，
   CLI 产物即完整；若要加中文，参考 `font-entry-form` 的 lv_font_conv 离线链路。
7. **不要在 tabview 外再套 changeScreen 翻页**：`changeScreen fadeMode` 动画与 tabview
   的 SCROLL_END 吸附有竞态（KB P-0029），本例单屏、原生吸附，从结构上绕开。
8. **离屏页 `lv_obj_get_width` 返回 0 是假象**：LVGL 惰性布局，未滚到的页未参与布局；
   判尺寸前先 `lv_obj_update_layout(tv)`，否则会误诊"第二页 0×0"。
