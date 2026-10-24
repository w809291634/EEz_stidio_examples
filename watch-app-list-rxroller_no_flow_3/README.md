# watch — 手表 UI 工程（EEZ no flow 方式）

流程唯一真值：`C:\Users\yjt54\Desktop\local_knowledge_base\embedded\EEZ Studio_ui_debug_kit\EEZ_FIRST_WORKFLOW_NO_FLOW.md`（§2 七步主线）

## 已定口径（2026-10-22 用户确认）

| 项 | 值 |
| --- | --- |
| 屏幕 | 圆形 466×466 |
| 框架方式 | **no flow**（§2 七步；预生成控件必须 EEZ 生成，src/ui 不手改） |
| 设计图来源 | 无用户图，由 AI 先写设计源 → `design/design_view.py` 渲染 → 交用户确认（第①步） |
| 固件基座参考 | `C:\Users\yjt54\Desktop\EEz_stidio_examples`（含 `PC_SIM`、`apl_lvgl_v9_4`、no-flow 样板 `watch-app-list-no-flow`） |
| 页面需求（第①步，2026-10-22） | **23 页**：tab_main（tabview：表盘+applist 两标签，左右滑）；14 个 APP 各 1 功能页（遥控相机已删）；子页 7（闹钟编辑 + 设置 6）；页面关系见 designer/控件清单表.md |
| applist 图标 | 圆角彩底 + **白色矢量图标**（design_view.py GLYPHS 13 个绘制器 + 血氧"97"文字标；闪电/心形/月牙/太阳/气泡/音符/铃/秒表/沙漏/计算器/罗盘/手机/齿轮）；导出形态（位图 or LVGL symbol 字体）第②步定，大图走 TF 卡与否第④步问 |
| applist 形态 | **纵向滚轮，参考 `EEz_stidio_examples\watch-app-list-rxroller`**（中心 150%、跨 3 行线性到底 59%、C 形弧 r=700、圆角彩底+白色矢量图标+名称；甩动/吸附等 scale 轴 EEZ 属性面没有 ⇒ 第⑦步按铁律0全功能阶段走 native，可复用该移植件） |

## 七步进度

- [x] 骨架搭建（本目录，按 kit §1.1 分层）
- [x] ① 设计图（**2026-10-22 用户确认冻结**；同日按拍板追加 7 子页 → **23 页**：designer/*.png + _overview.png）
- [x] ② 控件标注（**定稿**：designer/控件清单表.md，46 项行为控件；四项口径用户拍板：tabview 切页/整行可点/补子页/图标位图 PNG）
      └ **控件位置图**：`designer_annotated/`（22 张单页 + 树状总览 `_tree.svg`（交付真值）/`_tree.png`；
      总览=23 页全部用**已标注缩略图**（控件框+分类徽标可见），连线圆徽=发起控件
      （**绿底=UI 内部切换，红底=输出硬件/手机**），右侧含"板级硬件/手机 App(BLE)"两个外部节点及红连线；
      徽标分类号 1按钮/2开关/3滑条/4滚轮/5步进/6chips/7按键网格；
      由 `design/design_annotate.py` 从设计源 CONTROLS 注册表同源生成，改设计源后与 design_view.py 一起重跑）
- [x] ③ 框架确认（**no flow**；例外口径：表盘↔applist 用 EEZ tabview 同屏两标签，APP 页独立屏 native 三步切页）
- [ ] ④ 预生成 + **静态验收**（生成已完成：22 屏/构建 0 错 0 警/字体 11 档烘焙过/14 图标入工程；
      待跑 §2.2 两站：**A** 声明层 JSON↔设计源对账差异=0 → **B1** EEZ 画布逐屏截图对照 designer/）
- [ ] ⑤ 导航闭环核对（**C** 仿真 AUTOTEST 逐跳转边断言全 PASS + **B2** 仿真截图与 B1 互证；
      native 接线 watch_nav.cpp/sim_cmake 已备，待④全绿后编译执行）
- [ ] ⑥ 用户核对 + 真机（点头＝设计冻结）
- [-] ⑦ 逐个补全功能（五元组立项，各走 §2 内环）
      └ 2026-10-23 第 1 批：本机状态层已接通运动、血氧模拟、消息、音乐、闹钟/编辑器、
      秒表、倒计时、计算器、找手机、亮度/音量、表盘样式、蓝牙、勿扰、检查更新；
      PC_SIM 冒烟 + 导航回归 `61 PASS / 0 FAIL`。传感器、BLE、PWM 背光、功放/马达、
      手机响铃/更新仍是 `watch_platform_*` 适配点，待板级接口与协议真值后接入并真机验收。

## 目录约定（铁律）

- `designer/`＝给人看的设计效果图（design_view.py 渲染产物）；`design/`＝给机器的设计源与工具链。不一致时改设计源。
- `src/ui/`＝EEZ 覆盖式导出产物，**禁止手改**；功能逻辑一律进 `src/native/`。
- 界面只在设计源里定义一次；C 代码、仿真出图全部由设计源派生。
- `tmp/`＝核对过程临时件（探针/crop/pid，gitignore 随手可清）；`build/`＝核对报告与定稿产物；交付件进 `designer/`、`designer_annotated/`。

## 本机工具路径（用前可核）

- EEZ Studio：`C:\Users\yjt54\AppData\Local\Programs\eezstudio\EEZ Studio.exe`
- Python：`C:\Users\yjt54\AppData\Local\Programs\Python\Python311\python.exe`（本机实测已带 PIL 12.3 / matplotlib 3.11）
- PC_SIM 仿真根：`C:\Users\yjt54\Desktop\EEz_stidio_examples\PC_SIM`（第⑤步前核对可用性）
- LVGL 源码：`C:\Users\yjt54\Desktop\EEz_stidio_examples\apl_lvgl_v9_4`

- [x] applist 滚轮移植（2026-10-23 还原后重做）：Rxroller 上游件入库，账单 `PORTLOG.md`；参数唯一出处 `src/native/widgets/applist/watch_list_config.h`（设计源经 wconfig 读）；宿主改全屏、行全部 native 建；行数据 `generated/app_rows.c` 由生成器从 APPS 派生。验证：`[NAV] PASS 44/FAIL 0`，中心行落点 (176,195)≈(177,195)，截图 tmp/applist_now.png 穹顶排布/名称 26px 与设计图一致。
