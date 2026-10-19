# w67-w3-w2-slider-arc-bar — 调节与指示（手册 W67 Slider / W3 Bar / W2 Arc）：一个 flow 变量驱动全部指示器（A 级组合 1/5）

## 演示点

**零 C 代码的数据绑定主线**：一个 flow 全局变量 `g_val`（integer，初值 25）同时驱动
四个控件——

| 控件 | 绑定 | 方向 | 行为 |
|---|---|---|---|
| Slider（416×24） | `value` = `g_val`（expression, **assignable**） | 双向 | 拖动写回 g_val |
| Arc（170×170，可拖） | `value` = `g_val`（expression, assignable） | 双向 | 拖弧同样写回 |
| Bar（416×28） | `value` = `g_val`（expression, input） | 单向 | 跟随变化，`enableAnimation:true` 平滑过渡 |
| Label | `text` = `"Value: " + g_val`（textType: expression） | 单向 | 实时显示数值（EEZ flow 的 + 对 string+int 自动拼接转串） |

**效果**：拖 Slider 或 Arc 任一个，Bar/Label/另一方可调件全部同步——"调节与指示"
的最小数据流，全程不写一行 C。

## 工程结构

```
w67-w3-w2-slider-arc-bar/
├── build_example.py          ← 唯一设计源
├── slider-arc-bar.eez-project
├── design/
│   ├── cli_build.py          ← EEZ 无头 CLI 构建
│   └── sim_cmake/            ← PC_SIM 仿真器三件套
└── src/ui/
    ├── screens.c             ← 含双向绑定代码（VALUE_CHANGED 回写 + tick 同步）
    └── eez-flow.cpp/h        ← flow 引擎（g_val 的读写都在里面）
```

**关键生成代码**（`src/ui/screens.c`）：

```c
/* 拖 Slider → 写回 g_val（VALUE_CHANGED 事件里） */
int32_t value = lv_slider_get_value(ta);
/* tick 里三方同步 */
int32_t cur_val = lv_slider_get_value(objects.slider_main);
if (new_val != cur_val) lv_slider_set_value(objects.slider_main, new_val, LV_ANIM_OFF);
int32_t cur_val = lv_bar_get_value(objects.bar_main);
if (new_val != cur_val) lv_bar_set_value(objects.bar_main, new_val, LV_ANIM_ON);
```

## 构建与验收

```
python build_example.py                   # 重新生成工程
python design/cli_build.py                # EEZ CLI 构建
双击 design\sim_cmake\run_sim.bat          # 编译并弹仿真器
```

PC_SIM 里拖 Slider 或 Arc：Bar 平滑跟随、Label 数字实时变；两方可调件互相同步。

## 踩过的坑

1. **★ 全局变量 `native:true` vs `false`**：`native:true` = 变量归固件侧所有，
   EEZ 会生成对 `set_var_g_val` / `get_var_g_val` 的调用——**必须在你的 C 代码里
   实现这两个桥函数**（传感器/wifi/协议栈数据接入 UI 的标准入口，见 KB P-0083 的
   native_vars 桥），否则链接报 `undefined reference to set_var_g_val`。
   本例是纯 EEZ 演示，用 `native:false`（flow 引擎内部管理，零 C）。
2. **value 绑定类型语义不同**：Slider/Arc 的 value 是 **assignable**（双向，
   拖动会写回表达式变量）；Bar 的 value 是 **input**（单向只读）。别把 Bar 当输入件。
3. **文本拼接不用 IntToStr**：EEZ flow 的 `+` 对 string + int 自动转串拼接
   （`"Value: " + g_val` 直接可用；安装包里没有 IntToStr 这个函数）。
4. **三控件 flags 各不相同**（官方默认）：Slider v9 无 SCROLLABLE/CHAIN_HOR 但有
   SCROLL_ON_FOCUS；Bar 无 SCROLLABLE；Arc 无 SCROLLABLE 且**连 CHAIN 都没有**
   （不可滚动的独立件）——照抄本工程 DEFAULT_FLAGS 即可（P-0150：勿裁勿加）。
5. **★ cli_build.py 必须等 "Build successfully finished"**：`"No error and no
   warning detected"` 出现在文件列表**之前**，脚本提前 kill 会掐死 EEZ Flow
   engine 的发射（eez-flow.h/cpp 缺失 → `g_currentScreen` 链接错）——此前误判
   "时序抖动重跑即现"，真因是脚本提前退出（P-0152 坑 4 更正，已修全部脚本副本）。
6. **无字体/无图片条目**：CLI 产物即完整（P-0140/P-0151 仅影响字体/图片）。

## 依赖版本

EEZ Studio 0.29（projectVersion=v3）· LVGL 9.4 · 480x320 · PC_SIM 仿真验证
（CLI 构建 0 错 0 警 + 仿真器编译链接 0 错，2026-10-19）。
