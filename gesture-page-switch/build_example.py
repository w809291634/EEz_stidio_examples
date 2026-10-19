# -*- coding: utf-8 -*-
"""gesture-page-switch —— 页面手势切换示例（生成器）

本文件是示例的唯一设计源：gesture-page-switch.eez-project 由它生成，请勿手改产物。

    python build_example.py      # 重新生成 gesture-page-switch.eez-project

演示点（KB 依据：P-0123 / P-0141 / §11.35 / §11.41 / §48）：
  1. 多个「独立 screen」+ GESTURE 离散切屏，取代 tabview 跟手 —— 绕开「跟手 vs 独立屏互斥」。
  2. changeScreen 用 fadeMode='NONE' —— 无动画竞态，绕开 P-0029「陈旧 SCROLL_END 拉回旧 tab」的空转。
  3. 导航**完全不依赖 CHECKED 高亮链** —— 从设计上根除「高亮随手势不更新 / 状态来回翻」的空转。
  4. Switch 组件的 evt 输入显式 type:'any' —— 这是 §48 实证：缺了它 EEZ 后台 Checks 检查器持续转圈。
  5. 手势收件人规则：host 容器去掉 GESTURE_BUBBLE，子 label 保留 —— 冒泡链上第一个无该标志的祖先收件。

屏幕基线：480x320 · LVGL 9.4 · EEZ Studio 0.29（工程模型 projectVersion=v3）。
验证：CLI 构建 0 错 0 警；手势行为本身只能在 PC_SIM/真机验收（Run 预览不产生 GESTURE，见 P-0141）。
"""
import json
import os
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_FILE = os.path.join(HERE, "gesture-page-switch.eez-project")

SCREEN_W, SCREEN_H = 480, 320

# ---------------------------------------------------------------------------
# 构建模板：与 EEZ Studio 0.29 新建 LVGL 工程的 settings.build.files 逐字一致。
# ---------------------------------------------------------------------------
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

# 各控件类型的默认 widgetFlags（LVGL 9 口径，取自 EEZ Studio 0.29 控件定义）
DEFAULT_FLAGS = {
    "LVGLScreenWidget": "CLICKABLE|CLICK_FOCUSABLE|SCROLLABLE|SCROLL_MOMENTUM|SCROLL_ELASTIC|SNAPPABLE|SCROLL_CHAIN_VER",
    "LVGLLabelWidget": "GESTURE_BUBBLE",
    "LVGLContainerWidget": "GESTURE_BUBBLE",
}

ZERO_PAD = {
    "pad_top": 0, "pad_bottom": 0, "pad_left": 0, "pad_right": 0,
    "pad_row": 0, "pad_column": 0, "border_width": 0, "outline_width": 0,
}


def oid():
    return str(uuid.uuid4())


def widget(wtype, x, y, w, h, identifier=None, flags=None, local=None,
           children=None, **extra):
    wd = {
        "objID": oid(),
        "type": wtype,
        "left": x,
        "top": y,
        "width": w,
        "height": h,
        "customInputs": [],
        "customOutputs": [],
        "style": {"objID": oid(), "useStyle": "default",
                  "conditionalStyles": [], "childStyles": []},
        "timeline": [],
        "eventHandlers": [],
        "leftUnit": "px",
        "topUnit": "px",
        "widthUnit": "px",
        "heightUnit": "px",
        "children": children if children is not None else [],
        "widgetFlags": flags if flags is not None else DEFAULT_FLAGS[wtype],
        "hiddenFlagType": "literal",
        "clickableFlagType": "literal",
        "flagScrollbarMode": "OFF",
        "checkedStateType": "literal",
        "disabledStateType": "literal",
        "states": "",
        "localStyles": {"objID": oid(), "definition": local or {}},
        "groupIndex": 0,
    }
    if identifier:
        wd["identifier"] = identifier
    wd.update(extra)
    return wd


def label(x, y, w, h, text, color="0xFFFFFF", identifier=None):
    props = dict(ZERO_PAD, text_color=color)
    return widget(
        "LVGLLabelWidget", x, y, w, h,
        identifier=identifier,
        local={"MAIN": {"DEFAULT": props}},
        text=text,
        textType="literal",
        longMode="WRAP",
        recolor=False,
        useStaticText=True,
    )


def gesture_switch(name, gdir, target):
    """判定组件（SwitchActionComponent）：比较手势方向，命中则 GO。

    ★ evt 输入显式 type:'any' —— 缺了它 EEZ 后台 Checks 检查器持续转圈（KB §48 实证）。
    gdir: 1=LV_DIR_LEFT（左滑）  2=LV_DIR_RIGHT（右滑）
    """
    evt = {"objID": oid(), "name": "evt", "type": "any"}
    return {
        "objID": oid(),
        "type": "SwitchActionComponent",
        "left": 60, "top": 250, "width": 240, "height": 80,
        "customInputs": [evt],
        "customOutputs": [],
        "description": "判定 dir==%d -> %s" % (gdir, target),
        "tests": [{"objID": oid(),
                   "condition": "Event.getGestureDir(evt) == %d" % gdir,
                   "outputName": "GO"}],
    }


def gesture_action(name, target):
    """跳转组件（LVGLActionComponent）：离散切屏，fadeMode=NONE 无动画竞态。"""
    return {
        "objID": oid(),
        "type": "LVGLActionComponent",
        "left": 360, "top": 250, "width": 220, "height": 60,
        "customInputs": [],
        "customOutputs": [],
        "description": "切到 %s" % target,
        "actions": [{
            "objID": oid(),
            "action": "changeScreen",
            "screen": target,          # 引用目标页的 name
            "fadeMode": "NONE",        # 无动画 -> 绕开 P-0029 拉回竞态
            "speed": 0,
            "delay": 0,
            "useStack": False,
        }],
    }


def gesture_host(name, bg_color, left_target, right_target):
    """屏根下的 host 容器：挂 GESTURE 事件，且自身去掉 GESTURE_BUBBLE（成为收件人）。

    子 label 保留 GESTURE_BUBBLE，手势从 label 冒泡上来被本容器收件。
    """
    lbl_title = label(40, 120, 400, 48, "PAGE %s" % name, color="0xFFFFFF",
                      identifier="%s_title" % name.lower())
    lbl_hint = label(40, 180, 400, 40,
                    "swipe LEFT -> %s   swipe RIGHT -> %s"
                    % (left_target, right_target),
                    color="0xCCCCCC", identifier="%s_hint" % name.lower())
    return widget(
        "LVGLContainerWidget", 0, 0, SCREEN_W, SCREEN_H,
        identifier="host_%s" % name.lower(),
        # ★ 关键：容器本身不含 GESTURE_BUBBLE，否则它只是个透明转发层，收不到手势
        flags="CLICKABLE|CLICK_FOCUSABLE|PRESS_LOCK",
        local={"MAIN": {"DEFAULT": dict(ZERO_PAD, bg_opa=0)}},
        children=[lbl_title, lbl_hint],
        eventHandlers=[{"objID": oid(), "eventName": "GESTURE",
                        "handlerType": "flow", "userData": 0}],
    )


def gesture_page(name, bg_color, left_target, right_target, is_first):
    """一页 = 铺满屏的 LVGLScreenWidget + host 容器 + 左右两个「判定+跳转」流组件。"""
    screen = widget(
        "LVGLScreenWidget", 0, 0, SCREEN_W, SCREEN_H,
        identifier="screen_%s" % name.lower(),
        children=[gesture_host(name, bg_color, left_target, right_target)],
        local={"MAIN": {"DEFAULT": {
            "bg_color": bg_color, "bg_opa": 255, "radius": 0, "border_width": 0}}},
    )
    host_id = screen["children"][0]["objID"]

    sw_left = gesture_switch(name + "_L", 1, left_target)
    sw_right = gesture_switch(name + "_R", 2, right_target)
    lv_left = gesture_action(name + "_L", left_target)
    lv_right = gesture_action(name + "_R", right_target)

    conns = [
        # GESTURE 双线：执行线 -> @seqin，数据线 -> evt（都用裸名 'GESTURE'）
        {"objID": oid(), "source": host_id, "output": "GESTURE",
         "target": sw_left["objID"], "input": "@seqin"},
        {"objID": oid(), "source": host_id, "output": "GESTURE",
         "target": sw_left["objID"], "input": "evt"},
        {"objID": oid(), "source": host_id, "output": "GESTURE",
         "target": sw_right["objID"], "input": "@seqin"},
        {"objID": oid(), "source": host_id, "output": "GESTURE",
         "target": sw_right["objID"], "input": "evt"},
        # 判定命中 -> 跳转（每个 GO 都连接，避免 Checks 报 not connected）
        {"objID": oid(), "source": sw_left["objID"], "output": "GO",
         "target": lv_left["objID"], "input": "@seqin"},
        {"objID": oid(), "source": sw_right["objID"], "output": "GO",
         "target": lv_right["objID"], "input": "@seqin"},
    ]

    return {
        "objID": oid(),
        "components": [screen, sw_left, sw_right, lv_left, lv_right],
        "connectionLines": conns,
        "localVariables": [],
        "componentGroups": [],
        "userProperties": [],
        "name": name,                       # changeScreen 用此 name 引用
        "left": 0, "top": 0, "width": SCREEN_W, "height": SCREEN_H,
        "isUsedAsUserWidget": False,
        "createAtStart": is_first,           # 仅首屏启动即建，其余按需 changeScreen
        "deleteOnScreenUnload": False,
    }


def build_project():
    # 3 页循环切换：A(蓝) L->B R->C / B(绿) L->C R->A / C(红) L->A R->B
    pages = [
        gesture_page("A", "0x103A6B", "B", "C", True),
        gesture_page("B", "0x14532D", "C", "A", False),
        gesture_page("C", "0x7A1E1E", "A", "B", False),
    ]
    return {
        "themesVersion": 1,
        "objID": oid(),
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
        "variables": {"objID": oid(), "globalVariables": [],
                      "structures": [], "enums": []},
        "actions": [],
        "userPages": pages,
        "userWidgets": [],
        "lvglStyles": {"objID": oid(), "styles": [], "defaultStyles": {}},
        "lvglGroups": {"objID": oid(), "groups": []},
        "fonts": [],
        "bitmaps": [],
        "colors": [],
        "themes": [{"objID": oid(), "name": "Default", "colors": []}],
    }


def main():
    data = build_project()
    with open(PROJECT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("written: %s (%d bytes)"
          % (PROJECT_FILE, os.path.getsize(PROJECT_FILE)))


if __name__ == "__main__":
    main()
