# 实现映射：EEZ 里建什么 · 怎么和硬件交互

> **⚠ 本目录是 `app-wifi-scan-flow` 的 no-flow 变体**（`flowSupport=false`）。本文继承母工程，
> §7 已按双口径改写（Flow 版事实 / 本变体事实并列）。**通则**：本文凡写「变量表 / 表达式绑定 /
> `get_var_*`·`set_var_*` / 结构体数组 / Flow 运行时」的能力，本变体**一概没有**——
> EEZ 只出静态控件树，状态走 native `app_model` 契约 + `wifi_ui_sync` 直写控件。
> 需要这些能力时回母工程形态（或把两个开关改回 `true`）。

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
> 也能放进任意子容器（如设置页卡片 424×192，紧凑场景 408×176）。

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
| `pwd_open` | int | 1 = 半页/连接页展示中（UI 写，io 只读） |

> ★ **派生量不建变量**（`status_N` / `row_visible_N` 已删除）：状态文字、是否显示、信号点亮格数，全部在 EEZ 里用**表达式**从 `conn_N / saved_N / lock_N / rssi_N` 现算——两个真值源必然不一致（`reference/10_hw_ui_separation` §4.3）。

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

---

## 7. 结构体 / 数组：两条路线

> **路线 A（Flow）**：结构体 + 数组变量，绑定写 `aps[i].ssid`，变量数 37→3，
> 但要换运行时（`EEZ_FOR_LVGL` + eez-flow + assets）。落地清单见母工程
> **`../app-wifi-scan-flow/FLOW_STRUCT_ROUTE.md`**（本变体已删该文件——没有 Flow 就没有这条路）。
>
> **路线 B（本工程当前）**：EEZ 只有扁平标量，结构体留在 C 侧再投影。见下文 §7.4。
> ★ **本变体连路线 A 的前提都没有**（无 Flow ⇒ 无 `Value`/`ArrayValue`/结构体数组），
>   实际形态比 B 更彻底：**EEZ 零变量**，数据只在 io 静态数组，`wifi_ui_sync` 直读直画。
>
> 下面 §7.1 / §7.2 是「为什么默认走 B」的证据与代价，仍然有效。

### 7.1 事实核查（母工程 2026-10-20 · 本变体 2026-10-21 复测）

| 证据 | 结论 |
|---|---|
| 工程 JSON：`variables.structures` 字段存在（当前为空） | EEZ **有**结构体/数组类型（两变体同：字段在、值为空） |
| `settings.general.flowSupport` | **Flow 版 = `true`（已开启）；本变体 = `false`（关掉）** —— 同一个开关决定下面三行的真假 |
| 生成模板 `structs.h`：`#if defined(EEZ_FOR_LVGL)` + `#include <eez/flow/flow.h>` + `${FLOW_STRUCTS}` / `${FLOW_STRUCT_VALUES}` | 结构体声明**只生成在 `EEZ_FOR_LVGL` 分支**（两变体的模板都留着这两分支，本变体走 `#else`） |
| 实测 `src/ui/ui.c`：`ui_init()` 直接 `eez_flow_init(assets,…)`，`ui_tick()` 调 `eez_flow_tick()` | **Flow 版事实**（`ui.c:57`/`:61`，`assets[588]` 在 `:8`） |
| 「本工程 PC 仿真走 `tick_screen(g_currentScreen)`，所以我们**不在** Flow 运行时里」 | **错，两变体都别抄这句**：`g_currentScreen` 是 `EEZ_FOR_LVGL` 分支里的东西，`ui_init()` 已调 `eez_flow_init`。<br>**本变体事实**：`ui_init() = create_screens() + loadScreen()`，`ui_tick() = tick_screen(currentScreen)`，走的是模板 `#else` 分支，且 `src/ui/` 无 `eez-flow.cpp/h` |
| `reference/02_styles_fonts_vars.md` §P8.2.2 / §P8.2.5 | 「结构体/数组只能用于**启用了 EEZ Flow** 的项目」——本变体因此**永远拿不到** `aps[i].ssid` 这类写法 |

**结论**：在「生成 C 代码 + `get_var_*`/`set_var_*` 桥接」这条路上，EEZ 只有
`int / bool / string` 三种 native 标量，**没有结构体和数组**。要用 `aps[i].ssid`
这种写法，必须切到 **Flow 运行时**（`EEZ_FOR_LVGL`：assets 二进制 + `eez/flow` 库 +
`eez_flow_init/eez_flow_tick`）。

> **v4 收口（2026-10-21）**：本工程**最终未采用** Flow 运行时——EEZ 不持有任何变量，
> `native_vars.*` 已删除，状态由 native 经 `app_model` 契约直驱、列表直读 io 接口。
> 上段结论描述的是 EEZ 的**能力边界**（native 标量只有 int/bool/string），非本工程现状。

### 7.2 切 Flow 要付的代价

| 代价 | 说明 |
|---|---|
| 换执行模型 | **Flow 版：已就位**（`ui_init()` 就是 `eez_flow_init`）；**本变体：反着来**——执行模型已经退回纯 LVGL（`create_screens()`），要用 Flow 得把 `flowSupport`/`generateSourceCodeForEezFramework` 改回 `true` 并重新出码 |
| 换变量桥 | C 侧不能再用 `set_var_*`，要走 Flow 全局变量 API；`io_*` 全部要改 |
| 多一份运行时依赖 | 链接 `eez/flow`；PC_SIM 的 CMake 要额外集成（当前只链 lvgl + 源码） |
| 工具链打回原形 | `cli_build` 的 flow 守卫、`audit_chars`、`measure_ui`、check_project 全部围绕「生成 C 代码」建立 |
| 每帧求值成本 | Flow 表达式求值 + 数组成员访问，比标量绑定重（需实测帧率） |
| **仍然不是"任意长度列表"** | 结构体是静态类型、数组长度固定；运行时不能扩容 —— 等价于 N 槽，只是写法好看 |

### 7.3 "列表为空" 这件事也要一个变量

EEZ 表达式**没有 null / 空数组判断**，无论走哪条路都得有一个显式长度量：

- 扁平方案：`ap_count == 0`（或每行 `ssid_N == ""`）
- 结构体方案：`ap_len == 0`（数组本身不带 length 语义）

### 7.4 采用的方案：结构体留在 C 侧，EEZ 只收「投影」

> **v4 收口（2026-10-21）：本节为 v1→v3 采用的「投影到 5 扁平槽位」方案，已被废弃。
> 当前工程改为 native 直读 io 接口画列表，EEZ 不持有任何变量，`app_set_input_b` /
> `APP_IN_AP_COUNT` / `APP_IN_REMEMBER` 均已删除。仅作机制演进参考。**

```c
/* 契约层（C 侧，任意长度、可排序/去重/平滑） */
typedef struct { char ssid[33]; int auth; int rssi; bool lock, saved, conn; } ap_t;
static ap_t  s_aps[16];
static int   s_ap_cnt;

/* 投影：C 结构体 → EEZ 的 5 个扁平槽位（唯一跨界的地方） */
static void publish_to_vars(void)
{
    int shown = s_ap_cnt > 5 ? 5 : s_ap_cnt;
    for (int i = 0; i < 5; i++) {
        bool on = i < shown;
        app_set_input_s(kSsidId[i], on ? s_aps[i].ssid : "");
        app_set_input_i(kRssiId[i], on ? s_aps[i].rssi : -100);
        app_set_input_b(kLockId[i],  on && s_aps[i].lock);
        /* …auth/band/saved/conn 同理，全部走 §6 的显式表 */
    }
    app_set_input_i(APP_IN_AP_COUNT, shown);   /* 0 → UI 显示空态 */
    app_set_input_i(APP_IN_SCAN_STATE, 2);
}
```

**好处**：C 侧拿到完整能力（16 个 AP、排序、平滑、去重），EEZ 侧仍是纯标量绑定，
零 Flow 依赖、零工具链改动；超出 5 个时 `ap_count` 仍报真实数量（标题可写"共 N 个"）。

---

## 8. 密码链路：怎么下去、怎么上来（配 `mockup_19_password_flow`）

### 8.1 下行（UI → 硬件）

| 步 | 动作 | 代码归属 |
|---|---|---|
| 1 | 键盘输入进 `ta_pwd`（`password_mode`、`maxlength=63`） | EEZ 控件 |
| 2 | 点「连接」→ 生成事件 → `action_connect()` | `screens.c` 生成，函数你写 |
| 3 | **命令槽单份拷贝**（≤64B）+ `cmd_connect=1` | native |
| 4 | 同拍 drain：校验 8–63；不合规 → `fail_reason=5`，**不调硬件** | native |
| 5 | `io_wifi_join(slot.pwd, remember)` → `esp_wifi_set_config` + `esp_wifi_connect`（异步） | native → 驱动 |
| 6 | 返回后立即 `memset(slot, 0, …)` | native |

```c
/* 命令槽：单槽单写者，只活一帧 */
static struct { int cmd; char pwd[64]; bool remember; } s_slot;

void action_connect(lv_event_t *e) {          /* UI 任务 */
    const char *p = lv_textarea_get_text(objects.ta_pwd);
    size_t n = strlen(p);
    s_slot.cmd = CMD_CONNECT; s_slot.remember = app_get_input_b(APP_IN_REMEMBER);
    memcpy(s_slot.pwd, p, n < 63 ? n : 63); s_slot.pwd[63] = 0;
    if (n < 8) io_publish_fail(5);            /* 本地拦，不碰硬件 */
}

void app_model_poll(void) {                   /* 同一 UI 任务，每拍 */
    if (s_slot.cmd == CMD_CONNECT) {
        s_slot.cmd = 0;
        io_wifi_join(s_slot.pwd, s_slot.remember);
        memset(s_slot.pwd, 0, sizeof(s_slot.pwd));   /* 成功/失败都清 */
    }
}
```

### 8.2 上行（驱动 → UI）

```c
/* 驱动任务（esp_wifi 事件回调）：只写结果，绝不碰 LVGL/Flow */
static volatile struct { int state; int reason; } g_res;
case WIFI_EVENT_STA_DISCONNECTED: g_res.state = 3; g_res.reason = info->reason; break;
case WIFI_EVENT_STA_CONNECTED:    g_res.state = 2; g_res.reason = 0;         break;

/* UI 任务：pump 读走并发布变量 */
app_set_input_i(IN_WIFI_STATE, g_res.state);
app_set_input_i(IN_FAIL_REASON, g_res.reason);
```

- 成功（`state=2`）：`pwd_open=0` 收起半页、`conn_index=N` 行变「已连接」、清空 `ta_pwd`；
- 失败（`state=3`）：半页不关、按钮恢复可点、`ta_pwd` **保留**供重试（只有连接成功才清）；
- 进行中（`state=1`）：按钮禁用并显示「连接中…」，防重复投递。

### 8.3 reason → 文案（UI 侧，不在 C 里写中文）

| reason | 含义 | 文案 |
|---|---|---|
| 15 | 四次握手超时（密码错） | 密码错误，请重新输入 |
| 201 | 扫描不到 AP | 网络已消失，请重新扫描 |
| 205 / 2 / 3 | 连接失败 / 认证过期 | 连接超时，可重试 |
| 5（本地） | 长度不在 8–63 | 密码需 8–63 位 |

> 文案留在 EEZ（`lbl_sheet_err` 的表达式按 `fail_reason` 分支），native 只给数字——
> 这样换语言不用改 C。若表达式分支太深，退化为 C 发布 `fail_text` 字符串也行，但只选一种。

### 8.4 四条纪律

1. 密码**不进 Flow 变量**（会长期驻留堆、可能进快照）；
2. 日志**只打长度**，任何路径都不打明文；
3. **失败路径也要清零**临时缓冲（`memset` 放 `io_wifi_join` 返回后，不放在成功分支里）；
4. 只有 `remember=1` 才落盘（ESP 写 NVS；PC 写 WLAN profile）。
   平台差异：Windows 的 temporary profile 不稳，`remember=0` 也需要先建 profile 再删。
