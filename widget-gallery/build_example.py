# -*- coding: utf-8 -*-
"""widget-gallery —— 常用 LVGL 控件一屏览（生成器）

本文件是示例的唯一设计源：widget-gallery.eez-project 由它生成，请勿手改产物。

    python build_example.py      # 重新生成 widget-gallery.eez-project

屏幕基线：480x320 · LVGL 9.4 · EEZ Studio 0.29（工程模型 projectVersion=v3）。
控件形态全部复刻 EEZ Studio 0.29 调色板默认值（含 widgetFlags / 属性三件套），
是最稳妥的"已知能构建"形态；需要改行为时只改本文件，重跑即可。
"""
import json
import os
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_FILE = os.path.join(HERE, "widget-gallery.eez-project")

SCREEN_W, SCREEN_H = 480, 320
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
    "LVGLButtonWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_ON_FOCUS|SCROLL_WITH_ARROW|SNAPPABLE",
    "LVGLSwitchWidget": "CHECKABLE|CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_ON_FOCUS|SCROLL_WITH_ARROW|SNAPPABLE",
    "LVGLSliderWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_ON_FOCUS|SCROLL_WITH_ARROW|SNAPPABLE",
    "LVGLBarWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_WITH_ARROW|SNAPPABLE",
    "LVGLSpinnerWidget": "CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_WITH_ARROW|SNAPPABLE",
    "LVGLCheckboxWidget": "CHECKABLE|CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_ON_FOCUS|SCROLL_WITH_ARROW|SNAPPABLE",
    "LVGLPanelWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLLABLE|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_WITH_ARROW|SNAPPABLE",
}

# 显式清零默认主题的 padding/border（PLAYBOOK 红线 6：声明坐标 == 渲染坐标）
ZERO_PAD = {
    "pad_top": 0, "pad_bottom": 0, "pad_left": 0, "pad_right": 0,
    "pad_row": 0, "pad_column": 0, "border_width": 0, "outline_width": 0,
}


def oid():
    return str(uuid.uuid4())


def widget(wtype, x, y, w, h, identifier=None, flags=None, local=None,
           children=None, **extra):
    """通用控件构造：字段形态与 EEZ Studio 0.29 序列化结果一致。"""
    wd = {
        "objID": oid(),
        "type": wtype,
        "left": x,
        "top": y,
        "width": w,
        "height": h,
        "customInputs": [],
        "customOutputs": [],
        "style": {
            "objID": oid(),
            "useStyle": "default",
            "conditionalStyles": [],
            "childStyles": [],
        },
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


def label(x, y, w, h, text, color="0xFFFFFF", identifier=None, font=None):
    """Label：显式清零 padding/border，文字色/字体按需覆盖。"""
    props = dict(ZERO_PAD, text_color=color)
    if font:
        props["text_font"] = font
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


def page(name, screen_children, create_at_start=True):
    """一页 = 一个铺满屏幕的 LVGLScreenWidget + 其下挂的控件树。"""
    screen = widget("LVGLScreenWidget", 0, 0, SCREEN_W, SCREEN_H,
                    children=screen_children)
    return {
        "objID": oid(),
        "components": [screen],
        "connectionLines": [],
        "localVariables": [],
        "componentGroups": [],
        "userProperties": [],
        "name": name,
        "left": 0,
        "top": 0,
        "width": SCREEN_W,
        "height": SCREEN_H,
        "isUsedAsUserWidget": False,
        "createAtStart": create_at_start,
        "deleteOnScreenUnload": False,
    }


def caption(x, y, text):
    """演示区小标题（灰蓝色，与主内容区分）。"""
    return label(x, y, 140, 16, text, color="0x8E8E93")


def button(x, y, w, h, text, identifier=None):
    """Button：复刻 EEZ 调色板默认值 —— 子 Label（content 尺寸 + align CENTER），
    由 LVGL button 的 flex 布局自动居中（不要手摆像素，见 B9）。"""
    child = widget(
        "LVGLLabelWidget", 0, 0, 80, 32,
        widthUnit="content", heightUnit="content",
        local={"MAIN": {"DEFAULT": {"align": "CENTER"}}},
        text=text, textType="literal", longMode="WRAP",
        recolor=False, useStaticText=True,
    )
    return widget("LVGLButtonWidget", x, y, w, h,
                  identifier=identifier, children=[child])


def slider(x, y, w, h, value, identifier=None):
    """Slider：min/max/value 三件套 + mode；valueType=literal 时 previewValue 不生效。"""
    return widget("LVGLSliderWidget", x, y, w, h, identifier=identifier,
                  min=0, minType="literal", max=100, maxType="literal",
                  mode="NORMAL", value=value, valueType="literal",
                  previewValue=value, valueLeft=0, valueLeftType="literal",
                  previewValueLeft=0, enableAnimation=False)


def bar(x, y, w, h, value, identifier=None):
    """Bar：与 Slider 同族，但 value 是单向输入（不可交互）。"""
    return widget("LVGLBarWidget", x, y, w, h, identifier=identifier,
                  min=0, minType="literal", max=100, maxType="literal",
                  mode="NORMAL", value=value, valueType="literal",
                  previewValue=str(value), valueStart=0,
                  valueStartType="literal", previewValueStart="0",
                  enableAnimation=False)


def checkbox(x, y, text, identifier=None, checked=False):
    """Checkbox：content 尺寸（widthUnit/heightUnit=content，宽高由内容撑开）。"""
    return widget("LVGLCheckboxWidget", x, y, 105, 20,
                  identifier=identifier,
                  widthUnit="content", heightUnit="content",
                  text=text, textType="literal", useStaticText=True,
                  checkedState=checked)


def build_project():
    # ---- 页面内容：常用控件一屏览 ----
    screen_children = [
        label(16, 8, 448, 26, "Widget Gallery"),
        label(16, 34, 448, 16, "EEZ Studio 0.29 - LVGL 9.4 - 480x320",
              color="0xAAAAAA"),

        # 第一行：Button / Slider / Switch
        caption(16, 62, "Button"),
        button(16, 82, 100, 34, "Button", identifier="btn_demo"),
        caption(176, 62, "Slider"),
        slider(176, 88, 140, 20, 40, identifier="slider_demo"),
        caption(336, 62, "Switch"),
        widget("LVGLSwitchWidget", 336, 84, 50, 25,
               identifier="sw_demo", checkedState=True),

        # 第二行：Bar / Spinner / Checkbox
        caption(16, 134, "Bar"),
        bar(16, 154, 140, 14, 60, identifier="bar_demo"),
        caption(176, 134, "Spinner"),
        widget("LVGLSpinnerWidget", 176, 140, 56, 56,
               identifier="spinner_demo"),
        caption(336, 134, "Checkbox"),
        checkbox(336, 154, "Checkbox", identifier="chk_demo", checked=False),

        # 第三行：Panel + 子控件（子坐标相对父容器，见 B5/P-0007）
        caption(16, 210, "Panel + child"),
        widget("LVGLPanelWidget", 16, 230, 200, 78,
               identifier="panel_demo",
               local={"MAIN": {"DEFAULT": dict(ZERO_PAD)}},
               children=[label(12, 28, 176, 20, "panel child", color="0xFFFFFF")]),
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
        "variables": {
            "objID": oid(),
            "globalVariables": [],
            "structures": [],
            "enums": [],
        },
        "actions": [],
        "userPages": [page("Main", screen_children)],
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
