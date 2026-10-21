# watch-app-list-no-flow —— 手表蜂窝缩放应用列表（SiFli `app_mainmenu` 移植件）

一句话：把 SiFli SDK 手表 demo 里那个**中间大、两边小、能甩动能吸附**的应用列表
搬到本仓库，跑在 PC 仿真里；EEZ 只画外壳，列表本体是 native C，**全程零 Flow**。

## 1. 为什么这个工程长这样（两条口径的交叉点）

| 口径 | 取值 | 后果 |
|---|---|---|
| `settings.general.flowSupport` | **false** | EEZ 不发射 `eez-flow.h/cpp`，`ui.c` 走 `create_screens()` 分支 |
| `settings.build.generateSourceCodeForEezFramework` | **false** | 不链 EEZ Flow 运行时 |
| 变量表 | **空**（`gvs=[]`） | no-flow 下 EEZ 变量必须 `native:true`；本工程状态文本由 native 直接 `lv_label_set_text`，不需要变量参与 |
| 屏幕 | **368×448**（不是仓库基线 480×320） | 移植件的穹顶曲线以屏心为不动点，屏心一变半径/间距全变；三处对齐被 preflight 当硬判据 |

**为什么主体不在 EEZ 里**：EEZ 的 List 是零属性空壳，做不了"逐帧按离屏心距离重算每个
条目的缩放与径向位置"。按"EEZ 优先"铁律先做了四面对查（事件面/动作面/调度语义/运行时源码），
结论是 EEZ 侧无对应能力 ⇒ 出 EEZ，并已把这条判断写进 §6。

## 2. 移植账单（改动全在依赖层，算法一行没重写）

移植源：`D:\temp_d\SiFli-SDK\example\multimedia\lvgl\watch_v9\src\gui_apps\main\app_mainmenu.c`
（1575 行，`SPDX-License-Identifier: Apache-2.0`）→ 本工程 `src/native/watch_app_list.c`（1434 行）。
**改造由 `design/port_mainmenu.py` 自动完成**（9 处锚点补丁，每处打 `PORT:` 标记），
所以"重跑脚本 = 复现移植"，不靠手工 diff。

| 被替换的东西 | 原来 | 现在 |
|---|---|---|
| RT-Thread | `rt_kprintf`/`rt_calloc`/`rt_free`/`RT_ASSERT`/`rt_err_t` | `sifli_compat.h` 里映射到 stdio/stdlib |
| GUI 框架生命周期 | `msg_handler` 分发 ONSTART/ONRESUME/ONPAUSE/ONSTOP + `BUILTIN_APP_EXPORT` | 一个显式入口 `watch_app_list_create(host, status_label)` |
| 应用枚举 | `gui_builtin_app_list_open/get_next/close` | `sifli_compat.c` 里 16 项静态表（第 0 项固定 `clock`，沿用原文件规则） |
| 打开应用 | `gui_app_run(cmd)` 真切应用 | 写状态行 `已打开: <id>` + 打一行 `[APP]` |
| 动态加载应用 | `gui_script_app_list_get_next` 那条 while | 删（本工程无 DL 后端） |
| demo 填充图 | 52 个假图标铺满屏 | 删，只留真应用表 |
| 输入代理 | `monkey_mode()` 随机点击 | 删（判定条件等价于 `!scroll_actived`） |
| 图标资源 | `LV_IMG_DECLARE(img_*)` 26 个 + 资源管理器 | `design/gen_icons.py` 自绘 16 个 80×80 ARGB8888 |
| **穹顶曲线** | `get_icon_transform_param()` —— SDK 里是**预编译库**（`middleware/cell_transform/` 只有头 + `.a`，无源码） | `watch_icon_transform.c` 按同目录 `mainmenu.py` 的 r→m / r→d 公式**复算** |
| 页面父对象 | `lv_obj_create(lv_scr_act())` 自建全屏 | 挂到 EEZ 生成的 `objects.list_host`（整屏，故屏心与曲线中心同一点） |

LVGL 版本差（SiFli 分支 ↔ 本仓库 9.4）：`_lv_obj_scroll_by_raw`→`lv_obj_scroll_by_raw`、
`lv_disp_enable_invalidation`→`lv_display_enable_invalidation`、`LV_INDEV_DEF_READ_PERIOD` 已删
（映射到 `LV_DEF_REFR_PERIOD`）、`LV_HOR_RES/LV_VER_RES` 在 9.4 是**运行期调用**而原文件在
`#if` 里做预处理算术 ⇒ compat 里 `#undef` 后换成编译期常量。`lv_img_*` 由
`src/lv_api_map_v8.h` 兜着，不用动。

## 3. 目录

```
watch-app-list-no-flow/
├── build_example.py                 ← EEZ 外壳唯一设计源（368x448 + 字体条目 + 覆盖自检）
├── watch-app-list-no-flow.eez-project
├── fonts/simhei.ttf
├── design/
│   ├── cli_build.py                 ← EEZ headless CLI 构建
│   ├── port_mainmenu.py             ← ★ 从 SiFli 源重放 9 处移植补丁（可复现）
│   ├── gen_icons.py                 ← 自绘 16 个应用图标 → src/native/icons/*.c
│   ├── gen_font.py / audit_chars.py ← 字体链（屏上有中文，见根目录模板说明的铁律）
│   ├── preflight.py                 ← ★ 6 组硬门禁，交付前必跑
│   └── sim_cmake/                   ← run_sim.bat + main.c(含 WATCH_AUTOTEST) + lv_conf.h(SNAPSHOT=1)
├── src/native/                      ← 移植件（EEZ 不生成、不覆盖）
│   ├── watch_app_list.c/.h          ← 算法本体（port_mainmenu.py 的产物）
│   ├── sifli_compat.c/.h            ← 依赖替身层
│   ├── watch_icon_transform.c       ← 穹顶曲线复算
│   └── icons/img_app_*.c            ← 16 个图标
└── src/ui/                          ← EEZ 生成产物（★ 没有 eez-flow.*，这正是判据）
```

## 4. 怎么跑

```bat
python build_example.py            && rem 生成 .eez-project（含字体覆盖自检）
python design\cli_build.py         && rem EEZ CLI 构建
python design\port_mainmenu.py     && rem 从 SiFli 源重放移植补丁（源没变可跳）
python design\gen_icons.py         && rem 自绘图标
python design\gen_font.py          && rem ★ 必须在 cli_build 之后（P-0140）
python design\preflight.py         && rem ★ 6 组门禁，任一 FAIL 即退出码 1
双击 design\sim_cmake\run_sim.bat  && rem 起窗口，鼠标拖动/点击图标
```

无头自证（不需要人碰鼠标）：

```bat
set WATCH_AUTOTEST=1 && set WATCH_AUTOEXIT=1 && main.exe
```

## 5. 实测状态（2026-10-21）

| 检查 | 结果 |
|---|---|
| EEZ CLI 构建 | `Build successfully finished`，`No error and no warning detected` |
| no-flow 判据 | `src/ui/` 里**没有** `eez-flow.cpp/h`；`ui.c` 走 `create_screens()`、无 `eez_flow_init` ✓ |
| 分辨率三处对齐 | EEZ 368×448 == `WATCH_HOR_RES/VER_RES` == `SIM_W/SIM_H` ✓ |
| 字体链 | `ui_font_cn14.c` 36,452 B；native 侧上屏字面量 3 字全在子集内（**负控**：临时塞 `·测试` 二字 → 门禁 FAIL 并点名缺字，改回即 PASS）✓ |
| 移植残留 | 生效代码里已无 `rtthread.h`/`gui_app_fwk.h`/`BUILTIN_APP_EXPORT`/`cell_transform.h`/`monkey_mode`（注释里提到不算，`strip_comments` 后扫）✓ |
| PC_SIM 编译链接 | `[17/17] Linking main.exe → build succeeded`（含 16 个图标编译单元）✓ |
| ★ 穹顶真的在缩放 | `[LIST] init scroll=(751,1149) visible=16 scale=119..275 center=clock` ⇒ 同屏条目缩放**有区间**，不是等大平铺 |
| ★ 拖动换中心项 | `[LIST] drag+80 scroll=(671,1069) visible=13 scale=34..275 center=activity` ⇒ 沿蜂窝斜轴拖 (80,80) 后吸附到另一项，最大缩放仍是 275（中心恒最大） |
| ★ 中文渲染 | `shots/shot_init.png`：标题 `应用列表`、状态行 `就绪` 是实形汉字；16 个图标按离屏心距离分层缩放 |

### 5.1 截图怎么看

中心 `C`(clock) 最大，向外一圈圈变小并往屏心**压缩**（`radial_factor<1`），
所以远处的小图标会出现在近处大图标的**缝隙里**——这是穹顶的正常形态，不是叠错。
扫描线实测（`y=175`）：亮区 62/62/70 px，间隔 24/6 px ⇒ 图标之间确有间隙，
只是占位美术是实心圆角块，密度比真机图标高。要更接近真机观感，换带内边距的美术件即可
（`design/gen_icons.py` 的 `INSET/CORNER`）。

## 6. 踩过的坑 / 已知边界

- ★ **`get_icon_transform_param` 在 SDK 里没有源码**（只有 `.h` + 三个平台的预编译库）。
  本工程按 `mainmenu.py` 的公式复算，**不声称与原库逐位一致**；可核对的是两条单调性
  （`m(r)`、`d(r)` 都随 r 单调不增且 `m(0)=d(0)=1`）。真机上若观感不同，差异会出在这里。
- ★ **`LV_HOR_RES/LV_VER_RES` 在 LVGL 9.4 是运行期表达式**，而移植件在 `#if` 里拿它做
  预处理算术 ⇒ 必须 `#undef` 换编译期常量。这条不踩一遍想不起来。
- ★ **宿主容器必须整屏**：穹顶以屏心为不动点，宿主若被标题挤掉一条，视口中心与曲线
  中心就错开；标题/状态行靠 z 序浮在列表上面（`children[]` 里宿主排第一）。
- **未验**：真实鼠标拖动的 `PRESSING→RELEASED` 预测分支（`mainmenu_cell_predict_focus_icon`）
  要 `lv_indev_get_act()` 有活动输入设备，无头环境里发这个事件会踩空 ⇒ 只验了
  `lv_obj_scroll_by` 这条确定性路径，手测要开窗口拖。
- **未做**：真机（SiFli 面板）编译。本工程只保证 PC_SIM；回 SDK 用时把 `sifli_compat.*`
  换回真头文件、`watch_app_list_create` 接回 `msg_handler` 即可（算法不用动）。

## 7. 相关

- 移植源与闭源件的取证：本仓库 `flow-understanding/`（EEZ 侧能力四面对查的口径同源）
- no-flow 口径的由来：`app-wifi-scan-flow-no-flow/README.md`
- 中文字体铁律：`示例工程模板说明.md` 坑表 + `flow-examples/README.md` §3
