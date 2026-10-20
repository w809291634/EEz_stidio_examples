# WiFi 模板架构（Flow 路线）：EEZ 为主，native 极薄

> 配套图：`design/mockups/mockup_17_flow_arch.svg`
> 相关文档：`FLOW_STRUCT_ROUTE.md`（落地清单）· `EEZ_CHECKLIST.md`（控件/变量）· `IMPLEMENTATION.md`（交互机制）

## 0. 一句话

**界面、数据模型、逻辑判断全部活在 EEZ 工程里（约 90%），经 `cli_build` 生成源码；native 只保留"取值 → 装箱 → 回写状态"的硬件适配层（约 10%），且只有 3 个文件。**

## 1. 五层结构（图中 ①→⑤）

| 层 | 内容 | 谁写 | 能否手改 |
|---|---|---|---|
| ① EEZ 工程 `.eez-project` | 页面 / 组件 / 控件树 / Struct+数组 / 绑定表达式 / 事件动作 / 样式字体 | **设计源**（`build_example.py` 生成） | 通过生成器改；GUI 手改会被覆盖 |
| ② 生成源码 `src/ui/` | `screens.c`（控件树+绑定内联）· `structs.h`（Struct/数组声明）· `vars.h`（变量访问器）· `actions.c`（事件入口）· `assets`（Flow 资源） | `cli_build` 产出 | **禁止手改**（会被覆盖） |
| ③ Flow 运行时 | `eez-flow.cpp`（**9,923 行，已生成进 src/ui**）+ `Value`/`ArrayValue`/`StructValue` + `eez_flow_init` / `eez_flow_tick` | EEZ 生成（不是外部库） | 不改；已编进二进制 |
| ④ native 薄层 | `io_iface.h`（契约）· `bridge.cpp`（C 结构体 → Flow 数组，唯一跨界点）· `io_esp/io_win/io_pc`（三后端） | **人写** | 唯一允许业务改动的地方 |
| ⑤ 硬件 | esp_wifi + NVS / Windows WLAN API / 假数据 | 平台 | — |

## 2. 三处关键边界（架构真正的"接缝"）

1. **EEZ → 生成码**：`build_example.py` 是唯一设计源；`src/ui/` 是产物。要改 UI 一律改生成器。
2. **生成码 → 运行时**：`assets` 二进制 + `eez_flow_init(assets,…)`（`ui.c:48`）+ 每帧 `eez_flow_tick()`。
   ★ 实测：本工程**已经在跑 Flow**——`eez-flow.h` 自带 `#define EEZ_FOR_LVGL 1`，`eez-flow.cpp` 9,923 行一起生成，
   编出的 `main.exe` 里有 501 个 `eez::flow` 符号。所以不是"待迁移"，而是"已就位、只缺变量与结构体内容"。
3. **native → Flow 数组（`bridge.cpp`）**：**全工程唯一跨越语言/运行时的地方**。它只做三件事：
   ```c
   // 1) 硬件回调/C 侧结构体：ap_t  s_aps[16]; int s_ap_cnt;
   // 2) 装箱：写进 Flow 数组（字段名/长度）
   // 3) 回写状态：ap_len = n; scan_state = 2（最后一步）
   ```
   它不解析布局、不管文案、不做判据——所以换后端（PC/ESP）时它一行不改。

## 3. 数据流（两条主链路）

**扫描**
```
io_esp/io_win 扫描 → s_aps[]/s_ap_cnt（C 侧，可排序/去重/平滑）
   → bridge: 清空 Flow 数组 → 逐条 push StructValue
   → ap_len = 上限内条数；scan_state = 2（最后一步）
   → UI: 行显隐 = ap_len > N，文字 = aps[N].ssid，格数由 aps[N].rssi 现算
```

**连接**
```
行点击 → pick_index = N（Flow 变量）→ pwd_open = 1（半页上滑）
   → 连接按钮 → 写 cmd_connect=1 + pwd + remember（outputs）
   → app_model 每拍排空命令环 → io_wifi_join()
   → 成功：wifi_state=2、conn_index=N；失败：wifi_state=3（UI 变红字，不清输入）
   → UI 只读这些变量，不参与任何 WiFi 调用
```

## 4. 信息全面性（Struct 层保证）

`Struct ap_info` 7 个字段覆盖 UI 全部信息需求：

| 字段 | 类型 | UI 用途 |
|---|---|---|
| `ssid` | string | 名称（超长省略） |
| `auth` | int | 加密类型 → `WPA3 / WPA2 / WPA / 开放` |
| `rssi` | int | 强度数值 + 4 格信号条点亮数 |
| `band` | int | `2.4G / 5G` |
| `lock` | bool | 锁图标 / "无需密码" |
| `saved` | bool | 「已保存」胶囊 |
| `conn` | bool | 「已连接」胶囊 + 绿色描边 |

- **空列表判据**：`ap_len == 0`（Flow 表达式无 null，长度量必须显式存在）；
- **能力上限**：数组可装 16 条（C 侧），**UI 仍显示固定 5 行**（Flow 的 LVGL 工程无 repeater）；超出时标题显示"共 N 个"；
- **派生量不上报**：格数、状态文字、显隐全部在 UI 表达式现算，避免两个真值源。

## 5. 功能稳定性（8 条机制）

| # | 机制 | 防的问题 |
|---|---|---|
| 1 | 单一真值源：数据只在 Flow 数组 | C 侧另存一份 → 不同步 |
| 2 | 先填数据再置状态（`scan_state=2` 最后写） | 半成品渲染/闪烁 |
| 3 | 命令环：UI 只写 outputs，每拍排空执行 | 重入 / UI 阻塞 |
| 4 | 状态机三值（0 空闲 / 1 进行 / 2 成功 / 3 失败） | 无反馈的"点了没反应" |
| 5 | 失败不清输入、不关半页 | 重输成本 |
| 6 | 轮询节流 1s + SetProfile 后延迟 800ms 再连（PC 实测） | 高频查询卡死认证 |
| 7 | 三后端同签名，换文件即换平台 | 平台分支污染 UI |
| 8 | 关闭弹层只改 `pwd_open`，不动 `wifi_state` | 关窗误断连接 |

## 6. 封装高级性（少即是多）

| 维度 | 扁平槽位方案 | 本方案（Flow 结构体） |
|---|---|---|
| 变量数 | 37（5 槽 × 7 + 2） | **3**（`aps` / `ap_len` / `scan_state`） |
| 绑定写法 | `ssid_3` / `rssi_3` | `aps[2].ssid` / `aps[2].rssi` |
| 行模板 | 每行 12 个控件手连 5 遍 | 同样控件，**只改下标** |
| 加字段 | 每槽 +1 变量 ×5 | Struct +1 字段，绑定处 +1 表达式 |
| 换硬件 | 改 io + 改投影 | **只改 io**（bridge 已是通用装箱） |

## 7. 目录与归属红线

```
app-wifi-connect2/
├── build_example.py          ← 设计源（人写）★ 改 UI 只改这里
├── design/cli_build.py       ← EEZ CLI + flow 守卫
├── design/mockups/*.svg      ← 设计图（生成）
├── src/ui/                   ← EEZ 生成（禁手改）
└── src/native/
    ├── app_model.cpp         ← 命令环 + 周期任务
    ├── ui_behavior.cpp       ← 键盘弹出/收起等行为接线
    └── platform/
        ├── io_iface.h        ← 契约
        ├── bridge.cpp        ← ★ 唯一跨界（C → Flow）
        └── io_{pc,win,esp}.cpp
```

**自证判据（交付前跑）**
1. `grep -rn "Wlan\|esp_wifi\|nvs_" src/ui src/native/app_model.cpp src/native/ui_behavior.cpp` → **0 命中**；
2. 换 `io_pc` / `io_win`，`src/ui/` 编译产物逐字节相同；
3. 变量面板手改 `scan_state` / `aps[0].rssi` → UI 立即响应（证明"变量即接口"）；
4. `src/ui/` 里出现手工修改 → 视为缺陷（下次生成即丢）。

## 8. 已核实 / 已推翻的结论（2026-10-20 20:55 实测）

| 原结论 | 实测 | 证据 |
|---|---|---|
| 「本工程走 `create_screens()`，没在 Flow 运行时里」 | **错**：`ui_init()` 直接调 `eez_flow_init`，`ui_tick()` 调 `eez_flow_tick` | `src/ui/ui.c:46-54`；二进制含 501 个 `eez::flow` 符号 |
| 「`ArrayValue` 内部是 `std::vector<Value>`，可变长」 | **错**：`struct ArrayValue { uint32_t arraySize; uint32_t arrayType; Value values[1]; }`，由 `Value::makeArrayRef(size, type, id)` 定长创建 | `eez-flow.h:1278-1282` |
| 「需要额外链接 `eez/flow` 库」 | **错**：`eez-flow.cpp` 由 EEZ 生成在 `src/ui/`，已在构建里 | `wc -l` = 9923；构建产物可运行 |
| 「4 个 API 名未核实，只能猜」 | **已核实**：`getGlobalVariable(uint32_t index)` / `setGlobalVariable(index, Value)` / `Value::makeArrayRef` / `value.getArray()->values[i]` | `eez-flow.h:2220-2223`、`1228`、`1155` |

**引用计数语义**（决定数组能不能反复新建）：`Value` 有 `refCounter`，`operator=` 先 `freeRef()` 再给新值 `refCounter++`；`setGlobalVariable` 就是一次赋值。**所以每轮扫描重建数组不会泄漏**，但会有分配抖动。

## 9. 架构缺口清单（当前设计没覆盖到的）

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
