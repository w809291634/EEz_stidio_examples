# w1-animation-image — EEZ 手册 W1. AnimationImage 多帧动画图

> **手动操作入门**：想在 EEZ Studio 软件里用鼠标手动添加 AnimationImage？
> 看 [GUI-操作指南.md](GUI-操作指南.md)（导入帧图 → 拖控件 → Images/Duration/Repeat
> 三件套设置 → Build，含常见问题对照表）。

## 演示点

EEZ 控件面板 **Visualiser 组的 AnimationImage**（控件手册 W1 节）："多帧 Image"——
把一组位图按顺序逐帧播放，代替单张源图。本例 = 单 screen + 8 帧 96x96 旋转
spinner（240° 渐暗尾巴）+ 800ms/轮 + 无限循环。

**手册出处（官方目录）**：
- EEZ Studio 内置手册：`help/en-US/components/widgets/AnimationImage.md`
  （即 `EEZ-Studio-reference-guide.pdf` 的 W1 节；手册 EXAMPLES 节为空，故本示例即补位）；
- 官方 LVGL 文档：https://docs.lvgl.io/master/widgets/animimg.html

**属性三件套（手册原文）**：
| 属性 | 含义 | 本例 |
|---|---|---|
| Images | 帧位图名列表（按数组顺序播放） | anim_frame_0..7 |
| Duration | 一整轮时长（ms） | 800 |
| Repeat infinite / Repeat count | 无限循环开关 / 有限次数 | 无限 |

**生成代码**（`src/ui/screens.c`，与手册语义一一对应）：

```c
lv_obj_t *obj = lv_animimg_create(parent_obj);
static const lv_image_dsc_t *images[8] = { &img_anim_frame_0, ... };
lv_animimg_set_src(obj, (const void **)images, 8);
lv_animimg_set_duration(obj, 800);
lv_animimg_set_repeat_count(obj, LV_ANIM_REPEAT_INFINITE);
lv_animimg_start(obj);
```

## 工程结构

```
w1-animation-image/
├── build_example.py          ← 唯一设计源：生成 .eez-project（含 8 帧内嵌 PNG 位图）
├── w1-animation-image.eez-project
├── images/                   ← ★ 8 帧原图 PNG（export_frames.py 从工程 JSON 导出，可直接查看）
├── export_frames.py          ← 把工程内嵌位图导出为独立 PNG（ EEZ 位图是 data-URI 内嵌，无独立文件）
├── design/
│   ├── cli_build.py          ← EEZ 无头 CLI 构建
│   ├── gen_images.py         ← ★ 补烘帧图 .c（CLI 不产图片文件，见坑 1）
│   └── sim_cmake/            ← PC_SIM 仿真器三件套
└── src/ui/
    ├── images.c              ← EEZ 生成：位图名表（引用 img_anim_frame_N）
    └── images/               ← gen_images.py 补烘的 img_anim_frame_N.c（v9 dsc）
```

> **原图在哪**：EEZ 位图不做外部文件引用——8 帧原图以 `data:image/png;base64`
> 内嵌在 `.eez-project` 的 `bitmaps[]` 数组里；要看图/改图先跑
> `python export_frames.py` 导出 `images/anim_frame_N.png`，改完再 base64 塞回。

## 构建与验收

```
python build_example.py                   # 重新生成工程（含帧位图）
python design/cli_build.py                # EEZ CLI 构建
python design/gen_images.py               # ★ 补烘帧图 .c（CLI 构建之后必须跑）
双击 design\sim_cmake\run_sim.bat          # 编译并弹仿真器：spinner 持续旋转
```

## 踩过的坑

1. **★ EEZ CLI 构建不产图片 .c（P-0140 的图片版）**：CLI 只发 `images.c` 名表
   （`{"anim_frame_N", &img_anim_frame_N}`）和 `images.h` 声明，帧数据
   `img_anim_frame_N.c` 由 **GUI Build** 产出——纯 CLI 构建必现
   `undefined reference to img_anim_frame_N`。自愈方案与 gen_fonts.py 同款：
   `design/gen_images.py` 复算帧像素，按 EEZ v9 格式直接落
   `src/ui/images/img_anim_frame_N.c`（`lv_image_dsc_t`：magic + cf=ARGB8888 +
   w/h/stride=4w，像素字节序 **B,G,R,A**）。
2. **★ 帧位图 = 内嵌 data-URI**：EEZ 位图条目形如
   `{objID, name, description, image: "data:image/png;base64,...", bpp: 32,
   alwaysBuild: false}`——PNG 直接 base64 进 JSON，无需外部文件；bpp 32 = RGBA
   支持透明背景（spinner 四角透明靠它）。
3. **AnimationImage 帧条目没有独立时长**：duration 是整轮的（挂 widget 上），
   手册明示；别找 per-frame delay。
4. **widgetFlags 用官方默认整组**（`ADV_HITTEST|CLICK_FOCUSABLE|GESTURE_BUBBLE|
   PRESS_LOCK|SCROLLABLE|...|SNAPPABLE`）：P-0150 教训——flags 是最终态白名单，
   差集会发射 remove_flag，乱裁必出诡异行为。
5. **EEZ 无头 CLI 不烘字体**（KB P-0140）：本例只用默认字体 + ASCII；中文帧旁白
   参考 `font-entry-form` 的 lv_font_conv 链路。

## 依赖版本

EEZ Studio 0.29（projectVersion=v3）· LVGL 9.4 · 480x320 · PC_SIM 仿真验证
（CLI 构建 0 错 0 警 + 仿真器编译链接 0 错，2026-10-19）。
