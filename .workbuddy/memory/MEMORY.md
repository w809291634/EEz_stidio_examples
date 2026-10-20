# EEz_stidio_examples — 项目长期记忆

## 工程库形态
- 一个示例工程 = 一个独立子目录（kebab-case），必备 README.md（演示点/结构/版本/坑），
  根 README 第 3 节索引表同步加行；通用结论回灌本地经验库 embedded/EEZ_Studio_ui_debug_kit。
- 现有 6 例：minimal-lvgl-project / widget-gallery / font-entry-form / two-state-styles /
  gesture-page-switch（双向手势）/ one-way-gesture-switch（单向手势）。

## PC_SIM 仿真器适配（2026-10-19 完成并验证）
- 换工程 = 双击该工程 `design/sim_cmake/run_sim.bat`；`apl_lvgl_v9_4`、`PC_SIM` 两公共目录零改动。
- 机制：PC_SIM CMakeLists 优先读环境变量 `SIM_TARGET_PROJ_DIR`（回退 eez-test）；
  每工程三件套 run_sim.bat / main.c / lv_conf.h；SIM_H_RES/SIM_V_RES 在 PC_SIM 配置区改分辨率。
- 坑（详见根 README §4）：thorvg 需关 VECTOR_GRAPHIC/THORVG/LOTTIE；main.c 勿定义
  SDL_MAIN_HANDLED；bat 须 ASCII、括号块内 echo 不得含 `)`；换工程须强制 cmake 重配置；
  首编偶发 ninja 依赖目录竞态重跑即过；中文字体用 lv_font_conv 离线烘（产物落 src/ui/）。

## 协作偏好（本项目）
- **改动要克制**：用户明确反馈"改动太多了"，结构性优化（如改 run_sim.bat 重试逻辑）需先说明征得同意；
  我产生的临时文件（脚本/日志）任务结束后自行清理。
- 用户会自己还原不满意的改动；还原后以现状为准继续，不要擅自改回。

## 设计图约定（app-wifi-connect2）
- 图不累计：一个过程只留一张，与定稿冲突的直接删；编号是稳定 ID，删后不复用（允许跳号）。
- 唯一设计源 design/mockup_gen.py；改图改常量重生成，不手改 SVG。
