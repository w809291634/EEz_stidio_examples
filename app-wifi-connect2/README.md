# app-wifi-connect2 — WiFi 连接应用（基础工程模板）

## 定位

**基础工程模板**：空屏幕骨架（零控件/零字体/零动作/零变量），作为 WiFi 连接
应用 v2 的起点，功能按步骤逐个添加。原 `app-wifi-connect` 保持不动作为参考。

## 结构

```
app-wifi-connect2/
├── build_example.py              ← 唯一设计源（生成的 .eez-project 勿手改）
├── app-wifi-connect2.eez-project ← 生成产物（EEZ Studio 打开它）
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

### v1 已实现

- **列表页**：10 个固定行槽 + 滚动容器（`list_box` 448×242，行 pitch 50）；
  空槽 `HIDDEN` 自动收拢；右侧滚动条；
- **行内 7 项信息**：4 格信号条 / SSID / 加密类型 / RSSI dBm / 频段 / 状态胶囊；
- **排序**：扫描结果 **RSSI 降序**（C 侧 `qsort`，SSID 兜底稳定）；
- **数据源**：`io_pc` 假驱动（12 个 AP，2s 扫描），不接硬件；
- **变量 3 个**：`scan_state` / `ap_count` / `scan_status`（native，C 桥）；
  行内容由 `wifi_ui_sync.cpp` 直接写控件，**不建 Flow 绑定**；
- **截图钩子**：`WIFI_AUTOSCAN=1 WIFI_SHOT=1 WIFI_AUTOEXIT=1` 无头跑完自动退出。

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
