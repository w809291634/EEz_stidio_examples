# GUI 操作指南 — 在 EEZ Studio 里手动添加 AnimationImage 动图

> 适用：EEZ Studio 0.29.0 · LVGL 9.x 工程（projectVersion v3）。
> 本文档对应示例 `w1-animation-image/`（该示例由 `build_example.py` 生成，
> 手动操作走的是同一条路，只是"鼠标点"替代"JSON 生成"）。

---

## 0. 准备帧图

AnimationImage 的原料是**一组尺寸相同、内容连续的 PNG/JPG**（本例 8 帧 96×96，
透明背景 RGBA）。建议：

- 帧数 4~16，越大越流畅、越占 flash；
- 同一动画所有帧**尺寸必须一致**；
- 要透明就用带 alpha 的 PNG；
- 先把帧图放在一个文件夹里（如 `images/anim_frame_0.png ~ 7.png`，本例可
  `python export_frames.py` 导出后当模板）。

---

## 1. 把帧图导入工程（变成"位图"）

1. 打开工程，左侧**项目树**找到 LVGL 工程的 **Bitmaps** 节点；
2. 两种导入方式任选：
   - **拖拽**：从 Windows 资源管理器把 8 张 PNG **多选后一起拖**到 Bitmaps 面板；
   - **添加**：选中 Bitmaps → 工具条 **Add → Add bitmap(s)**（或右键），文件多选；
3. 导入后每张图生成一个**位图条目**（name 默认取文件名）。双击条目可改名——
   建议改成有序名（`anim_frame_0`、`anim_frame_1`…），**AnimationImage 按列表顺序
   播放，与文件名无关，但有序名方便后面批量添加时自动连选**；
4. 点开条目可看预览；`bpp`（每像素位数）默认 32 = RGBA 带透明。

> ⚠️ 本仓库经验（P-0140/P-0151）：**CLI/headless 构建不烘图片 .c 和字体 .c**，
> 手动 GUI 流程里你点的是 GUI 的 Build，它会一并产出，无此坑。

---

## 2. 拖一个 AnimationImage 到页面上

1. 左侧项目树展开 **Pages/Mains**，双击打开目标页（如 `Main`）进入画布编辑；
2. 右侧 **Widgets（控件面板）** 搜索框输入 `animation`，或在 **Visualiser** 分组里
   找到 **AnimationImage**（手册编号 W1）；
3. **按住 AnimationImage 拖到画布上松手**——页面上出现一个默认 180×100 的占位框；
4. 选中它，在右侧属性格里把 **left/top/width/height** 改成帧图尺寸（本例 96×96，
   位置随意），或直接在画布上拖动/拉角调整。

---

## 3. 设置属性（核心三件套）

选中 AnimationImage 后，右侧属性格（PropertyGrid）：

### 3.1 Images（帧序列）

1. 找到 **Images** 属性，点 **+**（添加）；
2. 弹出对话框：第一项选第 1 帧的位图名（下拉列出工程里所有 Bitmaps），
   **No. of images** 填帧总数（本例 8）→ 确定后 EEZ 会**按位图列表顺序自动填好
   8 个连续条目**（这就是 1.3 让你把帧图命名成连续有序名的原因，省去逐帧手挑）；
3. 条目列表可上下移动调整播放顺序，点每行的下拉可单独换图。

### 3.2 Duration（一轮时长）

- 单位**毫秒**，是"播完一整轮"的时间，不是单帧间隔；
- 本例 8 帧 → 800ms = 每帧 100ms；
- 值越小越快，越大越慢。

### 3.3 Repeat infinite / Repeat count（循环）

- **Repeat infinite** 打开（默认开）= 无限循环，生成
  `lv_animimg_set_repeat_count(obj, LV_ANIM_REPEAT_INFINITE)`；
- 关掉它则出现 **Repeat count**，填有限次数（如 3 = 播 3 轮后停在末帧）。

### 3.4 其他

- **widgetFlags 不要乱裁**：保持默认（含 SNAPPABLE 等）——
  见 P-0150：EEZ 的 flags 是"最终态白名单"，取消勾选的 flag 会被
  `lv_obj_remove_flag` 反向移除，曾导致 tabview 整页拖不动；
- 背景透明：AnimationImage 自身不用设背景，帧 PNG 自带 alpha 通道即可。

---

## 4. 构建与验收

1. 工具条 **Build**（锤子图标）→ 底部 Output 应显示
   `Build successfully finished`（GUI Build 会同时烘出图片 .c 与字体 .c）；
2. 产物检查：`src/ui/screens.c` 应有
   `lv_animimg_create → lv_animimg_set_src → lv_animimg_set_duration →
   lv_animimg_set_repeat_count → lv_animimg_start` 链；
   `src/ui/images/`（或 `src/ui/`，取决于是否勾选分目录）出现 `ui_image_<帧名>.c`；
3. 看动画：画布右上 **Run** 预览可看播放（EEZ 预览支持 animimg）；
   要"真机同款"验收就双击本工程 `design\sim_cmake\run_sim.bat` 在 PC_SIM 里看。

---

## 5. 常见问题对照

| 症状 | 原因 | 处置 |
|---|---|---|
| GUI 里能看到动画，MCU/仿真器链接报 `undefined reference to img_*/ui_image_*` | 用了 CLI/headless 构建（不烘图片 .c，P-0151） | 跑一次 GUI Build，或用本工程 `design/gen_images.py` 补烘 |
| 动画不动 | Repeat infinite 没开且 Repeat count=0；或 Duration 填 0 | 开 infinite 或填正数 |
| 动画方向/顺序不对 | Images 列表顺序乱 | 属性格里上下移动条目 |
| 帧有黑底（要透明没有透明） | 导入的是不带 alpha 的 JPG/24 位 PNG | 用 RGBA PNG 重新导入（bpp 32） |
| 改了帧图内容但界面没变 | 位图是**内嵌 data-URI**，改外部 PNG 不会自动同步 | 删旧位图条目重新导入，或用 `export_frames.py`/`build_example.py` 链路重新生成 |
| 控件拖进画布后拖不动周围控件/页 | 误裁了 flags（P-0150） | 恢复该控件默认 flags |
