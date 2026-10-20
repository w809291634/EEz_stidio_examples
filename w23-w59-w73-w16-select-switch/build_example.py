# -*- coding: utf-8 -*-
"""w23-w59-w73-w16-select-switch —— 选择与开关：Tabview 4 页 + 联动（A 级组合 3/5）

本文件是示例的唯一设计源：由它生成 .eez-project，请勿手改产物。

    python build_example.py

结构：**可见 tab 栏的 Tabview**（tabviewSize=30）承载 4 个分页，每页一种控件：

  Tab1 Dropdown(W23)：options(换行分隔多选项) + selected 双向绑定 g_sel
  Tab2 Roller(W59)：  options + selected 双向绑定 **同一个 g_sel**（mode NORMAL）
                      → ★ 联动主线：下拉和滚轮改任一个，另一件自动同步（同一索引）
  Tab3 Switch(W73)：  两实例 checkedState=false/true + CHECKED 样式态（EEZ 无
                      Switch 的数据绑定属性，状态联动需 flow 事件线，此页演示形态）
  Tab4 Checkbox(W16)：text 文本 + 两实例 checkedState=false/true（同上）
  （ToggleButton W85 剔除：EEZ-GUI 双态钮无 LVGL codegen，LVGL 等价物=CHECKABLE
     Button，widget-gallery 已覆盖。）

联动机制（同 w67-w3-w2）：assignable 属性 = VALUE_CHANGED 写回 g_sel +
tick 反向同步到其他绑定件——纯绑定、零 flow 图、零 C。

屏幕基线：480x320 · LVGL 9.4 · EEZ Studio 0.29（projectVersion=v3）。
"""
import json
import os
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_FILE = os.path.join(HERE, "w23-w59-w73-w16-select-switch.eez-project")

SCREEN_W, SCREEN_H = 480, 320
TAB_H = 30

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

DEFAULT_FLAGS = {
    "LVGLScreenWidget": "CLICKABLE|CLICK_FOCUSABLE|SCROLLABLE|SCROLL_MOMENTUM|SCROLL_ELASTIC|SNAPPABLE|SCROLL_CHAIN_VER",
    "LVGLLabelWidget": "GESTURE_BUBBLE|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER",
    "LVGLDropdownWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLLABLE|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_WITH_ARROW|SNAPPABLE",
    "LVGLRollerWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLLABLE|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_WITH_ARROW|SNAPPABLE",
    "LVGLSwitchWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLLABLE|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_WITH_ARROW|SNAPPABLE",
    "LVGLCheckboxWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLLABLE|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_WITH_ARROW|SNAPPABLE",
    "LVGLTabviewWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_WITH_ARROW|SNAPPABLE",
    "LVGLTabWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_WITH_ARROW|SNAPPABLE",
}

ZERO_PAD = {
    "pad_top": 0, "pad_bottom": 0, "pad_left": 0, "pad_right": 0,
    "pad_row": 0, "pad_column": 0, "border_width": 0, "outline_width": 0,
}

OPTIONS = "Red\nGreen\nBlue\nYellow"


def oid():
    return str(uuid.uuid4())


def widget(wtype, x, y, w, h, identifier=None, flags=None, local=None,
           children=None, **extra):
    wd = {
        "objID": oid(),
        "type": wtype,
        "left": x, "top": y, "width": w, "height": h,
        "customInputs": [], "customOutputs": [],
        "style": {"objID": oid(), "useStyle": "default",
                  "conditionalStyles": [], "childStyles": []},
        "timeline": [], "eventHandlers": [],
        "leftUnit": "px", "topUnit": "px",
        "widthUnit": "px", "heightUnit": "px",
        "children": children if children is not None else [],
        "widgetFlags": flags if flags is not None else DEFAULT_FLAGS[wtype],
        "hiddenFlagType": "literal", "clickableFlagType": "literal",
        "flagScrollbarMode": "OFF", "checkedStateType": "literal",
        "disabledStateType": "literal", "states": "",
        "localStyles": {"objID": oid(), "definition": local or {}},
        "groupIndex": 0,
    }
    if identifier:
        wd["identifier"] = identifier
    wd.update(extra)
    return wd


def label(x, y, w, h, text, color="0xFFFFFF", identifier=None, expr=None):
    return widget(
        "LVGLLabelWidget", x, y, w, h,
        identifier=identifier,
        local={"MAIN": {"DEFAULT": dict(ZERO_PAD, text_color=color)}},
        text=text if expr is None else expr,
        textType="literal" if expr is None else "expression",
        longMode="WRAP", recolor=False, useStaticText=True,
    )


def caption(x, y, w, text, color="0x8A94A6"):
    return label(x, y, w, 18, text, color=color)


def tab(name, children):
    return widget(
        "LVGLTabWidget", 0, 0, SCREEN_W, SCREEN_H - TAB_H,
        identifier="tab_%s" % name.lower(),
        children=children,
        tabName=name, tabNameType="literal",
    )


def build_project():
    # ---- Tab1 Dropdown：selected 双向绑 g_sel -------------------------------
    tab_drop = tab("Drop", [
        caption(40, 60, 400, "W23 Dropdown - options + selected (assignable, bound to g_sel)"),
        widget("LVGLDropdownWidget", 40, 90, 200, 40,
               identifier="dd_main",
               options=OPTIONS, optionsType="literal",
               selected="g_sel", selectedType="expression",
               direction="bottom", useStaticText=True),
        label(40, 150, 400, 24, None, color="0x8FD3FF", identifier="lbl_dd",
              expr='"Dropdown selected index = " + g_sel'),
        caption(40, 190, 400, "Change here -> Roller tab follows (shared g_sel)"),
    ])

    # ---- Tab2 Roller：selected 双向绑同一个 g_sel（联动对端）----------------
    tab_roll = tab("Roll", [
        caption(40, 50, 400, "W59 Roller - selected bound to the SAME g_sel"),
        widget("LVGLRollerWidget", 40, 80, 130, 150,
               identifier="roller_main",
               options=OPTIONS, optionsType="literal",
               selected="g_sel", selectedType="expression",
               mode="NORMAL", visibleRowCount=4),
        label(200, 100, 240, 24, None, color="0x8FD3FF", identifier="lbl_roll",
              expr='"Roller selected index = " + g_sel'),
        caption(200, 130, 240, "Two-way: dropdown <-> roller stay in sync"),
    ])

    # ---- Tab3 Switch：CHECKED 样式态 + 初始态两实例（EEZ 无绑定属性）--------
    tab_sw = tab("Sw", [
        caption(40, 50, 400, "W73 Switch - checkedState initial + CHECKED style"),
        widget("LVGLSwitchWidget", 40, 90, 50, 25,
               identifier="sw_off",
               local={"MAIN": {"DEFAULT": dict(ZERO_PAD, bg_color="0x3A4356",
                                               bg_opa=255),
                               "CHECKED": dict(ZERO_PAD, bg_color="0x2FA46A",
                                               bg_opa=255)}}),
        widget("LVGLSwitchWidget", 40, 140, 50, 25,
               identifier="sw_on",
               local={"MAIN": {"DEFAULT": dict(ZERO_PAD, bg_color="0x3A4356",
                                               bg_opa=255),
                               "CHECKED": dict(ZERO_PAD, bg_color="0x2FA46A",
                                               bg_opa=255)}},
               checkedState=True, checkedStateType="literal"),
        caption(120, 96, 320, "checkedState = false (default off)"),
        caption(120, 146, 320, "checkedState = true (starts checked, green track)"),
        caption(40, 190, 400, "Switch has no data-binding property in EEZ; "
                              "state linkage needs flow event lines (advanced)."),
    ])

    # ---- Tab4 Checkbox：text + 两实例初始态 ---------------------------------
    tab_chk = tab("Chk", [
        caption(40, 50, 400, "W16 Checkbox - text + checkedState initial"),
        widget("LVGLCheckboxWidget", 40, 90, 180, 20,
               identifier="chk_a",
               text="Checkbox A (off)", textType="literal", useStaticText=True),
        widget("LVGLCheckboxWidget", 40, 130, 180, 20,
               identifier="chk_b",
               text="Checkbox B (on)", textType="literal", useStaticText=True,
               checkedState=True, checkedStateType="literal"),
        caption(40, 180, 400, "Checkbox has no data-binding property in EEZ; "
                              "use event lines for state linkage."),
    ])

    tv = widget(
        "LVGLTabviewWidget", 0, 0, SCREEN_W, SCREEN_H,
        identifier="tv_pages",
        local={"MAIN": {"DEFAULT": dict(ZERO_PAD, bg_opa=0)}},
        children=[tab_drop, tab_roll, tab_sw, tab_chk],
        tabviewPosition="TOP", tabviewSize=TAB_H,   # ★ 可见页签（本例要切页）
        selectedTab=0, selectedTabType="literal",
    )

    screen = widget(
        "LVGLScreenWidget", 0, 0, SCREEN_W, SCREEN_H,
        identifier="screen_main",
        local={"MAIN": {"DEFAULT": {
            "bg_color": "0x101828", "bg_opa": 255, "radius": 0,
            "border_width": 0}}},
        children=[tv],
    )
    page = {
        "objID": oid(), "components": [screen], "connectionLines": [],
        "localVariables": [], "componentGroups": [], "userProperties": [],
        "name": "Main", "left": 0, "top": 0,
        "width": SCREEN_W, "height": SCREEN_H,
        "isUsedAsUserWidget": False, "createAtStart": True,
        "deleteOnScreenUnload": False,
    }
    return {
        "themesVersion": 1, "objID": oid(),
        "settings": {
            "objID": oid(),
            "general": {
                "objID": oid(), "projectVersion": "v3", "projectType": "lvgl",
                "lvglVersion": "9.4.0", "extensions": [], "imports": [],
                "flowSupport": True, "displayWidth": SCREEN_W,
                "displayHeight": SCREEN_H, "circularDisplay": False,
                "displayBorderRadius": 0, "darkTheme": True, "colorBpp": "16",
                "bitmapColorFormat": "BGR", "resourceFiles": [],
                "hiddenWidgetLines": "dimmed", "dimmedLinesOpacity": "20",
                "embedBitmaps": True, "embedFonts": True, "cacheFonts": True,
            },
            "build": {
                "objID": oid(),
                "configurations": [{"objID": oid(), "name": "Default"}],
                "destinationFolder": "src\\ui",
                "separateFolderForImagesAndFonts": True,
                "imageExportMode": "source", "fontExportMode": "source",
                "fileSystemPath": "", "lvglInclude": "lvgl.h",
                "screensLifetimeSupport": False, "useDockerDesktop": True,
                "generateSourceCodeForEezFramework": True,
                "compressFlowDefinition": False, "executionQueueSize": 1000,
                "expressionEvaluatorStackSize": 20,
                "files": [{"objID": oid(), "fileName": name, "template": tmpl}
                          for name, tmpl in BUILD_TEMPLATES.items()],
            },
        },
        "variables": {
            "objID": oid(),
            "globalVariables": [
                {"objID": oid(), "name": "g_sel",
                 "type": "integer", "defaultValue": "1",
                 "persistent": False, "native": False},
            ],
            "structures": [], "enums": [],
        },
        "actions": [], "userPages": [page], "userWidgets": [],
        "lvglStyles": {"objID": oid(), "styles": [], "defaultStyles": {}},
        "lvglGroups": {"objID": oid(), "groups": []},
        "fonts": [], "bitmaps": [], "colors": [],
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
