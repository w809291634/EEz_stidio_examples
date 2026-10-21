# EEZ_stidio_examples — Code Wiki

> **仓库定位**：EEZ Studio 示例工程库。一个示例 = 一个独立子目录，演示一类用法、给出一份可拷走复用的实例。
> **技术基线**：EEZ Studio **0.29.0**（工程模型 `projectVersion=v3`） · LVGL **9.4.0**（内核） · PC 仿真器 LVGL **9.5.0** · 屏幕 **480×320**、深色主题、`colorBpp=16`。
> **最后更新**：2026-10-20。

---

## 目录

1. [项目概述](#1-项目概述)
2. [仓库整体架构](#2-仓库整体架构)
3. [目录结构详述](#3-目录结构详述)
4. [主要模块职责](#4-主要模块职责)
5. [关键类与函数说明](#5-关键类与函数说明)
6. [依赖关系](#6-依赖关系)
7. [项目运行方式](#7-项目运行方式)
8. [示例工程索引](#8-示例工程索引)
9. [关键约定与坑（铁律速查）](#9-关键约定与坑铁律速查)

---

## 1. 项目概述

### 1.1 它是什么

本仓库不是一个"应用"，而是一套**示例工程的集合**。每个子目录是一份独立的 EEZ Studio 工程，
包含：

- **唯一设计源**：`build_example.py`（Python 脚本，生成 `.eez-project`）；
- **可打开的工程文件**：`<示例名>.eez-project`（EEZ Studio GUI 可直接打开，也可 headless CLI 构建）；
- **构建产物区**：`src/ui/`（EEZ 生成的 C/C++ 代码，可再生产物，gitignore）；
- **PC 仿真三件套**：`design/sim_cmake/`（一键编译/运行 PC 上跑 UI）；
- **说明文档**：每个示例的 `README.md`（演示点 / 工程结构 / 依赖版本 / 踩过的坑）。

### 1.2 为什么要这么组织

EEZ Studio 是"可视化画 UI → 生成 LVGL C 代码"的 IDE。本仓库把每个知识点固化成**最小可构建、可仿真验收**的工程，
以规避"临时手搓工程"的高犯错率。三条要求贯穿全仓：

1. **单一设计源**：UI 全部由 `build_example.py` 生成，`.eez-project` 是产物、**勿手改**；
2. **构建可判定**：headless CLI 构建的判据 = 日志标记 **+ 产物清单对账**；
3. **PC 上可验收**：所有示例都能在 PC 模拟器里真点击/自动演示，无需硬件。

### 1.3 使用经验从哪来（四条途径）

按优先级：本地经验库 `C:\Users\yjt54\Desktop\local_knowledge_base`（PLAYBOOK / skills / cases）→
EEZ 官方仓库 <https://github.com/eez-open/studio>（Templates / Examples / issues）→
在本仓库做示例积累 → AI 协作留痕。详见根 [README.md](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/README.md)。

---

## 2. 仓库整体架构

### 2.1 分层视图

```
┌──────────────────────────────────────────────────────────────────────┐
│  设计层（人写 / 单源）                                                 │
│  build_example.py ──生成──▶ <示例>.eez-project (JSON)                  │
│                                │                                       │
├────────────────────────────────┼───────────────────────────────────────┤
│  构建层（EEZ Studio 0.29 headless CLI）                                │
│  design/cli_build.py ──调用──▶ "EEZ Studio.exe --build-project ..."    │
│                                │ 展开 ${eez-studio ...} 模板占位符      │
│                                ▼                                       │
│  src/ui/  (ui.h/.c · screens.h/.c · vars.h · actions.h                │
│           · styles.h/.c · fonts.h · images.h/.c · structs.h            │
│           · eez-flow.h/.cpp ← Flow 引擎，占生成物体积大头)             │
│                                │                                       │
├────────────────────────────────┼───────────────────────────────────────┤
│  补烘层（CLI 不产字体/图片 .c，需离线补）                              │
│  design/gen_font.py ──▶ src/ui/fonts/ui_font_*.c                      │
│  design/gen_images.py ──▶ src/ui/images/img_*.c                       │
│  （自检：design/audit_chars.py · design/check_project.py）             │
│                                │                                       │
├────────────────────────────────┼───────────────────────────────────────┤
│  应用层（人写，可选）                                                  │
│  src/native/  ← 业务逻辑（契约头 + 变量桥 + 动作 + 平台 io 层）        │
│  显现于 app-wifi-connect（唯一带 native 层的复杂示例）                │
│                                │                                       │
├────────────────────────────────┼───────────────────────────────────────┤
│  仿真层（PC 上运行 UI 的构建/运行管线）                                │
│  design/sim_cmake/{run_sim.bat · main.c · lv_conf.h}                  │
│  run_sim.bat 注入 SIM_TARGET_PROJ_DIR → cmake → PC_SIM 出 main.exe    │
│                                │                                       │
├────────────────────────────────┼───────────────────────────────────────┤
│  公共支撑（全仓共用、不改）      ▼                                     │
│  PC_SIM/lv_port_pc_vscode_v9.5   (SDL2 窗口 + cmake 构建宿主 + FreeRTOS 可选) │
│  apl_lvgl_v9_4                   (LVGL 9.4 内核组件，被 PC_SIM add_subdirectory) │
│  envtest                         (SIM_TARGET_PROJ_DIR 环境探针)         │
└──────────────────────────────────────────────────────────────────────┘
```

### 2.2 一条示例的数据流（端到端）

```
build_example.py ──▶ <示例>.eez-project
                        │  cli_build.py
                        ▼
                     src/ui/*.c/.cpp ─┐
src/native/*（可选）───────────────────┤
design/sim_cmake/main.c ───────────────┤  cmake
lv_conf.h ─────────────────────────────┤  (PC_SIM/CMakeLists.txt)
                                       ▼
                              bin/main.exe  ← SDL 窗口，鼠标/键盘/手势真输入
```

---

## 3. 目录结构详述

### 3.1 仓库根

```
EEz_stidio_examples/
├── README.md                     ← 仓库总说明 + 示例索引 + PC 仿真器机制
├── 示例工程模板说明.md            ← 新建示例的目录骨架 / 逐字拷贝清单 / 五步流程
├── CODE_WIKI.md                  ← 本文件
│
├── <示例主题>/                    ← 每个示例一个独立子目录（见 §8）
│   ├── build_example.py          ← ★ 唯一设计源（生成器）
│   ├── <示例名>.eez-project      ← 生成物（勿手改）
│   ├── design/
│   │   ├── cli_build.py          ← EEZ headless CLI 构建
│   │   ├── gen_font.py           ← （有字体时）补烘中文字体 .c
│   │   ├── gen_images.py         ← （有图片时）补烘图片 .c
│   │   ├── audit_chars.py        ← 逐字审计（文案 ⊆ 字体字符集）
│   │   ├── check_project.py      ← 静态自检（7 项）
│   │   └── sim_cmake/
│   │       ├── run_sim.bat       ← 一键编译/运行 PC 仿真（逐字拷贝）
│   │       ├── main.c            ← 仿真入口（逐字拷贝）
│   │       ├── lv_conf.h         ← 仿真 LVGL 配置（逐字拷贝）
│   │       └── build_rel/        ← 本工程私有构建缓存（gitignore）
│   ├── src/
│   │   ├── ui/                   ← EEZ 生成产物（可再生产物）
│   │   └── native/               ← （可选）业务层，PC/真机共用
│   └── README.md                 ← 演示点 / 结构 / 依赖 / 坑
│
├── PC_SIM/                       ← ★ 公共：LVGL PC 仿真器（构建宿主）
│   ├── readme.txt
│   └── lv_port_pc_vscode_v9.5/
│       ├── CMakeLists.txt        ← ★ 读 SIM_TARGET_PROJ_DIR 定位目标工程
│       ├── setup_env.bat         ← 注入 mingw/cmake/SDL2 的 PATH
│       ├── build.bat
│       ├── main/src/             ← 仿真器自带 main.c / 光标位图 / FreeRTOS 入口
│       ├── config/FreeRTOSConfig.h
│       ├── CODE_WIKI.md          ← 仿真器自身的 Code Wiki（含 LVGL/FreeRTOS 细节）
│       ├── lv_conf.h             ← 仿真器默认配置（浮点/矢量图形开启）
│       └── bin/main.exe          ← ★ 每次编译覆盖的产物（"当前工程"的仿真器）
│
├── apl_lvgl_v9_4/                ← ★ 公共：LVGL 9.4 内核组件（被 PC_SIM 引用）
│   ├── CMakeLists.txt            ← 顶层检测：被 subdirectory 引用时跳过自身 project()
│   ├── src/  (core/ display/ draw/ drivers/ widgets/ ...)
│   ├── env_support/cmake/        ← custom.cmake 产出 lvgl 等 target
│   ├── demos/ examples/ docs/
│
└── envtest/                      ← 环境探针：CMakeLists 只打印 SIM_TARGET_PROJ_DIR
```

### 3.2 单个示例的"骨架 vs 填充"（模板说明）

| 文件 | 复制方式 | 需要改什么 |
|---|---|---|
| `design/cli_build.py` | 逐字拷贝 | **1 处**：`PROJ = ...'<工程名>.eez-project'` |
| `design/sim_cmake/run_sim.bat` | 逐字拷贝 | 无（工程路径由 `%~dp0` 自动推导） |
| `design/sim_cmake/lv_conf.h` | 逐字拷贝 | 无（ThorVG/Lottie 关闭等坑已固化，**勿改回 1**） |
| `design/sim_cmake/main.c` | 逐字拷贝 | 仅当分辨率 ≠ 480×320 改 `SIM_W/SIM_H`；要在 C 里操作 EEZ 对象则加 `#include "screens.h"` |
| `build_example.py` | 骨架照抄 + 内容重写 | 见 [§4.1](#41-设计源--build_examplepy) |

干净拷贝源：`tabview-swipe-switch/design/sim_cmake/` 或 `w1-animation-image/design/sim_cmake/`。
⚠️ 不要从 `app-list-scroll/design/sim_cmake/` 拷 `main.c`（含 List 对照实验的 C 扩展）。

---

## 4. 主要模块职责

### 4.1 设计源 — build_example.py

**职责**：本示例的**唯一真值**。执行后重写 `<示例名>.eez-project`。
以 [minimal-lvgl-project/build_example.py](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/minimal-lvgl-project/build_example.py) 为骨架蓝本。

**照抄段（逐字，跨示例一致）**：

| 段 | 作用 |
|---|---|
| `BUILD_TEMPLATES` | 12 个 `settings.build.files` 模板（screens/actions/vars/structs/images/fonts/styles/ui 的 .h/.c），与 EEZ 0.29 新建工程逐字一致；生成代码骨架 = 模板 + `${eez-studio ...}` 占位符展开 |
| `oid()` / `widget()` / `label()` / `page()` | 控件工厂，序列化形态与 EEZ 0.29 一致 |
| `ZERO_PAD` | 显式清零默认主题 padding/border（让"声明坐标 == 渲染坐标"） |
| `build_project()` 的 `settings` | general（分辨率/深度/主题/嵌入策略）+ build（`destinationFolder` / `lvglInclude` / files） |

**按示例重写段**：

1. `DEFAULT_FLAGS`：用到新控件就从 EEZ 定义挖该控件的官方 `defaultFlags` 补一条（flags 是**最终态白名单**）；
2. 页面控件树（`page()` 的 `children`）；
3. `variables.globalVariables[]`：`{objID, name, type, defaultValue, persistent, native}`（`native:true` 需自实现 `set_var_xxx/get_var_xxx` 桥）；
4. 位图工程另加帧绘制函数 + `bitmaps[]`（内嵌 data-URI PNG，bpp32）；
5. 工程文件名常量 `PROJECT_FILE`。

`settings.build.destinationFolder` 必须显式配（本例 `src\ui`），否则产物落工程根目录。

### 4.2 EEZ 无头构建 — design/cli_build.py

**职责**：调用 EEZ Studio 可执行文件，把 `.eez-project` 编译成 `src/ui/` 下的 C/C++ 代码。
参照实现：[tabview-swipe-switch/design/cli_build.py](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/tabview-swipe-switch/design/cli_build.py)（无字体版）、
[app-wifi-scan-flow/design/cli_build.py](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/app-wifi-scan-flow/design/cli_build.py)（含 flow 错误守卫版）。

要点：

- 命令行：`EEZ Studio.exe --build-project <proj> --no-sandbox --disable-gpu --enable-unsafe-swiftshader --disable-dev-shm-usage`；
- **必须去掉环境变量 `ELECTRON_RUN_AS_NODE`**，否则报 `bad option`；
- **必须等日志出现 `Build successfully finished`** 才终止进程——`No error and no warning detected`
  出现在文件列表**之前**，提前 kill 会掐死 EEZ Flow engine（`eez-flow.h/cpp`）的发射阶段；
- flow 检查错误**非致命**（构建仍"成功"），需正则显式拦截 `N errors? and no warning`；
- 判据（步后）：`src/ui` 下必须有 `eez-flow.h` 与 `eez-flow.cpp`，有位图时 `src/ui/images/` 出现全部 `img_*.c`。

### 4.3 资源补烘 — gen_font.py / gen_images.py

EEZ CLI **不烘字体 .c、不烘图片 .c**（GUI Build 才产），故纯 CLI 工作流需构建后补烘：

| 脚本 | 参照实现 | 产物 | 做法 |
|---|---|---|---|
| `gen_font.py` | [app-wifi-connect/design/gen_font.py](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/app-wifi-connect/design/gen_font.py) | `src/ui/fonts/ui_font_<name>.c` | `npx lv_font_conv --no-compress --bpp 4 --size 14 -r 0x20-0x7E --symbols <非ASCII字符> --format lvgl`；字形取自全量 TTF 的 cmap |
| `gen_images.py` | [w1-animation-image/design/gen_images.py](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/w1-animation-image/design/gen_images.py) | `src/ui/images/img_anim_frame_*.c` | 复算与 `build_example.py` 同源的帧像素，直接生成 EEZ v9 格式 `lv_image_dsc_t`（ARGB8888，内存字节序 **B,G,R,A**） |

顺序敏感：**`gen_font` 必须在 `cli_build` 之后**（EEZ 构建的孤儿清理会删字体 .c）。

### 4.4 交付前自检 — audit_chars.py / check_project.py

| 脚本 | 参照实现 | 检查内容 |
|---|---|---|
| `audit_chars.py` | [app-wifi-connect/design/audit_chars.py](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/app-wifi-connect/design/audit_chars.py) | 逐字审计：工程 JSON 的 `text`/`placeholder` + 表达式字符串字面量 + C 渲染字符串，其非 ASCII 字符必须 ⊆ 字体字符集（抓"方框/豆腐"与私有区字符） |
| `check_project.py` | [app-wifi-connect/design/check_project.py](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/app-wifi-connect/design/check_project.py) | 7 项静态自检：①变量引用 ②字符集⊆字体 ③字体条目形态（`renderingEngine`/`lvglRanges`/`lvglGlyphs`/`glyphs`）④字符集⊆TTF cmap ⑤`native_vars.h` 的 `extern "C"` ⑥C 头注释提前闭合 ⑦demo 无守卫 `exit()` |

### 4.5 PC 仿真三件套 — design/sim_cmake/

| 文件 | 职责 |
|---|---|
| `run_sim.bat` | 注入本工程绝对路径到 `SIM_TARGET_PROJ_DIR` → `call setup_env.bat`（注入 mingw/cmake/SDL2 的 PATH）→ cmake 配置 + 构建；`build_rel` 生成在 bat 同目录（每工程独立缓存）；参数 `build` 只编译不启动 |
| `main.c` | 仿真入口：`lv_init` → `hal_init`（SDL 窗口 + 鼠标/滚轮/键盘 indev）→ `ui_init` → 主循环 `lv_tick_inc(2)` + `lv_timer_handler()` + `ui_tick()` |
| `lv_conf.h` | 本工程专用仿真配置，经 `LV_CONF_PATH` 注入 LVGL 内核 |

### 4.6 PC_SIM 构建宿主 — PC_SIM/lv_port_pc_vscode_v9.5

参照实现：[CMakeLists.txt](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/PC_SIM/lv_port_pc_vscode_v9.5/CMakeLists.txt)。

**用户配置区（只认这几项，其余不用动）**：

| 变量 | 含义 |
|---|---|
| `TARGET_PROJ_DIR` | 目标工程根：优先读环境变量 `SIM_TARGET_PROJ_DIR`，未注入时回退默认工程 |
| `APL_LVGL_DIR` | LVGL 内核全路径（指向 `apl_lvgl_v9_4`） |
| `SIM_H_RES` / `SIM_V_RES` | 仿真窗口尺寸 |
| `LVGL_CONF_FILE` | = `<proj>/design/sim_cmake/lv_conf.h` |
| `UI_DIR` | = `<proj>/src/ui`（`file(GLOB_RECURSE)` 收 `.c/.cpp`） |
| `NATIVE_DIR` | = `<proj>/src/native`（`NATIVE_SOURCES`；**排除 `io_esp`/`test_native`**，否则链接期 `undefined reference to get_var_*`） |
| `SIM_MAIN_DIR` | = `<proj>/design/sim_cmake`（引用工程侧 `main.c`，不复制） |

**关键构建动作**：

- `add_subdirectory(${APL_LVGL_DIR})` 产出 `lvgl` 等 target；
- 通过 `CACHE` 变量把 `LV_CONF_PATH` 传进子作用域（普通变量传不进 `add_subdirectory`）；
- **关掉内核内置 ThorVG**：`CONFIG_LV_USE_THORVG_INTERNAL=OFF`，并把 `libs/thorvg`/`vg_lite` 源文件标 `HEADER_FILE_ONLY`（正则必须两种斜杠都吃）；
- `find_program(ccache)` 加速；`find_package(SDL2 REQUIRED)`；
- `add_executable(main SIM_MAIN_DIR/main.c + mouse_cursor_icon.c + UI_SOURCES + NATIVE_SOURCES)`。

### 4.7 公共支撑 — apl_lvgl_v9_4 / envtest

- **apl_lvgl_v9_4**：LVGL 9.4 源码组件。其 [CMakeLists.txt](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/apl_lvgl_v9_4/CMakeLists.txt) 加了"被作为 subdirectory 引用时跳过自身 `project()`"的顶层检测，使其能被 PC_SIM 直接 `add_subdirectory`。经 `env_support/cmake/custom.cmake` 产出 `lvgl`/`lvgl_examples`/`lvgl_demos`/`lvgl_thorvg`。
- **envtest**：CMake 探针，[CMakeLists.txt](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/envtest/CMakeLists.txt) 只有一句 `message(STATUS "SIM_TARGET_PROJ_DIR env = [$ENV{...}]")`，用于确认环境变量链路。

### 4.8 应用/业务层 — src/native/（app-wifi-connect）

唯一带业务层的示例，落地"**EEZ 画壳 + 业务全在 C**"的三层架构。
参照实现目录：[app-wifi-connect/src/native/](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/app-wifi-connect/src/native)。

| 模块 | 文件 | 职责 |
|---|---|---|
| 契约头 | `app_model.h/.cpp` | 单一侧 include 的头：`APP_IN_*` 输入状态数组（每 id 独立缓冲）+ `APP_OUT_*` 命令环（16 深度）+ `user_io_init/user_io_tick`；平台无关（不碰 LVGL/驱动） |
| 变量桥 | `native_vars.h/.cpp` | `get_var_*` 从契约状态读；`set_var_*` 空实现（EEZ 同时声明 get/set，**必须都给出本体**）；★ 声明 **必须包 `extern "C"`** |
| 动作 | `native_actions.cpp` | `action_*` 函数体**只有一行投递**（`app_set_output` / `app_set_input`），不写业务分支、不碰驱动 |
| 列表渲染 | `wifi_ui_sync.h/.cpp` | retry-until-success：`user_io_tick` 每拍调用；代数(`gen`)或行数变化 → `lv_obj_clean` 重建行；行点击回调按索引回链表查节点置 `APP_IN_PICK_SSID` |
| 平台接口 | `platform/io_iface.h` | 唯一提及"硬件"的薄接口：`wifi_ap_t` 链表 + `io_init/io_sample_inputs/io_wifi_scan/io_wifi_join/io_pwd_cancel/io_remember_toggle` + `wifi_ap_first/count/gen` |
| PC 假驱动 | `platform/io_pc.cpp` | 假 WiFi 世界：scan 2s 出 4 AP / join 2s 连上 / 记住密码（`lv_tick_get` 计时，状态机） |
| 真机骨架 | `platform/io_esp.cpp` | `esp_wifi`/NVS（TODO）；PC 构建由 CMake 正则自动排除 |
| PC 真 WiFi | `platform/io_win.cpp` | Windows WLAN API 后端：`APP_WIFI_REAL` 宏切换，`io_pc.cpp` 整体退场、UI/契约/native 层零改动 |

**数据流**：`UI 事件 → action 投递 APP_OUT → user_io_tick 排空 → io_* 执行 → io_sample_inputs 发布 APP_IN → EEZ 表达式自动刷新`。

---

## 5. 关键类与函数说明

### 5.1 EEZ 生成代码的稳定结构（`src/ui/`）

以 [tabview-swipe-switch/src/ui/](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/tabview-swipe-switch/src/ui) 为例。

| 文件 | 关键内容 |
|---|---|
| `ui.h` / `ui.c` | `ui_init()` / `ui_tick()`。EEZ 0.29 生成的是**纯 flow 工程**：`ui_init()` 内部调 `eez_flow_init(assets, sizeof(assets), (lv_obj_t**)&objects, sizeof(objects), images, sizeof(images), actions)`；`ui_tick()` 调 `eez_flow_tick()` + `tick_screen(g_currentScreen)` |
| `screens.h` | `enum ScreensEnum`（`SCREEN_ID_MAIN` …）、`typedef struct _objects_t { lv_obj_t *main; ... }` 控件句柄表、`extern objects_t objects`、`create_screens()` / `create_screen_main()` / `tick_screen(int)` / `tick_screen_by_id()` 声明 |
| `screens.c` | 控件树的实际创建（`lv_obj_create`/`lv_tabview_create`/… + `lv_obj_set_pos/size/style` + `lv_obj_remove_flag`），句柄写入 `objects.*`；`objects_t objects;` 定义在此 |
| `vars.h` | `enum FlowGlobalVariables`（flow 全局变量）+ `LVGL_VARS_DECL`（native 变量桥声明，如 `get_var_wifi_state`） |
| `actions.h` | `action_xxx(lv_event_t*)` 声明（流程动作） |
| `styles.h/.c` | 具名样式定义 |
| `fonts.h` / `images.h/.c` | 字体/图片资源声明与定义（core 在 `src/ui/fonts/`、`src/ui/images/`） |
| `structs.h` | flow 结构体/枚举定义（`EEZ_FOR_LVGL` 下） |
| `eez-flow.h` / `eez-flow.cpp` | ★ **EEZ Flow 引擎本体**。头部自带 `#define EEZ_FOR_LVGL 1`，公共 API 用 `extern "C"` 包装（C/C++ 兼容）。见 §5.2 |

### 5.2 EEZ Flow 引擎公共 API（eez-flow.h）

| 函数 | 说明 |
|---|---|
| `void eez_flow_init(const uint8_t *assets, uint32_t assetsSize, lv_obj_t **objects, size_t numObjects, const ext_img_desc_t *images, size_t numImages, ActionExecFunc *actions)` | 装配引擎：载入 assets 二进制、绑定控件句柄表、图片表、动作表 |
| `void eez_flow_tick()` | 引擎每拍主循环（执行 flow 状态机、表达式求值、数据绑定刷新） |
| `int16_t eez_flow_get_current_screen()` | 当前屏索引 |
| `FlowState *getFlowState(pageIndex, compIndex)` | 获取页面/组件的 flow 状态（生成代码里每个 `create_screen_*` 会取） |
| `void eez_flow_init_styles/groups/screen_names/object_names/fonts/themes(...)` | 各类名称表与主题初始化（生成代码按需调用） |
| `typedef struct _native_var_t { ... } native_var_t` + `extern native_var_t native_vars[]` | native 变量表（供引擎读取） |
| `void executeActionFunction(int actionId)` | 按 id 执行动作（转调 `actions[]` 表） |

> 生成 `ui.c` 里 `assets[]`（二进制 flow 定义 + 常量表）是 rodata 大头；`native_vars[]` / `actions[]` 在无 native 工程里是空表（`{NATIVE_VAR_TYPE_NONE,0,0}` / `{0}`）。

### 5.3 设计源工厂函数（build_example.py）

| 函数 | 签名 | 说明 |
|---|---|---|
| `oid()` | `→ str(uuid4())` | 生成 EEZ 对象唯一 id |
| `widget(wtype, x, y, w, h, identifier=None, flags=None, local=None, children=None, **extra)` | `→ dict` | 通用控件构造；字段形态与 EEZ 0.29 序列化一致（含 `style`/`localStyles`/`widgetFlags`/`hiddenFlagType`/`checkedStateType` 等）；`flags` 缺省取 `DEFAULT_FLAGS[wtype]` |
| `label(x, y, w, h, text, color="0xFFFFFF", identifier=None, font=None)` | `→ dict` | Label：显式 `ZERO_PAD` + `text_color`；`textType="literal"`、`longMode="WRAP"` |
| `page(name, screen_children, create_at_start=True)` | `→ dict` | 一页 = 铺满屏的 `LVGLScreenWidget` + 子树，包成 `userPages[]` 元素 |
| `build_project()` | `→ dict` | 组装 `themesVersion/settings/variables/actions/userPages/userWidgets/lvglStyles/lvglFonts/bitmaps/themes` 整棵工程 JSON |
| `main()` | — | `json.dump(..., ensure_ascii=False, indent=2)` 落盘 `<工程>.eez-project` |

### 5.4 应用层契约函数（app_model.h）

| 函数 | 说明 |
|---|---|
| `app_set_input_i/_b/_s(id, v)` | 发布输入状态（每 id 独立槽，禁 id-offset 算偏移） |
| `app_get_input_i/_b/_s(id)` | 读取输入状态（`get` 与 `set` 落在同一块内存） |
| `app_set_output(id, app_value_t v)` | UI 动作投递命令入环（满则丢弃） |
| `app_pop_output(id*, v*)` | 排空命令环 |
| `user_io_init()` | 生命周期入口 → `io_init()` |
| `user_io_tick()` | 每循环：排空命令环 → `io_*` 执行 → `io_sample_inputs()` 发布状态 → `wifi_ui_sync()` 渲染同步 |

### 5.5 平台端口函数（io_iface.h）

| 函数 | PC 实现（io_pc.cpp） |
|---|---|
| `io_init()` | 打印初始化 |
| `io_sample_inputs()` | 扫描状态机（2s 建链表）/ 连接状态机（2s 出结果）/ 更新 `connected` 标记 → `app_set_input_*` |
| `io_wifi_scan(v)` | v=1 发起扫描，置 `scan_state=1` |
| `io_wifi_join(v)` | 取 `APP_IN_PICK_SSID` + `APP_IN_PWD`，置 `wifi_state=1` |
| `io_pwd_cancel(v)` / `io_remember_toggle(v)` | 取消面板 / 翻转记住密码 |
| `wifi_ap_first/count/gen()` | 链表遍历入口 + 代数（内容变化 +1，UI 据此重建） |

### 5.6 仿真入口（sim_cmake/main.c）

| 函数 | 说明 |
|---|---|
| `hal_init(w, h)` | 创建 SDL 窗口 + 默认 group + 鼠标（含光标位图）/滚轮/键盘 indev，绑定同一 group |
| `main()` | `lv_init()` → `hal_init()` → `ui_init()` → `while(1){ lv_tick_inc(2); lv_timer_handler(); ui_tick(); usleep(4000); }` |

> ★ **不要定义 `SDL_MAIN_HANDLED`**：PC_SIM 链接了 `libSDL2main`，它把本文件 `main` 重命名为 `SDL_main`；定义了反而报 `undefined reference to SDL_main`。
> 应用层示例（如 app-wifi-connect）另加：假 indev 自动演示定时器（`demo_timer`）、`[STATE]` 状态打印、`lv_snapshot` 自证截图。

---

## 6. 依赖关系

### 6.1 运行时 / 构建时依赖（PC 仿真）

```
bin/main.exe
├── lvgl（静态；来自 add_subdirectory(apl_lvgl_v9_4)，用工程侧 lv_conf.h 编译）
├── PC_SIM/lv_port_pc_vscode_v9.5/main/src/mouse_cursor_icon.c（光标位图）
├── <proj>/design/sim_cmake/main.c            （工程侧仿真入口，引用不复制）
├── <proj>/src/ui/**/*.c|*.cpp                （UI_SOURCES：EEZ 生成代码）
├── <proj>/src/native/**/*.c|*.cpp            （NATIVE_SOURCES：业务层，排除 io_esp/test_native）
└── SDL2 (SDL2main/SDL2)  ← 系统/Mingw 安装
```

### 6.2 工具链外部依赖

| 依赖 | 用途 | 备注 |
|---|---|---|
| **EEZ Studio 0.29.0** | headless CLI 构建（`--build-project`） | 路径见 `cli_build.py` 的 `EXE` 常量（安装位置因人而异） |
| **LVGL 9.4.0** (`apl_lvgl_v9_4`) | 内核组件 | 与 PC_SIM 的 9.5.0 模块级同源，可编 9.2+ |
| **LVGL 9.5.0** (PC_SIM 内置) | 仿真器窗口驱动（SDL） | `LV_USE_SDL=1`、`LV_COLOR_DEPTH=32` |
| **CMake ≥ 3.10 / Ninja 或 MinGW Makefiles** | 构建 | `run_sim.bat` 自动选 generator |
| **mingw64 gcc + SDL2-2.32.4** | 编译/链接 | PATH 由 `setup_env.bat` 注入 |
| **ccache**（可选） | 加速 LVGL 首次全量编译 | CMake 自动探测 |
| **Python 3 + fontTools** | 生成器 / 自检（`check_project.py` 检查 4） | managed python |
| **npx lv_font_conv** | 烘中文字体 .c | `gen_font.py` 使用 |
| **Windows WLAN API**（仅真 WiFi） | `io_win.cpp` | `-lwlanapi` 经 `CMAKE_CXX_STANDARD_LIBRARIES` 注入（**必须排在目标文件之后**） |

### 6.3 版本锁定

| 项 | 值 |
|---|---|
| 工程模型 | `projectVersion=v3`，`projectType=lvgl` |
| LVGL 版本声明 | `general.lvglVersion="9.4.0"` |
| 屏幕 | `displayWidth/Height=480/320`，`colorBpp="16"`，`bitmapColorFormat="BGR"`，`darkTheme=true` |
| 产物目录 | `build.destinationFolder="src\\ui"`，`lvglInclude="lvgl.h"` |

---

## 7. 项目运行方式

### 7.1 新建 / 修改一个示例的五步固定流程（顺序别乱）

```bat
cd <示例名>
python build_example.py                && rem 1. 设计源 → .eez-project
python design\cli_build.py             && rem 2. EEZ CLI 构建（判据：0 错 0 警 + 产物对账）
python design\gen_font.py              && rem 3a. 有字体时补烘（必须在 cli_build 之后）
python design\gen_images.py            && rem 3b. 有图片时补烘（P-0151）
双击 design\sim_cmake\run_sim.bat       && rem 4. 编译并弹仿真器（加 build 参数只编译）
python design\audit_chars.py           && rem 5a. 逐字审计
python design\check_project.py         && rem 5b. 7 项静态自检
```

判据（步 2 后）：`ls src/ui` 必须有 `eez-flow.h` / `eez-flow.cpp`，有位图时 `src/ui/images/` 现全部 `img_*.c`。

### 7.2 PC 仿真器一键编译（推荐）

**换工程 = 双击对应工程里的 `run_sim.bat`**，`apl_lvgl_v9_4` 与 `PC_SIM` 两个公共目录不用改。

```
双击 <工程>\design\sim_cmake\run_sim.bat   → 编译并启动仿真器窗口
运行 run_sim.bat build                     → 只编译不启动
```

- 机制：bat 把工程根注入 `SIM_TARGET_PROJ_DIR` → `PC_SIM/CMakeLists.txt` 读该变量定位目标 → cmake 出 `bin/main.exe`；
- **缓存**：`build_rel` 在各工程 `design/sim_cmake/` 下、永不删除；每例首次全量编 LVGL（ccache 加速），之后增量秒级；切换工程互不污染。

### 7.3 用 EEZ Studio GUI

打开 `<示例名>.eez-project` → 工具栏 Build（扳手）。GUI Build 会**顺便烘字体/图片 .c**（CLI 不烘）。GUI 的 **Run 预览不产生 GESTURE 事件**，手势行为需 PC_SIM/真机验收。

### 7.4 PC 真 WiFi 模式（app-wifi-connect）

`双击 app-wifi-connect/design/sim_cmake/run_sim_realwifi.bat`：同框架的**真硬件后端**
（`APP_WIFI_REAL` 宏 → `io_win.cpp`，UI/契约/native 层零改动），
用 Windows WLAN API 真扫/真连（**会切换电脑网络**）。★ 零自动化，全程手动；
`run_sim.bat`（假模式）保留自动演示用于教学/CI。

### 7.5 运行模式小结

| 模式 | 入口 | UI 来源 | 业务来源 |
|---|---|---|---|
| 纯 UI 教学/对照 | `run_sim.bat` | `src/ui/`（EEZ 生成） | 无 |
| 应用（假 WiFi） | `run_sim.bat` | `src/ui/` + C 渲染列表 | `src/native/` + `io_pc.cpp` |
| 应用（真 WiFi） | `run_sim_realwifi.bat` | 同上（零改动） | `src/native/` + `io_win.cpp` |
| 原生对照实验 | `perf-*/native/design/sim_cmake/run_sim.bat` | 纯手写 LVGL（无 `src/ui`） | `main.c` |

---

## 8. 示例工程索引

> 验证状态：九个示例均通过 EEZ Studio 0.29 headless CLI 构建（0 错 0 警 + 产物清单对账），
> 且全部通过 PC_SIM 仿真器一键编译（编译 + 链接 0 错）。

### 8.1 基础与控件

| 目录 | 演示点 | 关键坑 / 要点 |
|---|---|---|
| [minimal-lvgl-project](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/minimal-lvgl-project) | 最小可构建工程：`.eez-project` JSON 骨架 + headless 构建判据 | ★"构建成功"≠有产物，要判据+产物对账；`destinationFolder` 要显式配 |
| [minimal-lvgl-project-no-flow](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/minimal-lvgl-project-no-flow) | 同上的 no-flow 姊妹版：`flowSupport`/`generateSourceCodeForEezFramework` 均 `false` → 纯 LVGL 出码 | ★ 不发射 `eez-flow.cpp/h`；`ui_init()` 走 `create_screens()` 分支；逻辑全放 native C 时用这版 |
| [widget-gallery](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/widget-gallery) | 7 类常用控件（Button/Slider/Switch/Bar/Spinner/Checkbox/Panel）的正确 JSON 形态 | ★ `widgetFlags` 漏 `CHECKABLE` → 控件变装饰件（LVGL 9.4 `lv_obj.c` 硬条件） |
| [font-entry-form](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/font-entry-form) | 中文字体条目正确形态：`renderingEngine` + `lvglRanges` 数字表 + 相对路径 | ★ 决定性变量是条目形态不是字体文件；CLI 不烘字体 .c |
| [two-state-styles](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/two-state-styles) | DEFAULT/CHECKED 两态样式 + `checkedState` 初始态 + 子元素颜色继承 | ★ 两态都要写全；toggle 按钮要显式加 CHECKABLE |

### 8.2 手势与切页

| 目录 | 演示点 | 关键坑 / 要点 |
|---|---|---|
| [gesture-page-switch](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/gesture-page-switch) | 多独立 screen + GESTURE 离散切屏（3 页循环） | ★ Switch 的 `evt` 输入要 `type:'any'`；双线裸 `GESTURE` 防静默丢线；手势只能 PC_SIM/真机验收 |
| [one-way-gesture-switch](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/one-way-gesture-switch) | 只允许单向手势：仅接 LEFT 左滑循环，右滑不画/不连线 | ★ 单向 = 干脆不生成另一方向的 Switch/Action |
| [tabview-swipe-switch](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/tabview-swipe-switch) | Tabview 隐藏 tab 栏 + 原生跟手滑动切页 | ★ Tabview 里必须放 Tab 控件；`tabviewSize=0` 隐藏 bar；Tab 必须保留 `SNAPPABLE` |

> 注：根 `README.md` 的索引表还列有 `app-list-scroll`（可滚动 App 列表），但该目录**当前不存在**（索引超前于实际目录）。

### 8.3 控件手册专题（W 号命名）

| 目录 | 演示点 | 关键坑 / 要点 |
|---|---|---|
| [w1-animation-image](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/w1-animation-image) | 手册 W1 AnimationImage 多帧动画图（8 帧 spinner） | ★ CLI 不产图片 .c → `gen_images.py` 补烘 `lv_image_dsc_t`（ARGB8888 字节序 B,G,R,A） |
| [w67-w3-w2-slider-arc-bar](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/w67-w3-w2-slider-arc-bar) | 调节与指示：一个 flow 全局变量 `g_val` 同时驱动 Slider/Arc/Bar/Label，零 C | ★ Slider/Arc 的 value 是 assignable（双向回写）；Bar 是 input（单向）；纯 EEZ 用 `native:false` |
| [w14-w35-w62-chart-led-scale](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/w14-w35-w62-chart-led-scale) | 数据可视化与状态指示（W14 Chart / W35 Led / W62 Scale） | ★ Chart 在 EEZ 是空壳（零属性）→ ui_init 后 C 喂 series；Meter 仅 LVGL 8.x → 用 Scale 替代 |
| [w23-w59-w73-w16-select-switch](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/w23-w59-w73-w16-select-switch) | 选择与开关（W23 Dropdown / W59 Roller / W73 Switch / W16 Checkbox），可见页签 Tabview 4 页 | ★ Dropdown+Roller 绑定同一 `g_sel`（assignable 双向）；ToggleButton(W85) 无 LVGL codegen |

### 8.4 应用与性能

| 目录 | 演示点 | 关键坑 / 要点 |
|---|---|---|
| [app-wifi-connect](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/app-wifi-connect) | WiFi 扫描/连接全流程 v3（链表渲染版）：EEZ 画壳 + native 业务层（契约头/命令环/io 平台分界/真 WiFi） | ★ 动作函数体只投递；★ `native_vars.h` 必须包 `extern "C"`；★ io 层不依赖 LVGL；新建 native 文件后删 `build_rel` 重配（GLOB 不重扫） |
| [app-wifi-scan-flow](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/app-wifi-scan-flow) | WiFi 连接应用基础模板：空屏幕骨架（0 控件/字体/动作/变量）+ cli_build/audit/PC 仿真管线齐备 | ★ 控件照抄 EEZ 原生形态；★ `gen_font` 在 `cli_build` 之后；★ flow 错误守卫；含 `DESIGN.md`/`EEZ_CHECKLIST.md`/`IMPLEMENTATION.md`/`SCAN_BINDING.md`/`mockups/` 设计资料 |
| [perf-tabview-native-vs-eez](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/perf-tabview-native-vs-eez) | 资源消耗对照：同构 tabview，原生 LVGL vs EEZ（RAM/Flash 实测 + ESP32-P4 真机 map 拆解） | ★ 结论：EEZ 核心真实代价 ≈ **259KB flash + 28KB RAM**（PC 差值里的 1.33MB 大头其实是中文字体）；见 `parse_map.py` |
| [app-wifi-scan-flow-no-flow](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/app-wifi-scan-flow-no-flow) | 上者的 **Flow on/off A/B 变体**：仅把 `flowSupport`/`generateSourceCodeForEezFramework` 改 `false`，native 层与控件树逐字相同 | ★ 实测关 Flow 后 native 动作**仍由生成码直挂** `lv_obj_add_event_cb(..., action_scan_start, LV_EVENT_CLICKED, 0)`，业务零改动；★ 判据反写：`eez-flow.*` **不得**出现（`preflight.check_no_flow`）；★ 生成码 548,573→13,950 字节、二进制 `eez::flow` 符号 501→0 |

### 8.5 公共 / 辅助目录

| 目录 | 说明 |
|---|---|
| [PC_SIM](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/PC_SIM) | LVGL PC 仿真器（构建宿主 + SDL 窗口 + FreeRTOS 可选）。其自身有 [CODE_WIKI.md](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/PC_SIM/lv_port_pc_vscode_v9.5/CODE_WIKI.md) 详述 LVGL/FreeRTOS 细节 |
| [apl_lvgl_v9_4](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/apl_lvgl_v9_4) | LVGL 9.4 内核组件（被 PC_SIM 引用） |
| [envtest](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/envtest) | `SIM_TARGET_PROJ_DIR` 环境探针 |
| `font-test/` · `wifi_connect_2/` | 仅含空目录骨架与 `build_rel` 缓存的工作中目录（暂无源文件） |

---

## 9. 关键约定与坑（铁律速查）

### 9.1 生成 / 构建类

| 坑 | 说明 |
|---|---|
| ★ CLI"构建成功"≠有产物 | 判据 = 日志标记 **+ 产物目录对账**（`src/ui/` 12 个模板文件 + `eez-flow.cpp/h`） |
| ★ cli_build 必须等 `Build successfully finished` | `No error...` 出现在文件列表**之前**，提前 kill 会掐死 Flow engine 的发射阶段 |
| ★ CLI 不烘字体/图片 .c | 纯 CLI 工作流需 `gen_font.py` / `gen_images.py` 补烘（GUI Build 才产） |
| ★ `flowSupport:false` ≠ 事件链断 | 关 Flow 后 EEZ 不再发射 `eez-flow.cpp/h` 与 `assets[]`，`ui_init()` 走 `create_screens()`；但 **`implementationType:"native"` 的动作仍直挂** `lv_obj_add_event_cb(obj, action_xxx, LV_EVENT_CLICKED, 0)`（实测 `app-wifi-scan-flow-no-flow`）。依赖 Flow 的是**表达式绑定 / flow 组件 / SetVariable**，不是 native 动作 |
| ★ `destinationFolder` 不配 → 产物落工程根 | 显式配 `src\ui` |
| 构建日志 Chromium 噪音 | `disk_cache`/`Gpu Cache Cache failed` 等**不是构建错误** |

### 9.2 控件结构类（P-0164）

- **控件结构照抄 EEZ 原生形态，禁止自创**；新建 UI 时 EEZ GUI 新建该控件 → 照抄默认 JSON → 只改 text/坐标/样式值；
- `widgetFlags` 是**最终态白名单**，漏写默认 flag 会被 `remove_flag` 反向移除；吸附容器子对象必须留 `SNAPPABLE`；
- 样式枚举属性传**名字符串**（如 `"VER"`），传数字会发射 `LV_GRAD_DIR_1` 编译错；
- 每个示例必须覆盖所含控件的**手册全部属性**（多实例演示不同 mode/取值）。

### 9.3 native 应用层类（P-0163）

- 动作函数体**只投递**，业务在 io 层；
- `native_vars.h` **必须包 `extern "C"`**（漏了 → C 侧链接 `undefined reference to get_var_xxx`）；
- EEZ native 变量的 `set_` 也必须给本体（不回写就空实现）；
- io 平台层**不依赖 LVGL**（计时用 `clock()`，别用 `lv_tick_get`）；
- 新建 native 文件后**删 `build_rel` 重配**（CMake `file(GLOB)` 不自动重扫新文件）；
- 头文件注释里别写 `xxx_*/`（注释里的 `*/` 会提前闭合，后面中文注释变成"代码"）。

### 9.4 仿真器类（PC_SIM）

1. ★ **ThorVG 编不过**（`fatal error: config.h`）：各工程 `lv_conf.h` 已关 `LV_USE_VECTOR_GRAPHIC`/`LV_USE_THORVG_*`/`LV_USE_LOTTIE`；CMakeLists 另有屏蔽 thorvg 源码的兜底，**新工程拷 `lv_conf.h` 时别改回 1**；
2. ★ **不要定义 `SDL_MAIN_HANDLED`**（PC_SIM 链 `SDL2main`）；
3. **`run_sim.bat` 必须 ASCII**：中文注释会被 GBK 控制台搞坏；括号块内 echo 不能含 `)`；
4. **换工程零成本**：每示例独立 `build_rel`；绝不拷别例的 build 目录混用；
5. **首次全量编译偶发 ninja 依赖竞态**：重跑一次即过；
6. **`SIM_TARGET_PROJ_DIR` 必须是工程根**（bat 已从 `%~dp0` 上跳两级）；
7. **中文字体**：EEZ CLI 不烘，需 `lv_font_conv` 离线生成（字形表取自 TTF 子集 cmap），产物落 `src/ui/`。

---

## 10. 相关文档

| 文档 | 位置 | 内容 |
|---|---|---|
| 仓库总说明 + 示例索引 | [README.md](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/README.md) | 四条经验获取途径、目录规范、PC 仿真器机制与坑 |
| 新建示例模板说明 | [示例工程模板说明.md](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/示例工程模板说明.md) | 目录骨架、逐字拷贝 vs 按例重写清单、五步流程、坑速查 |
| PC 仿真器 Code Wiki | [PC_SIM/.../CODE_WIKI.md](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/PC_SIM/lv_port_pc_vscode_v9.5/CODE_WIKI.md) | LVGL v9.5 子系统、FreeRTOS 集成、构建与调试 |
| 应用设计资料 | [app-wifi-scan-flow/](file:///c:/Users/yjt54/Desktop/EEz_stidio_examples/app-wifi-scan-flow) | `DESIGN.md`（UI 设计 v4）、`EEZ_CHECKLIST.md`（84 控件 / 51 变量照抄清单）、`IMPLEMENTATION.md`、`SCAN_BINDING.md`、`design/mockups/`（9 张过程图） |

> **文档生成日期**：2026-10-20 · **基线版本**：EEZ Studio 0.29.0 / LVGL 9.4.0 / PC_SIM LVGL 9.5.0
</content>
</invoke>
