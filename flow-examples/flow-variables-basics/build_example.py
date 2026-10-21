# -*- coding: utf-8 -*-
"""flow-variables-basics —— EEZ Flow「变量的使用方法」示例（纯 EEZ，零 native C）

本文件是工程唯一设计源：由它生成 .eez-project，请勿手改产物。

    python build_example.py        → flow-variables-basics.eez-project
    python design/cli_build.py     → src/ui/（EEZ CLI 生成，勿手改）

演示点 = Flow 变量的**四种用法 + 三条写路径 + 两种作用域**（每条都标了手册页码）：

  【读】① 控件表达式属性：Label.text = g_count            （P8.1 · P.58）
        ② 模板字符串：`count=${g_count} flag=${g_flag}`   （P8.2.8 · P.60）
        ③ Bar.value = g_count（单向 input，只跟随不回写）  （W 属性表）
  【写】④ Slider.value = g_count（assignable，拖动直接回写变量）（P8.2.7/控件 Assignable）
        ⑤ SetVariable 件：单条 / 批量多条                  （A73 · P.188 / P8.1）
        ⑥ Evaluate 件求值 → 数据 result 线 → SetVariable 用输入名 r 接 （A21 · P.53）
  【监听】⑦ Watch 件监听 g_count：变化即触发下游（**启动时必发一次**）（A91 / P8.1）
  【分支】⑧ Switch 件按变量值多路判断（A81/A36 同族，示例用 Switch）
  【作用域】⑨ 全局变量 g_*：所有 Flow 可见
             ⑩ 页面局部变量 l_step：只在定义它的这条 Flow 内可见（P8 · P.57）

变量属性面（同一张变量表，**两条轴**决定它怎么用）：
    flowSupport=false  → 全局变量**必须** native（值活在 C++ 里，UI 侧只能表达式读）
    flowSupport=true   → 全局变量 native=false：值由 Flow 引擎持有（本工程就是这种）
                         全局变量 native=true ：值活在 C++（需自实现 get_var_/set_var_，P-0153）
    persistent         → LVGL 工程**禁用**（手册 P.58：仅 Dashboard）
    defaultValue       → LVGL 且未开 Flow 时**禁用**（无 Flow 时值不由 EEZ 初始化）

文字全用 ASCII：本示例不带中文字体条目，避免把字体链（P-0140）混进变量主题里。
"""
import json
import os
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_FILE = os.path.join(HERE, "flow-variables-basics.eez-project")

SCREEN_W, SCREEN_H = 480, 320

# ---- 设计令牌（深色，与仓库其它示例一致）----
BG = "0x0b0f1a"
PANEL = "0x101a28"
EDGE = "0x26314a"
BTN = "0x1c2440"
TEXT1 = "0xf0f4fc"
TEXT2 = "0x8a99b3"
ACC = "0x3ddc97"

ZERO_PAD = {
    "pad_top": 0, "pad_bottom": 0, "pad_left": 0, "pad_right": 0,
    "pad_row": 0, "pad_column": 0, "border_width": 0, "outline_width": 0,
}

# flags 是**最终态白名单**，漏写会被反向移除（P-0150）；值取自各控件官方 defaultFlags
DEFAULT_FLAGS = {
    "LVGLScreenWidget": "CLICKABLE|CLICK_FOCUSABLE|SCROLLABLE|SCROLL_MOMENTUM|SCROLL_ELASTIC|SNAPPABLE|SCROLL_CHAIN_VER",
    "LVGLLabelWidget": "GESTURE_BUBBLE|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER",
    "LVGLButtonWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_ON_FOCUS|SCROLL_WITH_ARROW|SNAPPABLE",
    "LVGLContainerWidget": "CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SNAPPABLE",
    "LVGLSliderWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_ON_FOCUS|SCROLL_WITH_ARROW|SNAPPABLE",
    "LVGLBarWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_WITH_ARROW|SNAPPABLE",
}


def oid():
    return str(uuid.uuid4())


def widget(wtype, x, y, w, h, identifier=None, flags=None, local=None,
           children=None, eventHandlers=None, **extra):
    wd = {
        "objID": oid(),
        "type": wtype,
        "left": x, "top": y, "width": w, "height": h,
        "customInputs": [], "customOutputs": [],
        "style": {"objID": oid(), "useStyle": "default",
                  "conditionalStyles": [], "childStyles": []},
        "timeline": [],
        "eventHandlers": eventHandlers or [],
        "leftUnit": "px", "topUnit": "px", "widthUnit": "px", "heightUnit": "px",
        "children": children if children is not None else [],
        "widgetFlags": flags if flags is not None else DEFAULT_FLAGS[wtype],
        "hiddenFlagType": "literal", "hiddenFlag": False,
        "clickableFlagType": "literal",
        "flagScrollbarMode": "OFF",
        "checkedStateType": "literal", "disabledStateType": "literal",
        "states": "",
        "localStyles": {"objID": oid(), "definition": local or {}},
        "groupIndex": 0,
    }
    if identifier:
        wd["identifier"] = identifier
    wd.update(extra)
    return wd


def label(x, y, w, h, text, color=TEXT1, identifier=None, expr=None):
    """expr 非空 → textType="expression"（读变量）；否则字面量。"""
    return widget(
        "LVGLLabelWidget", x, y, w, h,
        identifier=identifier,
        local={"MAIN": {"DEFAULT": dict(ZERO_PAD, text_color=color)}},
        text=text if expr is None else expr,
        textType="literal" if expr is None else "expression",
        longMode="WRAP", recolor=False, useStaticText=True,
    )


def button(x, y, w, h, text, identifier):
    """按钮：子 label 用 EEZ 原生新建按钮形态（content 尺寸 + align CENTER，
    与官方 defaultValue 逐字段一致——P-0164 坑 20 定论）。
    handlerType="flow"：点击**不是**走 native 动作，而是把 CLICKED 事件送进 Flow。"""
    lbl = {
        "objID": oid(), "type": "LVGLLabelWidget",
        "left": 0, "top": 0, "width": 80, "height": 32,
        "widthUnit": "content", "heightUnit": "content",
        "text": text, "textType": "literal", "longMode": "WRAP",
        "recolor": False, "useStaticText": True,
        "localStyles": {"objID": oid(), "definition": {"MAIN": {"DEFAULT": {
            "align": "CENTER", "text_color": "0xFFFFFF"}}}},
    }
    return widget(
        "LVGLButtonWidget", x, y, w, h,
        identifier=identifier,
        local={"MAIN": {"DEFAULT": dict(ZERO_PAD, bg_color=BTN, bg_opa=255,
                                        radius=8, border_width=1,
                                        border_color=EDGE)}},
        children=[lbl],
        eventHandlers=[{"objID": oid(), "eventName": "CLICKED",
                        "handlerType": "flow", "userData": 0}],
    )


# --------------------------------------------------------------------------
# Flow 组件（type 名 = 装机 EEZ Studio 里的类名；属性键名 = classInfo 的 name）
# --------------------------------------------------------------------------
def action_component(ctype, x, y, w, h, description="", inputs=None,
                     outputs=None, **props):
    return {
        "objID": oid(),
        "type": ctype,
        "left": x, "top": y, "width": w, "height": h,
        "customInputs": inputs or [],
        "customOutputs": outputs or [],
        "description": description,
        **props,
    }


def set_var(entries, x, y, description="SetVariable", inputs=None):
    """A73 SetVariable：entries = [{variable: 可赋值表达式, value: 表达式}]。
    多条 = 一次执行批量写（手册 P8.1："Multiple entries are allowed"）。"""
    return action_component(
        "SetVariableActionComponent", x, y, 200, 60, description, inputs, [],
        entries=[{"objID": oid(), "variable": k, "value": v} for k, v in entries])


def data_input(name, vtype="any"):
    """自定义数据输入：表达式里**用它的名字**取值（P8.2.7："input_name"）。
    ★ 显式给 type，否则 Checks 检查器会一直转圈（P-0146 实证）。"""
    return {"objID": oid(), "name": name, "type": vtype}


def line(src, output, dst, inp):
    return {"objID": oid(), "source": src, "output": output,
            "target": dst, "input": inp}


def page(children, flow_components, conns, local_vars):
    screen = widget("LVGLScreenWidget", 0, 0, SCREEN_W, SCREEN_H,
                    local={"MAIN": {"DEFAULT": dict(ZERO_PAD, bg_color=BG,
                                                    bg_opa=255, radius=0)}},
                    children=children)
    return {
        "objID": oid(),
        "components": [screen] + flow_components,
        "connectionLines": conns,
        "localVariables": local_vars,
        "componentGroups": [],
        "userProperties": [],
        "name": "Main",
        "left": 0, "top": 0,
        "width": SCREEN_W, "height": SCREEN_H,
        "isUsedAsUserWidget": False,
        "createAtStart": True,
        "deleteOnScreenUnload": False,
    }


def build_project():
    # ================= 1. 控件（读/写变量的 UI） =================
    w_btn_add = button(16, 156, 104, 30, "+1 (SetVariable)", "btn_add")
    w_btn_many = button(128, 156, 104, 30, "批量写", "btn_many")
    w_btn_eval = button(240, 156, 104, 30, "Evaluate", "btn_eval")
    w_btn_local = button(352, 156, 112, 30, "+l_step", "btn_local")

    children = [
        label(16, 10, 448, 20, "EEZ Flow - how to USE variables", TEXT1,
              "lbl_title"),

        # —— 读路径 ①②：Label 表达式属性 + 模板字符串
        label(16, 34, 150, 18, "g_count (expression)", TEXT2, "cap_count"),
        label(170, 34, 60, 18, "", ACC, "val_count", expr="g_count"),
        label(240, 34, 224, 18, "", TEXT1, "val_tpl",
              expr="`count=${g_count} double=${g_double} flag=${g_flag}`"),
        # —— 谁写的看得见：Watch 写 g_status，Switch 写 g_branch
        label(16, 56, 150, 18, "g_status (Watch)", TEXT2, "cap_status"),
        label(170, 56, 294, 18, "", TEXT1, "val_status", expr="g_status"),
        label(16, 78, 150, 18, "g_branch (Switch)", TEXT2, "cap_branch"),
        label(170, 78, 294, 18, "", ACC, "val_branch", expr="g_branch"),
        # —— 读路径 ③：Bar 单向跟随（值改了 UI 自动走，但拖不动它）
        label(16, 100, 150, 18, "Bar = g_count (read)", TEXT2, "cap_bar"),
        widget("LVGLBarWidget", 170, 100, 294, 16, identifier="bar_count",
               min=0, minType="literal", max=20, maxType="literal",
               mode="NORMAL", value="g_count", valueType="expression",
               showProgress=False,
               local={"MAIN": {"DEFAULT": dict(ZERO_PAD, bg_color=PANEL,
                                               bg_opa=255, radius=6)}}),
        # —— 写路径 ④：Slider.value 是 assignable，拖动**回写**变量
        label(16, 124, 150, 18, "Slider -> g_count", TEXT2, "cap_sld"),
        widget("LVGLSliderWidget", 170, 124, 294, 24, identifier="sld_count",
               min=0, minType="literal", max=20, maxType="literal",
               mode="NORMAL", value="g_count", valueType="expression",
               previewValue=0, enableAnimation=False),

        w_btn_add, w_btn_many, w_btn_eval, w_btn_local,

        label(16, 196, 464, 32,
              "each button feeds a SetVariable / Evaluate / Switch node; "
              "Watch node watches g_count with no button at all", TEXT2,
              "cap_flow"),
    ]

    # ================= 2. Flow 组件（写变量的四种路子） =================
    # ⑤ 单条 SetVariable
    f_add = set_var([("g_count", "g_count + 1")], 16, 214,
                    description="写路径⑤：SetVariable 单条")
    # ⑤' 批量 SetVariable（一次写多个变量）
    f_many = set_var([("g_count", "0"),
                      ("g_double", "0"),
                      ("g_flag", "false"),
                      ('g_status', '"idle"'),
                      ('g_branch', '"none"')], 240, 214,
                     description="写路径⑤'：SetVariable 批量")
    # ⑥ Evaluate 求值 → result 数据线 → SetVariable 用输入名接住
    f_eval = action_component(
        "EvalExprActionComponent", 464, 214, 160, 60,
        description="写路径⑥：Evaluate 求值",
        expression="g_count * 2")
    f_store = set_var([("g_double", "r")], 464, 300,
                      description="写路径⑥'：result 线写回 g_double",
                      inputs=[data_input("r")])
    # ⑩ 局部变量用法：l_step 只在这条 Flow 内可见
    f_local = set_var([("g_count", "g_count + l_step")], 680, 214,
                      description="作用域⑩：读页面局部变量 l_step")
    # ⑦ Watch：监听 g_count，变化即触发（启动时先必发一次）
    f_watch = action_component(
        "WatchVariableActionComponent", 16, 300, 180, 40,
        description="监听⑦：Watch g_count",
        variable="g_count")
    f_flag = set_var([("g_flag", "v > 3"),
                      ('g_status', '`${v} is watched`')], 240, 300,
                     description="监听⑦'：变化结果写回",
                     inputs=[data_input("v")])
    # ⑧ Switch：按变量值分支（命中 FULL 写**另一个**变量 g_branch——
    #     故意不复用 g_status，否则和 Watch 链抢同一个变量，演示结论会含糊）
    f_switch = action_component(
        "SwitchActionComponent", 16, 370, 180, 44,
        description="分支⑧：Switch 判 g_count",
        tests=[{"objID": oid(), "condition": "g_count >= 10",
                "outputName": "FULL"}])
    f_full = set_var([('g_branch', '"full (>=10)"')], 240, 390,
                     description="分支⑧'：命中后写 g_branch")

    flow_components = [f_add, f_many, f_eval, f_store, f_local,
                       f_watch, f_flag, f_switch, f_full]

    # ================= 3. 连线 =================
    # 事件件的输出名 = 事件名；时序线走 @seqin，数据线走自定义输入名
    conns = [
        line(w_btn_add["objID"], "CLICKED", f_add["objID"], "@seqin"),
        line(w_btn_many["objID"], "CLICKED", f_many["objID"], "@seqin"),
        line(w_btn_eval["objID"], "CLICKED", f_eval["objID"], "@seqin"),
        line(w_btn_local["objID"], "CLICKED", f_local["objID"], "@seqin"),
        # Evaluate：@seqout（执行线）+ result（数据线）双连——
        # 只连数据线会被"至少一条时序输入"卡住（P6.2 就绪判定）
        line(f_eval["objID"], "@seqout", f_store["objID"], "@seqin"),
        line(f_eval["objID"], "result", f_store["objID"], "r"),
        # Watch：变化的值从 variable 输出（面板上显示为 changed）
        line(f_watch["objID"], "@seqout", f_flag["objID"], "@seqin"),
        line(f_watch["objID"], "variable", f_flag["objID"], "v"),
        # Switch：串在 +1 之后判阈值
        line(f_add["objID"], "@seqout", f_switch["objID"], "@seqin"),
        line(f_switch["objID"], "FULL", f_full["objID"], "@seqin"),
    ]

    # ================= 4. 变量表 =================
    # 全局：native=false ⇒ 值由 Flow 引擎持有（开 Flow 才有这一形态）
    gvs = [
        {"objID": oid(), "name": "g_count", "type": "integer",
         "defaultValue": "0", "persistent": False, "native": False},
        {"objID": oid(), "name": "g_double", "type": "integer",
         "defaultValue": "0", "persistent": False, "native": False},
        {"objID": oid(), "name": "g_flag", "type": "boolean",
         "defaultValue": "false", "persistent": False, "native": False},
        {"objID": oid(), "name": "g_status", "type": "string",
         "defaultValue": '"idle"', "persistent": False, "native": False},
        {"objID": oid(), "name": "g_branch", "type": "string",
         "defaultValue": '"none"', "persistent": False, "native": False},
    ]
    # 页面局部：只在定义它的那条 Flow 内可见（P8 · P.57）
    local_vars = [
        {"objID": oid(), "name": "l_step", "type": "integer",
         "defaultValue": "1", "persistent": False, "native": False},
    ]

    return {
        "themesVersion": 1, "objID": oid(),
        "settings": {
            "objID": oid(),
            "general": {
                "objID": oid(),
                "projectVersion": "v3",
                "projectType": "lvgl",
                "lvglVersion": "9.4.0",
                "extensions": [],
                "imports": [],
                "flowSupport": True,
                "displayWidth": SCREEN_W,
                "displayHeight": SCREEN_H,
                "circularDisplay": False,
                "displayBorderRadius": 0,
                "darkTheme": True,
                "colorBpp": "16",
                "bitmapColorFormat": "BGR",
                "resourceFiles": [],
                "hiddenWidgetLines": "dimmed",
                "dimmedLinesOpacity": "20",
                "embedBitmaps": True,
                "embedFonts": True,
                "cacheFonts": True,
            },
            "build": {
                "objID": oid(),
                "configurations": [{"objID": oid(), "name": "Default"}],
                "destinationFolder": "src\\ui",
                "separateFolderForImagesAndFonts": True,
                "imageExportMode": "source",
                "fontExportMode": "source",
                "fileSystemPath": "",
                "lvglInclude": "lvgl.h",
                "screensLifetimeSupport": False,
                "useDockerDesktop": True,
                "generateSourceCodeForEezFramework": True,
                "compressFlowDefinition": False,
                "executionQueueSize": 1000,
                "expressionEvaluatorStackSize": 20,
                "files": [
                    {"objID": oid(), "fileName": name, "template": tmpl}
                    for name, tmpl in BUILD_TEMPLATES.items()
                ],
            },
        },
        "variables": {
            "objID": oid(),
            "globalVariables": gvs,
            "structures": [], "enums": [],
        },
        "actions": [],
        "userPages": [page(children, flow_components, conns, local_vars)],
        "userWidgets": [],
        "lvglStyles": {"objID": oid(), "styles": [], "defaultStyles": {}},
        "lvglGroups": {"objID": oid(), "groups": []},
        "fonts": [],
        "bitmaps": [], "colors": [],
        "themes": [{"objID": oid(), "name": "Default", "colors": []}],
    }


BUILD_TEMPLATES = {
    'screens.h': '#ifndef EEZ_LVGL_UI_SCREENS_H\r\n#define EEZ_LVGL_UI_SCREENS_H\r\n\r\n//${eez-studio LVGL_INCLUDE}\r\n\r\n#ifdef __cplusplus\r\nextern "C" {\r\n#endif\r\n\r\n//${eez-studio LVGL_SCREENS_DECL}\r\n//${eez-studio LVGL_SCREENS_DECL_EXT}\r\n\r\n#ifdef __cplusplus\r\n}\r\n#endif\r\n\r\n#endif /*EEZ_LVGL_UI_SCREENS_H*/',
    'screens.c': '#include <string.h>\n\n#include "screens.h"\n#include "images.h"\n#include "fonts.h"\n#include "actions.h"\n#include "vars.h"\n#include "styles.h"\n#include "ui.h"\n\n//${eez-studio LVGL_SCREENS_DEF}\n//${eez-studio LVGL_SCREENS_DEF_EXT}',
    'actions.h': '#ifndef EEZ_LVGL_UI_EVENTS_H\r\n#define EEZ_LVGL_UI_EVENTS_H\r\n\r\n//${eez-studio LVGL_INCLUDE}\r\n\r\n#ifdef __cplusplus\r\nextern "C" {\r\n#endif\r\n\r\n//${eez-studio LVGL_ACTIONS_DECL}\r\n\r\n#ifdef __cplusplus\r\n}\r\n#endif\r\n\r\n#endif /*EEZ_LVGL_UI_EVENTS_H*/',
    'vars.h': '#ifndef EEZ_LVGL_UI_VARS_H\r\n#define EEZ_LVGL_UI_VARS_H\r\n\r\n#include <stdint.h>\r\n#include <stdbool.h>\r\n\r\n#ifdef __cplusplus\r\nextern "C" {\r\n#endif\r\n\r\n// enum declarations\r\n\r\n//${eez-studio FLOW_ENUMS}\r\n\r\n// Flow global variables\r\n\r\n//${eez-studio FLOW_GLOBAL_VARIABLES_ENUM}\r\n\r\n// Native global variables\r\n\r\n//${eez-studio LVGL_VARS_DECL}\r\n\r\n#ifdef __cplusplus\r\n}\r\n#endif\r\n\r\n#endif /*EEZ_LVGL_UI_VARS_H*/',
    'structs.h': '#ifndef EEZ_LVGL_UI_STRUCTS_H\n#define EEZ_LVGL_UI_STRUCTS_H\n\n//${eez-studio EEZ_FOR_LVGL_CHECK}\n\n#if defined(EEZ_FOR_LVGL)\n\n#include <eez/flow/flow.h>\n#include <stdint.h>\n#include <stdbool.h>\n\n#include "vars.h"\n\nusing namespace eez;\n\n//${eez-studio FLOW_STRUCTS}\n\n//${eez-studio FLOW_STRUCT_VALUES}\n\n#endif\n\n#endif /*EEZ_LVGL_UI_STRUCTS_H*/\n',
    'images.h': '#ifndef EEZ_LVGL_UI_IMAGES_H\r\n#define EEZ_LVGL_UI_IMAGES_H\r\n\r\n//${eez-studio LVGL_INCLUDE}\r\n\r\n#ifdef __cplusplus\r\nextern "C" {\r\n#endif\r\n\r\n//${eez-studio LVGL_IMAGES_DECL}\r\n\r\n#ifdef __cplusplus\r\n}\r\n#endif\r\n\r\n#endif /*EEZ_LVGL_UI_IMAGES_H*/',
    'images.c': '#include "images.h"\n\n//${eez-studio LVGL_IMAGES_DEF}',
    'fonts.h': '#ifndef EEZ_LVGL_UI_FONTS_H\r\n#define EEZ_LVGL_UI_FONTS_H\r\n\r\n//${eez-studio LVGL_INCLUDE}\r\n\r\n#ifdef __cplusplus\r\nextern "C" {\r\n#endif\r\n\r\n//${eez-studio LVGL_FONTS_DECL}\r\n\r\n#ifdef __cplusplus\r\n}\r\n#endif\r\n\r\n#endif /*EEZ_LVGL_UI_FONTS_H*/',
    'styles.h': '#ifndef EEZ_LVGL_UI_STYLES_H\r\n#define EEZ_LVGL_UI_STYLES_H\r\n\r\n//${eez-studio LVGL_INCLUDE}\r\n\r\n#ifdef __cplusplus\r\nextern "C" {\r\n#endif\r\n\r\n//${eez-studio LVGL_STYLES_DECL}\r\n\r\n#ifdef __cplusplus\r\n}\r\n#endif\r\n\r\n#endif /*EEZ_LVGL_UI_STYLES_H*/',
    'styles.c': '#include "styles.h"\n#include "images.h"\n#include "fonts.h"\n\n//${eez-studio LVGL_STYLES_DEF}\n',
    'ui.h': '#ifndef EEZ_LVGL_UI_GUI_H\n#define EEZ_LVGL_UI_GUI_H\n\n//${eez-studio LVGL_INCLUDE}\n\n//${eez-studio EEZ_FOR_LVGL_CHECK}\n\n#if defined(EEZ_FOR_LVGL)\n#include <eez/flow/lvgl_api.h>\n#endif\n\n#if !defined(EEZ_FOR_LVGL)\n#include "screens.h"\n#endif\n\n#ifdef __cplusplus\nextern "C" {\n#endif\n\n//${eez-studio GUI_ASSETS_DECL}\n\nvoid ui_init();\nvoid ui_tick();\n\n#if !defined(EEZ_FOR_LVGL)\nvoid loadScreen(enum ScreensEnum screenId);\n#endif\n\n#ifdef __cplusplus\n}\n#endif\n\n#endif // EEZ_LVGL_UI_GUI_H',
    'ui.c': '#if defined(EEZ_FOR_LVGL)\n#include <eez/core/vars.h>\n#endif\n\n#include "ui.h"\n#include "screens.h"\n#include "images.h"\n#include "actions.h"\n#include "vars.h"\n\n//${eez-studio GUI_ASSETS_DEF}\n\n//${eez-studio LVGL_NATIVE_VARS_TABLE_DEF}\n\n//${eez-studio LVGL_ACTIONS_ARRAY_DEF}\n\n#if defined(EEZ_FOR_LVGL)\n\nvoid ui_init() {\n    eez_flow_init(assets, sizeof(assets), (lv_obj_t **)&objects, sizeof(objects), images, sizeof(images), actions);\n}\n\nvoid ui_tick() {\n    eez_flow_tick();\n    tick_screen(g_currentScreen);\n}\n\n#else\n\nstatic int16_t currentScreen = -1;\n\nstatic lv_obj_t *getLvglObjectFromIndex(int32_t index) {\n    if (index == -1) {\n        return 0;\n    }\n    return ((lv_obj_t **)&objects)[index];\n}\n\nvoid loadScreen(enum ScreensEnum screenId) {\n    currentScreen = screenId - 1;\n    lv_obj_t *screen = getLvglObjectFromIndex(currentScreen);\n    lv_scr_load_anim(screen, LV_SCR_LOAD_ANIM_FADE_IN, 200, 0, false);\n}\n\nvoid ui_init() {\n    create_screens();\n//${eez-studio LVGL_LOAD_FIRST_SCREEN}\n}\n\nvoid ui_tick() {\n    tick_screen(currentScreen);\n}\n\n#endif\n',
}


def _assert_flow_boxes(flow_components):
    """流组件在画布上不许互相压着（叠在一起时 Studio 里根本看不出连线走向，
    而且改一个件的坐标会连带看不见另一个）。屏幕件不算（它是 UI 层）。"""
    boxes = [(c.get("description") or c["type"], c["left"], c["top"],
              c["width"], c["height"]) for c in flow_components]
    for i, (n, x, y, w, h) in enumerate(boxes):
        for n2, x2, y2, w2, h2 in boxes[i + 1:]:
            if x < x2 + w2 and x2 < x + w and y < y2 + h2 and y2 < y + h:
                raise SystemExit("流组件画布重叠：%s × %s" % (n, n2))


def main():
    data = build_project()
    _assert_flow_boxes(data["userPages"][0]["components"][1:])
    with open(PROJECT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("written: %s (%d bytes)"
          % (PROJECT_FILE, os.path.getsize(PROJECT_FILE)))


if __name__ == "__main__":
    main()
