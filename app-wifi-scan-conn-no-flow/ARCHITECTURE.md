> **⚠ 本目录是 `app-wifi-scan-flow` 的 no-flow 变体**（`flowSupport=false` +
> `generateSourceCodeForEezFramework=false`）。本文从母工程继承，已按**双口径**就地改写：
> 同一处并列「Flow 版」与「本变体（no-flow）」两条事实，别只读半句。
> 已改：§1 ②③（②′/③′ 是 Flow 版）、§2 第 2 条、§3 连接链路、§7 目录与自证判据、§8 全表、
> §9 表前口径说明、§10 本变体定位。
> **不属于本变体、本目录已删除的继承件**：`FLOW_STRUCT_ROUTE.md`（Flow 结构体路线）、
> `mockup_17_flow_arch.svg`（连同 `mockup_gen.py` 里的 `sc_flow_arch()`）、`提示词.txt`（母工程会话留痕）、
> `*.eez-project-ui-state`（母工程 GUI 编辑态）、`shot_*.{bmp,png}`（母工程历史截图）、`__pycache__/`。
> 需要这些内容请去 `../app-wifi-scan-flow/`。
> **本变体一句话事实**：不发射 `eez-flow.cpp/h`、`ui.c` 无 `assets[]`/`eez_flow_init`/`eez_flow_tick`、
> 二进制 `eez::flow` 符号 **0 个**（Flow 版 501 个），但 native 动作仍由生成码直挂
> （`screens.c:91`）。实测与账单见 `README.md`。

> **★ 修订 v4（2026-10-21 08:57）**：**数组变量移出 EEZ**（`ap_info`/`aps[]`/`ap_len` 已删，
> `structs.h` 空壳，`ap_store` 桥删除）；标量走 EEZ native 变量。
> **★ 修订 v4 收口（2026-10-21）**：**EEZ 不再持有任何变量**——`scan_state`/`ap_gen`/`scan_status`
> 的 native 变量桥（`native_vars.*`）删除，`gvs=[]`；状态由 native 经 `app/wifi_model` 契约直驱，EEZ 仅画外壳。
> 列表数据由 native 直读 io 接口（`wifi_ap_at`/`wifi_ap_count`），§2 第 3 条、§3 扫描链路、§4/§6 相关行已同步。
> **修订 v2（2026-10-20 21:25）**：列表改为 **可滚动容器 + C 侧按 `ap_cnt` 建行**；
> §4「数组 16 条 / UI 固定 5 行」、§6 槽位对比表、§9 第 3 条（16→5 容量）**作废**。

# WiFi 模板架构（v4 收口）：EEZ 画界面（无变量），状态 native 直驱，列表数据 native 直读 io

> 配套图：**`design/mockups/mockup_20_noflow_arch.svg`（本变体唯一架构图；重生成 `python design/mockup_gen.py`）**
> · `mockup_18_scan_to_ui.svg`（v4 扫描回流）· Flow 形态的 `mockup_17` 属母工程，本目录已删（见 `design/mockups/README.md`）
> 相关文档：`EEZ_CHECKLIST.md`（控件/变量）· `IMPLEMENTATION.md`（交互机制）
> · Flow 结构体路线 `../app-wifi-scan-flow/FLOW_STRUCT_ROUTE.md`（v3 历史，**本变体永不适用，本目录已不复制**）

## 0. 一句话

**界面活在 EEZ 工程里（约 85%），经 `cli_build` 生成源码；状态（扫描态/文案/代数）不进 EEZ——
由 native 经 `app/wifi_model` 契约直驱、列表直读 io 静态数组（`wifi_ap_at`/`wifi_ap_count`/`wifi_ap_gen`）
自绘 List 行（约 15%），唯一真值源是 io 静态数组。EEZ 不持有任何变量。**

## 1. 五层结构（图中 ①→⑤）

| 层 | 内容 | 谁写 | 能否手改 |
|---|---|---|---|
| ① EEZ 工程 `.eez-project` | 页面 / 组件 / 控件树 / 绑定表达式 / 事件动作 / 样式字体（**无变量**） | **设计源**（`build_example.py` 生成） | 通过生成器改；GUI 手改会被覆盖 |
| ② 生成源码 `src/ui/` | `screens.c`（控件树+样式内联）· `vars.h`（空枚举，无变量）· `actions.h`（native 动作声明）；`structs.h` 空壳 | `cli_build` 产出 | **禁止手改**（会被覆盖） |
| ②′ 同上（**Flow 版差异**） | 母工程还多发 `ui.c` 里的 `assets[588]` + `actions[]` 表 | 同一 `cli_build` | 同上 |
| ③ 执行模型（**本变体：无 Flow 运行时**） | `ui_init() = create_screens() + loadScreen()`、`ui_tick() = tick_screen(currentScreen)`；**不发射 `eez-flow.cpp/h`**，`src/ui/` 只有 12 个模板文件 | EEZ 生成 | 不改 |
| ③′ 执行模型（**Flow 版**） | `eez-flow.cpp`（**9,923 行 / 369,589 B，生成进 src/ui**）+ `Value`/`ArrayValue` + `eez_flow_init` / `eez_flow_tick`（母工程 v4 未用 Struct 数组） | EEZ 生成（不是外部库） | 不改；已编进二进制 |
| ④ native 层 | `platform/wifi_platform.h`（契约）· `app/wifi_model·view·events·logic`（平铺四组）· `widgets/wifi_list/wifi_list.cpp`（★ 唯一画列表处）· `widgets/wifi_busy/`（连接中整屏遮罩）· `navigation/wifi_nav.cpp`（模态显隐）· `platform/pc|device/`（宏二选一） | **人写** | 唯一允许业务改动的地方 |
| ⑤ 硬件 | esp_wifi + NVS / Windows WLAN API / 假数据 | 平台 | — |

## 2. 三处关键边界（架构真正的"接缝"）

1. **EEZ → 生成码**：`build_example.py` 是唯一设计源；`src/ui/` 是产物。要改 UI 一律改生成器。
2. **生成码 → 执行模型（两变体不同）**
   - **本变体（no-flow）**：没有 Flow 这一层。`ui.c` 只有 `create_screens()`/`loadScreen()`/`tick_screen()`，
     没有 `assets[]`、没有 `eez_flow_init/eez_flow_tick`；按钮 → native 动作由生成码**直挂**
     （`screens.c:91`：`lv_obj_add_event_cb(obj, action_scan_start, LV_EVENT_CLICKED, (void *)0)`），
     `nm main.exe | grep -i eez` 只剩误命中的 `lv_group_focus_freeze`，**`eez::flow` 符号 0 个**。
   - **母工程（flow）**：`assets` 二进制 + `eez_flow_init(assets,…)` + 每帧 `eez_flow_tick()`；
     ★ 实测**已经在跑 Flow**——`eez-flow.h` 自带 `#define EEZ_FOR_LVGL 1`，`eez-flow.cpp` 9,923 行一起生成，
     编出的 `main.exe` 里有 501 个 `eez::flow` 符号。所以不是"待迁移"，而是"已就位"（v4 起只承载界面渲染，不承载任何变量）。
3. **native ↔ io 数组（v4，无桥）**：数组变量已移出 EEZ，**没有跨运行时桥**。
   native 直接读写 io 静态数组，UI 列表行由 `widgets/wifi_list/wifi_list.cpp` 按 `wifi_ap_count()` 循环
   `lv_list_add_button` 自绘（EEZ List 控件 wip，P-0152）。EEZ 不持有任何变量。
   换后端（PC/真机）时 `app/`、`widgets/` 与 EEZ 侧都不改。

## 3. 数据流（两条主链路）

**扫描（v4：无桥，native 直读）**
```
io_esp/io_win 扫描 → s_aps[]/s_ap_cnt（io 静态数组，可排序/去重/平滑）
   → 置 APP_IN_SCAN_STATE = 2（native 契约，最后一步；无 Flow 数组桥）
   → native wifi_list_rebuild：lv_obj_clean + 按 wifi_ap_count() 循环 lv_list_add_button
   → 行内信号条/副行/状态全部 native 自绘；EEZ 不持有变量（连接中/空态文案由 native 直写）
```

**连接 / 忘记**（⑦-2a 状态口径 + ⑦-2 PC 真接口；三态反馈与真机后端未做）
```
行手势（widgets/wifi_list）→ wifi_events_select(ssid) 记下"这条命令针对哪个网络"
   → 有锁且没存过密码 → 开半页；已保存 / 开放 → 直接投连接命令（navigation 只管显隐）
   → wifi_logic 每拍排空命令环 → io_wifi_connect(ssid, pwd) / io_wifi_forget(ssid)
   → platform 落地：假世界改 s_aps[]（全表唯一 connected、给密码才 saved）；
     真接口（默认，WIFI_PC_FAKE=1 才退回假）下发 WlanSetProfile/WlanConnect/WlanDeleteProfile
   → 后端异步报进度 APP_IN_CONN_STATE：下发即 1（标题「正在连接 X…」+ 收半页 +
     全屏转圈锁住操作），回查真值后 2 成功 / 3 超时失败，logic 收到 2/3 收圈
   → 重排 + gen++ → wifi_view_sync 回显标题文案 + wifi_list_rebuild 重画行
```
- 还没做：半页内的红字错误行（`mockup_05/07` 有，④ 没生成该控件——失败提示现在只在标题栏）、
  真机后端（`platform/device/` 是编译期占位，接口签名已对齐，可照 `pc/wifi_platform_win.cpp` 抄时序）。
- 母工程原文把 `pick_index`/`pwd_open`/`wifi_state` 写成「Flow 变量」——那是 v3 口径，v4 收口后
  **EEZ 不持有任何变量**：目标 SSID 落在 `APP_IN_SEL_SSID`，模态显隐落在 `navigation/wifi_nav`，
  连接结果落在 `wifi_ap_t.connected/saved`，文案落在 `APP_IN_SCAN_STATUS`。

## 4. 信息全面性（io 契约层保证）

`wifi_ap_t`（platform/wifi_platform.h）7 个字段覆盖 UI 全部信息需求：

| 字段 | 类型 | UI 用途 |
|---|---|---|
| `ssid` | string | 名称（超长省略） |
| `auth` | string | 加密类型 → `WPA3 / WPA2 / WPA / 开放` |
| `rssi` | int | 强度数值 + 4 格信号条点亮数 |
| `band` | string | `2.4G / 5G` |
| `lock` | bool | 锁图标 / "无需密码" |
| `saved` | bool | 「已保存」胶囊 |
| `connected` | bool | 「已连接」胶囊 + 绿色描边 |

- **空列表判据**：`wifi_ap_count() == 0`（native 侧判据，驱动空态文案走 `APP_IN_SCAN_STATUS` 契约）；
- **行数不限**：列表行 native 动态建（`lv_list_add_button`），可滚动（v2 起）；
- **派生量不上报**：格数、状态文字、显隐全部现算，避免两个真值源。

## 5. 功能稳定性（8 条机制）

| # | 机制 | 防的问题 |
|---|---|---|
| 1 | 单一真值源：数据只在 io 静态数组 | C 侧另存一份 → 不同步 |
| 2 | 先填数据再置状态（`scan_state=2` 最后写） | 半成品渲染/闪烁 |
| 3 | 命令环：UI 只写 outputs，每拍排空执行 | 重入 / UI 阻塞 |
| 4 | 状态机三值（0 空闲 / 1 进行 / 2 成功 / 3 失败） | 无反馈的"点了没反应" |
| 5 | 失败不清输入、不关半页 | 重输成本 |
| 6 | 轮询节流 1s + SetProfile 后延迟 800ms 再连（PC 实测） | 高频查询卡死认证 |
| 7 | 三后端同签名，换文件即换平台 | 平台分支污染 UI |
| 8 | 关闭弹层只改 `pwd_open`，不动 `wifi_state` | 关窗误断连接 |

## 6. 封装高级性（少即是多 · v4）

| 维度 | 说明 |
|---|---|
| EEZ 变量数 | **0**（EEZ 不持有任何变量；状态经 `app/wifi_model` 契约由 native 直驱） |
| 列表数据 | io 契约 7 字段（`wifi_ap_t`），native 直读，零拷贝进 Flow |
| 行模板 | native 按 `wifi_ap_count()` 动态建行，行数不限、可滚动 |
| 加字段 | `platform/wifi_platform.h` 的 `wifi_ap_t` +1 字段，`build_row` 画它 |
| 换硬件 | **只改 `platform/pc/` 或 `platform/device/`**（`app/` 与 EEZ 侧都不动） |

## 7. 目录与归属红线

```
app-wifi-scan-conn-no-flow/
├── build_example.py          ← 设计源（人写）★ 改 UI 只改这里；两个 no-flow 开关在本文件
├── design/cli_build.py       ← EEZ CLI + flow 错误守卫
├── design/preflight.py       ← 全链预检 + ★ check_no_flow 门禁（本变体新增）
├── design/mockups/*.svg      ← 设计图（继承母工程；no-flow 架构图见 mockup_20）
├── src/ui/                   ← EEZ 生成（禁手改）；★ 无 eez-flow.cpp/h
└── src/native/               ← 零 Flow 引用（实测 grep = 0 命中）；分层见 kit reference/12
    ├── app/                  业务层：平铺四组，**不建功能子目录**
    │   ├── wifi_model.{h,cpp}    契约状态 + 命令环（无 LVGL、无平台头）
    │   ├── wifi_view.{h,cpp}     model/平台快照 → objects.*（只回显）
    │   ├── wifi_events.cpp       EEZ 动作回调 → 投递命令
    │   └── wifi_logic.{h,cpp}    user_io_init / user_io_tick（不读 objects.*）
    ├── navigation/wifi_nav.{h,cpp}   模态显隐与互斥；不持业务状态
    ├── widgets/wifi_list/wifi_list.{h,cpp}  ★ 唯一画列表处 + 行手势
    ├── widgets/wifi_busy/wifi_busy.{h,cpp}   连接中的整屏遮罩 + 转圈（CLICKABLE 锁操作）
    └── platform/             硬件边界：接口一份，实现按平台分文件
        ├── wifi_platform.h       窄接口（不引用 LVGL / objects.*）
        ├── pc/wifi_platform_pc.cpp        #ifndef WIFI_PLATFORM_DEVICE；分发器 + 假世界
        ├── pc/wifi_platform_win.{h,cpp}   ★ 真接口（wlanapi）：**默认走它**，WIFI_PC_FAKE=1 才退回假
        └── device/wifi_platform_device.cpp #ifdef WIFI_PLATFORM_DEVICE（真机，待接）
```

> 母工程本文的原目录树写了 `ui_behavior.cpp` 与 `io_{win,esp}.cpp`，**两工程实际都不存在**
> （上面按 `find src/native -type f` 实测写）。

**自证判据（交付前跑）**
1. `grep -rn "Wlan\|esp_wifi\|nvs_" src/ui src/native/app src/native/navigation src/native/widgets`
   → **0 命中**（硬件名字只许出现在 `platform/`；那里现在确实有 `Wlan*`，那是它的职责）
   —— 已固化成 `preflight.py:check_layers()` 的「硬件符号不外溢」规则；
2. 换 `platform/pc/` ↔ `platform/device/`（只切 `WIFI_PLATFORM_DEVICE` 宏），
   `src/ui/` 编译产物与 `app/` 一行不改；
3. **Flow 版**：变量面板手改 `scan_state` / `scan_status` → UI 立即响应；**本变体（EEZ 零变量 + 无 Flow）没有这条可验**，
   等价判据改成：native 写 `APP_IN_SCAN_STATUS` → `objects.lbl_status` 立即变字；
4. `src/ui/` 里出现手工修改 → 视为缺陷（下次生成即丢）；
5. **★ 本变体独有（反向）**：`src/ui/eez-flow.cpp|h` **不得存在**，`ui.c` 不得出现 `eez_flow_init`/`assets[]`
   —— 已固化成 `design/preflight.py:check_no_flow()`，出现即 FAIL。

## 8. 已核实 / 已推翻的结论（母工程 2026-10-20 20:55 实测 + 本变体 2026-10-21 复测）

| 原结论 | 实测 | 证据 |
|---|---|---|
| 「本工程走 `create_screens()`，没在 Flow 运行时里」 | **Flow 版：错**——`ui_init()` 直接调 `eez_flow_init`，`ui_tick()` 调 `eez_flow_tick`（二进制含 501 个 `eez::flow` 符号）。<br>**本变体：对**——`ui_init() = create_screens() + loadScreen()`，`nm` 里 `eez::flow` 符号 **0 个**。<br>★ 同一条结论的真假**只由 `flowSupport` 决定**，所以两工程别互抄结论 | Flow 版 `src/ui/ui.c:46-54`；本变体 `src/ui/ui.c`（623 B，无 assets）+ `nm main.exe` |
| 「`ArrayValue` 内部是 `std::vector<Value>`，可变长」 | **错**：`struct ArrayValue { uint32_t arraySize; uint32_t arrayType; Value values[1]; }`，由 `Value::makeArrayRef(size, type, id)` 定长创建。**本变体用不上**：没有 Flow 就没有 `Value`/`ArrayValue` | `eez-flow.h:1278-1282`（仅 Flow 版发射该头） |
| 「需要额外链接 `eez/flow` 库」 | **错**：`eez-flow.cpp` 由 EEZ 生成在 `src/ui/`，已在构建里。**本变体**：`src/ui/` 里根本没有该文件，`PC_SIM` 的 `file(GLOB_RECURSE)` 自动少收两个，CMake 无需改 | `wc -l` = 9923（Flow 版）；本变体 `ls src/ui` = 12 个模板文件 |
| 「4 个 API 名未核实，只能猜」 | **已核实**：`getGlobalVariable(uint32_t index)` / `setGlobalVariable(index, Value)` / `Value::makeArrayRef` / `value.getArray()->values[i]`——**本变体一个都不调用** | `eez-flow.h:2220-2223`、`1228`、`1155` |
| 「事件 handler 依赖 `flowSupport`」（经验库 `reference/07_project_json_schema.md` §2） | **不完全成立**：`flowSupport:false` 下，`implementationType:"native"` 的动作**照样发射** `lv_obj_add_event_cb(obj, action_scan_start, LV_EVENT_CLICKED, 0)`；依赖 Flow 的是**表达式绑定 / flow 组件 / SetVariable**，不是 native 动作接线 | 本变体 `src/ui/screens.c:91`；全链 `preflight.py --with-sim` PASS |

**引用计数语义**（决定数组能不能反复新建）：`Value` 有 `refCounter`，`operator=` 先 `freeRef()` 再给新值 `refCounter++`；`setGlobalVariable` 就是一次赋值。**所以每轮扫描重建数组不会泄漏**，但会有分配抖动。（本变体不涉及：数据只在 io 静态数组。）

## 9. 架构缺口清单（当前设计没覆盖到的）

> **读这张表的两变体口径**：下面凡是写 `setGlobalVariable` / 表达式 / Flow 函数表 / `assets` 的条目
> （P0 #1、P1 #7、P1 #11、P1 #12、P2 每帧求值成本），**在本变体里不适用**——没有 Flow 运行时，
> 对应义务直接转成 native 侧责任：状态写 `app/wifi_model` 契约 + `app/wifi_view` 直写控件，
> 文案拼接/截断/类型转换全部自己用 C 实现，也不存在"每帧表达式求值"的成本；
> 字体不进 `assets`（走 `src/ui/fonts/ui_font_cn14.c`，5.0 MB 源文件）。
> 其余条目（线程边界、字库覆盖、失败原因、去重、错误可见性）两变体同判。
> ★ 顺带纠正一处母工程老数字：P1 #12 写「`assets` 仅 444 B」，母工程 v4 实测是 **`assets[588]`**
> （`src/ui/ui.c:8`）；本变体则根本没有 `assets`。

### P0 · 不补就会出错

| # | 缺口 | 后果 | 建议 |
|---|---|---|---|
| 1 | **线程边界**：`WIFI_EVENT_SCAN_DONE` 在 WiFi driver task，Flow/LVGL 都无锁 | 偶发花屏、断言、崩溃（最难复现） | 事件里只置标志/写 C 缓冲；投影与 `setGlobalVariable` 一律在 UI 任务（`ui_tick` 里）做 |
| 2 | **数组生命周期**：`makeArrayRef` 定长 | 写成「push 第 6 条」直接越界；每轮新建 → 堆抖动 | 固定 5 条（或 16 条）一次建好，之后只改字段；不 push |
| 3 | **容量与 UI 行数不一致**：数据 16 条、UI 5 行 | 用户看不到其余 11 个网络（信息缺失） | 显示「共 N 个，仅示前 5」+ 分页/换页按钮，或按信号排序取前 5 |
| 4 | **失败原因被压成一个 `wifi_state=3`** | "密码错误 / 超时 / AP 消失"都显示同一句 → 误导 | 增加 `fail_reason`（1 密码错 2 超时 3 找不到 4 认证失败）+ 文案映射表 |
| 5 | **动态文字的字库覆盖**：SSID 来自扫描，是任意 UTF-8 | GB2312 子集必然缺字（emoji、生僻字、繁体、日文 SSID）→ 豆腐 | 明确兜底：缺字替换为 `?`，或打包更大字符集；`audit_chars` 只能校验静态文案，管不到 SSID |

### P1 · 影响体验/维护

| # | 缺口 | 说明 |
|---|---|---|
| 6 | **开机恢复路径** | 已保存网络应在启动时自动连；谁发起（native）、UI 初始态怎么显示「连接中」 |
| 7 | **密码生命周期** | 明文在 textarea / Flow 变量里停留多久；连接成功后清空、日志禁打、崩溃转储不落盘 |
| 8 | **SSID 去重与标识** | 同名双频（2.4G/5G）、隐藏网络（空 SSID）、多个同名 AP：需要 BSSID 或 (auth,band,rssi) 组合才能区分 |
| 9 | **已连接网络的 RSSI 刷新** | 只在扫描时更新；连接后信号变化不反映，用户看到的是旧值 |
| 10 | **组件多实例** | `wifi_panel` 放两个实例时共享全局变量 → 状态互串；要么禁止多实例，要么变量按实例隔离 |
| 11 | **表达式能力边界** | 长 SSID 截断（是否有 substring）、int→string 格式、大小写转换：需按 Flow 函数表逐条确认，不能假设 |
| 12 | **字体打包体积** | 当前 `assets` 仅 444 B、无字体；中文全字库进 assets 会显著增大 flash，需算清预算 |
| 13 | **错误可见性** | Flow 表达式写错通常静默；需要开发期断言/日志，否则"UI 不刷新"很难定位 |

### P2 · 后续优化

- 每帧求值成本（5 行 × 十几个绑定）实测帧率；
- 主题/多语言切换；
- 平板/横屏适配（布局常量是 480×320 写死）。

## 10. 这份架构的适用边界

- **适合**：网络数固定可截断、交互以列表+表单为主、需要快速改 UI 的产品；
- **不适合**：需要无限滚动/动态建行、需要复杂动画、需要把 UI 逻辑放进多线程回调的场景；
- 一旦要"任意长度列表"，必须回到 C 侧自绘（`lv_obj_create` 循环），那就退出了本架构的收益区。

> **本变体的定位（对上一条的正面回应）**：v4 收口后列表已经在 C 侧动态建行（`widgets/wifi_list/wifi_list.cpp`），
> EEZ 只剩静态外壳——母工程 §2 的"退出收益区"这条，正是本变体把 Flow 关掉的依据
> （经验库 `P-0170` §3 第 3 条：静态控件 + 单一点击回调的页面不该为完整引擎付费）。
> 换句话说：**本变体 = 用 EEZ Studio 画界面、逻辑全在 native C**；
> 需要 Flow 收益（表达式绑定、多页导航、动效、`Switch/Watch` 编排）时回母工程形态或把两开关改回 `true`。
