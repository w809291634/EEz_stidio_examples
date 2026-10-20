# 实现映射：EEZ 里建什么 · 怎么和硬件交互

> 目标：UI 层**零硬件代码**，硬件只在 io 层；两边通过「变量表」单向传数据。
> 对应设计：`DESIGN.md`（v4 列表式 + 连接页两种形态）、`design/mockups/`（12/13 解释图）。

---

## 1. EEZ 里要创建的东西

### 1.1 页面（Screens）

| 名称 | 用途 | 尺寸 | 说明 |
|---|---|---|---|
| `scr_list` | WiFi 列表页（扫描结果） | 480×320 | 5 个**固定行槽**，不动态建对象 |
| `scr_pwd` | 连接 WiFi 页 | 480×320（整页）或 480×200（半页） | 同一套控件，两种高度 |
| `scr_host`（可选） | 宿主设置页，演示"嵌在子容器里" | 480×320 | 卡片内放 User Widget |

> 组件化：把列表页的控件组做成 **User Widget**（`wifi_panel`），既能铺满当页面，
> 也能放进任意子容器（如设置页卡片 408×176）。

### 1.2 控件（按页，全部静态、不动态创建）

**列表页 / wifi_panel（5 槽 × 7 元素）**

| 元素 | 数量 | 说明 |
|---|---|---|
| 标题 / 计数 / 刷新按钮 | 1 / 1 / 1 | 计数绑 `ap_count`；刷新 → `action_scan` |
| 组标签「已连接 · 已保存」/「可用网络」 | 2 | `hiddenFlag` 绑 `grp1_visible` |
| 行容器 `row_N` | 5 | 可点（CLICKED）、可长按（LONG_PRESSED） |
| 信号条 `bar_N_1..4` | 5×4 | 4 个 3px rect，用 `hiddenFlag` 按 `rssi_N` 点亮前几条 |
| SSID `lbl_ssid_N` | 5 | 绑 `ssid_N` |
| 副行 `lbl_meta_N` | 5 | 绑 `auth_N` + `rssi_N` + `band_N` 拼串 |
| 锁 `img_lock_N` | 5 | `hiddenFlag` 绑 `lock_N` |
| 状态 `lbl_state_N` | 5 | 绑 `status_N`（已连接/已保存/无需密码/空） |

**连接页（`scr_pwd`）**

| 元素 | 说明 |
|---|---|
| 返回 / 把手（半页用） | 返回 → `action_pwd_back` |
| SSID 标题 + 副标题 | 绑 `pick_ssid`、`pick_meta` |
| 密码框 `pwd_ta` | password 模式；CLICKED → 弹键盘 |
| 眼睛按钮 | 切明文/密文（`action_eye`） |
| 记住密码 开关 | `VALUE_CHANGED` → `action_remember`；绑 `remember` |
| 连接按钮 | CLICKED → `action_connect` |
| 忘记此网络（红字） | CLICKED → `action_forget`；`hiddenFlag` 绑 `pick_saved` |
| 键盘 `kb` | **默认 hidden**；READY / CANCEL → 隐藏 |

### 1.3 变量（Global variables）

**inputs（io 写 → UI 读，UI 只读）**

| 变量 | 类型 | 含义 |
|---|---|---|
| `scan_state` | int | 0 未扫描 / 1 扫描中 / 2 完成 |
| `wifi_state` | int | 0 未连 / 1 连接中 / 2 已连 / 3 失败 |
| `ap_count` | int | 发现数量 |
| `pick_ssid` / `pick_meta` / `pick_saved` | string/string/int | 当前选中网络 |
| `conn_ssid` | string | 已连接 SSID |
| `ssid_N` `auth_N` `rssi_N` `band_N` `lock_N` `saved_N` `conn_N` | string/int/bool… | 每槽 7 个，N=1..5（共 35 个） |
| `status_N` / `row_visible_N` / `grp1_visible` | string/bool | UI 派生值（io 里算好直接给） |

**outputs（UI 写 → io 读，命令通道）**

| 变量 | 含义 |
|---|---|
| `cmd_scan` | 1 = 请求扫描 |
| `cmd_pick` | 1..5 = 选中第 N 槽（0 = 无） |
| `cmd_connect` / `cmd_forget` / `cmd_back` | 1 = 连接 / 忘记 / 返回 |
| `pwd` | 用户输入的密码 |
| `remember` | 记住密码开关 |
| `pwd_open` | 1 = 连接页/半页展示中（方案 B 用） |

> 约定：**outputs 是"命令"，不是"状态"**。io 收到后执行硬件动作，再用
> `app_set_input_*` 把结果写进 inputs；UI 只跟着 inputs 变。

### 1.4 动作（Actions）与事件绑定

| 控件 | 事件 | EEZ Action | C 实现（`native_actions.cpp`） |
|---|---|---|---|
| 刷新 | CLICKED | `action_scan` | `app_set_output(APP_OUT_SCAN, 1)` |
| `row_N` | CLICKED | `action_pick_N` | `APP_OUT_PICK = N` |
| `row_N` | LONG_PRESSED | `action_forget_N` | `APP_OUT_FORGET = N` |
| 连接 | CLICKED | `action_connect` | 读 `pwd`/`remember` → `APP_OUT_CONNECT` |
| 返回 / 完成 | CLICKED | `action_pwd_back` | `APP_OUT_BACK = 1` |
| 忘记此网络 | CLICKED | `action_forget` | `APP_OUT_FORGET = 1` |
| 记住密码开关 | VALUE_CHANGED | `action_remember` | `APP_OUT_REMEMBER = v` |
| 密码框 | CLICKED | `action_pwd_focus` | 显示键盘（纯 UI，无 io） |
| 键盘 | READY / CANCEL | `action_kb_hide` | 隐藏键盘（纯 UI） |

> 每个 action 都必须有 C 实现——漏一个就链接失败（P-0164 坑 17，已踩）。

### 1.5 事件到硬件：一次连接的完整时序

```
用户点行  → action_pick_N  → cmd_pick=N      （out）
          → io 填 pick_ssid/pick_meta/pick_saved（in）→ 打开 scr_pwd（UI 自身切页）
用户输密码 → 点连接 → cmd_connect=1 + pwd + remember（out）
          → io: 校验/建 profile/连接（硬件）
          → wifi_state=1（in）→ UI 显示"连接中"
          → 硬件回调/轮询成功 → wifi_state=2 + conn_ssid（in）
          → UI 自动刷新：行变绿、状态"已连接"、连接页关闭
```

---

## 2. 怎么保证和硬件交互（7 条机制）

1. **单出口**：所有 WiFi/NVS 调用只出现在 `src/native/platform/io_*.cpp`。
   EEZ 生成的 UI 代码与 `native_actions.cpp` 里**不出现任何** `Wlan*` / `esp_wifi_*`。
2. **命令环解耦**：UI 事件只写 outputs（`app_set_output`），不直接调硬件；
   `user_io_loop()` 每拍调 `sample_inputs()` 排空命令再执行 → UI 不阻塞、不重入。
3. **单向数据流**：io 用 `app_set_input_*` 回写状态；EEZ 的变量绑定把控件自动刷新。
   UI 永远不"猜"状态，也不自己改 inputs。
4. **批量发布会话**：扫描结果先填满槽位变量，最后一步才 `scan_state=2`；
   UI 只在 `scan_state==2` 时读槽位 → 不会渲染到半成品数据。
5. **时间统一**：所有计时用 `lv_tick_get()`（PC / ESP 同一来源），不直接读 HAL 计时器。
6. **防卡死（PC 实测）**：`WlanQueryInterface` 轮询节流 **1s/次**（250Hz 会把接口卡在
   authenticating）；`WlanSetProfile` 后**延迟 800ms** 再 `WlanConnect`（立即连静默失败）。
7. **密码安全**：密码只在 io 内存与系统 profile/NVS 里；日志只打印长度；
   自动化测试用环境变量注入（不落盘）。

**三后端等价**：`io_pc.cpp`（假数据）/ `io_win.cpp`（Windows WLAN API）/
`io_esp.cpp`（esp_wifi + NVS）实现**同一组 `io_*` 签名**——换硬件只换一个文件，
UI 与 `app_model` 一行不改。

---

## 3. 落地顺序（每步都能验）

| 步 | 做什么 | 验证 |
|---|---|---|
| 1 | 变量表 + 静态壳（5 槽 × 7 元素 + 连接页控件） | `cli_build` 0 错误 + 截图对照 mockup_01/04 |
| 2 | 命令环 + `io_pc` 假数据（扫描→填槽→点行→切页） | 仿真跑起来：列表出现、点行能进连接页 |
| 3 | 连接页键盘弹出 + 记住/忘记 + 失败反馈 | 点密码框弹键盘；空密码连接 → "请输入密码" |
| 4 | 换 `io_win` 真 WiFi（复用 P-0164 已验证实现） | 应用日志 + `netsh wlan show interfaces` 双验证 |

> 每步跑：`python build_example.py` → `python design\cli_build.py` → `run_sim.bat`
> → 截图 + `measure_ui.py`（居中/对齐），绿了再进下一步。
