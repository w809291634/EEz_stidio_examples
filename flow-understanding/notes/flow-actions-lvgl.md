# Flow 动作件清单（LVGL 工程视角）—— 以装机 Studio 为准，手册只是二手

> 生成方式（可复现）：`python flow-understanding/tools/extract_studio_facts.py`
> → `_lvgl_palette_availability.txt`（件级可用性）+ `_lvgl_action_registry_extract.txt`（A43 子动作注册表）。
> 数据源是**本机 EEZ Studio 0.29 的 `app.asar`**（★ 机器相关路径，换机请传参）。
> 手册对应位置：P7.3（P.52，LVGL 的 Actions 面板是 **Fig.78 图片，没有文字清单**）、附录 A43（第 215–223 页）。

## 1. 为什么不能只读手册（本次实测出来的三条证据层级）

| 层级 | 判据 | 能回答什么 | 局限 |
|---|---|---|---|
| ① 手册文字 | 附录 A1–A92 | 件的**语义与属性** | **滞后**：A43 手册列 63 项，装机注册表 **65 项**（对账产物 `notes/_manual_vs_registry_diff.txt`：真缺 `objGetDisplayX`/`objGetDisplayY` 两项，其余 63 项**措辞零差异**）；P7.3 明说"件的数量随工程类型而变"，但 LVGL 那张面板**是图片**，文字里查不到 |
| ② 装机包的面板谓词 | `enabledInComponentPalette` | LVGL 工程**能不能把这个件拖进来** | "能拖进来" ≠ "构建出来的 C++ 里有实现" |
| ③ CLI 构建产物 | 生成的 `src/ui/` | 该件的**代码真被发射/能否跑** | 只能逐个件实测（→ `EXAMPLE_PLAN.md` 示例②③） |

**规矩**：以后判"EEZ 能不能做 X"，必须先过②（本文件），再做③（示例实测），
手册①只用来解释语义。**只凭手册下"框架做不到 X"的结论，一律无效。**

## 2. 件级可用性（从装机包抽出来的判定）

### 2.1 ★ LVGL 面板**禁用**的 9 件（谓词含 `"lvgl"!==e`）

| 件 | 手册条目 | 备注 |
|---|---|---|
| `OnEvent` | A53 | **LVGL 里做不了"页面 open/close 事件流"** |
| `ShowPage` | A78 | LVGL 换页走 **A43 的 `changeScreen`**，不是 ShowPage |
| `ShowKeyboard` | A75 | LVGL 用真 `lv_keyboard` 控件 + A43 `keyboardSetTextarea` |
| `ShowKeypad` | A76 | 同上，LVGL 无此件 |
| `ShowMessageBox` | A77 | LVGL 无内置消息框件（自建容器弹层） |
| `OverrideStyle` | A55 | **只能 EEZ-GUI**（样式覆盖）；LVGL 用 A43 `objAddStyle/objRemoveStyle/objStyleSetProperty` |
| `SelectLanguage` | A65 | **LVGL 没有语言切换件**（i18n 要自己接） |
| `SetPageDirection` | A72 | LTR/RTL 是 GUI 页概念，LVGL 无 |
| `SCPI` | A63 | 仪表件 |

> 直接后果：`EXAMPLE_PLAN.md` 第一版里我按手册提的三件事——
> **OnEvent 页面生命周期(⑦)、ShowKeyboard/Keypad(⑨)、SelectLanguage 多语言(⑪)**——
> 在 LVGL 工程里**根本拖不出来**，已按 §4 改写。

### 2.2 ★ LVGL **专属**件

- `LVGL`（A43 / `COMPONENT_TYPE_LVGL_ACTION_API`，面板组 `!2LVGL`）——
  谓词 `e=>"lvgl"===e`，**只在 LVGL 工程出现**；内含 65 个子动作（§3）。

### 2.3 面板允许（仍需③实测）的件

`Animate(A2)`、`Compare(A8)`、`Constant(A10)`、`Counter(A11)`、`CatchError`、`Error(A19)`、
`Evaluate(A21)`、`Input(A32)`、`IsTrue(A36)`、`Output(A54)`、`SortArray(A79)`、`TestAndSet(A88)`、
`MQTT*(A45–A51)`、`SetVariable(A73)`、`Watch(A91)`、`Loop(A42)`、`Delay(A15)`、`Start/End(A80/A18)`、
`SwitchCase(A81)`、`Label IN/OUT(A39/A40)`、`Comment(A7)`、`NoOp(A52)`、`Log(A41)`、
`SetColorTheme`、`DynamicCallAction(A17)`。

⚠ 其中 **`MQTT*` / `Log` / `EvalJS` / `File*` / `Serial*` / `TCP*` / `UDP*` / `Python*` / `HTTP` / `Modbus`**
虽然在包里没有被 `"lvgl"!==e` 挡掉，但它们的属性依赖 `object:` 变量类型，而 **`object` 变量是 Dashboard 专属**
（手册 P8.2.4）→ **LVGL 里连输入都喂不进去，视同不可用**。别据此立项示例。

## 3. A43 `LVGL` 件的 65 个子动作（装机注册表，含手册没写的 2 项）

> 属性名照注册表原文（`object` 用**控件 identifier** 引用——手册在控件 `Name` 属性处说明
> "we reference the Widget within the project by its name, for example in the LVGL action"）。

| 组（装机注册表的 `group` 字段，逐条核对） | 数量 | 子动作 |
|---|---|---|
| Screen | 5 | `changeScreen`(screen, fadeMode, speed, delay, **useStack**) · `changeToPreviousScreen`(fadeMode, speed, delay) · `createScreen` · `deleteScreen` · `isScreenCreated`(→ result) |
| Widget - Position and Size | 10 | `objSetX`/`objGetX` · `objSetY`/`objGetY` · `objSetWidth`/`objGetWidth` · `objSetHeight`/`objGetHeight` · **`objGetDisplayX` / `objGetDisplayY`（手册没有这两项）** |
| Widget - Styles | 5 | `objSetStyleOpa` / `objGetStyleOpa` · `objAddStyle` · `objRemoveStyle` · `objStyleSetProperty`(property, value, part, state) |
| Widget - Flags | 5 | `objSetFlagHidden` · `objAddFlag` · `objClearFlag` · `objHasFlag`(→ result) · **`objSetStateChecked`（注册表把它归在 Flags，不是 States）** |
| Widget - States | 4 | `objSetStateDisabled` · `objAddState` · `objClearState` · `objHasState`(→ result) |
| Group（焦点） | 7 | `groupFocusObj` · `groupFocusNext` · `groupFocusPrev` · `groupGetFocused`(→ result) · `groupFocusFreeze` · `groupSetWrap` · `groupSetEditing` |
| Animation | 7 | `animX` · `animY` · `animWidth` · `animHeight` · `animOpacity` · `animImageZoom` · `animImageAngle`（共同属性：object, start, end, delay, time, relative, instant, path） |
| 控件专用 | 22 | Arc 2：`arcSetValue`、`arcRotateObjToAngle`(objToRotate, offset) · Bar 1：`barSetValue`(animated) · Slider 3：`sliderSetValue`(animated)、`sliderSetValueLeft`、`sliderSetRange`(min,max) · Dropdown 1：`dropdownSetSelected` · Roller 1：`rollerSetSelected`(animated) · Tabview 2：`tabviewSetActiveTab`、`tabviewGetActiveTab` · Label 1：`labelSetText` · Image 3：`imageSetSrc`、`imageSetAngle`(0.1°)、`imageSetZoom`(256=1×) · Keyboard 1：`keyboardSetTextarea` · QRCode 1：`qrCodeUpdate` · Calendar 4：`setTodayDate`、`setShowedDate`、`setHighlightedDate`、`getPressedDate` · ButtonMatrix 2：`setButtonCtrl`、`clearButtonCtrl` |
| 输入/输出 | — | `seqin SEQ\|OPTIONAL`、`seqout SEQ\|OPTIONAL`（手册原话："标准时序输入/输出"，**不带数据**） |

> 合计 5+10+5+5+4+7+7+22 = **65**，与 `_lvgl_action_registry_extract.txt` 逐条一致（可重跑脚本对账）。

★ 三条能直接改变我们写法的读解：

1. **弹层/半页动画有原生路子**：`objSetFlagHidden` + `animY`/`animOpacity` + `objSetY`
   —— WiFi 待做的"密码半页上滑"不必再用 native 手搓（前提是③实测通得过）；
2. **编码器/旋钮导航有原生路子**：`groupFocus*` / `groupSetWrap` / `groupSetEditing`
   配合工程 JSON 里的 `lvglGroups` 段——医疗器械物理编码器的焦点管理可以在 EEZ 里配；
3. **`changeScreen.useStack`** 手册只给一句"Put active screen on the stack"，
   栈的语义（深度、弹出是否销毁屏幕）没写 → 属③必须实测项。

## 4. `Animate(A2)` 的 LVGL 疑点（单列，别当已确认）

包里的谓词是 `"eez-gui-lite"!==e` → **LVGL 面板允许**；
但手册 A2 描述通篇是"**Page/User Widget 的动画时间线**"语义（From/To 单位是**秒**、Speed 是倍率、
`seqout` 在动画放完时触发），而 LVGL 侧我们已知控件 JSON 里有 `timeline: []` 字段。
→ **到底在 LVGL 工程里能不能真的动，属③未验证**。`EXAMPLE_PLAN.md` 已把它列为示例③的一个必测项，
不许再拿"手册写着 Animate"当可行性依据。

## 5. 附带发现：native 变量类型（推翻仓库旧口径，待实测）

装机包里 LVGL 工程类型的 traits 原话：

```js
isVariableTypeSupportedAsNative(e) =>
    isEnumType(e) || "integer" == e || "float" == e || "double" == e || "boolean" == e || "string" == e
```

→ **官方认为 LVGL 的 native 变量支持 enum/integer/float/double/boolean/string**。
而本仓库现在的口径是"稳定可用的只有 integer/string，**布尔要用 integer 0/1**"
（`07_project_json_schema.md` §3 / 经验库记载，来自我们踩过的 `get_var_*/set_var_*` 签名问题）。
**两者冲突**：很可能是"面板/traits 允许"与"代码生成的桥签名"两层不一致。
→ 已列为示例候选（`EXAMPLE_PLAN.md` 新增 **⑬ native 变量类型矩阵**），实测出结论后回灌经验库并改那一句。
