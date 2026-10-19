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

---

## ★ MCU 实测（ESP32-P4 真机工程 idf 编译，lvgl_demo_ai 含 eez-test 全量 UI）

用 `idf.py build` 产物 `lvgl_demo_v9.map` 按组件/成员拆分（`parse_map.py`）：

### 按组件

| 组件 | flash(B) | RAM-bss(B) |
|---|---|---|
| ESP-IDF 系统组件 | 2,267,056 | 16,849 |
| **★ EEZ 自身（ui 组件：生成代码 + flow 引擎 + 字体/位图资源）** | **2,020,894** | **25,705** |
| LVGL 内核（lvgl__lvgl，-Os） | 402,120 | 912 |
| main 应用层 | 267,025 | 1,064 |
| native 层 | 52,629 | 3,512 |
| **合计** | **5,010,320** | **48,042** |

### EEZ ui 组件 2.02MB 内部拆解（真相：字体才是大头）

| 成员 | flash(B) | 说明 |
|---|---|---|
| ui_font_ya_hei_consolas_hybrid_13 | **1,343,625** | ★ 13px 中文字体（GB2312 一二级全量 ~6770 字） |
| **eez-flow.cpp（flow 引擎本体）** | **205,771** | ★ EEZ 框架底价 ≈ **206KB flash** |
| screens.c（全部 UI 生成代码，几十个屏） | 139,080 | |
| 其余 6 档字体（54/15/26/11/16/22/19px） | ≈ 211,790 | |
| ui.c（装配）+ 位图等 | ≈ 120,630 | |
| **RAM：eez-flow.cpp 的 bss** | — | **25,705 B（flow 引擎静态表，全组件 RAM 全在它）** |

### MCU 结论（修正 PC 推算）

1. **EEZ 框架底价 = ~206KB flash + ~25.7KB RAM-bss**——远小于 PC 推算的 1.33MB
   （PC 差值里大头其实是**字体/资源内容**，跟框架无关）。
2. **真正的 flash 大头是中文字体**（一档全量 = 1.34MB）——与 EEZ/原生无关，
   任何方案都要付；预算按字库档位算。
3. RAM：flow 引擎 bss 25.7KB + 运行时堆（PC 实测 ~1.4KB 起步），
   对 P4（768KB SRAM + PSRAM）毫无压力；192KB RAM 的 STM32 也放得下框架，
   但帧缓冲才是决定项。
4. P4 实测整机 flash 5.0MB（含 xiaozhi、wifi 等全部），16MB flash 余量充足。

---

## ★★ 公平账单：EEZ 核心框架**独有**的空间（section 级实测）

> 记账原则：**屏幕 UI 创建代码原生方案同样要写**（手写等价 `lv_xxx_create` 链），
> 所以 `screens.c`（139KB）算中性项；字体/位图任何方案都要（中性项）。
> 只列 **原生方案不需要、纯因 EEZ 而存在** 的部分（`lvgl_demo_v9.map` section 级实测）：

| EEZ 独有项 | flash(B) | RAM(B) | 实测来源 |
|---|---|---|---|
| **flow 引擎代码**（解释器/控件工厂/数据绑定/tick） | **186,108** (.flash.text) | — | eez-flow.cpp.obj |
| **flow 引擎常量表** | **18,419** (.flash.rodata) | — | eez-flow.cpp.obj |
| **assets 二进制**（flow 定义压缩流 + 常量表，原生方案没有这个概念） | **≈52,376** (.flash.rodata 主体) | — | ui.c.obj |
| **flow 引擎静态表**（bss） | — | **25,701** (.dram0.bss) | eez-flow.cpp.obj |
| 绑定/装配的 .data 初值 | ≈2,456 | ≈2,456(.data) | 两文件 .dram0.data |
| **EEZ 核心独有合计** | **≈259KB** | **≈28KB** | |

### 对照结论（修正后的公平数字）

| 口径 | flash | RAM |
|---|---|---|
| ~~PC 推算的"框架开销"~~（误把字体算进去） | ~~1.33MB~~ | — |
| **EEZ 核心独有（本节公平账单）** | **≈259KB** | **≈28KB（bss+data）** |
| 中性项（原生同样要付）：UI 创建代码 | 139KB（EEZ 生成；原生=手写等价） | ≈0 |
| 中性项：字体 7 档 / 位图 | ≈1.55MB / 25KB | ≈0 |

**一句话：EEZ 核心的真实代价 ≈ 259KB flash + 28KB RAM（都在 P4 上可忽略；
1MB flash 的 MCU 要掂量，512KB 以下排除）。**

### 数字可信度（三重交叉验证 + 两个附注）

1. **map 分桶**（组件级→成员级→section 级三层递进，本节所有数字的直接来源）；
2. **assets 符号实测**：map 中 `.rodata.assets  0xcc98` = **52,376B**，与账单
   "assets ≈52,376" 完全一致（ui.c 的 rodata 几乎 100% 就是 assets 数组）；
3. **obj 静态 vs 链接后**：`size` 直接量 `eez-flow.cpp.obj` 得 284,344B(text)——
   比最终链接的 206KB 大，因为 IDF 链接开 `--gc-sections`，引擎里未被引用的
   部件（未用控件工厂/表达式分支）在链接期被裁掉。**obj 是上限，map 是真相**。
4. **优化等级**：当前 sdkconfig 是 `CONFIG_COMPILER_OPTIMIZATION_PERF`(-O2)。
   切 `SIZE`(-Os) 后 flow 引擎还能再缩（经验值 15~30%）；要压 flash 就切它。
