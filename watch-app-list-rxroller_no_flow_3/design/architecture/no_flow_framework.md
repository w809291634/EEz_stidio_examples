# 框架方案（no flow）— watch 工程

方式选型（§2 第③步结论，2026-10-22 已定）：**no flow**。
- 不用 flow 变量桥；`src/ui`（EEZ 生成、不手改）直接对接 native 的事件回调与业务代码。
- 按钮跳页正解 = 不依赖 flow 引擎：native 里三步等价 replacePageHook
  （createScreen + 取屏对象 + `lv_scr_load_anim(ANIM_NONE, auto_del=false)`）。
- 命令型按钮走 User Action 直调（A/B/C 通道纪律见 kit skills §11.14；命令别做成变量）。
- 平台层 `io_pc.cpp / io_esp.cpp` 视是否保留 PC 仿真决定去留（第⑤步要跑仿真 ⇒ 保留）。

分层归属：
| 层 | 位置 | 归属 |
| --- | --- | --- |
| 界面结构与样式 | `design/design_source.py` → EEZ 工程 → `src/ui` | 生成物，禁手改 |
| 业务状态 / UI 刷新 / 事件 / 调度 | `src/native/app/` | 扁平的 `watch_model / watch_view / watch_events / watch_logic`；不建功能子目录 |
| 外部硬件控制 | `src/native/platform/watch_platform.h` + `pc/` / `device/` | 编译时二选一；PC 与真机共享接口，EEZ 之外唯一允许区 |
| 页面跳转 | `src/native/navigation/watch_nav.cpp` | 只管去向，不保存业务状态 |
| 专用动态控件 | `src/native/widgets/applist/` | 父层必须来自 EEZ，几何从设计源派生 |
| 上游滚轮件 / native 生成数据 | `src/native/third_party/rxroller/` / `src/native/generated/` | 前者冻结，后者由设计源生成；都不手改 |

当前文件树与新增文件规则见 [`src/native/ARCHITECTURE.md`](../../src/native/ARCHITECTURE.md)。

待补（第②步控件标注后）：页面关系图（是否归 tabview、top/bottom bar）、页面跳转表。

**第②步定稿（2026-10-22 用户拍板）**：表盘+applist 归 **tabview**（EEZ 同屏两标签、原生左右滑）；
其余 21 页为独立屏，行点击/返回钮走 native 三步等价 replacePageHook；无 top/bottom bar。
跳转全表见 designer/控件清单表.md。
