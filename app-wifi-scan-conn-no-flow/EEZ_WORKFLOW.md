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

### 5.6 ⑦-1 导航闭环（2026-10-23 交付 · 点击口径已被 §5.7 取代）

单击开半页 / × 与遮罩关 / 长按开忘记对话框 / 取消与忘记关——通路先打通。
`[NAV] RESULT: PASS 17 / FAIL 0`，反向测试（掐掉长按通路）rc=1 且点名两条 FAIL。

两条实现口径（都写进代码注释，别再改回去）：

- **LVGL 长按抬手后仍会补发一次 `CLICKED`**（`lv_indev.c:1046` 只对 short_click 判
  `long_pr_sent`），不吞掉它，长按就是"先开对话框、再被补发的 CLICKED 换成半页"。
  吞法：`LONG_PRESSED` 记下本次手势的行，`CLICKED` 见到同一行就丢弃并清标记，
  `PRESSED` 一律清零（防止标记泄漏到下一次点击）。
- 打开走 native（行是 native 建的，EEZ 侧没有可挂的控件）；**关闭走 EEZ 生成的 action**
  （× / 遮罩 / 取消按钮 → `APP_OUT_*` → `user_io_tick` 排空时回调 close）。
  所以 EEZ 工程里那两个模态容器的 `hiddenFlag` 仍是 `True`，[④A] 门禁继续断言。

### 5.7 ⑦-2a 点击口径修正 + 状态真的落地（2026-10-24 本轮）

现口径（用户 2026-10-24 定，与 `wifi_list.cpp:row_event_cb` 注释同源）：

| 手势 | 目标行 | 结果 |
|---|---|---|
| 单击 | 已连接 | 不动作（不重复操作） |
| 单击 | 有锁且**没存过**密码 | 开半页要密码 |
| 单击 | 已保存 / 开放网络 | **直连**，不弹半页 |
| 长按 | 已保存 | 开「忘记此网络」对话框 |
| 对话框 | 忘记 / 取消 | 忘记＝清 `saved`（之后同一条重新要密码）；取消＝只关窗不改状态 |
| 半页「连接」 | 密码为空（纯空格也算空） | **不发起连接、不转圈、半页不收**，标题栏提示「请输入密码」 |
| 长按对话框 | 断开 | 只断开**这条若是当前连接**；不是当前连接就只提示「未连接 X」（`WlanDisconnect` 是整口断，不认 SSID） |

后端（PC 假世界）负责状态：`io_wifi_connect()` 清掉别人的 `connected`、置目标为唯一已连接，
有锁且给了密码才置 `saved`；`io_wifi_forget()` 只清 `saved`（对齐 Windows 删 profile 不断连）。
两者都走 `resort_and_publish()`：重排 + `s_gen++`，UI 才会重画。

证据：`[NAV] RESULT: PASS 30 / FAIL 0`（连跑 3 次一致），全部是注入 SDL 鼠标的真点击。

本轮抓到两个真 bug，都已反向测试：

1. **重排后读悬垂指针**——`io_wifi_connect` 拿到的是 `&s_aps[i]`，而 `resort_and_publish()`
   里 `qsort` 会把整个数组搬家；文案/日志在重排**之后**读 `ap->ssid`，就会写成
   "已连接 <另一个网络>"。修法：重排前把 SSID 与 `saved` 抄进局部变量。
   反向测试（改回 `ap->ssid`）→ `[NAV] FAIL 状态文案点名「已连接 <这条 SSID>」`，rc=1。
2. **状态文案上不了屏**——`wifi_view_sync()` 原来只在 `APP_IN_SCAN_STATE` 变化时回显标题，
   而连接/忘记之后 state 恒为 2，标题就永远停在「已发现 12 个网络」。
   修法：文案也单独比（新增 `s_last_status`）。
   反向测试（退回只比 state）→ `[NAV] FAIL 标题 label 上真的写着这句（渲染层）`，rc=1。

断言口径为此收紧两条：状态文案必须**点名到目标 SSID**（只查"已连接"三个字会放过串台），
且标题要量 `lv_label_get_text`（渲染层）——model 槽改了不等于界面改了。
用例里的目标行一律按 SSID 认（`row_of_ssid`），因为连接/忘记都会重排，缓存行号必错。

### 5.8 ⑦-2 PC 真接口（wlanapi，2026-10-24 已交付）

口径（用户 2026-10-24 定）：扫描 / 连接 / 忘记**全走真接口**。
本轮交付时真接口要靠 `WIFI_PC_REAL=1` 才开，**下一轮（§5.9）已把默认翻向真接口**，
门禁与出图改成**主动设** `WIFI_PC_FAKE=1` 才回到假世界——保护的方向跟着反了，
但同一件事不变：**门禁环境里"走哪个后端"必须被显式写死并打印出来**
（不写死，跑分就是一次真连真删，断言再也不可以复现）。

落点：`platform/pc/wifi_platform_win.cpp`（wlanapi 实现）+ `wifi_platform_pc.cpp` 降级成分发器。
真接口全是异步的：`WlanScan` 后 2s 回查、`WlanConnect` 后 5s 回查，
**结论只看系统真值**——回查里目标 `connected` 才写「已连接 X」，否则写「连接失败 X」。

四条口径（都写进代码注释，别再改回去）：

- mingw 的 `wlanapi.h` 把 profile 名与 profile XML 都声明成**宽字符**（`LPCWSTR`），
  照 MSDN 上看着像 ANSI 的签名直接传 UTF-8 会静默失配；本层统一 UTF-8 ↔ UTF-16。
- 中文 SSID 优先用 Windows 已解码的 `strProfileName`，没 profile 的才按 AP 原样字节当 UTF-8 显示。
- 写进 profile XML 的 SSID 与密码必须做 XML 转义（`& < "` 会写坏整份 profile）。
- WPA3-SAE 在这个 API 里仍报成 RSNA，界面按 WPA2 显示（Windows 自己也这么报），日志留原始值。

链接方式：`run_sim.bat` 传 `-DCMAKE_CXX_STANDARD_LIBRARIES=-lwlanapi`，**共享的 PC_SIM 脚本一行没改**。
不能用 `CMAKE_EXE_LINKER_FLAGS`——它落在目标文件**之前**，GNU ld 从左往右解析，wlanapi 符号会报未定义。

证据（真机，不是假表）：真扫描出真网络列表（`build/sim_shots/real_scan.png`，隐藏网络不列的口径见 §5.10）；
`WIFI_AUTOSCAN=1 WIFI_REACH=connect` 注入点击 →
`[WIN] WlanConnect 已下发：YJT-1号楼办公` → 系统侧独立回读
`netsh wlan show interfaces` 给 `状态: 已连接 / SSID: YJT-1号楼办公 / 通道 36`，
界面同步出「已连接」胶囊与标题文案（`build/sim_shots/real_connect.png`）。
假世界门禁回归 `[NAV] PASS 30 / FAIL 0`、`preflight` 全绿。

未做：真「忘记」没在你机器上试（`WlanDeleteProfile` 会真删系统里存的密码，要你点名才跑）。

### 5.9 ⑦-2b 连接三态 + 真接口改成默认（2026-10-24 交付 · 连接中交互已被 §5.10 取代）

用户报的两件事是同一个根因链：「点另一个已保存的 WiFi，硬件没切换，也没看到连接中提示」。

1. **默认后端翻向**（用户定）：双击 `run_sim.bat` 就是**真接口**；假世界改成 `WIFI_PC_FAKE=1` 才走。
   方向一反，门禁的保护也跟着反：`check_nav()` 与 `shot_states.py` 现在**主动设**
   `WIFI_PC_FAKE=1`（而不是只 pop 掉一个开关），并打印
   `OK 门禁已强制假世界（WIFI_PC_FAKE=1），真接口不会被触发`。
   不设的话，一次跑分就是一次真连网 + 真删密码，且"附近有哪些网"每次都变。
2. **三态走契约，不靠猜**：新增 `APP_IN_CONN_STATE`（0 空闲 / 1 连接中 / 2 成功 / 3 失败），
   后端负责写、`wifi_logic` 负责消费——**半页在"连接中"保持前台，收到 2 才自动关**
   （设计 `mockup_06` 的口径），收到 3 不关窗（本轮定的最小方案：失败只改标题栏文案，
   不补半页内红字控件）。假后端与真后端**同一套时序口径**，所以这条通路在门禁里可验。
3. 真接口是每秒回查（`CONNECT_POLL_MS=1000`，15s 判失败），不再"5 秒后才看一眼"；
   假后端用 `CONNECT_SEC=1.2` 演出同一段"正在连接"。

证据：`[NAV] RESULT: PASS 40 / FAIL 0`（新增 10 条，含"点下先看到正在连接""连接中半页仍在前台"
"成功才自动关"）。两条反向测试各自 rc=1：把 logic 退回"一点就关窗"→ 抓到 1 条；
把假后端退回同步完成 → 抓到 3 条。

真机复现与副作用（必须记下来）：不设任何变量跑 `WIFI_REACH=connect` →
`[IO] io_init (pc REAL wlanapi)`、`[REACH] 点下之后标题=正在连接 yjt_dev_2.4G…`、
15s 后 `[REACH] ... 文案=连接失败 yjt_dev_2.4G`，`netsh` 独立回读 `状态: 关联 → 已断开连接`。
**换网失败会连原来连着的网一起掉**（`WlanConnect` 先断后连，这是 Windows 的行为不是本层缺陷），
测试后已用 `netsh wlan connect name="1号楼6层WiFi"` 恢复。
`yjt_dev_2.4G` 这条在本机存着 profile 但连不上（大概率密码已失效），界面上会看到它报"连接失败"。

### 5.10 ⑦-2c 连接中改成全屏转圈（2026-10-24 本轮）

用户口径（推翻 §5.9 的"半页留作连接中背景"）：**点「连接」→ 半页收起 → 全屏圆圈动画 → 期间不可操作**。

- 新控件在 `widgets/wifi_busy/`（懒建的整屏遮罩 + `lv_spinner` + 一行文案）。
  它是运行时的过程态，EEZ 侧没有控件、也不持有变量，所以按"动态内容可原生"的口径放在 widgets 层。
- **锁操作只靠一件事**：遮罩是整屏 `LV_OBJ_FLAG_CLICKABLE` 的子对象且建在最后面，
  LVGL 的 hit test 停在这层，下面的列表/半页/对话框一律收不到事件——不去逐个禁用控件。
- `wifi_logic`：发完连接命令就 `wifi_nav_close_sheet()` + `wifi_busy_show("正在连接 X…")`；
  `APP_IN_CONN_STATE` 变 2/3 时 `wifi_busy_hide()`。真接口回查改成 0.5s 一次、10s 判失败（原来 1s/15s）。

本轮抓到的三个问题：

1. **遮罩其实是 0×0**：`lv_obj_remove_style_all()` 会把 local style 一起删掉，而 `width/height`
   就是 local style——先 `set_size` 再 `remove_style_all`，尺寸就被清没了，点击全部穿透。
   修法是把 `remove_style_all` 放到最前。反向测试（退回原顺序）→
   `[NAV] FAIL 转圈期间点带锁行不生效（输入被锁住）` 等 8 条、rc=1。
2. **隐藏网络画成空白行**：`WlanGetAvailableNetworkList` 对隐藏网给的 `dot11Ssid` 是全零字节，
   列表里就多出一行没有名字的条目（用户截图里第一行）。修法：显示名为空就不收进列表。
   真扫描从 8 条变 7 条，空白行消失（`build/sim_shots/real_scan.png`）。
3. **"总是连接失败"不是本层缺陷**：系统日志 `Microsoft-Windows-WLAN-AutoConfig` 给的是
   `Id 8002 失败原因: 特定的网络不可用，RSSI: 255`；脱离仿真器用
   `netsh wlan connect name="YJT-1号楼办公"` 单连一次得到**同一个错误**，
   而 profile 里密钥确实存在（`netsh wlan show profile ... key=clear`）。
   → 判据：连接失败先分"系统也连不上"还是"我们没下发成功"，别先改代码。
   顺带发现期间有 profile 被删过（`1号楼6层WiFi`、`yjt_dev` 已不在 `show profiles` 里），
   所以"已保存"胶囊与系统真实状态可能不一致——刷新一次即重扫真值。

4. **「已保存」判错了**：原来用可用网络条目的 `AWN_HAS_PROFILE` 位判，真机上会漏报——
   profile 明明在（`netsh wlan show profiles` 有），整张表却一条 `saved=1` 都没有。
   后果不是"显示错"这么轻：点已保存的网络会被当成"没存过密码"**弹半页**，
   用户输一次错的就把好 profile 覆盖了，之后越连越失败。
   修法：`WlanGetProfileList()` 一次取 profile 库，按名字匹配 SSID 判 `saved`，
   条目标志位只作兜底。修完 `[WIN] #3 "YJT-1号楼办公" ... saved=1`，点它直接连、不再弹半页。
   排查入口：`WIFI_WIN_DUMP=1` 会把每一行连 profile 名一起打出来。

证据：`[NAV] RESULT: PASS 44 / FAIL 0`（新增转圈可见、期间点击不生效、结果后收起等 4 条）、
`preflight` 全绿；连接中那一屏出图 `build/sim_shots/busy.png`；
六屏既有态 SHA1 与改动前**逐字节一致**（遮罩默认隐藏不影响既有截图）。

### 5.11 ⑦-2d 把失败原因显示出来（2026-10-24 本轮）

用户口径（选 2）：失败别只说「连接失败 X」，把 Windows 给的原因一起写进标题栏。

做法：`WlanRegisterNotification(WLAN_NOTIFICATION_SOURCE_ACM)` 订阅通知，
收到 `connection_attempt_fail / connection_complete / disconnected` 时用
`WlanReasonCodeToString()` 把原因码翻成系统文案，拼成
**「连接失败 X（特定的网络不可用）」**；翻不出文案就退化成「错误码 N」。
顺带一个收益：服务 2 秒内就判失败时，立刻收圈报错，不再干等 10 秒超时。

三个坑（都写进代码注释）：

1. **`sizeof(WLAN_CONNECTION_NOTIFICATION_DATA)` 比实际 payload 大**——结构体尾部是
   `strProfileXml[1]` 的变长尾巴，实测通知 `dwDataSize=572`，用 sizeof 判"太短"会把
   **所有**通知丢掉（第一版就是这样，日志里一条 notify 都没有）。判据改用
   `offsetof(..., strProfileXml)`。
2. **通知里的 `dot11Ssid` 不是空口字节**：同一条中文 SSID，空口 17 字节（UTF-8），
   通知里只有 13 字节（ANSI 码页）。拿原始字节比对永远不相等 → 改成按
   **profile 名（宽字符）** 认领本次尝试。
3. 系统文案自带句号，「（特定的网络不可用。）」很难看 → 拼之前去掉尾部标点/空白。

证据（真机）：点 `YJT-1号楼办公` →
`[WIN] notify code=10 reason=163851 "特定的网络不可用"` →
标题栏 `连接失败 YJT-1号楼办公（特定的网络不可用）`，全程 4.6 秒结束（含 2s 扫描），
出图 `build/sim_shots/real_fail_reason.png`。假世界没有失败分支，所以这条文案
只在真机验过；门禁仍是 `[NAV] PASS 44 / FAIL 0`。

排查开关：`WIFI_WIN_DUMP=1` 会打印每个通知（src/code/size + 解析出的 ssidlen/reason/profile）。

同轮补的口径（用户 2026-10-24）：**半页路径密码不能空**。守卫放在 `wifi_logic` 消费命令的那一处，用 `wifi_nav_sheet_open()` 区分上下文——半页开着就必须有可见字符，否则不发起、不转圈、不关窗，标题写「请输入密码」；直连路径（已保存/开放网络）本来就没密码可输，照旧。证据：`[NAV] PASS 47 / FAIL 0`（新增 3 条：半页不收 / 不转圈 / 有提示），反向测试（去掉守卫）rc=1 且这三条全红。

### 5.12 ⑦-2e「总是连接失败」的真正根因：profile 的 SSID 存成了 GBK

先说结论：**`WlanSetProfile` 的 XML 只写 `<name>` 时，Windows 会把这个名字按
ANSI(GBK) 码页存成 profile 的 SSID 字节**。中文 SSID 于是与空口广播的 UTF-8 字节对不上，
之后每次连接都在 2 秒内报「特定的网络不可用 / 无可见连接接入点」，`RSSI 255`——
而我们自己的 `netsh`/事件日志/新重建 profile 全是同一个错，绕了很久。

证据（导出 profile 的 XML，看 `<hex>`）：

```
旧 profile： <hex>594A542D31 BAC5C2A5B0ECB9AB 2032</hex>   ← 「号楼办公」=GBK，末尾还多了 " 2"
空口实际： 594a542d31 e58fb7 e6a5bc e58a9e e585ac        ← 「号楼办公」=UTF-8
```

修法（`platform/pc/wifi_platform_win.cpp`）：生成 profile XML 时**同时写 `<hex>`**，
直接把空口抓到的原始字节填进去（`<SSID><hex>…</hex><name>…</name></SSID>`），名字只用于显示。
修完真机：`8001 已连接`、协商 `AES-CCMP`、`netsh` 回读 `SSID: YJT-1号楼办公 / 通道 36`；
**app 自己走点击路径 4.2 秒连上**（`[REACH] connect … 文案=已连接 YJT-1号楼办公`）。

同轮第二处根因：**profile 名不一定等于 SSID**——Windows 重名时会存成「SSID 2」，
我们原来一律拿 SSID 当 profile 名去 `WlanConnect`/`WlanDeleteProfile`，名字对不上同样报"网络不可用"。
修法：`WlanGetProfileList` + 逐个 `WlanGetProfile` 读出 XML 里的 SSID，建立
「profile 名 ↔ SSID」对照表；`saved`、连接、忘记都用表里的**真实 profile 名**。

两个附带坑：
- 通知里的 `dot11Ssid` 是 ANSI 字节（13 字节），空口是 UTF-8（17 字节）→ 认领通知要按 profile 名比；
- Windows 的 `getenv` 返回 ANSI，夹具读中文 SSID 的环境变量要 `GetEnvironmentVariableW` + 转 UTF-8
  （`main.c:env_u8`，`WIFI_REACH_TARGET=<SSID>` 用它）。

留了口子的话记得自己清：本机现在多了一条坏 profile「YJT-1号楼办公 2」（本轮排查产物）。

### 5.15 ⑦-3 长按菜单加「断开」（2026-10-25 本轮）

用户口径：长按菜单（原「忘记此网络？」对话框）**中间加一颗「断 开」**，三颗等宽：忘记 / 断开 / 取消。

- 设计源：`DIALOG_BTN_L/M/R = (90|186|282, 182, 92, 32)`，三颗同高同宽、间距 4；
  新增 native 动作 `wifi_disconnect`、控件 `btn_dlg_disconnect`。
- 链路：按钮 → `APP_OUT_WIFI_DISCONNECT` → `wifi_logic` → `io_wifi_disconnect(选中 SSID)` → 关对话框。
  假世界清 `connected` 位并重排（gen+1）；真接口走 `WlanDisconnect`。
- **真接口的语义坑**：`WlanDisconnect` 断的是**整个接口**，不认 SSID。
  所以真接口先查"目标是不是当前连接"，不是就只提示「未连接 X」，绝不去断别人的网。
- 成功后标题栏「已断开 X」；列表里该条回到未连接、全表 `connected` 归零。

证据：`[NAV] RESULT: PASS 57 / FAIL 0`（新增 8 条）；反向测试（掐掉 `io_wifi_disconnect`）→ 3 条红、rc=1；
几何门禁三颗按钮出码=设计=`(20|116|212, 92, 92, 32)`（相对卡片）。出图 `build/sim_shots/dialog_open.png`，
设计图 `mockup_08_forget_confirm.svg`。

待用户定文案：对话框提示仍是「将删除已保存的密码，下次连接需重新输入。」，只解释了「忘记」；
要不要改成同时说明「断开」，等口径。

### 5.13 ⑦-2f 半页入场动画（2026-10-24 本轮）

用户问「密码弹出窗口可以加弹出动画吗」——可以，而且设计图 `mockup_06` 的备注本来就写着
「遮罩淡入 + 半页自底部上滑」，之前只是没实现。

实现（`navigation/wifi_nav.cpp`，显隐本来就归这一层）：

- 半页 `translate_y` 从「自身高度」→ 0（200ms，`ease_out`）；遮罩 `bg_opa` 0 → 设计值（115），
  同一个时长。**用 `translate_*` 而不是改 `y`**：不动布局值，退出时一键复位。
- `wifi_nav_animating()` 暴露"动画是否在跑"，夹具的 `pred_sheet_visible` 改成
  "已显示 **且动画结束**"——`translate` 会同时影响**命中测试**，动画期间点按钮的坐标是偏的
  （这正是"渲染坐标 ≠ 布局坐标"那条老坑的另一面）。
- **退场对称**：点 × / 遮罩 / 连接成功关闭时，半页滑下去 + 遮罩淡出（同 200ms，ease_in），`ready_cb` 里才真正 `HIDDEN`；逻辑状态（`wifi_nav_sheet_open`）立刻为假，所以"半页开着才要求密码"这类判据不会因为动画而误判。退场途中被重新打开 / 被对话框互斥切走时，取消动画并立刻落位。
- 关闭/互斥切走时 `lv_anim_delete` + 复位 translate 与遮罩透明度，避免下次打开从半路开始。

**编译期开关**：`WIFI_SHEET_ANIM`（默认 1，定义在 `navigation/wifi_nav.h`）整体控制入场/退场动效。
关掉：`set SIM_DEFS=-DWIFI_SHEET_ANIM=0` 再跑 `run_sim.bat build`（脚本会把宏同时传给 C 与 C++），
或命令行 `-DWIFI_SHEET_ANIM=0`。夹具里两条"动画在跑"的断言也用同一个宏包裹，所以两种模式门禁都绿
（开=49 条、关=47 条）。

证据：`[NAV] RESULT: PASS 49 / FAIL 0`（两条动效断言：「点开后半页正在上滑」「点 × 后半页正在滑下去」）；
反向测试：注释掉入场 → 前者 rc=1；把关闭改回"立刻隐藏"→ 后者 rc=1。

> 顺带记一笔：本轮跑门禁时 ④A 抓到一次**出码与设计源不一致**
> （`pwd_ta` 高 35、`kb_main` y=86，而设计源是 36 / 92）——`src/ui` 被用非当前设计源生成过一次。
> 按 G1→G2→G5 重跑 `build_example.py / cli_build.py / gen_font.py` 后恢复一致。
> 这说明该门禁不是摆设：`src/ui` 任何时候可疑，重跑生成链而不是手改。

设计侧待办：`mockup_06_connecting` 画的是"半页仍在 + 标题栏正在连接"，与本轮定的
"收半页 + 全屏转圈"已不一致——**要不要重画这张交付图等你点名**，本轮没动 `design/mockups/`。

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
