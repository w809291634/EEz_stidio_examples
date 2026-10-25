# PORTING —— 把这套 WiFi 模块插进新工程

> 目标：新 EEZ（no-flow）工程里，**只复制目录 + 对齐契约**，不改业务代码。
> 自检一条命令：`python design/port_check.py --ui <新工程>/src/ui`

## 1. 模块边界（复制这些）

```
src/native/
├── app/          wifi_model / wifi_view / wifi_events / wifi_logic   ← 业务+契约
├── navigation/   wifi_nav                                            ← 模态显隐与动效
├── widgets/      wifi_list / wifi_busy / wifi_eye                    ← 动态控件
└── platform/     wifi_platform.h + pc/ + device/                     ← 硬件边界
```

`platform/pc/` 三份：`wifi_platform_pc.cpp`（分发器+假世界）、`wifi_platform_win.*`（Windows 真接口）。
真机构建定义 `WIFI_PLATFORM_DEVICE` 后换 `device/` 那份（目前是占位，见 §6）。

## 2. 契约（新工程的 EEZ 必须提供）

| 类别 | 必须有的名字 |
|---|---|
| 对象（11） | `main` `list_box` `lbl_status` `btn_refresh` `overlay_root` `scrim` `sheet` `lbl_pwd_ssid` `pwd_ta` `dlg_root` `lbl_dlg_ssid` |
| 动作（6） | `scan_start` `wifi_connect` `pwd_cancel` `dlg_forget` `wifi_disconnect` `dlg_cancel`（`implementationType: native`） |
| 平台接口（9） | `io_init` `io_sample_inputs` `io_wifi_scan` `io_wifi_connect` `io_wifi_forget` `io_wifi_disconnect` `wifi_ap_at` `wifi_ap_count` `wifi_ap_gen` |
| lv_conf | `LV_USE_ARC` `LV_USE_SPINNER` `LV_FONT_MONTSERRAT_14` `LV_FONT_MONTSERRAT_16`（眼睛/转圈用符号字形） |

几何没有硬依赖：半页动画取 `lv_obj_get_height(sheet)`，眼睛跟随 `pwd_ta` 实测矩形。
只有**列表行**的参数在本仓库里定死（见 §5），换设计要改。

## 2b. 两个"只改一处"的集中点

| 想改什么 | 改哪里 |
|---|---|
| 界面状态文案 | `src/native/app/wifi_text.h`（假/真/真机 + logic 共用） |
| 行高、配色、遮罩/转圈、眼睛尺寸 | `src/native/widgets/wifi_skin.h` |

## 3. 五步

1. 复制 `src/native/**` 到新工程同名目录（`app/` 必须保持平铺，不要建功能子目录）；
2. 新工程的 EEZ 侧照抄本仓库 `build_example.py` 里的「连接半页 + 忘记对话框」两段
   （标识符别改；`sheet` 建议 224 高、键盘 132 高，见设计图）；
3. 在 `ui_init()` 之后调 `user_io_init()`，每帧调 `user_io_tick()`；
4. 改皮肤参数（§5 的一处头文件），按新设计调行高/颜色/控件尺寸；
5. 跑：`python design/port_check.py --ui <新工程>/src/ui` → 全 OK 再跑你自己的门禁
   （本仓库把它接进了 `preflight.py`，所以本工程每次跑门禁都会顺带自检契约）。

## 4. 接线的两条纪律

- **命令只投递，不直接调平台**：EEZ 动作 → `wifi_events` → `app_set_output()`；
  `user_io_tick()` 排空时才调 `io_*`。这样假/真后端可换、可以无头测。
- **模态显隐只走 `navigation/wifi_nav`**：EEZ 的 `hiddenFlag` 是逐对象字面量，
  整块模态靠 `overlay_root` / `dlg_root` 原子显隐（kit cases/B16）。

## 5. 皮肤参数（换设计只改这里）

`src/native/widgets/wifi_skin.h`：行高 `ROW_H`、行内颜色（信号条/胶囊/文字/分隔）、
眼睛尺寸与内边距、转圈尺寸/线宽/弧长/时长。改完重新编译即可。

## 6. 已知边界

- `platform/device/` 是**占位**：嵌入式无线栈要自己接（TODO 里写了要照 `pc/wifi_platform_win.cpp`
  的时序与状态口径抄）；
- Windows 真接口依赖 `wlanapi`（`run_sim.bat` 用 `-DCMAKE_CXX_STANDARD_LIBRARIES=-lwlanapi` 链）；
- 真接口默认开启，`WIFI_PC_FAKE=1` 回到假世界（门禁与出图必须显式设它）。
