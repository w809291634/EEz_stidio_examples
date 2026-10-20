# 扫描界面：硬件怎么隔离（UI 只认变量）

> 一句话：**扫描页的 UI 只依赖 1 个状态变量 + 1 个计数 + 35 个槽位变量**，
> 它不知道 WiFi 存在、不知道是 PC 还是 ESP、不知道扫描用了 2 秒还是 8 秒。
> 硬件的一切只体现在「变量被写成什么值」。

---

## 1. 三个时刻：io 侧（唯一碰硬件的地方）

| 时刻 | 硬件侧做什么 | 写哪些变量 | UI 立即发生什么 |
|---|---|---|---|
| ① 开始 | `WlanScan` / `esp_wifi_scan_start` / 假数据定时器 | `scan_state = 1` | 列表隐、骨架显、按钮变"扫描中"且不可点 |
| ② 结果到达 | 读回 AP 列表（异步回调或轮询） | 35 个槽位变量（`ssid_N … conn_N`）**逐个填** | **看不到任何变化**（骨架盖着） |
| ③ 发布完成 | 无 | `ap_count = N`，**最后**`scan_state = 2` | 骨架隐，按槽位一次性显示 N 行（或空态） |

**关键**：② 写槽位时 UI 不可见（被骨架遮住），所以不需要双缓冲、不需要锁，
也不会出现"行文字先变、信号条后到"的半成品闪烁 —— 这是"先骨架后列表"的真正价值。

---

## 2. 三态：一个变量决定，UI 侧零分支代码

`scan_state` 只有三个值，UI 用 **hiddenFlag 表达式** 分流（不是 C 代码）：

| scan_state | 列表 `list` | 骨架 `skel` | 空态 `empty` | 按钮文字 / 可点 |
|---|---|---|---|---|
| 0 空闲 | 隐 | 隐 | 隐（显示"点击刷新"提示） | "刷新" / 可点 |
| 1 扫描中 | **隐** | **显** | 隐 | "扫描中" / **不可点** |
| 2 完成且 `ap_count>0` | **显** | 隐 | 隐 | "刷新" / 可点 |
| 2 完成且 `ap_count==0` | 隐 | 隐 | **显** | "刷新" / 可点 |

对应表达式（照抄）：

| 控件 | hiddenFlag |
|---|---|
| `list` | `!(scan_state == 2 && ap_count > 0)` |
| `skel`（4 行骨架组） | `scan_state != 1` |
| `empty`（图标+文案+重扫按钮） | `!(scan_state == 2 && ap_count == 0)` |
| `lbl_hint`（空闲提示） | `scan_state != 0` |
| 刷新按钮文字 | `scan_state == 1 ? "扫描中" : "刷新"` |
| 刷新按钮可点 | `clickableFlag = scan_state != 1`（防重复触发扫描） |

---

## 3. 逐控件绑定（扫描界面 37 个变量全覆盖）

### 3.1 头部

| 控件 | 绑定 |
|---|---|
| `lbl_title` "WiFi" | 静态 |
| `lbl_count` | `scan_state == 0 ? "点击刷新开始扫描" : scan_state == 1 ? "正在扫描…" : "已发现 " + ap_count + " 个网络"` |
| `btn_refresh` 文字 | `scan_state == 1 ? "扫描中" : "刷新"` |
| `btn_refresh` 可点 | `scan_state != 1` |

### 3.2 每行（N = 1..5）

| 控件 | 绑定 | 硬件侧只需 |
|---|---|---|
| `row_N` 显隐 | `ssid_N == ""` → hidden | 空槽把 `ssid_N` 写 `""` |
| `lbl_ssid_N` | `ssid_N` | 原始 SSID 字符串 |
| `lbl_meta_N` | `auth_N + " · " + rssi_N + "dBm · " + band_N` | 认证类型、RSSI、频段（三个原始量） |
| `bar_N_1..4` 显隐 | `rssi_N < TH[k]` → hidden，TH = `-85,-75,-65,-55` | **只上报 rssi**，格数由 UI 算 |
| `img_lock_N` 显隐 | `lock_N == 0` | 是否需要密码（bool） |
| `pill_conn_N` | `conn_N == 0` → hidden | 是否已连接（bool） |
| `pill_saved_N` | `saved_N == 0` → hidden | 是否已保存（bool） |
| `lbl_open_N` "无需密码" | `lock_N` → hidden（有锁才隐藏） | 同上 |
| 行描边绿色 | `conn_N`（条件样式或直接绑前景色） | 同上 |

> **派生量一个都不上报**：信号格数、状态文字、"无需密码"、绿色描边，全部 UI 侧由
> `rssi_N / lock_N / saved_N / conn_N` 现算。硬件只报 7 个原始量 —— 契约面最小，
> 也避免"两个真值源不一致"（`reference/10_hw_ui_separation` §4.3）。

---

## 4. 代码形状（三后端完全一致）

```c
/* ① 开始扫描：只写一个变量，然后调平台 API 或起假数据定时器 */
void io_scan_start(void)
{
    app_set_input_i(APP_IN_SCAN_STATE, 1);     /* UI 立刻切骨架 */
    /* platform: WlanScan / esp_wifi_scan_start / 仿真: 定时 2s 后调 publish() */
}

/* ② + ③ 结果发布：先填槽位，最后才置 2 */
static void publish(const ap_t *aps, int n)
{
    if (n > 5) n = 5;                          /* 槽位上限，多的丢掉并在 ap_count 里保留真值 */
    for (int i = 0; i < 5; i++) {
        int on = (i < n);
        app_set_input_s(kSsidId[i], on ? aps[i].ssid : "");
        app_set_input_s(kAuthId[i], on ? auth_str(aps[i].auth) : "");
        app_set_input_i(kRssiId[i], on ? aps[i].rssi : -100);
        app_set_input_s(kBandId[i], on ? aps[i].band : "");
        app_set_input_b(kLockId[i],  on && aps[i].lock);
        app_set_input_b(kSavedId[i], on && aps[i].saved);
        app_set_input_b(kConnId[i],  on && aps[i].conn);
    }
    app_set_input_i(APP_IN_AP_COUNT, n);
    app_set_input_i(APP_IN_SCAN_STATE, 2);      /* 最后一步 = 一次性显示 */
}
```

```c
/* 槽位 id 走「一张表」，不写 APP_IN_SSID_1 + i —— 中途插入新 id 会整体错位 */
static const app_id_t kSsidId[5] = { APP_IN_SSID_1, ..., APP_IN_SSID_5 };
/* kAuthId / kRssiId / kBandId / kLockId / kSavedId / kConnId 同理 */
```

`io_pc.cpp` 的假数据版就是把 `publish()` 用定时器调一次，签名字节相同 ——
**换真机时只换这一个文件，`src/ui/` 一行不动**。

---

## 5. 怎么自证"真的分离了"（4 条硬判据）

1. **grep 判据**：`grep -rn "Wlan\|esp_wifi\|nvs_" src/ui src/native/native_*.cpp` **必须 0 命中**
   —— 硬件符号只出现在 `platform/io_*.cpp`。
2. **变量面板判据**：在 EEZ 里把 `scan_state` 手改成 1 或 2、把 `rssi_N` 改成 -90，
   UI 必须**立刻**变骨架 / 变列表 / 信号条减格，而不需要任何硬件动作。
3. **后端替换判据**：`io_pc.cpp` ↔ `io_win.cpp` 互换，`src/ui/` 编译产物**逐字节相同**。
4. **契约面判据**：扫描界面用到的输入变量恰好 = 37 个（2 + 35），多一个就说明
   有派生量被塞进了契约（§3 表里已经算过）。

---

## 6. 扫描特有的 4 个坑（都在这层解决）

| 坑 | 表现 | 解法 |
|---|---|---|
| 扫描中直接写槽位 | 行文字/图标分几次冒出，闪烁 | 骨架盖住列表（§1 ②），最后一步才 `scan_state=2` |
| 清空方式不一致 | 上次 5 个这次 3 个，残留 2 行 | 每次**全量重写 5 槽**，空槽写 `""` / `-100` / false |
| `ap_count` 与槽位不符 | 显示"6 个网络"但只看到 5 行 | `ap_count` 报真实总数，槽位上限 5（或把标题写成"共 N 个，显示前 5"） |
| 按 `id + i` 遍历槽位 | 中途插 id 后串行错位 | 用 `kSsidId[]` 这类**显式表** |
