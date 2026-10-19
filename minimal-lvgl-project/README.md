# minimal-lvgl-project —— 最小可构建的 EEZ Studio LVGL 工程

> **演示点**：一个 480×320 单页工程的最小完备结构 —— 从 `.eez-project` JSON 到 headless 构建出码。
> 适合作为"第一个 EEZ 工程"的参照：工程 JSON 每个段落为什么长这样，注释里都写了。

## 演示点

1. EEZ LVGL 工程 JSON 的最小完备集：`settings` / `variables` / `userPages` / `lvglStyles` / `themes` 各段长什么样、缺了会怎样；
2. 单页单屏 + 两个 Label：`localStyles` 里**显式清零** padding/border（红线 6：让"声明坐标 == 渲染坐标"）；
3. headless CLI 构建：0 错 0 警的判据 + **产物清单对账**（"构建成功"≠"有产物"）。

## 工程结构

| 文件 | 说明 |
|---|---|
| `build_example.py` | ★ 唯一设计源：生成本工程的 `.eez-project`，改 UI 改它 |
| `minimal-lvgl-project.eez-project` | 生成产物，EEZ Studio 可直接打开 |
| `src/ui/` | 构建产物（可再生产物，已 gitignore；重新构建即再生） |

## 依赖版本

| 项 | 值 |
|---|---|
| EEZ Studio | 0.29.0（工程模型 `projectVersion=v3`） |
| LVGL | 9.4.0 |
| 屏幕 | 480×320，深色主题，16bpp |
| 字体 | 无自定义字体条目，文字走 LVGL 内置 Montserrat（要中文字体见同仓库 `font-entry-form`） |

## 怎么用

```bash
python build_example.py     # 生成 minimal-lvgl-project.eez-project
```

构建（二选一）：

- **GUI**：EEZ Studio 打开工程 → 工具栏 Build（扳手图标）；
- **CLI**（无头，适合流水线）：
  ```bash
  "EEZ Studio.exe" --build-project minimal-lvgl-project.eez-project \
      --no-sandbox --disable-gpu --enable-unsafe-swiftshader --disable-dev-shm-usage
  ```
  判据：日志出现 `No error and no warning detected`（或 `Build successfully finished`）。

## 踩过的坑

- ★ **CLI"构建成功"≠有产物**：判据 = 日志标记 **+ 产物目录对账**（`src/ui/` 下应有 12 个模板文件 + `eez-flow.cpp/h`）。案例见经验库 `cases/B7`。
- ★ **不配 `settings.build.destinationFolder`，产物落工程根目录**：本工程显式配 `src\ui`，与参考工程（Design Watch）的目录约定一致。
- 构建日志里的 Chromium 噪音（`ERROR:disk_cache`、`Gpu Cache Creation failed` 等）**不是构建错误**；噪音过滤正则与两次误判史见经验库 `P-0010` / `P-0016`。
- 本工程不含字体条目，**CLI 构建不涉及字体 .c**；一旦工程带字体，CLI 只写 `fonts.h` 声明、不产 `ui_font_*.c`，需 GUI Build 补（`P-0140`）——详见 `font-entry-form` 示例。

## 经验库对照

- 方法论：`PLAYBOOK.md` §2.6（六类体检）/ 红线 6（清零默认 padding）/ 红线 9（数值证据）
- 案例：`B7`（构建成功却零产出）；`P-0005`/`P-0006`（CLI 四坑）
