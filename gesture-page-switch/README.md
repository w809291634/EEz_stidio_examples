# gesture-page-switch —— 页面手势切换（不会 Checks 空转 · 不会出错）

## 演示点

用「多个独立 screen + GESTURE 离散切屏」实现左右滑翻页，并把「Checks 空转 / CHECKED 状态乱翻 / 构建报错」三类坑从设计上根除。

- **3 页循环切换**：A(蓝) 左滑→B、右滑→C；B(绿) 左滑→C、右滑→A；C(红) 左滑→A、右滑→B。
- 手势判定链路：`host 容器 GESTURE 事件 → Switch(判定方向) → LVGLAction(changeScreen)`。

## 为什么「不会 checks 空转、不会出错」（KB 依据）

| 风险点 | 对策 | KB |
|---|---|---|
| **EEZ 后台 Checks 检查器持续转圈**（"checks 空转"字面义） | Switch 的 `evt` 自定义输入显式写 `type:'any'`；缺了这个字段，编辑器会静默丢字段，Checks 图标永远在转 | §48 / P-0148 同类 |
| **CHECKED 高亮随手势不更新、状态来回翻**（"checks 空转"工程义） | 导航**完全不依赖 CHECKED 高亮链**，每页只放静态文字标签，无共享选中态 | P-0028 / P-0029 |
| **动画竞态把屏拉回旧页**（陈旧 SCROLL_END 拉回旧 tab） | `changeScreen` 的 `fadeMode:'NONE'`，离散切屏无动画竞态 | P-0029 |
| **跟手 vs 独立屏互斥** | 直接离散切屏，不做 tabview 跟手 | P-0123 |
| **GESTURE 线被静默丢弃（构建照样 0 警，但手势失效）** | 事件执行线→`@seqin`、数据线→`evt`，**都用裸名 `GESTURE`**（绝不写 `GESTURE@seqout`） | §11.41 |
| **手势收不到** | 收件人规则：host 容器**去掉 `GESTURE_BUBBLE`**，子 label 保留 → 冒泡链上第一个无该标志的祖先收件 | §11.35 / §11.41 |

## 结构

```
gesture-page-switch/
├── build_example.py            # 唯一设计源（生成 .eez-project）
├── gesture-page-switch.eez-project
├── README.md
├── .gitignore
└── src/ui/                     # 构建产物（可再生成，已 gitignore）
```

- `build_example.py` 里的关键函数：`gesture_host()`（挂 GESTURE 事件、去 GESTURE_BUBBLE）、`gesture_switch()`（判定方向，evt.type='any'）、`gesture_action()`（changeScreen/fadeMode=NONE）、`gesture_page()`（组装一页 + 6 条连线）。
- 手势方向码：`Event.getGestureDir(evt) == 1` 左滑、`== 2` 右滑（LVGL `LV_DIR_LEFT/RIGHT`）。

## 依赖版本

- EEZ Studio **0.29.0** · LVGL **9.4** · 屏幕基线 **480×320**（与全套示例一致）。
- 工程模型 `projectVersion=v3`，构建模板与 EEZ 0.29 新建 LVGL 工程逐字一致。

## 验证状态

| 项目 | 结果 |
|---|---|
| CLI headless 构建 | ✅ **0 错 0 警**（EEZ 自带报告 "No error and no warning detected"） |
| 产物 | ✅ 15 文件，screens.c 已为 3 个 host 注册 `LV_EVENT_GESTURE` 回调并移除 `GESTURE_BUBBLE` |
| 连线完整性 | ✅ GESTURE 双线 + 两个 GO→changeScreen 全部命中，无未连接告警 |
| 手势运行时行为 | ⚠️ **必须 PC_SIM / 真机验收**：EEZ Run 预览的输入通道不产生 GESTURE 事件（P-0141），用 Run 预览判手势死刑是误区 |

## 复现步骤

```bash
cd gesture-page-switch
python build_example.py                       # 重新生成 .eez-project
# 用 EEZ Studio 打开 .eez-project → Build（GUI 构建可做字体/资源提取）
# 或 CLI：
#   "C:\Users\yjt54\AppData\Local\Programs\eezstudio\EEZ Studio.exe" --build-project gesture-page-switch.eez-project
```
