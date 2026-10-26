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
   - `EEZ_FIRST_WORKFLOW_FLOW.md` / `EEZ_FIRST_WORKFLOW_NO_FLOW.md`：栈专属流程（flow / no flow 两份；验证金字塔[静看 EEZ·动看仿真] / no flow 七步主线）
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
├── flow-examples/          ← ★ 例外：**Flow 机制类示例**统一住这里（每个仍是独立子目录）
│   ├── README.md          ← 归属判据 / 命名 / 骨架 / 登记规则
│   └── <flow-主题>/
└── ...
```

### 新建一个示例工程的固定动作

1. 在本仓库根新建 `<示例主题>/` 子目录；**演示点是 Flow 机制本身**（变量/执行语义/动作件/表达式）的
   改建在 `flow-examples/<flow-主题>/`（判据见 [`flow-examples/README.md`](flow-examples/README.md) §1）；
2. 拷入 EEZ 工程文件（`.eez-project`、`.ei`、`vars/` 等），
   **剔除可再生产物**：`build/`、`generated/`、SDK 拷贝、大体积缓存；
3. 为该工程写 `README.md`，最少写清四件事：
   - **演示点**：这个示例演示什么用法；
   - **工程结构**：关键文件各自是什么；
   - **依赖版本**：EEZ Studio 版本、LVGL 版本、目标平台；
   - **踩过的坑**：症状 / 根因 / 修法（严重坑在标题加 ★）；
4. 在本文件第 3 节索引表加一行（`flow-examples/` 里的工程链接写 `flow-examples/<名>/`，
   并在 [`flow-examples/README.md`](flow-examples/README.md) §6 清单再登一行）。

### 与经验库的分流

- **只在本示例工程成立** → 写进该工程子目录的 `README.md`；
- **换一个 EEZ 工程还成立**（组件树通用坑、对照查验方法、工具用法）→
  回灌经验库 `embedded/EEZ Studio_ui_debug_kit/` 记录区（`intake/` / `skills.md`）；
- **机器相关路径**（每台电脑不同的 B 类路径）不当事实写死，一律按 `{占位符}` 处理。

---

## 3. 示例工程索引

> **不是示例的专区目录**：[`flow-understanding/`](flow-understanding/) ——
> EEZ Flow 的**理解与取证专区**（手册锚点地图、执行语义/表达式/动作件三篇蒸馏笔记、
> 从装机 Studio 抽出的权威可用性表、以及"该补哪些示例"的规划）。
> 判"EEZ 能不能做 X"先查它，别靠试错猜；它里面的结论会持续回灌本仓库各示例 README 与经验库。

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
| `app-list-scroll/`（**目录未落地，仅索引**） | **可滚动 App 列表**（watch applist 同款：竖向吸附滚动容器 + CHECKABLE 行 + PRESSED 高亮）+ List 控件 vs 容器左列对照 | ★ List (LVGL) 是 wip → 用普通 Container 自建；`flagScrollDirection:"ver"`+`scrollSnapY:"center"`；行必须保留 SNAPPABLE（P-0150）；样式枚举传名字符串（"VER"）；lv_list 动态行=ui_init 后 C 补 |
| [`w67-w3-w2-slider-arc-bar/`](w67-w3-w2-slider-arc-bar/) | **调节与指示**（W67 Slider / W3 Bar / W2 Arc）：一个 flow 全局变量 `g_val` 同时驱动 Slider/Arc（可拖双向）/Bar（跟随）/Label（表达式拼接），零 C | ★ Slider/Arc 的 value 是 assignable（双向回写）、Bar 是 input（单向）；全局变量 `native:true` 需自实现 `set_var_xxx` 桥，纯 EEZ 用 `false`；文本拼接 `"s"+int` 直接可用 |
| [`perf-tabview-native-vs-eez/`](perf-tabview-native-vs-eez/) | **资源消耗对照**：同构 tabview，原生 LVGL vs EEZ 实测（RAM/Flash） | ★ 实测：RAM 堆 EEZ 仅多 ~1.4KB（+9%，frag 0）；flash text 多 ~1.33MB（flow 引擎+assets）——**RAM 可忽略，flash 是 MCU 主要代价**；perf 对照明细见其 README |
| [`w14-w35-w62-chart-led-scale/`](w14-w35-w62-chart-led-scale/) | **数据可视化与状态指示**（W14 Chart / W35 Led / W62 Scale） | ★ Chart 在 EEZ 是空壳（零属性）→ ui_init 后 C 喂 series；★ Meter 仅 LVGL 8.x（9.4 没有）→ 用 Scale 替代；Led 的 color/brightness 都是 expression 可绑定；Scale 属性可选项多、只写要覆盖的键 |
| [`w23-w59-w73-w16-select-switch/`](w23-w59-w73-w16-select-switch/) | **选择与开关**（W23 Dropdown / W59 Roller / W73 Switch / W16 Checkbox），可见页签 Tabview 4 页 | ★ 联动主线：Dropdown+Roller 的 selected 绑同一 g_sel（assignable 双向，零 flow 图）；★ ToggleButton(W85) 是 EEZ-GUI 件、无 LVGL codegen（lvglBuild 报错）；Switch/Checkbox 无绑定属性；排障用 per-tab bisect |
| [`app-wifi-connect/`](app-wifi-connect/) | **WiFi 扫描/连接全流程 v2**（KB 10 号架构迷你版）：EEZ 画壳+6 状态变量，业务/列表/驱动全在 src/native（契约头+命令环+io_iface 平台分界） | ★ 动作函数体只投递；★ native_vars.h 必须包 extern "C"；★ io 层不依赖 LVGL（clock() 计时）；★ 注释里别写 `xxx_*/`（提前闭合）；hiddenFlag 键名/字体全量/textarea 单向等 v1 坑仍有效 |
| [`app-wifi-scan-flow/`](app-wifi-scan-flow/) | **WiFi 扫描列表 v4（母工程 · Flow 在跑）**：EEZ 画静态外壳（标题/状态行/刷新 + 空 `lv_list`）+ **EEZ 零变量**，状态与列表全由 native 直驱/直读 io | ★ 控件照抄 EEZ 原生形态；★ gen_font 在 cli_build 之后；★ flow 错误守卫；★ v4 起 `gvs=[]`，数组变量已移出 EEZ（见其 `ARCHITECTURE.md`） |
| [`app-wifi-scan-flow-no-flow/`](app-wifi-scan-flow-no-flow/) | **同上的 no-flow 变体**：只把 `flowSupport`/`generateSourceCodeForEezFramework` 关成 `false`，实测纯 LVGL 出码链路完整（生成码 548,573→13,950 字节，`eez::flow` 符号 501→0） | ★ **关 Flow 后 native 动作照样接线**：`screens.c` 直接 `lv_obj_add_event_cb(obj, action_scan_start, LV_EVENT_CLICKED, 0)`，业务零改动（纠正经验库 07 §2"事件 handler 依赖 flowSupport"）；★ 判据要反着写：`eez-flow.*` **不得**出现（preflight `check_no_flow`）；★ `BUILD_TEMPLATES` 的 `#if EEZ_FOR_LVGL/#else` 两分支都得留 |
| [`watch-app-list-no-flow/`](watch-app-list-no-flow/) | **手表蜂窝缩放应用列表（SiFli `watch_v9/app_mainmenu.c` 移植件）**：EEZ 只出外壳（整屏宿主+标题+状态行），列表本体是 native C，零 Flow、零 eez-flow 产物 | ★ 屏是 **368×448**（不是 480×320 基线），EEZ/compat/SIM 三处对齐由 `preflight` 硬判；★ 穹顶曲线 `get_icon_transform_param` 在 SDK 里**只有预编译库**，本工程按 `mainmenu.py` 公式复算（不声称逐位一致）；★ `LV_HOR_RES` 在 9.4 是运行期表达式而原文件在 `#if` 里做算术 ⇒ 必须 `#undef` 换常量；★ 验收：`[LIST] init scale=119..275 center=clock` → 拖 (80,80) → `scale=34..275 center=activity` |
| [`watch-app-list-rxroller_no_flow/`](watch-app-list-rxroller_no_flow/) | **手表纵向滚轮应用列表（移植开源件 rxwind7/Rxroller，MIT）**：22 行"圆图标+中文名"，中心行最大、上下按距离渐变、快滑惯性+吸附、中心图标定在屏宽 42%（**渲染坐标**口径）、松手弹回第 n 个（行程放开）、主屏胶囊遮罩（EEZ 属性面出 radius+clip_corner，native 零改动）；EEZ 只出外壳，no-flow。★ 同级 `watch-app-list-rxroller_no_flow_2/` 是本工程的**逐字副本**（`diff -rq` 零差异），留给后续「更换 applist 图标」方案另起一轮，**不是误留的重复目录，别删** | ★ **`settings.general.circularDisplay` 不生成任何代码**（只在编辑器预览上加 CSS `border-radius`，app.asar 里 8 处命中全在 React 渲染层）⇒ 要做圆角必须用控件级 `radius` + `clip_corner`，只设 radius 不设 clip_corner 背景圆了但子对象照样糊到角外；★ 410×502 上 `LV_RADIUS_CIRCLE` 是**胶囊**不是正圆（半径钳到 205，上下各留 92px 直边），加圆角后贴直角上的标题/状态行会被整个裁掉，外壳落点要按 `d = R - sqrt(R²-h²)` 算 | ★ 上游标称 LVGL v8，编到 9.4 只需 12 处 `user_data` 访问器化 + 内存 API 别名（补丁可重放，preflight 逐字节比对产物）；★ 值得回报上游两条：缩放衰减窗口写死 1 个行距（只有中心行放大）、中心档写死 255 = 位图原尺寸（“中心想比原图还大”调不出来），两者已参数化；★ 全部观感参数收在单份 `src/native/watch_list_config.h`（图标/行距/缩放三档/曲线/吸附/惯性），`gen_assets.py`、`port_rxroller.py`、`preflight.py` 都从它读，改完不重跑就被门禁抓住、`inertia_divisor` 是死字段（只被兜底赋值、从不读取，配了没用）⇒ 惯性整套做在自家 `watch_list_native.c`；★ 缺陷史集中在 `FIXLOG.md`（25 条：现象/根因/修复/证据/防再犯），源码注释只留 `见 FIXLOG FX-###` 一行指路，且 preflight 会反查引用是否悬空；曾误判“上游漏初始化 `*x`”，核对原文后撤销补丁并留撤回条目；★ `lv_snapshot_take` 在这棵树上不返回 ⇒ 取证改读 `lv_display_get_buf_active`，且**不能**先调 `lv_refr_now`（带它取帧 200 s 内没出图）；★ 上游不做屏外回收，撑满宿主后必须自己隐藏远处行；★ **观感断言要量渲染坐标，不是布局坐标**——上游 CONTAINER 模式把 `transform_zoom` 打在整行上、轴心在行中点，图标偏左排布 ⇒ 放大后被拽离布局位置（150% 档实测偏 42px），`lv_obj_get_coords` 看不见这件事，断言会按「落在 1/3」绿着而用户看到的是 23%；★ 无头自证默认摘掉真鼠标（一次手滑就能把断言量歪）；★ **手势回调必须同时挂行和滚轮根对象**——屏外回收把远处行置 HIDDEN，LVGL 跳过隐藏对象，只挂行时按在"隐藏行/空白"上根对象收不到事件，快滑与松手弹回**静默失效**（用户报的"滑到最上面不返回"），行级 API 夹具测不到这条链路，必须留一套走真 indev 的 SDL 合成拖动夹具（注意上游 `SDL_MOUSEBUTTONDOWN` 读的是 `motion.x/y` 不是 `button.x/y`） |
| [`flow-examples/flow-variables-basics/`](flow-examples/flow-variables-basics/) | **Flow 变量的使用方法**（纯 EEZ、零 native C）：读（表达式 / 模板串 / Bar 单向）· 写（Slider 回写、`SetVariable` 单条与批量、`Evaluate`→数据线→`SetVariable`）· 监听（`Watch`）· 分支（`Switch`）· 作用域（全局 `g_*` vs 页面局部 `l_step`） | ★ 变量表只有一张，**两条轴**决定用法：`flowSupport` × 变量 `native`；关 Flow 时"只能全局且必须 native"；LVGL 的 `persistent`、（未开 Flow 时的）`defaultValue` 均禁用；★ Flow 件的 JSON `type` = Studio 类名（`SetVariableActionComponent`/`WatchVariableActionComponent`…）不能猜；★ `Watch` 的输出名是 `variable`（changed 只是显示名）；★ 数据线要配自定义输入名且与时序线成对；★ 负控验证 Checks 真校验标识符（写 `l_bogus` → 2 errors，改回 0 错） |
| [`flow-examples/flow-page-timeline-animation/`](flow-examples/flow-page-timeline-animation/) | **页面动画时间线 + `Animate` 件**：关键帧挂控件、游标在页面级；播放 / 跳帧(`speed=0`) / 倒放(`to<from`) / `seqout` 只在放完时发 / `pageTimelinePosition()` 读数 | ★ 关键帧 `opacity` 是 **0..1** 不是 0..255（写 70 会被夹成全不透明，且构建 0 错 0 警）；★ `rotate` 单位是 **0.1°**（填 45 只转 4.5°）；★ 命中第一个满足区间的帧就 `break` ⇒ 同区间不能拆两帧；★ `start==end` 是「At X s set」且对该时刻及其之后一直生效；★ 插值从创建初值重放到当前游标 ⇒ 倒放/跳帧可复现；★ 缓动名共 31 个，写错要到链接期才炸；★ 动画控件要排在 `children[]` 文字之前（z 序）；中文必挂字体条目，见 `flow-examples/README.md` 字体铁律 |

> 验证状态：**2026-10-19 那轮全量体检覆盖的是当时 9 个示例**（EEZ Studio 0.29 headless CLI
> 构建 0 错 0 警 + 产物清单对账，且 PC_SIM 编译链接 0 错）。**索引现有 19 行 / 磁盘 18 个示例目录**
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
- 同样的 CMakeLists 还认一个**可选**的 `SIM_BIN_DIR`：设了就把 exe 输出到那里，不设仍是
  老的 `PC_SIM\bin`。示例 bat 一律设成 `build_rel\bin` ⇒ **每个工程有自己的 exe**。
- 每个 EEZ 工程自带 `design/sim_cmake/` 三件套（**应用侧变动全部放在各工程内**）：

| 文件 | 作用 |
|---|---|
| `run_sim.bat` | 注入本工程绝对路径到 `SIM_TARGET_PROJ_DIR`、输出目录到 `SIM_BIN_DIR`，直接调 `setup_env.bat` + cmake；**build_rel 与 exe 都在本 bat 同目录**（每工程独立） |
| `main.c` | 仿真入口：`lv_init` + SDL 窗口/鼠标/滚轮/键盘 + `ui_init` 主循环 |
| `lv_conf.h` | 本工程专用仿真配置（经 `LV_CONF_PATH` 传入） |

### 4.2 用法

```
双击  <工程>\design\sim_cmake\run_sim.bat        → 编译并启动仿真器窗口
运行  run_sim.bat build                          → 只编译不启动
```

- 产物：`<工程>\design\sim_cmake\build_rel\bin\main.exe`（**每个工程一份**）。
  ⚠ 2026-10-23 之前是 `PC_SIM\bin\main.exe`，全仓库共用 —— 两个工程交替构建时后链的会覆盖，
  双击 A 却跑起 B（实测：本仓库示例与 `D:\temp_d\AI_Temporary_Reply\watch` 互相覆盖，
  打印的 rows/pitch 与自身 config 对不上）。现在不设 `SIM_BIN_DIR` 也不会再被本仓库的示例影响。
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

---

## 5. 子模块（`project-reference/`）

所有 git 子模块统一放 `project-reference/<仓库名>/`，父库只记录 commit 指针。

- 首次克隆：`git clone --recurse-submodules <url>`；已克隆的补拉 `git submodule update --init`。
- 更新子模块：`git submodule update --remote project-reference/<名>`，再在父库提交新指针。
- 当前：`watch2` → <https://github.com/w809291634/watch2.git>
