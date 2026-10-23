# EEz_stidio_examples — 项目长期记忆

## 工程库形态
- 一个示例工程 = 一个独立子目录（kebab-case），必备 README.md（演示点/结构/版本/坑），
  根 README 第 3 节索引表同步加行；通用结论回灌本地经验库 embedded/EEZ_Studio_ui_debug_kit。
- 现有 6 例：minimal-lvgl-project / widget-gallery / font-entry-form / two-state-styles /
  gesture-page-switch（双向手势）/ one-way-gesture-switch（单向手势）。

## PC_SIM 仿真器适配（2026-10-19 完成并验证；2026-10-23 加输出隔离）
- 换工程 = 双击该工程 `design/sim_cmake/run_sim.bat`；示例代码层仍不碰 `apl_lvgl_v9_4`。
- 机制：PC_SIM CMakeLists 优先读环境变量 `SIM_TARGET_PROJ_DIR`（回退 eez-test）；
  每工程三件套 run_sim.bat / main.c / lv_conf.h；SIM_H_RES/SIM_V_RES 在 PC_SIM 配置区改分辨率。
- **输出目录按工程隔离（2026-10-23）**：PC_SIM CMakeLists 多认一个 `SIM_BIN_DIR`（不设＝老行为
  `PC_SIM/bin`）；所有示例 bat 都设 `SIM_BIN_DIR=%BUILD_DIR%\bin` 并跑自己那份 exe。
  原因：`PC_SIM/bin/main.exe` 是全仓库共用路径，两个工程交替构建时后链的会覆盖，
  双击 A 却跑起 B（实测：本仓库示例 vs `D:\temp_d\AI_Temporary_Reply\watch` 互相覆盖，
  打印的 rows/pitch 与自身 config 对不上）。**新增示例照抄任意现有 bat 即可继承隔离。**
- 坑（详见根 README §4）：thorvg 需关 VECTOR_GRAPHIC/THORVG/LOTTIE；main.c 勿定义
  SDL_MAIN_HANDLED；bat 须 ASCII、括号块内 echo 不得含 `)`；换工程须强制 cmake 重配置；
  首编偶发 ninja 依赖目录竞态重跑即过；中文字体用 lv_font_conv 离线烘（产物落 src/ui/）。

## 协作偏好（本项目）
- **改动要克制**：用户明确反馈"改动太多了"，结构性优化（如改 run_sim.bat 重试逻辑）需先说明征得同意；
  我产生的临时文件（脚本/日志）任务结束后自行清理。
- 用户会自己还原不满意的改动；还原后以现状为准继续，不要擅自改回。

## 设计图约定（app-wifi-scan-flow）
- 图不累计：一个过程只留一张，与定稿冲突的直接删；编号是稳定 ID，删后不复用（允许跳号）。
- 唯一设计源 design/mockup_gen.py；改图改常量重生成，不手改 SVG。

## app-wifi-scan-flow v4 收口（2026-10-21）：EEZ 不持有任何变量
- v4 落地（数组变量移出 EEZ）后进一步收口：连标量 native 变量（scan_state/ap_gen/
  scan_status）也删了——`native_vars.{h,cpp}` 删除，`build_example.py` 的 `gvs=[]`，
  vars.h 空枚举、structs.h 空壳；main.c/io_pc/wifi_ui_sync/app_model 全部改走
  `app_model` 契约 + 直读 io。
- 当前数据流：io 静态数组 s_aps → `wifi_ap_at()/wifi_ap_count()/wifi_ap_gen()` →
  `wifi_ui_sync` 直读（每帧比对状态/代数后直写 LVGL）；状态走 app_model 契约
  （APP_IN_SCAN_STATE / APP_IN_SCAN_STATUS），EEZ 仅画静态外壳 + 空 lv_list。
- 顺手删：APP_IN_AP_GEN 冗余镜像通道（io 已有 wifi_ap_gen）、app_get_input_b/app_set_input_b
  闲置 bool 接口。
- 验证：PC_SIM 重编 542/542 全过（main.exe 链接成功），无 get_var_/undefined reference 残留。
- 真契约始终是 io_iface.h（wifi_ap_t + 三个访问器），删变量不破坏硬件/UI 分离。
