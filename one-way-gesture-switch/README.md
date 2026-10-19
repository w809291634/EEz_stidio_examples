# one-way-gesture-switch —— 只允许单向手势的页面切换

一个 **只允许「左滑」一种方向** 翻页的 EEZ Studio 示例。右滑被彻底「无视」：工程里
根本不存在右滑的判定与动作组件，因此从设计上不可能反向翻页。

> 本示例是 [`../gesture-page-switch`](../gesture-page-switch/)（双向手势：左滑+右滑都能翻）
> 的「单向约束」变体。两者共享同一套已验证的安全骨架，本示例额外演示「如何把手势锁死成单向」。

## 演示点（你会在这个示例里看到什么）

1. **单向手势锁**：三页只接受 `LEFT`（左滑），左滑循环 `A → B → C → A`。
   右滑（RIGHT）在工程里**不生成任何流组件、不连线** —— 右滑毫无反应，天然单向。
2. 三个「独立 screen」+ GESTURE 离散切屏（非 tabview 跟手），绕开 P-0123。
3. `changeScreen` 用 `fadeMode:'NONE'`，无动画竞态，绕开 P-0029 的「拉回旧页」空转。
4. 导航**完全不用 CHECKED 高亮链**，从设计上根除「高亮不更新 / 状态来回翻」的空转。
5. Switch 的 `evt` 输入显式 `type:'any'` —— 缺了它 EEZ 后台 Checks 检查器会持续转圈（§48 实证）。

## 结构

```
one-way-gesture-switch/
├── build_example.py              # 唯一设计源（生成 .eez-project）
├── one-way-gesture-switch.eez-project
├── README.md
├── .gitignore
└── src/ui/                       # 构建产物（可再生产物，重新构建即再生）
```

每页由「铺满屏的 Screen + host 容器 + 一条 LEFT 判定→跳转链」组成：

| 组件 | 作用 | 数量/页 |
|---|---|---|
| `LVGLScreenWidget` | 一页 | 1 |
| host `LVGLContainerWidget` | 收手势者：去 `GESTURE_BUBBLE`，挂 `GESTURE` 事件 | 1 |
| `SwitchActionComponent` | 判定 `Event.getGestureDir(evt) == 1`（LEFT）→ `GO` | **仅 1（LEFT）** |
| `LVGLActionComponent` | `changeScreen` 到下一页（`fadeMode:NONE`） | **仅 1（LEFT）** |

> 双向版每页有 2 条判定/跳转（LEFT + RIGHT）；本示例每页只有 1 条，
> 这就是「单向」在 JSON 上的直接体现：RIGHT 方向的组件与连线**整个不存在**。

## 依赖版本（与本机已安装一致，已实测）

- EEZ Studio **0.29.0**
- LVGL **9.4.0**
- 屏幕基线 **480×320**（与 watch 工程区分，布局计算简单）
- 工程模型 `projectVersion: v3`

## 关键实现点（直接复用到你自己的工程）

- **只允许单向 = 只生成单向的流组件**：不要为另一个方向画 Switch/Action，也不要连线。
  不要试图"画了但不连"——那样 Checks 会报 `not connected`。正确做法是**干脆不画**。
- **手势收件人**：host 容器去掉 `GESTURE_BUBBLE`，子 `Label` 保留（冒泡上来被收件）。
- **GESTURE 双线**：执行线 → `@seqin`，数据线 → `evt`，都用**裸名 `GESTURE`**
  （绝不写 `GESTURE@seqout`，否则 §11.41 静默丢线、构建照样 0 警）。
- **`evt.type:'any'`**：Switch 的自定义输入必须显式声明，否则 Checks 转圈。

## 验证

- **CLI headless 构建**：`EEZ Studio.exe --build-project` → **0 错 0 警**
  （EEZ 自带报告 `No error and no warning detected`）。
- **生成代码核对**：`screens.c` 为 3 个 host 注册 `LV_EVENT_GESTURE` 回调并
  `lv_obj_remove_flag(..., LV_OBJ_FLAG_GESTURE_BUBBLE)`，收件人正确；
  全工程检索无 `dir==2` / `LV_DIR_RIGHT` 残留 → 单向性已落地。
- **从零复现**：`python build_example.py` → 重新构建，结果一致。

## ⚠️ 必须知道的边界（与双向版相同）

手势的**运行时行为只能在 PC_SIM / 真机验收** —— EEZ 的 Run 预览输入通道不产生
`GESTURE` 事件（P-0141）。拿 Run 预览判手势「死刑」是误区；构建与连线正确性已用
CLI 兜底，运行时翻页手感请在仿真器里滑一下确认（左滑能循环、右滑无反应即达标）。

重新生成：`python build_example.py`  → 重新构建：EEZ Studio `Build` 或 CLI。
