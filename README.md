# EEZ_stidio_examples — EEZ Studio 示例工程库

> 本仓库收 **EEZ Studio 示例工程**：一个工程一个独立子目录，每个工程演示一类用法、提供一份可拷走复用的实例。
> 使用经验与方法论的沉淀在本地经验库 `C:\Users\yjt54\Desktop\local_knowledge_base`（下称「经验库」）。
> 最后更新：2026-10-19。

---

## 1. 怎么获取 EEZ Studio 的使用经验

按优先级四条途径（详细说明见经验库
`embedded/EEZ_Studio_examples/README.md`）：

1. **先查经验库已有积累**（最快）—— `local_knowledge_base/embedded/EEZ Studio_ui_debug_kit/`：
   - `PLAYBOOK.md`：通用方法论（三层图策略 / 差异量化四步法 / 组件树 8 个通用坑 / 十条红线）
   - `skills.md`：操作手册（自动设计 → 对照查验 → 仿真器真点击）
   - `EEZ_FIRST_WORKFLOW.md`：EEZ 为主、仿真为辅的栈专属流程（验证优先级金字塔 / 七步主链）
   - `cases/`、`intake/`、`prompts/`：历史案例、问题登记、提示词留痕
2. **官方渠道** —— <https://github.com/eez-open/studio>（`docs/` 有使用文档）；
   新建工程向导里的 **Templates / Examples** 是最直接的写法参照；issues 区搜报错关键字。
3. **做示例工程积累** —— 每学会一类用法，就在本仓库落一个最小示例工程（见第 2 节），
   踩的坑写进该工程的 `README.md`，通用结论回灌经验库。
4. **AI 协作留痕** —— 让 AI 改 EEZ 工程时，用 ui_debug_kit 的
   `log_entry.py` 把提示词与新问题追加进经验库记录区（规约见其 `INTAKE.md`）。

---

## 2. 怎么建子目录保存工程文件夹

**一个示例工程 = 一个独立子目录**，目录名即示例主题（kebab-case，见名知意）：

> ★ **新建示例照 [`示例工程模板说明.md`](示例工程模板说明.md) 走**：目录骨架、
> 逐字拷贝 vs 按例重写的文件清单、五步固定流程、固化坑速查表都在那里
> （以 `w1-animation-image` 为蓝本）。

```
EEZ_stidio_examples/
├── README.md              ← 本文件
├── <示例主题>/             ← 每个工程一个独立文件夹
│   ├── README.md          ← ★ 必备（写什么见下）
│   ├── <工程名>.eez-project
│   └── ...
└── ...
```

### 新建一个示例工程的固定动作

1. 在本仓库根新建 `<示例主题>/` 子目录；
2. 拷入 EEZ 工程文件（`.eez-project`、`.ei`、`vars/` 等），
   **剔除可再生产物**：`build/`、`generated/`、SDK 拷贝、大体积缓存；
3. 为该工程写 `README.md`，最少写清四件事：
   - **演示点**：这个示例演示什么用法；
   - **工程结构**：关键文件各自是什么；
   - **依赖版本**：EEZ Studio 版本、LVGL 版本、目标平台；
   - **踩过的坑**：症状 / 根因 / 修法（严重坑在标题加 ★）；
4. 在本文件第 3 节索引表加一行。

### 与经验库的分流

- **只在本示例工程成立** → 写进该工程子目录的 `README.md`；
- **换一个 EEZ 工程还成立**（组件树通用坑、对照查验方法、工具用法）→
  回灌经验库 `embedded/EEZ Studio_ui_debug_kit/` 记录区（`intake/` / `skills.md`）；
- **机器相关路径**（每台电脑不同的 B 类路径）不当事实写死，一律按 `{占位符}` 处理。

---

## 3. 示例工程索引

| 目录 | 演示什么 | 一句话 / 关键坑 |
|---|---|---|
| [`minimal-lvgl-project/`](minimal-lvgl-project/) | 最小可构建工程：`.eez-project` JSON 骨架 + headless 构建判据 | ★ "构建成功"≠有产物，要判据+产物对账；`destinationFolder` 要显式配 |
| [`minimal-lvgl-project-no-flow/`](minimal-lvgl-project-no-flow/) | 同上的 no-flow 姊妹版：`flowSupport`/`generateSourceCodeForEezFramework` 均 `false` → 只出纯 LVGL 代码，无 `eez-flow.cpp/h` | ★ 逻辑全放 native C 时用这版；`ui_init()` 走 `create_screens()` 分支 |
| [`widget-gallery/`](widget-gallery/) | 7 类常用控件（Button/Slider/Switch/Bar/Spinner/Checkbox/Panel）的正确 JSON 形态 | ★ widgetFlags 漏 `CHECKABLE` → 控件变装饰件（LVGL 9.4 `lv_obj.c` 硬条件） |
| [`font-entry-form/`](font-entry-form/) | 中文字体条目正确形态：`renderingEngine` + `lvglRanges` 数字表 + 相对路径 | ★ 决定性变量是条目形态不是字体文件；CLI 不烘字体 .c（P-0140） |
| [`two-state-styles/`](two-state-styles/) | DEFAULT/CHECKED 两态样式 + `checkedState` 初始态 + 子元素颜色继承 | ★ 两态都要写全（只写默认态被主题盖住）；toggle 按钮要显式加 CHECKABLE |
| [`gesture-page-switch/`](gesture-page-switch/) | 多独立 screen + GESTURE 离散切屏（3 页循环），不靠 CHECKED 高亮 | ★ Switch 的 `evt` 输入要 `type:'any'` 否则 Checks 空转；双线裸 `GESTURE` 防静默丢线；手势只能 PC_SIM/真机验收（P-0141） |
| [`one-way-gesture-switch/`](one-way-gesture-switch/) | **只允许单向手势**：仅接 LEFT（左滑循环 A→B→C→A），右滑根本不画组件/不连线 | ★ 单向 = 干脆不生成另一方向的 Switch/Action（别"画了不连"否则 Checks 报 not connected）；其余安全要点与双向版一致 |
| [`tabview-swipe-switch/`](tabview-swipe-switch/) | **Tabview 隐藏 tab 栏 + 原生跟手滑动切页**（与手势版互补：跟手可弹回 vs 离散整页翻） | ★ Tabview 里必须放 Tab 控件（手册配置 1）；`tabviewSize=0` 隐藏 bar；★ Tab（页）必须保留 `SNAPPABLE`——吸附滚动模式下页是吸附点，裁掉它=零吸附点=拖不动（eez-test 同款：都只裁 SCROLLABLE） |
| [`w1-animation-image/`](w1-animation-image/) | **手册 W1. AnimationImage 多帧动画图**：8 帧 spinner，Duration/Repeat 语义，`lv_animimg_*` 代码链 | ★ CLI 构建不产图片 .c（P-0140 图片版）——`gen_images.py` 补烘 `lv_image_dsc_t`（ARGB8888 字节序 B,G,R,A）；帧位图=内嵌 data-URI PNG（bpp32 透明） |
| [`app-list-scroll/`](app-list-scroll/) | **可滚动 App 列表**（watch applist 同款：竖向吸附滚动容器 + CHECKABLE 行 + PRESSED 高亮）+ List 控件 vs 容器左列对照 | ★ List (LVGL) 是 wip → 用普通 Container 自建；`flagScrollDirection:"ver"`+`scrollSnapY:"center"`；行必须保留 SNAPPABLE（P-0150）；样式枚举传名字符串（"VER"）；lv_list 动态行=ui_init 后 C 补 |
| [`w67-w3-w2-slider-arc-bar/`](w67-w3-w2-slider-arc-bar/) | **调节与指示**（W67 Slider / W3 Bar / W2 Arc）：一个 flow 全局变量 `g_val` 同时驱动 Slider/Arc（可拖双向）/Bar（跟随）/Label（表达式拼接），零 C | ★ Slider/Arc 的 value 是 assignable（双向回写）、Bar 是 input（单向）；全局变量 `native:true` 需自实现 `set_var_xxx` 桥，纯 EEZ 用 `false`；文本拼接 `"s"+int` 直接可用 |
| [`perf-tabview-native-vs-eez/`](perf-tabview-native-vs-eez/) | **资源消耗对照**：同构 tabview，原生 LVGL vs EEZ 实测（RAM/Flash） | ★ 实测：RAM 堆 EEZ 仅多 ~1.4KB（+9%，frag 0）；flash text 多 ~1.33MB（flow 引擎+assets）——**RAM 可忽略，flash 是 MCU 主要代价**；perf 对照明细见其 README |
| [`w14-w35-w62-chart-led-scale/`](w14-w35-w62-chart-led-scale/) | **数据可视化与状态指示**（W14 Chart / W35 Led / W62 Scale） | ★ Chart 在 EEZ 是空壳（零属性）→ ui_init 后 C 喂 series；★ Meter 仅 LVGL 8.x（9.4 没有）→ 用 Scale 替代；Led 的 color/brightness 都是 expression 可绑定；Scale 属性可选项多、只写要覆盖的键 |
| [`w23-w59-w73-w16-select-switch/`](w23-w59-w73-w16-select-switch/) | **选择与开关**（W23 Dropdown / W59 Roller / W73 Switch / W16 Checkbox），可见页签 Tabview 4 页 | ★ 联动主线：Dropdown+Roller 的 selected 绑同一 g_sel（assignable 双向，零 flow 图）；★ ToggleButton(W85) 是 EEZ-GUI 件、无 LVGL codegen（lvglBuild 报错）；Switch/Checkbox 无绑定属性；排障用 per-tab bisect |
| [`app-wifi-connect/`](app-wifi-connect/) | **WiFi 扫描/连接全流程 v2**（KB 10 号架构迷你版）：EEZ 画壳+6 状态变量，业务/列表/驱动全在 src/native（契约头+命令环+io_iface 平台分界） | ★ 动作函数体只投递；★ native_vars.h 必须包 extern "C"；★ io 层不依赖 LVGL（clock() 计时）；★ 注释里别写 `xxx_*/`（提前闭合）；hiddenFlag 键名/字体全量/textarea 单向等 v1 坑仍有效 |
| [`app-wifi-scan-flow/`](app-wifi-scan-flow/) | **WiFi 扫描列表 v4（母工程 · Flow 在跑）**：EEZ 画静态外壳（标题/状态行/刷新 + 空 `lv_list`）+ **EEZ 零变量**，状态与列表全由 native 直驱/直读 io | ★ 控件照抄 EEZ 原生形态；★ gen_font 在 cli_build 之后；★ flow 错误守卫；★ v4 起 `gvs=[]`，数组变量已移出 EEZ（见其 `ARCHITECTURE.md`） |
| [`app-wifi-scan-flow-no-flow/`](app-wifi-scan-flow-no-flow/) | **同上的 no-flow 变体**：只把 `flowSupport`/`generateSourceCodeForEezFramework` 关成 `false`，实测纯 LVGL 出码链路完整（生成码 548,573→13,950 字节，`eez::flow` 符号 501→0） | ★ **关 Flow 后 native 动作照样接线**：`screens.c` 直接 `lv_obj_add_event_cb(obj, action_scan_start, LV_EVENT_CLICKED, 0)`，业务零改动（纠正经验库 07 §2"事件 handler 依赖 flowSupport"）；★ 判据要反着写：`eez-flow.*` **不得**出现（preflight `check_no_flow`）；★ `BUILD_TEMPLATES` 的 `#if EEZ_FOR_LVGL/#else` 两分支都得留 |

> 验证状态：**2026-10-19 那轮全量体检覆盖的是当时 9 个示例**（EEZ Studio 0.29 headless CLI
> 构建 0 错 0 警 + 产物清单对账，且 PC_SIM 编译链接 0 错）。**索引现有 17 行 / 磁盘 16 个示例目录**
> （`app-list-scroll` 仍只有索引行、目录未落地），此后新增示例的验证状态**以各自 README 为准**，
> 本行不为未复测的工程背书。最近一次复测：2026-10-21 `app-wifi-scan-flow-no-flow`
> 全链 `preflight.py --with-sim` PASS（含新增 no-flow 反向门禁）。
> 手势运行时行为（gesture-page-switch / one-way-gesture-switch）按 P-0141
> 必须在 PC_SIM/真机验收，Run 预览不产生 GESTURE 事件。
> `font-entry-form` 的字体 .c 已落地：`src/ui/ui_font_cn14.c` / `ui_font_cn20.c`
> （黑体子集 159 字形，lv_font_conv bpp4 生成，仿真器链接通过）。
>
> **PC 仿真器一键编译机制见第 4 节；换工程 = 双击该工程 `design\sim_cmake\run_sim.bat`。**

---

## 4. PC 仿真器一键编译（PC_SIM 适配）

**换工程 = 双击对应工程里的一个 bat**，`apl_lvgl_v9_4` 与 `PC_SIM` 两个公共目录不用改。

### 4.1 机制

- `PC_SIM/lv_port_pc_vscode_v9.5/CMakeLists.txt` 优先读环境变量 `SIM_TARGET_PROJ_DIR`
  定位目标工程（未注入时回退 eez-test，兼容旧用法）；
- 每个 EEZ 工程自带 `design/sim_cmake/` 三件套（**应用侧变动全部放在各工程内**）：

| 文件 | 作用 |
|---|---|
| `run_sim.bat` | 注入本工程绝对路径到 `SIM_TARGET_PROJ_DIR`，直接调 `setup_env.bat` + cmake；**build_rel 生成在本 bat 同目录**（每工程独立缓存） |
| `main.c` | 仿真入口：`lv_init` + SDL 窗口/鼠标/滚轮/键盘 + `ui_init` 主循环 |
| `lv_conf.h` | 本工程专用仿真配置（经 `LV_CONF_PATH` 传入） |

### 4.2 用法

```
双击  <工程>\design\sim_cmake\run_sim.bat        → 编译并启动仿真器窗口
运行  run_sim.bat build                          → 只编译不启动
```

- 产物：`PC_SIM\lv_port_pc_vscode_v9.5\bin\main.exe`（每次编译覆盖，即"当前工程"的仿真器）。
- **缓存**：`build_rel` 在各工程 `design\sim_cmake\` 下、永不删除；每个示例首次编译全量编
  LVGL 一次（ccache 加速），之后增量秒级（`ninja: no work to do`）；切换工程互不污染。
- 旧机制（共享 `PC_SIM\build_rel` + 每次删除重编）已废弃；PC_SIM 下遗留的
  `build_rel`/`build_dbg` 不再被 run_sim.bat 使用，可手动删除腾空间。

### 4.3 关键坑（已解决，改回/新工程时注意）

1. **★ ThorVG 编不过**（`fatal error: config.h`）：全树缺 thorvg 的 `config.h`。
   各工程 `lv_conf.h` 已关 `LV_USE_VECTOR_GRAPHIC`/`LV_USE_THORVG_*`/`LV_USE_LOTTIE`；
   CMakeLists 另有屏蔽 thorvg 源码的兜底。新工程拷 `lv_conf.h` 时别把这些改回 1。
2. **★ SDL 入口**：`main.c` **不要**定义 `SDL_MAIN_HANDLED`（PC_SIM 链 `SDL2main`，
   它的 `main` 转调 `SDL_main`，定义了反而报 undefined reference to SDL_main）。
3. **run_sim.bat 必须 ASCII**：bat 里写中文注释会被 GBK 控制台搞坏字节导致 set 失效；
   括号块内的 echo 文本不能含 `)`（会被当成块结束括号，报"此时不应有 …"且退出码 255）。
4. **换工程零成本**：每示例独立 `build_rel`（bat 同目录），环境变量恒定、cmake 自动增量
   重配置，不需要任何删除动作；绝不要把别的示例的 build 目录拷过来混用。
5. **首次全量编译偶发 ninja 依赖文件目录竞态**（个别 LVGL 文件报
   `opening dependency file ...: No such file or directory`）：重跑一次 run_sim.bat 即过。
6. **路径层级**：`SIM_TARGET_PROJ_DIR` 必须是**工程根**（CMakeLists 往后拼
   `/design/sim_cmake/...`、`/src/ui`），run_sim.bat 里已从 `%~dp0` 上跳两级，别改。
7. **中文字体**：EEZ CLI 不烘字体 .c，需 lv_font_conv 离线生成
   （`--format lvgl --lv-font-name ui_font_cnXX`，字形表取自 TTF 子集 cmap），产物落 `src/ui/`。
