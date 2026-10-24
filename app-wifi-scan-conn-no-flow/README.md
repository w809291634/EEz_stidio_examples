# app-wifi-scan-conn-no-flow —— WiFi 扫描列（关掉 EEZ Flow 运行时的姊妹工程）

> **演示点**：同一份 UI/native 设计，把 EEZ Flow 运行时整个摘掉之后，工程还能不能构建、
> 按钮点击还能不能触到 native 动作。结论是**能，而且不用改一行业务代码**——
> 本文件下面记录的就是这次实测的判据与账单。
>
> **与 `app-wifi-scan-flow` 的唯一设计差异**：`build_example.py` 里
> `settings.general.flowSupport = False`、`settings.build.generateSourceCodeForEezFramework = False`。
> 其余（控件树、字体条目、native 层、仿真三件套）逐字相同。

## 演示点

1. **Flow 关闭后的出码形态**：`src/ui/` 只剩 12 个模板文件，**不发射 `eez-flow.cpp/.h`**，
   `ui.c` 走 `#else`（纯 LVGL）分支 —— `ui_init() = create_screens() + loadScreen()`，
   `ui_tick() = tick_screen(currentScreen)`，没有 `eez_flow_init/assets/eez_flow_tick`；
2. **事件 → native 动作在无 Flow 下依然接线**：`screens.c:91` 生成
   `lv_obj_add_event_cb(obj, action_scan_start, LV_EVENT_CLICKED, (void *)0)`，
   对比 Flow 版的 `event_handler_cb_main_btn_refresh(..., LV_EVENT_ALL, flowState)`
   —— 少了 flowState 中转，直连到 `.eez-project` 里 `implementationType:"native"` 的那个动作；
3. **native 层的平台无关性验证**：`src/native/` 对 Flow API **零引用**
   （`grep -r "eez_flow|getGlobalVariable|setGlobalVariable|EEZ_FOR_LVGL" src/native` = 0 命中），
   所以摘掉运行时不需要改业务代码，只删运行时；
4. **no-flow 双向门禁**：`design/preflight.py` 除产物存在性外，新增
   `check_no_flow()` —— 断言 `eez-flow.*` **不得出现**（开关被改回去就 FAIL），
   且断言 `screens.c` 里仍有 `lv_obj_add_event_cb` + `action_scan_start`（动作链静默断裂就 FAIL）。

## 工程结构

```
app-wifi-scan-conn-no-flow/
├── build_example.py                    ← 唯一设计源（改 UI 改它；两个 False 开关在本文件）
├── app-wifi-scan-conn-no-flow.eez-project ← 生成产物，EEZ Studio 可直接打开
├── design/
│   ├── preflight.py                    ← ★ 一键全链 + no-flow 判据（本变体新增）
│   ├── cli_build.py                    ← EEZ CLI 构建 + flow 错误守卫
│   ├── gen_font.py / audit_chars.py / check_project.py / ui_check.py
│   ├── mockup_gen.py                   ← 出图；★ 本变体新增 sc_noflow_arch() → mockup_20
│   ├── mockups/mockup_20_noflow_arch.svg ← ★ 本变体架构图（五层 + Flow/本变体对照 + 账单）
│   └── sim_cmake/                      ← run_sim.bat + main.c + lv_conf.h（PC 仿真）
├── fonts/simhei.ttf
└── src/
    ├── native/                         ← 人写：app/ 平铺四组 + navigation/ + widgets/wifi_list（画列表）+ platform/pc
    └── ui/                             ← EEZ 生成（禁手改）；★ 无 eez-flow.cpp/h
```

> **继承过来的设计文档**（`ARCHITECTURE.md` / `IMPLEMENTATION.md`）已按**双口径**改写：
> 同一处并列「Flow 版」与「本变体」事实，别只读半句——
> `ARCHITECTURE.md` §1②③/§2/§3/§7/§8/§9/§10、`IMPLEMENTATION.md` §7 通则与 §7.1/§7.2。
> `DESIGN.md` / `EEZ_CHECKLIST.md` / `EEZ_WORKFLOW.md` / `SCAN_BINDING.md` 不含 Flow 断言，原样继承。
>
> **★ 不属于本变体、已删除的继承件**（要看就去 `../app-wifi-scan-flow/`，别再拷回来）：
> `FLOW_STRUCT_ROUTE.md`（Flow 结构体路线，本变体永不适用）、
> `mockup_17_flow_arch.svg`（Flow 形态架构图；生成函数 `sc_flow_arch()` 与出图调用已一并删除，
> 重跑 `python design/mockup_gen.py` 不会再生成它）、
> `提示词.txt`（母工程会话提示词留痕）、`*.eez-project-ui-state`（母工程 EEZ GUI 编辑态）、
> `design/sim_cmake/shot_{fake.bmp,final.png,scan.png}`（母工程历史截图，本变体跑仿真会重新落盘）、
> `__pycache__/`。本目录现存过程图 **11 张**（10 张继承 + 本变体新增 `mockup_20_noflow_arch.svg`）。
>
> ★ `src/native/` **故意逐字节不改**（含 `app/wifi_model.h` 注释里的母工程名）——
> `diff -r ../app-wifi-scan-flow/src/native src/native` 必须为空，这正是"只删运行时、不动业务"的证据。

## 依赖版本

| 项 | 值 |
|---|---|
| EEZ Studio | 0.29.0（`projectVersion=v3`） |
| LVGL | 9.4.0（PC 仿真宿主 9.5） |
| 屏幕 | 480×320，深色主题，16bpp |
| 字体 | `ui_font_cn14`（simhei 14px，GB2312 符号区+一二级汉字 + ASCII，bpp4） |
| 目标平台 | PC 仿真（`platform/pc/` 假数据）；真机走 `platform/device/`，同一份 `wifi_platform.h` 接口 |

## 怎么用

```bat
set PYTHONIOENCODING=utf-8        rem ★ 必设，见"踩过的坑"第 3 条
python build_example.py           rem 设计源 → .eez-project
python design\cli_build.py        rem EEZ CLI 构建（判据 = 日志 + 产物对账）
python design\gen_font.py         rem 补烘字体（CLI 不烘，P-0140）
双击 design\sim_cmake\run_sim.bat rem 编译 + 启动 PC 仿真
```

一条命令跑完全链（含 no-flow 判据）：

```bat
python design\preflight.py --with-sim
```

### 仿真器默认走**真** WiFi（wlanapi）

双击 `design\sim_cmake\run_sim.bat` 就是真网卡：列表是本机扫到的真网络（隐藏网络不列），
点「已保存」的行是真的 `WlanConnect`——半页收起、全屏转圈、期间点不动，
结果出来才收圈（**换网会先断掉原来连着的**，连不上就两头空，标题写「连接失败 X」），
长按已保存的行会出三按钮菜单：**忘记**（真删系统里的密码）/ **断开**（只断当前这条连接）/ **取消**。
`WlanDisconnect` 断的是整口、不认 SSID，所以「断开」只在目标确实是当前连接时才动手，否则只提示「未连接 X」。
失败时标题栏会带上系统给的原因（如「连接失败 X（特定的网络不可用）」），原因码翻不出文案时显示「错误码 N」；
要深挖就先分清"系统也连不上"还是"我们没下发"：
`Get-WinEvent -ProviderName Microsoft-Windows-WLAN-AutoConfig`（8002 给失败原因）
与 `netsh wlan connect name="<SSID>"` 各跑一次即可裁决。

要回到可复现的假世界（12 条假 AP，门禁与出图用的就是它）：

```bat
set WIFI_PC_FAKE=1
```

没有无线接口 / `wlansvc` 没起时会自动退回假世界并打印原因。
无头取证入口：`WIFI_AUTOSCAN=1 WIFI_REACH=connect WIFI_AUTOEXIT=1`（不设 `WIFI_PC_FAKE` 即真接口）。

## 实测账单（本次 2026-10-21，Flow 版 → no-flow 版）

| 测项 | Flow 版 | no-flow 版 | 量法 |
|---|---|---|---|
| `src/ui/` 发射文件 | 12 模板 + `eez-flow.cpp`(369,589 B / 9,923 行) + `eez-flow.h`(160,060 B / 4,384 行) | 12 模板，**无 flow 运行时** | `ls src/ui` |
| `src/ui/` 生成码总字节（**不含 `fonts/` 子目录**） | 548,573 | 13,950 | `find src/ui -maxdepth 1 -type f -printf '%s\n'` 求和（**−534,623 B**） |
| `ui.c` 里的 assets | `const uint8_t assets[588]` + `eez_flow_init(...)` | 两者都不存在 | `grep assets src/ui/ui.c` |
| `screens.c` | 266 行（含 flowState、event_handler 中转、object_names 表） | 249 行（直挂动作回调） | `wc -l` |
| 二进制 `eez` 符号 | 501 个 `eez::flow` 符号 | **0 个**（`nm` 仅误命中 `lv_group_focus_freeze`） | `nm main.exe \| grep -i eez` |

> 固件级（MCU flash/RAM）净收益不在此重复测：见经验库 `P-0155` / `P-0157` / `P-0170`
> —— 未优化 EEZ 核心约 259KB Flash / 28KB RAM，三项编译优化后约 92.4KB / 3.4KB。
> 要自己 A/B：两工程各跑 `run_sim.bat build`，再 `size PC_SIM\...\bin\main.exe` 比 text 段。

## 踩过的坑

- ★ **关 Flow 后事件动作仍发射**（纠正经验库记载）：经验库
  `reference/07_project_json_schema.md` §2 记 `flowSupport` 是"开 flow 的总开关（**事件 handler/组件都依赖它**）"。
  实测：只要动作是 `implementationType:"native"`，`flowSupport:false` 下 EEZ **照样**生成
  `lv_obj_add_event_cb(obj, action_scan_start, LV_EVENT_CLICKED, 0)`，直连 native 函数，不经 flow 队列。
  **但只有这一形态被验证过**——`Switch/If/Animate` 等 flow 组件、表达式绑定、`SetVariable`
  在无 Flow 下必然失效（没有运行时）。所以适用边界是"**事件 → 单个 native 动作**"，不是"全部交互"。
- ★ **`BUILD_TEMPLATES` 别精简**：`ui.c`/`ui.h`/`structs.h` 模板里的
  `#if defined(EEZ_FOR_LVGL) ... #else ... #endif` 两分支都要留着。
  只留 flow 分支的话，no-flow 出码就没有 `create_screens()` 调用路径（`ui_init` 变空）。
- **`build_example.py` 在无 GUI 的 Git Bash 里会 `UnicodeEncodeError`**：
  打印"字体未覆盖字符"时 GBK 控制台编不出 `・`。根因是控制台编码，不是字符集逻辑；
  设 `PYTHONIOENCODING=utf-8` 即可（不改脚本，保持与设计源一致）。
- **`check_no_flow` 为什么反着写**：本变体的"构建成功"判据多了反向一条——
  `eez-flow.cpp` 出现 = 开关被改回去 = 缺陷。正向产物对账（P-0005）不足以守住这个不变量。
- **native 层一条都没改**，但 `design/sim_cmake/main.c` 顶部注释原来写的是
  "ui_init 内部无条件调用 eez_flow_init"——那是 Flow 版事实，本工程已改成 no-flow 事实。
  注释会随工程复制而失真，复制示例时这类"环境描述"要逐条核对。
- **PC 仿真那条 `lv_sdl_mouse_handler` 隐式声明 warning 是从 flow 版继承的**
  （`drag_scroll_test` 里），不影响链接，两个工程都有，不是本变体引入。

## 什么时候该用这个变体

经验库 `P-0170` §3 的判据：**只有静态控件 + 单一点击回调、没有表达式/页面/动画/复用逻辑的页面**，
完整引擎成本摊不平，就该关 Flow。本工程正好落在这条线上（v4 收口后 EEZ 不持有变量、
列表由 native 直读 io 自绘、动作只有一个 `scan_start`）。

反过来，一旦要加密码半页、`wifi_state` 分支、页面转场、EEZ 动效（母工程 README「待做」第 1 条），
就把 `flowSupport` 开回来 —— 保留时记得把 `executionQueueSize` 1000 降到已验证的 128
（实测省 10,464 B RAM，`P-0157`）。

## 经验库对照

- 案例：`P-0170`（Flow 收益与体积取舍、no-flow 适用边界）、`P-0155`/`P-0157`（引擎账单与优化）、
  `P-0152`（CLI 提前退出掐死 eez-flow 发射，本变体不再发射该文件，但守卫仍保留）、
  `P-0140`（CLI 不烘字体）、`P-0005`（构建成功≠有产物）；
- 方法论：`PLAYBOOK.md` 红线 9（数值证据）、`skills.md`（对照查验）；
- **待回灌**：本文件"踩过的坑"第 1 条应修正 `reference/07_project_json_schema.md` §2 对
  `flowSupport` 的一句话描述（native 动作不依赖它）。
