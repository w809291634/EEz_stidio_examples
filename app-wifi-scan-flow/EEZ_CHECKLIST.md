# EEZ 里要创建的控件与变量（照抄清单）

> 坐标基于 480×320。**控件全部静态**（不动态建对象），共 **84 个控件 / 51 个变量**。
> 槽位类全部 `for N in 1..5` 循环生成 —— 别在 EEZ GUI 里手点 5 遍。

---

## 1. 控件总览

| 屏 / 组件 | 控件数 | 说明 |
|---|---|---|
| `scr_host`（宿主设置页） | 17 | 卡片 + 组件实例 + **overlay_root（遮罩 + 半页）** |
| `wifi_panel`（User Widget） | 67 | 列表容器 + 5 槽 × 12 元素 |
| **合计** | **84** | |

层级（z 序从上到下）：

```
scr_host
├── lbl_host_title / lbl_host_sub
├── card
│   ├── lbl_card_wifi / lbl_card_manage
│   └── wifi_panel            ← 424×192（组件实例）
└── overlay_root              ← 全屏，hidden = !pwd_open
    ├── scrim                 ← 全屏 45% 黑，点它关闭
    └── sheet                 ← 480×224，贴底
        ├── sheet_handle / lbl_sheet_ssid / lbl_sheet_err / btn_close
        ├── ta_pwd / btn_connect
        └── kb_pwd            ← 464×132，随半页一起出现
```

---

## 2. scr_host 控件表（17）

| # | 名称 | 类型 | x, y, w, h | 关键属性 / 绑定 |
|---|---|---|---|---|
| 1 | `root_host` | LVGLScreenWidget | 0, 0, 480, 320 | bg `#0B0F1A` |
| 2 | `lbl_host_title` | LVGLLabelWidget | 20, 22, 140, 28 | "设置" 17px |
| 3 | `lbl_host_sub` | LVGLLabelWidget | 20, 52, 180, 16 | "网络与连接" 11px `#5C6A85` |
| 4 | `card` | LVGLContainerWidget | 20, 56, 440, 238 | bg `#0D1420` r12；**CLICKABLE 关** |
| 5 | `lbl_card_wifi` | LVGLLabelWidget | 36, 72, 80, 18 | "WiFi" 11px `#5C6A85` |
| 6 | `lbl_card_manage` | LVGLLabelWidget | 380, 72, 64, 18 | "管理" 10px，右对齐 |
| 7 | `wifi_panel` | **UserWidget 实例** | 28, 86, 424, 192 | 见 §4 |
| 8 | `overlay_root` | LVGLContainerWidget | 0, 0, 480, 320 | 透明；`hiddenFlag = pwd_open == 0`；CLICKABLE 关 |
| 9 | `scrim` | LVGLContainerWidget | 0, 0, 480, 320 | bg `#000` opacity 45%；CLICKED → `action_sheet_close` |
| 10 | `sheet` | LVGLContainerWidget | 0, 96, 480, 224 | bg `#101A28`；上圆角 12；CLICKABLE 关 |
| 11 | `sheet_handle` | LVGLContainerWidget | 224, 102, 32, 3 | r1.5 `#2C3852` |
| 12 | `lbl_sheet_ssid` | LVGLLabelWidget | 16, 108, 200, 20 | 13px；text = `pick_ssid` |
| 13 | `lbl_sheet_err` | LVGLLabelWidget | 16, 108, 200, 20 | 12px `#E06A6A` "密码错误，请重试"；`hiddenFlag = pwd_err == 0` |
| 14 | `btn_close` | LVGLButtonWidget | 432, 106, 32, 24 | "×"；CLICKED → `action_sheet_close` |
| 15 | `ta_pwd` | LVGLTextareaWidget | 16, 132, 364, 36 | one-line；**password 模式**；placeholder "请输入密码" |
| 16 | `btn_connect` | LVGLButtonWidget | 388, 132, 76, 36 | 子 label text = `wifi_state == 1 ? "连接中…" : "连 接"`；CLICKED → `action_connect` |
| 17 | `kb_pwd` | LVGLKeyboardWidget | 8, 176, 464, 132 | mode `TEXT_LOWER`；textarea = `ta_pwd`；key 高 30 |

> 半页内在 sheet 坐标系里的纵向预算：把手 6 + 标题 12..30 + 输入行 36..72 + 键盘 80..212（共 224）。

---

## 3. 变量清单（51）

### 3.1 inputs（io 写 → UI 读，共 42）

| 名称 | 类型 | 默认 | 绑定到 |
|---|---|---|---|
| `scan_state` | int | 0 | 刷新按钮/提示文案（0 空闲 / 1 扫描中 / 2 完成） |
| `wifi_state` | int | 0 | `btn_connect` 文字（1=连接中）；行连接态由 `conn_N` 决定 |
| `ap_count` | int | 0 | 卡片标题旁"共 N 个"（可选） |
| `pick_ssid` | string | "" | `lbl_sheet_ssid` |
| `pick_meta` | string | "" | 半页副标题（可选） |
| `pick_saved` | bool | 0 | 「忘记」入口显隐（长按菜单用） |
| `conn_ssid` | string | "" | 宿主页状态文字（可选） |
| `ssid_N` | string | "" | `lbl_ssid_N`；空串 → 整行隐藏 |
| `auth_N` | string | "" | `lbl_meta_N`（WPA3 / WPA2 / 开放网络） |
| `rssi_N` | int | -100 | `lbl_meta_N` 数值 + 4 根信号条显隐 |
| `band_N` | string | "" | `lbl_meta_N`（5 GHz / 2.4 GHz） |
| `lock_N` | bool | 0 | `img_lock_N` 显隐；`lbl_open_N` 反向显隐 |
| `saved_N` | bool | 0 | `pill_saved_N` 显隐 |
| `conn_N` | bool | 0 | `pill_conn_N` 显隐 + 行描边 |

> `N = 1..5`；`ssid_N … conn_N` 每组 5 个，共 35 个。

### 3.2 outputs（UI 写 → io 读，共 7）

| 名称 | 类型 | 默认 | 写入点 |
|---|---|---|---|
| `cmd_scan` | int | 0 | 刷新按钮（值恒 1，收到即执行） |
| `cmd_pick` | int | 0 | `row_N` CLICKED → N（**同时** `pwd_open=1`） |
| `cmd_connect` | int | 0 | `btn_connect` |
| `cmd_forget` | int | 0 | 长按 `row_N` → 确认后 N |
| `cmd_back` | int | 0 | 返回/关闭半页（也可只用 pwd_open） |
| `pwd` | string | "" | `ta_pwd`（连接时读一次） |
| `remember` | bool | 0 | 记住密码开关（当前半页没放，留接口） |

### 3.3 UI 状态（native output，只存不发命令，共 2）

| 名称 | 类型 | 默认 | 用途 |
|---|---|---|---|
| `pwd_open` | int | 0 | `overlay_root` 的 hiddenFlag |
| `pwd_err` | int | 0 | `lbl_sheet_err` 的 hiddenFlag（io 在 `wifi_state=3` 时置 1） |

> 这两个**不要**走 io 命令环：它们只是 UI 状态，io 侧看到即忽略。
> 派生量（状态文字/行显隐/信号格数）**不建变量**，见 §5。

---

## 4. wifi_panel 组件控件表（67）

根：`panel_root`（Container 424×192，透明）＋ `list`（Container 424×192，pad 12，`scroll_dir=VER`，CLICKABLE 关）。

**每槽 12 个元素**，槽位 `N`，行顶 `y = 12 + (N-1)×50`（行高 44 + 间距 6）：

| # | 名称 | 类型 | 相对行坐标 | 属性 / 绑定 |
|---|---|---|---|---|
| a | `row_N` | Container | 12, y, 400, 44 | r10 bg `#101A28`；**CLICKABLE 开**；CLICKED → pick_N；LONG_PRESSED → forget_N |
| b | `bar_N_1..4` | Container ×4 | 10+b×6, y+30-h, 3, h | h = 5/8/11/14；bg 蓝（连接行用绿） |
| c | `lbl_ssid_N` | Label | 30, +6, 210, 20 | 14px；text = `ssid_N` |
| d | `lbl_meta_N` | Label | 30, +25, 200, 14 | 11px `#8A99B3`；表达式见 §5 |
| e | `img_lock_N` | Image | 326, +18, 10, 8 | `lock.png`；`hiddenFlag = lock_N == 0` |
| f | `pill_conn_N` | Container | 344, +13, 52, 17 | r9 bg `#0E2A22` 描边绿；`hiddenFlag = conn_N == 0` |
| g | `lbl_conn_N` | Label | 356, +15, 40, 14 | 10px `#3DDC97` "已连接" |
| h | `pill_saved_N` | Container | 350, +13, 46, 17 | r9 bg `#16203A` 描边蓝；`hiddenFlag = saved_N == 0` |
| i | `lbl_saved_N` | Label | 356, +15, 38, 14 | 10px `#9DB8FF` "已保存" |
| j | `lbl_open_N` | Label | 320, +13, 76, 17 | 10px `#5C6A85` "无需密码" 右对齐；`hiddenFlag = lock_N` |

> 状态位用**三个互斥元素 + hiddenFlag**，不用 conditionalStyles 换色——少一层绑定技巧，
> 出问题一眼能看出来。想省控件可换成「1 个 pill + 1 个 label + 条件样式」，但会多一处
> 表达式依赖（5 槽 ×1 处），不推荐。

---

## 5. 表达式速查（派生量现算，不建变量）

| 用途 | 表达式 |
|---|---|
| 行显隐 | `ssid_N == ""` → hidden |
| 状态文字 | `conn_N ? "已连接" : saved_N ? "已保存" : ""` |
| 信号条 k 显隐 | `rssi_N < TH[k]` → hidden；TH = `-85, -75, -65, -55`（k=1..4） |
| 副行文本 | `auth_N + " · " + rssi_N + "dBm · " + band_N` |
| 半页显隐 | `pwd_open == 0` → hidden |
| 错误行显隐 | `pwd_err == 0` → hidden |
| 连接按钮文字 | `wifi_state == 1 ? "连接中…" : "连 接"` |
| 按钮防重复点 | `clickableFlag = wifi_state != 1` |

---

## 6. 创建顺序（照这个顺序不会漏）

1. **变量**：42 inputs + 7 outputs + 2 UI 状态（脚本循环生成槽位）；
2. **图标资源**：`lock.png`（10×8 白）；
3. **`wifi_panel` 组件**：`list` → 5 个 `row_N` → 每行 12 元素；
4. **`scr_host`**：标题 / 卡片 / `wifi_panel` 实例；
5. **overlay**：`overlay_root` → `scrim` → `sheet` → 输入行 → `kb_pwd`；
6. **绑定**：hiddenFlag + text 表达式（§5）；
7. **事件**：7 个 action + 5 个 `pick_N` + 5 个 `forget_N`（共 17 个 C 函数，缺一个就链接失败）；
8. `build_example.py` → `cli_build.py`（0 flow 错误）→ `run_sim.bat` → 截图核对。
