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
| [`widget-gallery/`](widget-gallery/) | 7 类常用控件（Button/Slider/Switch/Bar/Spinner/Checkbox/Panel）的正确 JSON 形态 | ★ widgetFlags 漏 `CHECKABLE` → 控件变装饰件（LVGL 9.4 `lv_obj.c` 硬条件） |
| [`font-entry-form/`](font-entry-form/) | 中文字体条目正确形态：`renderingEngine` + `lvglRanges` 数字表 + 相对路径 | ★ 决定性变量是条目形态不是字体文件；CLI 不烘字体 .c（P-0140） |
| [`two-state-styles/`](two-state-styles/) | DEFAULT/CHECKED 两态样式 + `checkedState` 初始态 + 子元素颜色继承 | ★ 两态都要写全（只写默认态被主题盖住）；toggle 按钮要显式加 CHECKABLE |
| [`gesture-page-switch/`](gesture-page-switch/) | 多独立 screen + GESTURE 离散切屏（3 页循环），不靠 CHECKED 高亮 | ★ Switch 的 `evt` 输入要 `type:'any'` 否则 Checks 空转；双线裸 `GESTURE` 防静默丢线；手势只能 PC_SIM/真机验收（P-0141） |
| [`one-way-gesture-switch/`](one-way-gesture-switch/) | **只允许单向手势**：仅接 LEFT（左滑循环 A→B→C→A），右滑根本不画组件/不连线 | ★ 单向 = 干脆不生成另一方向的 Switch/Action（别"画了不连"否则 Checks 报 not connected）；其余安全要点与双向版一致 |

> 验证状态（2026-10-19）：六个示例均通过 EEZ Studio 0.29 headless CLI 构建（0 错 0 警 +
> 产物清单对账）。手势运行时行为（gesture-page-switch / one-way-gesture-switch）按 P-0141
> 必须在 PC_SIM/真机验收，Run 预览不产生 GESTURE 事件。
> `font-entry-form` 的字体 .c 已落地：`src/ui/ui_font_cn14.c` / `ui_font_cn20.c`
> （黑体子集 159 字形，lv_font_conv bpp4 生成，仿真器链接通过）。
>
> **六个示例均另通过了 PC_SIM 仿真器一键编译验证（编译+链接 0 错，方法见第 4 节）。**

---

## 4. PC 仿真器一键编译（PC_SIM 适配）

**换工程 = 双击对应工程里的一个 bat**，`apl_lvgl_v9_4` 与 `PC_SIM` 两个公共目录不用改。

### 4.1 机制

- `PC_SIM/lv_port_pc_vscode_v9.5/CMakeLists.txt` 优先读环境变量 `SIM_TARGET_PROJ_DIR`
  定位目标工程（未注入时回退 eez-test，兼容旧用法）；
- 每个 EEZ 工程自带 `design/sim_cmake/` 三件套（**应用侧变动全部放在各工程内**）：

| 文件 | 作用 |
|---|---|
| `run_sim.bat` | 注入本工程绝对路径到 `SIM_TARGET_PROJ_DIR`，删 `build_rel` 强制重配置，再调 PC_SIM 的 `build.bat` |
| `main.c` | 仿真入口：`lv_init` + SDL 窗口/鼠标/滚轮/键盘 + `ui_init` 主循环 |
| `lv_conf.h` | 本工程专用仿真配置（经 `LV_CONF_PATH` 传入） |

### 4.2 用法

```
双击  <工程>\design\sim_cmake\run_sim.bat        → 编译（产物 PC_SIM\...\bin\main_rel.exe）
双击  <工程>\design\sim_cmake\run_sim.bat run    → 编译并运行（手势/点击在窗口里验）
```

首次编译全量编 LVGL 较慢（ccache 缓存加速）；之后换工程重跑即可。

### 4.3 关键坑（已解决，改回/新工程时注意）

1. **★ ThorVG 编不过**（`fatal error: config.h`）：全树缺 thorvg 的 `config.h`。
   各工程 `lv_conf.h` 已关 `LV_USE_VECTOR_GRAPHIC`/`LV_USE_THORVG_*`/`LV_USE_LOTTIE`；
   CMakeLists 另有屏蔽 thorvg 源码的兜底。新工程拷 `lv_conf.h` 时别把这些改回 1。
2. **★ SDL 入口**：`main.c` **不要**定义 `SDL_MAIN_HANDLED`（PC_SIM 链 `SDL2main`，
   它的 `main` 转调 `SDL_main`，定义了反而报 undefined reference to SDL_main）。
3. **run_sim.bat 必须 ASCII**：bat 里写中文注释会被 GBK 控制台搞坏字节导致 set 失效；
   括号块内的 echo 文本不能含 `)`（会被当成块结束括号，报"此时不应有 …"且退出码 255）。
4. **切换工程靠重配置**：PC_SIM 的 CMakeLists 内容不变时 cmake 不会重配置，会一直编旧工程，
   所以 run_sim.bat 删 `build_rel` 强制重配置——代价是每次全量重编（ccache 已大幅缓解）。
5. **首次全量编译偶发 ninja 依赖文件目录竞态**（个别 LVGL 文件报
   `opening dependency file ...: No such file or directory`）：重跑一次 run_sim.bat 即过。
6. **路径层级**：`SIM_TARGET_PROJ_DIR` 必须是**工程根**（CMakeLists 往后拼
   `/design/sim_cmake/...`、`/src/ui`），run_sim.bat 里已从 `%~dp0` 上跳两级，别改。
7. **中文字体**：EEZ CLI 不烘字体 .c，需 lv_font_conv 离线生成
   （`--format lvgl --lv-font-name ui_font_cnXX`，字形表取自 TTF 子集 cmap），产物落 `src/ui/`。
