# 页面动画时间线（LVGL）—— 机制与数据模型

> 为什么单开这篇：手册只用一段话 + 一张图讲 Animation timeline（P3 · P.24–25），
> **关键帧 JSON 形态、取值域、失效条件一个字都没写**；而装机 codegen 与运行时源码里全都有。
> 示例：[`../../flow-examples/flow-page-timeline-animation/`](../../flow-examples/flow-page-timeline-animation/)。
> 复抽证据：`python tools/extract_studio_facts.py`（同一套逆向法，只读装机件）。

## 1. 三层数据模型（谁持有什么）

| 层 | 持有者 | 内容 |
|---|---|---|
| 关键帧数组 | **控件（Widget）** | `widget.timeline = [keyframe, ...]` —— 不在页面对象上 |
| 游标（秒） | **页面级 FlowState** | `FlowState::timelinePosition`，由 `Animate` 件写 |
| 插值实现 | **生成的 C**（页面 tick 函数） | `lvglBuildPageTimeline()` 发射，不是运行时函数 |

⇒ 一个 `Animate` 推的是**整页**游标，屏上所有带关键帧的控件同时跟着走；
⇒ 反过来：`Animate` 会沿 `parentFlowState` **上溯**（`eez-flow.cpp:2650-2652`），
所以放在 User Widget 里的 `Animate` 推的仍是**宿主页面**的游标——多实例复用会互相带动画。

## 2. 关键帧 JSON 形态（手册没有，从 `TimelineKeyframe` 类抽出来的）

```json
{
  "objID": "<uuid>",
  "start": 1.0, "end": 2.0,
  "left":  {"enabled": true, "value": 300, "easingFunction": "easeInOutCubic"},
  "top":   {"enabled": true, "value": 60,  "easingFunction": "easeOutBack"},
  "width": {"enabled": true, "value": 150, "easingFunction": "linear"},
  "height": …, "scale": …, "scaleX": …, "scaleY": …,
  "rotate": {"enabled": true, "value": 45, "easingFunction": "easeInOutSine"},
  "opacity": {"enabled": true, "value": 0.27, "easingFunction": "linear"},
  "controlPoints": ""
}
```

- 可动属性共 9 个：`left top width height scale scaleX scaleY rotate opacity`；
- `beforeLoadHook` 会把裸数字升成 `{enabled:true, value, easingFunction:"linear"}`，
  缺省的 `scale/scaleX/scaleY/rotate` 补成 `enabled:false` ⇒ **写对象形式才能指定缓动**；
- 缓动名共 31 个（`linear` + In/Out/InOut × Quad/Cubic/Quart/Quint/Sine/Expo/Circ/Back/Elastic/Bounce），
  写错会生成 `eez_<名字>` 这种**不存在的函数**（链接期才炸）→ 示例生成器里已做成断言。

## 3. ★ 三条手册没写、但决定成败的机制

### 3.1 `opacity` 是 **0..1**，不是 0..255

codegen 两侧各乘除一次：

```c
init:  ... = lv_obj_get_style_prop(obj, LV_PART_MAIN, LV_STYLE_OPA).num / 255.0f;   // 归一
write: value.num = (int32_t)roundf(opacity_value * 255.0f);                          // 还原
```

⇒ 关键帧写 `opacity: 70` 会被当 70.0（远超 1），`*255` 后夹成全不透明——
**现象是"淡出动画没反应"**，而 CLI 构建 0 错 0 警，完全不报。
（示例 `build_example.py` 里 `_check_keyframes` 已把 0..1 做成硬断言。）

### 3.2 命中第一个满足条件的关键帧就 `break` ⇒ **同区间不能拆两帧**

生成的每帧结构是：

```c
if (timeline_position >= start && timeline_position < end) {
    float t = (timeline_position - start) / (end - start);
    x_value = (1 - eez_<easing>(t)) * x_value + eez_<easing>(t) * 300;
    break;                      // ← 这里
}
```

⇒ 同一时刻要一起动的属性**必须写进同一帧**；拆成两帧时第二帧永远轮不到，
现象是"只有一半属性在动"。`start == end` 的帧退化成纯赋值（`At X s set ...`），
并且**对该时刻及其之后**一直生效，不是只有一瞬。

### 3.3 插值是"从初值重放到当前游标"的纯函数

生成的静态结构在第一次 tick 抓一次初值（`obj_<id>_<prop>_init_value`），此后每帧
**从初值起沿关键帧重放**到当前游标。且外层有 `if (timeline_position != last_timeline_position)`
守卫——**游标不动就一行都不重算**。

⇒ 推论（都可直接用）：
1. **倒放、跳帧、来回拖都可复现**（没有累积误差），所以时间线动画适合做回归夹具；
2. 关键帧的 `value` 是**绝对目标**，不是增量；控件的创建位置就是 0 秒状态；
3. 想要"只在某一刻闪一下"必须用后一帧写回，或者改用 A43 的 `animX/animOpacity`（件级一次性动画）。

## 4. `Animate(A2)` 的三行运行时语义（`eez-flow.cpp:2650-2699`）

| 行为 | 实现 |
|---|---|
| 找到该推谁的游标 | 从当前 action flowState 沿 `parentFlowState` 上溯到**非 action** 的页面级 flowState |
| 正向 | `currentTime = start + speed*(millis()-startTimestamp)/1000`，到 `To` 收口 |
| 反向 | `To < From` 时走 `currentTime = start - speed*Δt`，到 `To` 收口 ⇒ **倒放原生支持** |
| 通知 | 每帧写 `timelinePosition` 并 `onFlowStateTimelineChanged`；**仅当 `currentTime == endPosition` 才 `propagateValueThroughSeqout`** ⇒ `seqout` = "放完了" |
| `Speed=0` | 手册另述：立即跳到 To，此时 From 无意义（等价于"设游标"） |

## 5. 与 A43 件级动画的选择（示例 ⑮ vs ⑭）

| 维度 | 页面时间线（⑮，本篇） | A43 `animX/animY/animOpacity/...`（⑭） |
|---|---|---|
| 编辑方式 | GUI 拖关键帧 / JSON 数组 | 流图里放件，参数可用表达式 |
| 目标值 | 绝对（从初值重放） | 可 `Relative`（相对当前值） |
| 同时驱动多控件 | ✅ 一次推整页 | ❌ 一件一目标，要并列多个子动作 |
| 中途改距离/时长 | 要重写关键帧（静态） | ✅ 表达式现算（运行时决定） |
| 适合 | 固定的入场/转场/进度条 | 弹层高度随内容、可被变量影响的动效 |
