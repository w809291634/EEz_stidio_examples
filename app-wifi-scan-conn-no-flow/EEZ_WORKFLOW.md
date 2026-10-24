# EEZ 一次性做对的流程

> 目标：**一轮做完，不靠反复试**。所有步骤都有判据；判据不过不许进下一步。
> 依据：本地经验库 `EEZ Studio_ui_debug_kit`（P-0005/0009/0013/0020/0033、P-0163/0164 的 15+ 坑）。

---

## 0. 前提：谁是真源

| 东西 | 真源 | 规则 |
|---|---|---|
| 界面/控件/变量/动作 | `build_example.py` | 只改它；GUI 手改会被下次生成覆盖 |
| `.eez-project` | 生成产物 | 不手改；要改就改生成器 |
| `src/ui/**` | EEZ 生成 | **禁止手改**（下次构建即丢） |
| 设计图 | `design/mockup_gen.py` | 改常量重生成，不手改 SVG |
| 设计位置 | `design/check_spec.json` | 与设计图共用同一套坐标常量 |

**Python 用 managed 解释器**（Pillow / fontTools 只装在这里）：

```bat
set PY=C:\Users\yjt54\.workbuddy\binaries\python\envs\default\Scripts\python.exe
```

---

## 1. 生成源码：顺序是硬约束

```bat
%PY% build_example.py          :: 1 生成 .eez-project
%PY% design\cli_build.py       :: 2 EEZ CLI 构建 + flow 守卫（必须退出码 0）
%PY% design\audit_chars.py     :: 3 文案字符 ⊆ 字体字符集
%PY% design\check_project.py   :: 4 静态自检 7 项（模板工程需从 app-wifi-connect 拷）
%PY% design\gen_font.py        :: 5 烘字库（必须在 cli_build 之后！）
```

或一键：`%PY% design\preflight.py --with-sim`（任一步失败立即停，并校验产物文件）。

**为什么顺序不能换**

| 顺序错误 | 后果 |
|---|---|
| `gen_font` 放在 `cli_build` 之前 | CLI 的孤儿清理会把字体 `.c` 删掉 → `undefined reference to ui_font_cn14`（坑 7） |
| 新建 native 文件后不删 `build_rel` | CMake GLOB 不重扫 → `lv_conf.h not found` / 新文件不参与编译（坑 8） |
| EEZ Studio 还开着就构建 | 单实例锁 → 构建 TIMEOUT（坑 9） |

**"成功"的三个假象（都必须挡）**

| 假象 | 真相 | 怎么挡 |
|---|---|---|
| `Build successfully finished` | 可能一个文件都没产出（`settings.build.files` 被删，P-0005） | `preflight.py` 校验 `screens.c/ui.c/vars.h/actions.h/structs.h` 存在且 >200B |
| `No error and no warning detected` | flow 检查错误**非致命**，坏表达式照样进产物（坑 5） | `cli_build.py` 抓 `N errors`，N>0 判 `FLOW_ERRORS` |
| 日志里一堆红字 | 可能是 Chromium 噪音（P-0010/0016） | 只认 `BUILD RESULT:` 行与 `N errors` |

---

## 2. 语法错误防火墙

### 2.1 生成器（Python→JSON）层 —— 这里错，EEZ 打开就报错

| 错法 | 症状 | 正确写法 |
|---|---|---|
| 颜色写成 `0x2a3044`（没引号） | EEZ 报 `invalid color`；**CLI 不报**（P-0009） | `"0x2A3044"` 字符串 |
| 隐藏用 `hiddenExpr` | 静默无效，面板盖住全屏吃点击（坑 1） | `hiddenFlag` + `hiddenFlagType:"expression"`（true=隐藏） |
| 表达式少一个右括号 | 引用检查报 `is neither input or local or global variable`（坑 5） | 生成后 grep 一次表达式括号平衡 |
| label 缺 `width` 字段 | 发 `set_size(NaN,NaN)` 或 `(0,h)` → 文字叠成竖条 | `widthUnit:"content"`（坑 20） |
| 自创控件结构 | 画布/真机行为分裂 | 照抄 EEZ 新建控件的默认 JSON（11 号文档 §6） |
| 动作只在 `actions[]` 里加了名字 | 链接 `undefined reference to action_xxx`（坑 17） | 同步在 `app/wifi_events.cpp` 实现，一个不能少 |
| Textarea 绑 `text` 表达式 | 打字被每拍 tick 覆盖（坑 6） | 动作里 `lv_textarea_get_text(objects.xxx)` 现读 |

### 2.2 C / 头文件层

| 错法 | 症状 | 正确写法 |
|---|---|---|
| 注释里出现 `xxx_*/yyy` | `extended character is not valid in an identifier` 一串错（坑 10） | 注释里避免 `*/` 序列 |
| 头文件漏 `extern "C"` | C 侧 `undefined reference`（C/C++ 互操作，曾见于 `get_var_*`） | 声明全部包 `extern "C" { }` |
| 平台层调 `lv_tick_get()` | 平台层离不开 LVGL，不可移植（坑 12） | 平台层用 `clock()` / 自己的 tick |
| `printf("...\n")` 经 heredoc 写入 | 变成真换行，编译错 | 用 Write 工具写补丁脚本，别用 shell heredoc 传 `\n` |
| 调试 `exit(0)` 忘了守卫 | "一点就退出"（坑 13） | `if (getenv("WIFI_AUTOEXIT")) exit(0);` |

### 2.3 工具链层

| 现象 | 首疑 | 处置 |
|---|---|---|
| 编译 rc=1，**零输出** | gcc 不在 PATH（P-0013） | 把 mingw `bin` 加进 PATH 再跑 |
| 链接缺 native 符号 | native 符号未定义 / 库顺序（P-0020，曾见于 `get_var_*`；v4 收口后 EEZ 无 native 变量） | 查符号定义 + `extern "C"` |
| CLI 挂住不返回 | EEZ 残留进程（坑 9） | `taskkill /F /IM "EEZ Studio.exe"` |

---

## 3. 本地 15 坑速查（照 P-0164 分类）

| 类 | 坑 | 一句话正解 |
|---|---|---|
| A1 | `hiddenExpr` 无效 | 键名是 `hiddenFlag` |
| A2 | 字体条目四要点缺失 | `renderingEngine/lvglRanges/lvglGlyphs/glyphs[]` 一个不能少 |
| A3 | 字符集含字体里没有的字 | fontTools 读 cmap 求交集 |
| A4 | 字符集漏 ASCII | 必须并 `0x20-0x7E`（否则画布拉丁全豆腐，仿真却正常） |
| A5 | flow 错误非致命 | CLI 守卫抓 `N errors` |
| A6 | Textarea text 是单向 input | 动作里读控件，别绑表达式 |
| B7 | CLI 不烘字体且会孤儿清理 | `gen_font` 放最后 |
| B8 | GLOB 不重扫 | 删 `build_rel`（及 `_rw`）重配 |
| B9 | EEZ 单实例锁 | 构建前 taskkill |
| C10 | 注释 `*/` 提前闭合 | 注释里别写 `xxx_*/` |
| C11 | 漏 `extern "C"` | 头文件全包 |
| C12 | 平台层依赖 LVGL | 用 `clock()` |
| D13 | 调试 exit 残留 | env 守卫 |
| D14 | 碎片化 replace 改同一函数 | 整段读-改-写 |
| D15 | mingw wlanapi 四件套 | 照抄已验证的 `io_win.cpp` |

**追加 5 坑（本轮）**：键盘构造自带 `BOTTOM_MID`（要 `align(TOP_LEFT)` 清）；`lv_obj_get_x` 是**父相对**坐标；label 文字从**盒顶**绘制（垂直居中靠收缩高度）；`widthUnit:"content"` 必填；EEZ 画布是**真实 LVGL wasm**，"画布不渲染某样式"这种结论要先怀疑字体/资源。

---

## 4. 怎么用 EEZ 核对 UI（三层，别混用）

| 层 | 看什么 | 可信度 | 盲区 |
|---|---|---|---|
| ① Studio 画布 / Run | 布局、层级、点击区域、绑定是否报错 | 高（wasm 跑的是真 LVGL） | 字体/资源没配好时文字异常；**headless 不查结构合法性**（P-0033：Tab 位置非法只在 GUI 报） |
| ② PC_SIM 运行 | 真实交互、键盘、动效、状态切换 | 权威 | 需要编译；截图靠程序内 `lv_snapshot` |
| ③ 像素测量 | 坐标/对齐/字号是否与设计一致 | 客观 | 需要一份设计坐标（spec） |

**顺序**：① 看结构与绑定（抓 GUI 报错）→ ② 跑流程（抓行为）→ ③ 量像素（抓"看起来差一点"）。

> 注意：EEZ 画布报的错**必须清零**再构建——headless 会放过结构错误（P-0033），
> 到真机才炸。

---

## 5. 截图与设计图对照 SOP

### 5.1 截图必须用程序内快照（不要系统截图）

系统截图抓不到 GPU 帧，且不可复现。用 LVGL 自己的快照：

```c
#include "src/others/snapshot/lv_snapshot.h"

static void take_shot(const char *path)
{
    lv_draw_buf_t *buf = lv_snapshot_take(lv_screen_active(), LV_COLOR_FORMAT_XRGB8888);
    if (!buf) { printf("[SHOT] failed\n"); return; }
    /* 写 32 位 BMP：宽/高/stride 从 buf->header 取，行序 -h（自顶向下） */
    ...
}
/* 触发：状态到位 + env 守卫 */
if (getenv("WIFI_SHOT")) take_shot("shot_fake.bmp");
```

- 通道顺序：`XRGB8888` 在内存里是 **B,G,R,X**；BMP 写出后若颜色反了（深蓝变棕），
  用 `ui_check.py --swap-rb` 纠正（P-0008）。
- 截图时机要固定（例如"连接成功后第 1 帧"），否则每次对比都在比不同状态。

### 5.2 对照（一条命令）

```bat
%PY% design\ui_check.py ^
  --shot design\sim_cmake\shot_fake.bmp ^
  --spec design\check_spec.json ^
  --design design\mockups\mockup_01_list.svg
```

产出 `design/check/`：`shot.png`、`overlay.png`（绿框=设计位置、红线=设计中心、黄点=实测中心）、
`report.html`（**设计 SVG ｜ 截图 ｜ 叠加图** 三栏并排 + 偏差表，浏览器直接打开）。

### 5.3 判读规则

| 现象 | 结论 |
|---|---|
| Δx/Δy 在 ±4px 内 | PASS（1px 属渲染舍入） |
| 整块元素**同方向**偏 20–40px | 九成是**坐标空间搞错**（父相对 vs 屏幕），不是设计错 |
| 文字整体贴顶 | label 定高 > 文字高（垂直居中没做，坑 19） |
| 颜色整体反相 | 快照通道顺序（P-0008），不是主题配错 |
| 文字是方块 | 字体字符集/条目（A2–A4），先修字体再谈对齐 |

> 每次改完**同一套方法复测**：改布局 → 重跑 5.1–5.3，不要换判据。

### 5.4 逐屏对照交付图（一条命令）

```bat
%PY% design\shot_states.py          :: 逐状态出图 -> build\sim_shots\*.png
%PY% design\compare_shots.py        :: 设计图 vs 仿真 并排 -> build\sim_shots\step5_compare.svg
```

状态开关在 `design/sim_cmake/main.c` 的无头钩子里（`WIFI_SHOT_AT=idle|scanning|done`、
`WIFI_FAKE_STATE=empty`、`WIFI_KBPROBE=1`）；两个模态由 `WIFI_REACH=sheet|dialog`
**用注入鼠标真实点击/长按列表行**到达（⑦-1 接线后不再翻 hiddenFlag）。

导航闭环另有断言集：`WIFI_NAVTEST=1 main.exe` → `[NAV] RESULT: PASS n / FAIL m`，
FAIL 反映到退出码；反向测试见 `tmp/_negtest_nav.py`（掐掉长按通路 → rc=1）。
`design/preflight.py --with-sim` 现在**自带这套断言**（编译完就跑，红就停）。

验证默认**不开桌面窗口**：脚本给子进程设 `SDL_VIDEODRIVER=dummy`（实测六屏出图与有窗口
逐字节一致，事件链同一条）。要肉眼看窗口：`SHOT_STATES_WINDOWED=windows`。

注入夹具的五个实测坑（都踩过，别再猜）：
1. 启动后约 300 帧（≈600ms LVGL 时间）之前压进 SDL 队列的鼠标事件不会被消费；
2. SDL indev 是 `LV_INDEV_MODE_EVENT`，**没有新事件就不会 read**，待派发的 CLICKED
   会挂到下一次点击——抬起后补一次同坐标 MOUSEMOTION 喂读（按住时喂会被判成拖动，
   CLICKED 反而被吃掉）；
3. `pump()` 每帧只把 `lv_tick` 推 2ms，所以"长按 400ms"要按**帧数**换算（260 帧），
   按真实毫秒估会短一截、长按判不出来；
4. 行是 native 刚 `clean+add` 出来的，取点击坐标前必须 `lv_obj_update_layout(list)`，
   否则 `lv_obj_get_coords` 给的是布局前旧值——实测中心算到标题区，整笔点击落空，
   表现成"1/5~1/8 概率第一条断言假失败"；
5. `setvbuf(stdout, NULL, _IONBF, 0)` 必须是**本进程第一次 I/O**：LVGL 已经写过 stdout
   之后再调是未定义行为，管道场景下会把整条输出流打断。

### 5.5 ⑤ 核对结论（2026-10-23 本轮）

已核对 5 屏（列表主态 / 扫描中 / 空态 / 连接半页 / 忘记对话框），逐屏对照见
`build/sim_shots/step5_compare.svg`。抓到的差异按归属分三档：

| 档 | 差异 | 归口 |
|---|---|---|
| 本轮已修 | 行内分隔符「·」烘成豆腐：Python `gb2312` 把 0xA1A4 解成 U+30FB（simhei 没有），CP936 才是 U+00B7；`audit_chars.py` 原来只扫 EEZ 工程不扫 native 文案 | 字符集 + 门禁（已反向测试） |
| ④ 未做全（native 画行缺元素） | 行内**锁图标**、状态**胶囊（圆点+描边）**、**分组标题**（已连接·已保存 / 可用网络）、已连接行**绿色描边**、空态**WiFi 图标 + 重新扫描按钮**、底部**长按提示**、扫描中**骨架行**、状态文案与设计不一致（「正在扫描…」vs「正在扫描附近网络…」） | ④ 补全（不是 ⑦：这些是预生成界面内容） |
| 待用户裁决 | 对话框「取 消」与卡片同色＝隐形；`FAIL`/`FAIL_BG`/`TEXT3` 令牌设计图与出码两套值 | 配色对账（见上轮汇报） |

### 5.6 ⑦-1 导航闭环（2026-10-23 已交付）

点带锁行 → 半页；× / 遮罩空白 → 关；长按已保存行 → 忘记对话框；取消 / 忘记 → 关。
`[NAV] RESULT: PASS 17 / FAIL 0`，反向测试（掐掉长按通路）rc=1 且点名两条 FAIL。

两条实现口径（都写进代码注释，别再改回去）：

- **LVGL 长按抬手后仍会补发一次 `CLICKED`**（`lv_indev.c:1046` 只对 short_click 判
  `long_pr_sent`），不吞掉它，长按就是"先开对话框、再被补发的 CLICKED 换成半页"。
  吞法：`LONG_PRESSED` 记下本次手势的行，`CLICKED` 见到同一行就丢弃并清标记，
  `PRESSED` 一律清零（防止标记泄漏到下一次点击）。
- 打开走 native（行是 native 建的，EEZ 侧没有可挂的控件）；**关闭走 EEZ 生成的 action**
  （× / 遮罩 / 取消按钮 → `APP_OUT_*` → `user_io_tick` 排空时回调 close）。
  所以 EEZ 工程里那两个模态容器的 `hiddenFlag` 仍是 `True`，[④A] 门禁继续断言。

---

## 6. 一次性完成：Gate 表（全绿才交付）

| Gate | 命令 | 通过判据 |
|---|---|---|
| G0 设计定稿 | — | 设计图/`check_spec.json`/令牌三者坐标一致 |
| G1 生成 | `%PY% build_example.py` | 生成时间更新、JSON 可被 `json.load` 解析 |
| G2 构建 | `%PY% design\cli_build.py` | 退出码 0 且 `BUILD RESULT: ok` |
| G3 产物 | `preflight.py` 的产物检查 | 5 个核心文件存在且非空（P-0005） |
| G4 静态 | `audit_chars.py` + `check_project.py` | 全 OK；字符集 ⊆ cmap |
| G5 字库 | `gen_font.py` | 生成 `src/ui/fonts/ui_font_*.c` |
| G6 运行 | `run_sim.bat build` + 跑 | 编译 succeeded；关键日志断言通过 |
| G7 视觉 | `ui_check.py` | 所有元素 ±4px；`report.html` 目检无差异 |
| G8 GUI 结构 | EEZ Studio 打开工程 | **错误面板为空**（P-0033：headless 查不到） |

---

## 7. 失败 → 第一个该怀疑谁

| 症状 | 首疑 | 而不是 |
|---|---|---|
| 点控件没反应 | 容器是否 `CLICKABLE`（装饰容器不响应，P-0004）；是否被覆盖层吃掉点击 | 事件没绑 |
| 控件整体偏移 | 嵌套容器坐标二次偏移 / 父相对坐标（P-0007、坑 16） | 设计坐标写错 |
| 文字豆腐 | 字体条目/字符集（A2–A4） | 对齐样式 |
| 画布正常、仿真异常 | 字库没烘（B7）/ 产物没更新（G3） | "EEZ 有 bug" |
| 仿真正常、画布异常 | 画布缺字体/资源，不是渲染引擎不支持 | 样式写法 |
| 出码几何对账全绿、仿真里控件却错位/塌高 | 控件构造函数改写 align/height（kit cases **B16**：`lv_keyboard` 写死 BOTTOM_MID、`oneLineMode` 强改 LV_SIZE_CONTENT）。用 `WIFI_KBPROBE=1` 跑 main.exe 量绝对坐标 | "这个尺寸装不下" |

---

## 8. 交付物清单

- `design/preflight.py`：一键预检（生成→构建→产物→静态→字库→可选编译）
- `design/ui_check.py`：截图 vs 设计图对照 + 像素校验 + HTML 报告
- `design/check_spec.example.json`：测量规格模板（复制成 `check_spec.json` 再填）
- 本文件：顺序、语法防火墙、15 坑、三层核对、Gate 表
