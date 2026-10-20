# app-wifi-connect — WiFi 扫描/连接全流程（v3：链表渲染版）

> **v3 变更（响应用户需求"扫描结果用链表表达"）**：扫描结果不再走 4 个槽位变量，
> 改为 **io 层维护真链表（wifi_ap）+ C 渲染行**（wifi_ui_sync，retry-until-success）。
> EEZ 侧进一步收敛：变量 26→6、动作 9→4、控件树里不再有列表行（只剩空容器 list_box）。
> 其余架构（契约头/命令环/变量桥/平台分界）与 v2 相同，蓝本仍为 KB 10 号文档。

# 前版标题：v2 —— KB 10 号"硬件⇄UI 分离"架构迷你版

> 蓝本：`lvgl_demo_ai/eez-test` 真机工程（KB `reference/10_hw_ui_separation.md`）。
> v1 的教训：26 个槽位变量 + 动作里写业务，是"动态数据硬套固定变量集"的反模式。
> **v2 分层**：EEZ 只画静态壳和标量状态绑定；动态列表和业务逻辑全在 C（native 层）。

## 架构（三层 + 三通道）

```
EEZ（Studio 里画）：页面骨架 + 空状态绑定（6 个 native 变量）+ 密码面板/键盘
native（C，src/native/）：
  app_model.h/.cpp    契约头：APP_IN_* 输入状态数组（每 id 独立缓冲）+
                      APP_OUT_* 命令环（16 深度）+ user_io_init/user_io_tick
  native_vars.cpp     变量桥：get_var_* 从契约状态读（extern "C" ★必加）
  native_actions.cpp  动作：函数体只有一行 app_set_output 投递（铁律）
  platform/io_iface.h 薄接口（唯一提及"硬件"的文件）
  platform/io_pc.cpp  PC 假 WiFi 驱动：scan 2s 出 4 AP / join 2s 连上 / 记住密码
  platform/io_esp.cpp 真机骨架（TODO：esp_wifi/NVS；PC 构建自动排除）
数据流：UI 事件 → action 投递 APP_OUT → user_io_tick 排空 → io_* 执行 →
        io_sample_inputs 发布 APP_IN → EEZ 表达式自动刷新
```

**三条通道选型**（KB 10 §3）：扫描/连接/取消 = A 动作（一次性命令，不声明变量）；
wifi_state/conn_ssid = C 输入变量（状态回显）；本例无 B 连续量。
**动态列表**：4 个槽位变量渲染（C 填槽，真机 AP 多于 4 就分页）；
行数真无限的扩展路径 = C 直接渲染（app-list-scroll 右列模式）。

## EEZ 侧留了什么（6 变量 + 7 动作）

| EEZ 变量（native:true） | C 桥 | 用途 |
|---|---|---|
| scan_state / wifi_state / ap_count / conn_ssid | get_var 从契约状态读 | 状态标签三元表达式 |
| pick_ssid | 同上 | 选中行 SSID（面板 hiddenFlag = `pick_ssid == ''`） |
| g_remember | 同上 | 记住密码标签 |
| （槽位变量已移除） | — | 列表行由 C 渲染：io 层链表 wifi_ap（ssid/rssi/lock/connected/next）经 wifi_ap_first() 遍历，wifi_ui_sync 重建行，行内字体/徽标/点击回调全在 C |

| 动作（native 实现） | 函数体 |
|---|---|
| scan_start | `app_set_output(APP_OUT_WIFI_SCAN, 1)` |
| wifi_pick_0..3 | `app_set_input_s(APP_IN_PICK_SSID, slotN_ssid)` |
| wifi_connect | 捕获密码 `APP_IN_PWD`（textarea）+ 投递 `APP_OUT_WIFI_JOIN` |
| panel_cancel / chk_remember | 清 pick_ssid / 投递 REMEMBER_TOGGLE |

## 目录结构

```
app-wifi-connect/
├── build_example.py            ← EEZ 工程生成器（UI 壳 + 变量/动作声明）
├── design/cli_build.py         ← EEZ CLI（支持 argv 指定工程文件）
├── design/audit_chars.py       ← 逐字审计（文案 vs 字体字符集）
├── design/gen_font.py          ← 烘 cn14 中文字体（CLI 构建后跑）
├── fonts/simhei.ttf            ← 全量黑体（EEZ 提取字形用，别用子集 TTF）
│                                  ★ 字符集 = GB2312 符号区+一二级汉字 7445 字形
├── src/native/                 ← ★ 业务层（人写，PC/真机共用）
│   ├── app_model.h/.cpp        ← 契约头 + 状态 + 命令环 + lifecycle
│   ├── native_vars.h/.cpp      ← 变量桥 6 个（extern "C" ★必加）
│   ├── native_actions.cpp      ← 动作投递 4 个（含 textarea 密码捕获）
│   ├── wifi_ui_sync.h/.cpp     ← ★ 链表渲染：gen 变化时重建 list_box 行
│   │                              （行点击回调按索引回链表查节点置 PICK_SSID）
│   └── platform/               ← io_iface.h(wifi_ap 链表+遍历入口) +
│                                  io_pc.cpp(假驱动) + io_esp.cpp(TODO)
├── src/ui/                     ← EEZ 生成产物（只读）+ fonts/ui_font_cn14.c
└── design/sim_cmake/main.c     ← 瘦 main：lv_init/hal/ui_init/user_io_init
                                   + 循环(handler→ui_tick→user_io_tick) + 自动演示
```

## 构建与验收（顺序敏感）

```
python build_example.py && python design/cli_build.py
python design/audit_chars.py     && python design/gen_font.py
双击 design\sim_cmake\run_sim.bat   （新建 native 文件后删 build_rel 重配）
```

自动演示日志（`[IO]`/`[UI]`/`[STATE]`/`[TAP]`/`[DEMO]` 全程可断言）：
`scan start` → `scan done: 4 APs (linked list)` → `[UI] list rebuilt: 4 rows (gen=1)` →
`[TAP]` → `pick='Office-2G'` → `join pwd=''` → `wifi=1` → `[IO] connected` →
`[UI] list rebuilt (gen=2)`（已连接徽标更新）→ `[DEMO] done`。

## 踩过的坑（v2 重构新增）

1. **★ native 层头文件的注释里别写 `xxx_*/yyy_*`**：注释里的 `*/` 会提前闭合
   注释，后面中文注释全变成"代码"→ `extended character 。 is not valid in an
   identifier` 一串错（app_model.h 实翻车）。
2. **★ native_vars.h 必须包 `extern "C"`**：漏了 → 变量桥导出 C++ 修饰名，
   main.c(C) 链接报 `undefined reference to get_var_xxx`（nm 看 obj 一眼定位）。
3. **★ io 平台层不依赖 LVGL**：计时用 `clock()`，别用 `lv_tick_get`——
   平台层保持可移植（真机 io_esp 不拖 LVGL 头）。
4. **EEZ native 变量的 set_ 也必须给本体**（EEZ 同时声明 get/set；UI 不回写的
   就空实现），否则链接失败。
5. **新建 native 文件后删 build_rel 重配**：file GLOB 不自动重扫新文件
   （同 P-0163 坑 8 的字体）。
6. **v1 遗留坑仍有效**：hiddenFlag 键名 / textarea input 单向（密码用
   `lv_textarea_get_text` 在动作里读）/ 字体条目 source 全量 / printf setvbuf /
   假 indev 自动演示——见 git 历史版 README 与 KB P-0163。
7. **自动演示点的是开放网络 Guest**（空密码直连）；带密码网络在真机由
   键盘输入（textarea 已就位），演示跳过打字。

## ★ 真模式操作（零自动化）

`run_sim_realwifi.bat` 启动后**一切手动**：点"刷新"扫描 → 点行 → 密码面板 →
键盘输入 → 连接。测试辅助开关（不影响正常使用）：`WIFI_AUTOSCAN=1` 自动发起
一次扫描、`WIFI_AUTOEXIT=1` 扫描完成自动截图退出（无头验证用）。

## ★ PC 真 WiFi 模式（io_win.cpp，Windows WLAN API）

`run_sim_realwifi.bat` = 同一框架的**真硬件后端**（`APP_WIFI_REAL` 宏切换，
`io_pc.cpp` 整体退场、`io_win.cpp` 登场，UI/契约/native 层零改动）：

| 契约函数 | Windows 实现 |
|---|---|
| io_wifi_scan | WlanScan（异步）→ 2.5s 后 WlanGetAvailableNetworkList 建 wifi_ap 链表 |
| io_wifi_join | WlanSetProfile（WPA2PSK/open XML，密码=APP_IN_PWD）+ WlanConnect（**真连接，会切电脑网络**） |
| io_sample_inputs | WlanQueryInterface 查当前连接 → wifi_state/conn_ssid 回发 |
| 记住密码 | Windows profile 本身持久化（天然 NVS） |

实测（2026-10-20）：真机扫描到 13/12 个真实网络（两次数量不同=实时环境），
`yjt_dev_2.4G`/`yjt_dev` 等真实 SSID + 信号强度 + 锁标志全部正确渲染；
list_box 挂 SCROLLABLE 支持超一屏滚动。

★ **真模式零自动化**（用户要求）：开机不自动扫描（初始"未扫描 - 点击刷新"），
扫描/选行/输密码/连接/取消全部手动；main.c 真模式分支只周期打印 [STATE]，
demo 定时器不参与。假模式（默认 run_sim.bat）保留自动演示用于教学/CI。

**mingw 接入要点**：①`libwlanapi.a`/`wlanapi.h` mingw64 自带；②链接库必须排在
目标文件之后——用 `-DCMAKE_CXX_STANDARD_LIBRARIES=-lwlanapi` 注入（放前面无效）；
③mingw 头缺 `WLAN_AVAILABLE_NETWORK_CONNECTED/HAS_PROFILE` 宏（本地 #ifndef 补）、
auth 枚举名是 `DOT11_AUTH_ALGO_80211_OPEN`（非 MS 的 dot11_auth_algorithm_none）、
连接参数字段名 `strProfile`（非 strProfileName）；④PrintWindow 用
GetProcAddress 动态取（导入库缺 PrintWindowA），GPU 渲染窗口 BitBlt/PrintWindow
都可能黑屏 → **权威自证用 lv_snapshot**（lv_conf 开 LV_USE_SNAPSHOT，
`lv_snapshot_take(lv_screen_active(), XRGB8888)` 直接从 LVGL 帧缓冲出图）。

## 依赖版本

EEZ Studio 0.29（projectVersion=v3）· LVGL 9.4 · 480x320 · PC_SIM 仿真验证
（CLI 0 错 0 警 + 仿真器编译链接 0 错 + 自动演示日志断言，2026-10-20）。
