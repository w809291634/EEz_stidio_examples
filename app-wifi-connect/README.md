# app-wifi-connect — WiFi 扫描/连接全流程（EEZ 实现 UI + native 桥数据）

> 架构蓝本：eez-test 的 WiFi 配网（KB P-0080/0085/0094 同款模式）。
> **UI 全部在 EEZ 里实现**（列表/密码面板/键盘/状态/记住密码），数据走 native 桥；
> 真机上只需把 main.c 的"假 WiFi 驱动"换成 esp_wifi 扫描/连接/NVS，**UI 零改动**。

## 架构

```
┌─ EEZ 工程（UI 全量）────────────────────┐   ┌─ main.c（native 桥 + 假驱动）────┐
│ 变量(26 个，全 native:true)：            │   │ action_scan_start()  → 假扫描2s  │
│  scan_state 0/1/2 扫描状态               │←──│ action_wifi_pick_N() → 选中行    │
│  ap_count     扫描数                     │   │ action_wifi_connect()→ 读密码连接 │
│  wifi_state  0/1/2 连接状态              │──→│ action_chk_remember()→ 切记住密码 │
│  wifi_conn_ssid / g_pick / g_pick_ssid   │   │ action_panel_cancel()→ 关面板    │
│  g_remember(记住密码) / saved_ssid(已存) │   │ get/set_var_* × 26（变量桥实现）  │
│  wifi_slotN_ssid/_rssi/_lock（N=0..5）   │   │ 假驱动：2s 出 6 假 AP / 连接 2s 成 │
│ 动作(9 个，native 实现)：                 │   │ 自动演示：假 indev 点行→点连接     │
│  scan_start / wifi_pick_0..5 /           │   └──────────────────────────────────┘
│  wifi_connect / chk_remember /           │    真机替换点：esp_wifi 扫描/连接/NVS，
│  panel_cancel                            │    UI 零改动
└─────────────────────────────────────────┘
```

## UI（单屏 + 密码面板覆盖层，P-0080 同款）

- **头部**：标题 + 扫描状态标签（三元表达式：扫描中.../已发现 N 个网络/未扫描）+
  刷新按钮（CLICKED → `action scan_start`）。
- **列表 6 行**：SSID 标签、锁标志（hiddenFlag 按有无密码显隐）、信号强度
  （`rssi + " dBm"`）、"已连接"徽标（`wifi_state==2 && conn_ssid==slot_ssid` 时显示）、
  **点击热区**（透明容器盖整行，CLICKED → `action wifi_pick_N`）。
- **底部**：连接状态（未连接/连接中.../已连接: SSID 三态表达式）。
- **密码面板**（覆盖层，`hiddenFlag = "g_pick < 0"`）：
  标题(选中 SSID) + 密码 Textarea（`passwordMode`+`oneLineMode`，由键盘直接输入，
  **连接时 C 侧 `lv_textarea_get_text(objects.pwd_ta)` 读取**——textarea 的 text
  是 input 型单向属性，别绑变量否则打字会被 tick 覆盖）+ **Keyboard**
  （`textarea:"pwd_ta"` 属性直接指定绑定对象，EEZ 原生支持）+ "记住密码"可点标签
  （CLICKED → 切 g_remember）+ 连接/取消按钮。

## 关键机制（EEZ 侧实现要点）

1. **事件 → native 动作**：`eventHandlers = [{eventName:"CLICKED",
   handlerType:"action", action:"xxx"}]`，动作在 EEZ actions 数组声明
   （`implementationType:"native"`），C 侧实现 `void action_xxx(lv_event_t*)`。
2. **native 变量桥**：全局变量 `native:true` → EEZ 生成 vars.h 声明
   `get_var_xxx/set_var_xxx`（string 为 `const char*`），C 侧给实现——C 填
   set_var 即驱动 UI 表达式刷新，UI 改值 C 在 get_var 里读。
3. **行显隐**：空槽隐藏用 `hiddenFlag = "wifi_slotN_ssid == ''"`
   —— **JSON 键名是 `hiddenFlag`（hiddenFlagType:"expression"）**，
   hiddenExpr 是 DSL 层字段名（P-0080 的"true=隐藏"语义不变）。
4. **定长槽位 + 空槽隐藏**（P-0080 同款）：不用结构体数组，6 个槽位变量
   按名直读最稳；真机 AP 数超过 6 就分页。
5. **自动演示**（main.c）：假指针 indev 单击行/按钮（走真实输入管线），
   开机自动：扫描 → 点开放网络 Guest → 面板弹出 → 点连接 → 2s 后底部
   显示"已连接: Guest"。`[STATE]`/`[WIFI]` 日志全程可断言。

## 构建与验收

```
python build_example.py && python design/cli_build.py
python design/audit_chars.py     ← ★ 逐字审计（UI 文案字符 vs 字体字符集，缺字即报）
python design/gen_font.py        ← ★ 烘中文字体（必须在 cli_build 之后跑，见坑 8）
双击 design\sim_cmake\run_sim.bat  ← 开机自动演示全流程
```

验收（自动演示日志）：
`[WIFI] scan done: 6 APs` → `[TAP]` → `pick=1, panel_hidden=0` →
`connect to 'Office-2G'` → `wifi=1` → `connected` → `[DEMO] done`；
屏幕上：列表出现 6 行、密码面板弹出、底部最终显示绿色"已连接: Guest"。

## 踩过的坑

1. **★ 隐藏表达式的 JSON 键名是 `hiddenFlag`**（配 `hiddenFlagType:"expression"`）；
   写成 `hiddenExpr` 会被静默忽略 → 面板/热区永远可见/隐藏（本例面板盖住全屏
   吸收点击，行点击全失效）。hiddenExpr 是 DSL 层字段名，json2eez 后变 hiddenFlag。
2. **★ CLI 不烘字体**（P-0140）：工程里建了字体条目（P-0125 四要点格式）只会让
   fonts.h 生成 `extern` 声明，字体 .c 用 lv_font_conv 离线烘——本工程
   `design/gen_font.py`（simhei.ttf 14px bpp4，字符集=UI 静态文案并集），产物
   `src/ui/fonts/ui_font_cn14.c`。**字体条目的 source 必须指向全量字体**：
   指向子集 TTF 时 GUI 提取报 `Font "cn14" extraction failed: ... doesn't have
   any characters included in range ...`（字符集里的字在子集里没有）——本例已改用
   全量 `fonts/simhei.ttf`。
3. **Textarea 的 text 是 input 型单向**：绑定变量会被 tick 用变量值覆盖打字内容；
   密码读取走"native 动作里 lv_textarea_get_text(objects.pwd_ta)"。
4. **Keyboard 的 textarea 属性**（枚举本页 textarea 的 identifier）直接在 EEZ 里
   指定绑定对象，生成 `lv_keyboard_set_textarea`，不需要 C。
5. **运行期 SSID 的字体覆盖**：演示字体只烘了静态文案字符集；真机上 SSID 是
   运行期数据，字库要按产品需求扩（KB 09 号作业卡：13px 档 GB2312 全量 ~6770 字）。
6. **自动演示的 printf 要 `setvbuf(stdout, NULL, _IONBF, 0)`**：重定向到文件时
   全缓冲会吞掉被 kill 前的日志。
7. **假指针单击 = 假 indev + 状态机**（press 3 read → release 1 read），
   走真实管线不占真鼠标（同 perf 工程的假拖动法）。
8. **★ gen_font 必须在 cli_build 之后跑**：CLI 重建 src/ui 时孤儿清理会把
   已烘的字体 .c 删掉——顺序错了链接报 `undefined reference to ui_font_cn14`；
   新建字体 .c 后还要删 sim_cmake 的 build_rel（GLOB 不自动重扫新文件）。
9. **★ 逐字审计工具 `design/audit_chars.py`**：遍历工程全部 text/placeholder/
   表达式字符串字面量，与 FONT_CHARS 比对列出缺字（含私有区字符检查）——
   改文案/加标签后必跑；曾实抓 `入`（placeholder 漏字）和锁形私有区字符
   U+F003（默认字体必豆腐，已改用文本"锁"并入字符集）。

## 依赖版本

EEZ Studio 0.29（projectVersion=v3）· LVGL 9.4 · 480x320 · PC_SIM 仿真验证
（CLI 0 错 0 警 + 仿真器编译链接 0 错 + 自动演示全流程日志断言，2026-10-20）。
