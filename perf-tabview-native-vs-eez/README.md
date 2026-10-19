# perf-tabview-native-vs-eez — 资源消耗对照：原生 LVGL vs EEZ（同构 tabview）

> **对照方法**：两个独立"工程根"（`eez/`、`native/`），各自 `design/sim_cmake/`
> 直连同一个 `PC_SIM` + 同一份 `lv_conf.h`（1MB 内建堆），生成**同构 UI**：
> `lv_tabview`（tab 栏隐藏）+ 2 个 Tab ×（渐变图标块 + 标题 + 副标题）——
> 逐控件一致，只差"UI 由谁生成"：
> - `native/`：纯 LVGL C（`main.c` 里直接 `lv_tabview_create`，无 EEZ/无 flow）
> - `eez/`：EEZ 工程（`build_example.py` 生成 + EEZ flow 引擎 + screens.c）

## 实测结果（2026-10-19，PC_SIM / mingw64 gcc 13.1 -O3 / LVGL 9.4 / 480×320）

### RAM（LVGL 1MB 内建堆，lv_mem_monitor 实测）

| 指标 | 原生 LVGL | EEZ | 差值（EEZ 多） |
|---|---|---|---|
| UI 建成后 used | 16,360 B | 17,840 B | **+1,480 B (+9.0%)** |
| 稳态 +3s used | 16,416 B | 17,840 B | +1,424 B |
| max_used（峰值） | 17,248 B | 18,672 B | +1,424 B |
| 碎片率 frag | 0% | 0% | — |
| 堆总量 | 1,024,000 B | 1,024,000 B | 同一份 lv_conf.h |

**结论：RAM 侧 EEZ 只多 ~1.4KB 堆（flow 运行时状态），占比 9% 但绝对值极小，
1MB 堆下可忽略；frag 均为 0。**

### Flash（链接产物，size 工具）

| 指标 | 原生 LVGL | EEZ | 差值（EEZ 多） |
|---|---|---|---|
| text（代码+常量） | 1,395,580 B | 2,787,300 B | **+1,391,720 B (≈+1.33MB)** |
| data | 5,236 B | 10,464 B | +5,228 B |
| bss（含 1MB 堆） | 1,050,080 B | 1,071,216 B | +21,136 B（flow 静态数据） |
| exe 文件大小 | 1,630,965 B | 3,146,641 B | **+1,515,676 B (≈+1.45MB)** |

**结论：flash 侧 EEZ 多 ~1.33MB text**（EEZ flow 引擎代码 + assets + screens 胶水层）
——**这才是嵌入式 MCU 上的主要代价**（1MB flash 的芯片直接放不下）；
PC 仿真无所谓。注意两变体均无位图/字体资源，差值即纯框架开销。

## 目录结构

```
perf-tabview-native-vs-eez/
├── eez/                      ← EEZ 侧"工程根"
│   ├── build_example.py      ← 生成 perf-eez-tabview.eez-project
│   ├── design/cli_build.py
│   └── design/sim_cmake/     ← run_sim.bat + main.c(EEZ+PERF打点) + lv_conf.h
└── native/                   ← 原生侧"工程根"（无 src/ui，CMake GLOB 空即过）
    └── design/sim_cmake/     ← run_sim.bat + main.c(纯LVGL同构UI+PERF打点) + lv_conf.h
```

两个 bat 零改动可独立使用（各自向上两级推导自己的工程根）；
产物 `bin/main.exe` 每次构建互相覆盖， README 数据对应
`main_eez.exe` / `main_native.exe` 两份留存。

## 复测方法

```bat
cd eez\design\sim_cmake    && run_sim.bat build    && bin\main_eez.exe   看 [PERF]
cd native\design\sim_cmake && run_sim.bat build    && bin\main_native.exe 看 [PERF]
```

`[PERF]` 打点：UI 建成后一次、steady+3s 一次（lv_mem_monitor）。

## 注意事项

1. **公平性**：同一份 lv_conf.h（1MB 内建堆、同编译参数）、逐控件同构 UI；
   EEZ 侧含 flow 引擎初始化（ui_tick 里 eez_flow_tick），native 侧无。
2. **PC 数字 ≠ MCU 数字**：PC 的 text 含 SDL/调试符号等平台差异，但**两侧差值**
   （flow 引擎增量 ~1.33MB text / ~1.4KB 堆）数量级可信；MCU 上还会因
   -Os、无断言（LV_USE_ASSERT_* 关闭）整体缩小。
3. 本例结论只针对 **tabview+静态控件** 这类简单 UI；控件越多，EEZ 的
   assets/screens 胶水占比越低，flow 的 **动态数据绑定收益**越大
   （见 slider-arc-bar：零 C 完成三方联动）。
