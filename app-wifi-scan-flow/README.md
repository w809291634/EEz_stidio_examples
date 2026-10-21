# app-wifi-scan-flow — WiFi 扫描列表（母工程 · Flow 在跑）

## 定位

**v4 现行形态**：单屏静态外壳（标题 / 状态行 / 刷新按钮 / 空 `lv_list`）+ cn14 中文字库
+ 1 个 native 动作，**EEZ 持有 0 个变量**——状态由 native 经 `app_model` 契约直驱，
列表由 native 直读 io 接口自绘（唯一真值源 = io 静态数组）。

> 演进：v1 空屏幕骨架 → v2 List 控件 → v3 Flow 数组变量 → **v4 数组变量与全部变量移出 EEZ**。
> 现行架构与账单见 `ARCHITECTURE.md`（v4 收口）；原 `app-wifi-connect` 保持不动作为参考。

> **姊妹版**：[`../app-wifi-scan-flow-no-flow/`](../app-wifi-scan-flow-no-flow/) —— 只把
> `flowSupport` / `generateSourceCodeForEezFramework` 关成 `false` 的**无 Flow 运行时**对照版
> （native 层逐字节相同）。Flow on/off 实测账单与结论见其 `README.md`。

## 结构

```
app-wifi-scan-flow/
├── build_example.py              ← 唯一设计源（生成的 .eez-project 勿手改）
├── app-wifi-scan-flow.eez-project ← 生成产物（EEZ Studio 打开它）
├── design/
│   ├── cli_build.py              ← EEZ CLI 构建（含 flow 检查错误守卫）
│   ├── audit_chars.py            ← 逐字审计（加文字后启用）
│   └── sim_cmake/                ← run_sim.bat + main.c + lv_conf.h（PC 仿真）
└── src/ui/                       ← EEZ 生成区（勿手改）
```

## 构建（顺序敏感）

```bat
rem 一键预检：生成 → CLI 构建 → 产物校验 → 字符审计 → 静态自检 → 字库 → 仿真编译
python design\preflight.py --with-sim

rem 或分步：
python build_example.py           && rem 设计源 → 工程
python design\cli_build.py        && rem EEZ CLI 构建（0 flow 错误才继续）
双击 design\sim_cmake\run_sim.bat   && rem 编译 + 启动 PC 仿真
```

**完整流程 / 语法防火墙 / 15 坑 / 截图对照 / 一次完成 Gate 表**：见 `EEZ_WORKFLOW.md`。
**截图与设计图对照**：`python design\ui_check.py --design design\mockups\mockup_01_list.svg`
（产出 `design/check/report.html`：设计图 ｜ 截图 ｜ 叠加图 三栏 + 偏差表）。

## 当前状态（2026-10-20 22:20 验证 · v1 列表已跑通）

| 步骤 | 命令 | 结果 |
|---|---|---|
| 生成工程 | `python build_example.py` | 531,897 字节（10 槽列表）✓ |
| CLI 构建 | `python design\cli_build.py` | BUILD RESULT: ok（0 flow 错误）✓ |
| 产物校验 | `python design\preflight.py` | **PREFLIGHT PASS**（5 产物齐全）✓ |
| 逐字审计 | `python design\audit_chars.py` | OK ✓ |
| 静态自检 | `python design\check_project.py` | OK（7 项）✓ |
| 烘焙字库 | `python design\gen_font.py` | `ui_font_cn14.c` 5.0 MB ✓ |
| PC 仿真编译 | `run_sim.bat` | succeeded ✓ |
| 无头运行 | `WIFI_AUTOSCAN=1 WIFI_SHOT=1` | `scan done: 12 APs (sorted by RSSI)` + 截图 ✓ |

### v3 已实现（List 控件 + Flow 结构体数组变量 · 2026-10-21 验证）

- **列表页**：EEZ **List (LVGL) 控件**（`lv_list_create`，448×242，scrollbar AUTO）；
  行由 C 侧 `lv_list_add_button()` 按数组长度动态创建——**行数不限、原生可滚动**；
- **行内 7 项信息**：4 格信号条 / SSID / 加密类型 / RSSI dBm / 频段 / 状态文字；
- **排序**：扫描结果 **RSSI 降序**（io 层 `qsort`，SSID 兜底稳定）；
- **数据模型（核心）**：EEZ 里定义 **Struct `ap_info`（7 字段）+ 数组变量
  `aps: ap_info[]` + `ap_len`**——native 通过 `ap_store.cpp`
  （`makeArrayRef` + `setGlobalVariable`）**直接读写这个 C++ 容器**；
  io 层扫描完成即 publish，UI 层从同一变量读。数据全动态，无固定槽；
- **EEZ 不持有变量**：状态（扫描态/文案/内容代数）由 native 经 `app_model` 契约直驱，EEZ 仅画界面外壳与空 lv_list；
- **滚动已验证**：`WIFI_SCROLLTEST=1` 无头拖拽（注入真实 SDL 事件），
  3/3 次 `scroll_y 0→165+` PASS；
- **截图钩子**：`WIFI_AUTOSCAN=1 WIFI_SHOT=1 WIFI_AUTOEXIT=1` 无头跑完自动退出。

> 演进：v1「容器+10 固定槽」废弃（hit_test 要求 CLICKABLE，P-0166）；
> v2 改 List 控件；v3 数据源换 Flow 数组变量 aps[]（P-0167）；
> **v4（现行，2026-10-21）：数组变量移出 EEZ**（`ap_info`/`aps[]`/`ap_len` 与 `ap_store` 桥删除），
> 列表数据由 native 直读 io 接口（`wifi_ap_at`/`wifi_ap_count`/`wifi_ap_gen`）。
> **v4 收口（同日稍后）：EEZ 不再持有任何变量**——`scan_state`/`ap_gen`/`scan_status` 三层
> native 变量桥（`native_vars.*`）删除，`gvs=[]`；状态改由 native 经 `app_model` 契约直驱，
> EEZ 仅画静态外壳。单一真值源 = io 静态数组。
> 架构图/回流图已同步 v4（`mockup_17` / `mockup_18`），详见 `ARCHITECTURE.md` §修订 v4。

### v4 改动（2026-10-21）

- **EEZ 工程**：`gvs=[]`、`structures=[]`、`flow_vars=[]`（**无任何变量**）；`vars.h` 空枚举、`structs.h` 空壳；
- **native**：`ap_store.{h,cpp}` 删除；`wifi_ui_sync.cpp` 直读 `wifi_ap_at()`/`wifi_ap_count()`；io_pc 不再 publish；
- **验证**：重编 12/12 过；无头运行 `[UI] list rebuilt: 12 rows from io (gen=1, count=12)`；
  截图渲染与 v3 逐区域一致。

### 待做（按顺序）

1. 点行 → 半页连接面板（密码框 + 键盘 + 连接/取消，224 高，overlay 挂 screen 根）；
2. 真 WiFi 后端（`io_win` / `io_esp`，替换 `io_pc`）；
3. 记住密码 / 忘记网络（长按或显式按钮）。

## 加功能时照抄的铁律（经验库 P-0164 / reference/11 §6）

1. **控件结构照抄 EEZ 原生形态，禁止自创**（按钮 = 子 label
   `widthUnit:"content"` + `align:"CENTER"`，只改文字）；
2. 加文字前先配字体（GB2312 全集 + ASCII + fontTools cmap 过滤）+ audit_chars；
3. 交付前跑 cli_build 的 flow 守卫，不只看 "Build successfully finished"；
4. 真 WiFi 后端参考 `../app-wifi-connect/src/native/platform/io_win.cpp`
   （WPA3SAE + mingw 参数顺序 + 轮询节流 + 延迟连接，已实测连通）。
