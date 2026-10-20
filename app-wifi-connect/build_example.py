# -*- coding: utf-8 -*-
"""app-wifi-connect —— WiFi 扫描/连接全流程（EEZ 实现 UI + native 桥数据）

本文件是示例的唯一设计源：由它生成 .eez-project，请勿手改产物。

    python build_example.py

架构（UI 全部在 EEZ 里，数据走 native 桥——模式抄自 eez-test/KB P-0080）：

  变量（全部 native:true，C 侧 get_var_/set_var_ 桥直填）：
    scan_state   int   0=未扫 1=扫描中 2=完成
    ap_count     int   扫描到的网络数
    wifi_state   int   0=未连 1=连接中 2=已连接
    wifi_conn_ssid str 已连接的 SSID
    g_pick       int   当前选中的行（-1=无，密码面板 hiddenExpr 用）
    g_pick_ssid  str   选中行 SSID（面板标题用）
    g_remember   bool  记住密码
    wifi_slotN_ssid/_rssi/_lock（N=0..5）  扫描结果槽位（P-0080 同款：定长槽位
    + 空槽隐藏，不用结构体数组——EEZ flow 表达式按槽位名直读最稳）

  页面（单屏 + 密码面板覆盖层，P-0080 同款）：
    头部：标题 + 扫描状态标签（表达式三元）+ 刷新按钮(CLICKED→action scan_start)
    列表：6 行 ×（SSID 标签 + 锁标志 + 信号强度 + "已连接"徽标 + 点击热区）
          热区 hiddenFlag = "wifi_slotN_ssid == ''"  ★ true=隐藏（JSON 键名是 hiddenFlag，DSL 里才叫 hiddenExpr）（P-0080 语义）
          锁   hiddenExpr = "!wifi_slotN_lock"
          徽标 hiddenExpr = "!(wifi_state == 2 && wifi_conn_ssid == wifi_slotN_ssid)"
    底部：连接状态标签（wifi_state 三态表达式）
    密码面板（hiddenExpr = "g_pick < 0"）：
      标题(g_pick_ssid) + 密码 Textarea(passwordMode+oneLineMode, 由键盘直接输入)
      + Keyboard(textarea 属性直接指定 pwd_ta——EEZ 原生支持)
      + "记住密码"可点标签(CLICKED→action chk_remember 切换 g_remember)
      + 连接按钮(→action wifi_connect，C 里 lv_textarea_get_text 读密码) + 取消

  动作（EEZ actions，implementationType=native，C 侧实现 action_<name>(lv_event_t*)）：
    scan_start / wifi_pick_0..5 / wifi_connect / chk_remember / panel_cancel

屏幕基线：480x320 · LVGL 9.4 · EEZ Studio 0.29（projectVersion=v3）。
"""
import json
import os
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_FILE = os.path.join(HERE, "app-wifi-connect.eez-project")

SCREEN_W, SCREEN_H = 480, 320
N_SLOTS = 6
ROW_Y0, ROW_H = 46, 36

FONT_FILE = "fonts/simhei.ttf"   # 全量黑体（相对工程目录 P-0035）；
                                 # 用子集 TTF 会在 GUI 提取时报
                                 # "doesn't have any characters in range"
# UI 用到的全部字符（运行期表达式产出的静态文案并集；SSID 属运行期数据，
# 演示字体只覆盖静态文案，真机按产品字库预算扩，见 README）
FONT_CHARS = (
    "扫描中已发现个网络未点击刷新连接中记住密码是否取消输"
    "WiFi0123456789.-:dBm "
)
FONT_NAME = "cn14"


def font_entry(name, size, description):
    """EEZ LVGL 字体条目——P-0125 A/B/C 对照定论：renderingEngine=LVGL +
    lvglRanges 数字区间串 + lvglGlyphs.encodings + glyphs 留空，缺一不可。"""
    cps = sorted({ord(c) for c in FONT_CHARS})
    encodings, ranges = [], []
    start = prev = cps[0]
    for cp in cps[1:]:
        if cp == prev + 1:
            prev = cp
            continue
        encodings.append({"from": start, "to": prev})
        ranges.append(str(start) if start == prev else "%d-%d" % (start, prev))
        start = prev = cp
    encodings.append({"from": start, "to": prev})
    ranges.append(str(start) if start == prev else "%d-%d" % (start, prev))
    return {
        "objID": oid(), "name": name, "description": description,
        "renderingEngine": "LVGL",
        "source": {"objID": oid(), "filePath": FONT_FILE, "size": size},
        "bpp": 4, "threshold": 128, "glyphs": [],
        "screenOrientation": "all", "alwaysBuild": False,
        "lvglRanges": ",".join(ranges),
        "lvglSymbols": "",
        "lvglAdditionalSources": [],
        "lvglGlyphs": {"encodings": encodings, "symbols": ""},
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

DEFAULT_FLAGS = {
    "LVGLScreenWidget": "CLICKABLE|CLICK_FOCUSABLE|SCROLLABLE|SCROLL_MOMENTUM|SCROLL_ELASTIC|SNAPPABLE|SCROLL_CHAIN_VER",
    "LVGLLabelWidget": "GESTURE_BUBBLE|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER",
    "LVGLButtonWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_ON_FOCUS|SCROLL_WITH_ARROW|SNAPPABLE",
    "LVGLContainerWidget": "CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SNAPPABLE",
    "LVGLTextareaWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_WITH_ARROW|SNAPPABLE",
    "LVGLKeyboardWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLLABLE|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_WITH_ARROW|SNAPPABLE",
}

ZERO_PAD = {
    "pad_top": 0, "pad_bottom": 0, "pad_left": 0, "pad_right": 0,
    "pad_row": 0, "pad_column": 0, "border_width": 0, "outline_width": 0,
}


def oid():
    return str(uuid.uuid4())


def widget(wtype, x, y, w, h, identifier=None, flags=None, local=None,
           children=None, eventHandlers=None, hiddenExpr=None, **extra):
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
        "hiddenFlagType": "literal", "clickableFlagType": "literal",
        "flagScrollbarMode": "OFF", "checkedStateType": "literal",
        "disabledStateType": "literal", "states": "",
        "localStyles": {"objID": oid(), "definition": local or {}},
        "groupIndex": 0,
    }
    if identifier:
        wd["identifier"] = identifier
    if hiddenExpr is not None:
        wd["hiddenFlagType"] = "expression"
        wd["hiddenFlag"] = hiddenExpr
    wd.update(extra)
    return wd


def label(x, y, w, h, text=None, color="0xFFFFFF", identifier=None, expr=None,
          font=None, center=False):
    props = dict(ZERO_PAD, text_color=color)
    if font:
        props["text_font"] = font
    if center:
        props["text_align"] = "CENTER"
    return widget(
        "LVGLLabelWidget", x, y, w, h,
        identifier=identifier,
        local={"MAIN": {"DEFAULT": props}},
        text=text if expr is None else expr,
        textType="literal" if expr is None else "expression",
        longMode="WRAP", recolor=False, useStaticText=True,
    )


def button(x, y, w, h, text, action, identifier=None, bg="0x5B7CFA"):
    lbl = widget("LVGLLabelWidget", 0, 0, w, h,
                 local={"MAIN": {"DEFAULT": dict(ZERO_PAD,
                                                 text_color="0xFFFFFF",
                                                 text_align="CENTER",
                                                 text_font=FONT_NAME)}},
                 text=text, textType="literal", longMode="WRAP",
                 recolor=False, useStaticText=True)
    return widget(
        "LVGLButtonWidget", x, y, w, h,
        identifier=identifier,
        local={"MAIN": {"DEFAULT": dict(ZERO_PAD, bg_color=bg, bg_opa=255,
                                        radius=8)}},
        children=[lbl],
        eventHandlers=[{"objID": oid(), "eventName": "CLICKED",
                        "handlerType": "action", "action": action,
                        "userData": 0}],
    )


def build_project():
    ch = []

    # ---------------- 头部 ----------------
    ch.append(label(16, 8, 100, 24, "WiFi", color="0xFFFFFF",
                    identifier="lbl_title", font=FONT_NAME))
    ch.append(label(140, 8, 220, 24, None, color="0x8FD3FF",
                    identifier="lbl_scan", font=FONT_NAME, center=True,
                    expr='scan_state == 1 ? "扫描中..." : '
                         '(scan_state == 2 ? "已发现 " + ap_count + " 个网络" : '
                         '"未扫描 - 点击刷新")'))
    ch.append(button(380, 4, 84, 30, "刷新", "scan_start",
                     identifier="btn_refresh"))

    # ---------------- 6 行扫描结果 ----------------
    for i in range(N_SLOTS):
        y = ROW_Y0 + i * ROW_H
        s = str(i)
        ch.append(label(24, y, 190, 20, None, identifier="lbl_ssid_" + s,
                        expr="wifi_slot" + s + "_ssid"))
        ch.append(label(220, y, 22, 20, None, color="0xFFD38F",
                        identifier="lbl_lock_" + s,
                        expr='"\\xEF\x80\xA3"'))  # 占位锁形符（默认字体无此字形则显示方块，仅示意）
        # 锁标志可见性：hiddenExpr true=隐藏
        ch[-1]["hiddenFlagType"] = "expression"
        ch[-1]["hiddenFlag"] = "!wifi_slot" + s + "_lock"
        ch.append(label(250, y, 90, 20, None, color="0x8A94A6",
                        identifier="lbl_rssi_" + s,
                        expr="wifi_slot" + s + "_rssi + \" dBm\""))
        badge = label(390, y, 74, 20, None, color="0x6CE69C",
                      identifier="lbl_conn_" + s, expr='"已连接"',
                        font=FONT_NAME, center=True)
        badge["hiddenFlagType"] = "expression"
        badge["hiddenFlag"] = ("!(wifi_state == 2 && "
                               "wifi_conn_ssid == wifi_slot" + s + "_ssid)")
        ch.append(badge)
        # 点击热区（P-0080：空 SSID 隐藏；CLICKED → 对应 pick 动作）
        hit = widget(
            "LVGLContainerWidget", 8, y - 4, 464, 32,
            identifier="hit_" + s,
            flags="CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|"
                  "SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER",
            local={"MAIN": {"DEFAULT": dict(ZERO_PAD, bg_opa=0)}},
            eventHandlers=[{"objID": oid(), "eventName": "CLICKED",
                            "handlerType": "action",
                            "action": "wifi_pick_" + s, "userData": 0}],
        )
        hit["hiddenFlagType"] = "expression"
        hit["hiddenFlag"] = "wifi_slot" + s + "_ssid == ''"
        ch.append(hit)

    # ---------------- 底部连接状态 ----------------
    ch.append(label(16, 268, 448, 30, None, color="0x6CE69C",
                    identifier="lbl_state", font=FONT_NAME, center=True,
                    expr='wifi_state == 2 ? "已连接: " + wifi_conn_ssid : '
                         '(wifi_state == 1 ? "连接中..." : "未连接")'))

    # ---------------- 密码面板（覆盖层）----------------
    panel_children = [
        label(20, 12, 360, 24, None, color="0xFFFFFF",
              identifier="lbl_panel_title", expr="g_pick_ssid",
              font=FONT_NAME, center=True),
        widget("LVGLTextareaWidget", 20, 44, 360, 42,
               identifier="pwd_ta",
               local={"MAIN": {"DEFAULT": dict(ZERO_PAD, bg_color="0x0C1220",
                                               bg_opa=255, radius=6,
                                               text_color="0xFFFFFF")}},
               text="", textType="literal", placeholder="输入密码",
               oneLineMode=True, passwordMode=True,
               acceptedCharacters="", maxTextLength=64),
        widget("LVGLKeyboardWidget", 20, 96, 360, 118,
               identifier="kb_main",
               textarea="pwd_ta",
               mode="TEXT_LOWER"),
        # 记住密码（可点标签，点击切 g_remember）
        widget("LVGLLabelWidget", 20, 222, 200, 24,
               objID=oid(), identifier="lbl_remember", font=FONT_NAME,
               local={"MAIN": {"DEFAULT": dict(ZERO_PAD, text_color="0xFFD38F")}},
               text='"记住密码: " + (g_remember ? "是" : "否")',
               textType="expression", longMode="WRAP", recolor=False,
               useStaticText=True,
               eventHandlers=[{"objID": oid(), "eventName": "CLICKED",
                               "handlerType": "action",
                               "action": "chk_remember", "userData": 0}]),
        button(60, 250, 140, 26, "连  接", "wifi_connect",
               identifier="btn_connect"),
        button(230, 250, 140, 26, "取  消", "panel_cancel",
               identifier="btn_cancel", bg="0x3A4356"),
    ]
    panel = widget(
        "LVGLContainerWidget", 40, 20, 400, 280,
        identifier="panel_pwd",
        flags="CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|"
              "SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER",
        local={"MAIN": {"DEFAULT": dict(ZERO_PAD, bg_color="0x1A2438",
                                        bg_opa=255, radius=12)}},
        children=panel_children,
    )
    panel["hiddenFlagType"] = "expression"
    panel["hiddenFlag"] = "g_pick < 0"
    ch.append(panel)

    screen = widget(
        "LVGLScreenWidget", 0, 0, SCREEN_W, SCREEN_H,
        identifier="screen_main",
        local={"MAIN": {"DEFAULT": {
            "bg_color": "0x101828", "bg_opa": 255, "radius": 0,
            "border_width": 0}}},
        children=ch,
    )
    page = {
        "objID": oid(), "components": [screen], "connectionLines": [],
        "localVariables": [], "componentGroups": [], "userProperties": [],
        "name": "Main", "left": 0, "top": 0,
        "width": SCREEN_W, "height": SCREEN_H,
        "isUsedAsUserWidget": False, "createAtStart": True,
        "deleteOnScreenUnload": False,
    }

    # ---------------- 变量（全部 native:true）----------------
    gvs = [
        ("scan_state", "integer", "0"), ("ap_count", "integer", "0"),
        ("wifi_state", "integer", "0"), ("wifi_conn_ssid", "string", "''"),
        ("g_pick", "integer", "-1"), ("g_pick_ssid", "string", "''"),
        ("g_remember", "boolean", "false"), ("saved_ssid", "string", "''"),
    ]
    for i in range(N_SLOTS):
        gvs += [("wifi_slot%d_ssid" % i, "string", "''"),
                ("wifi_slot%d_rssi" % i, "integer", "0"),
                ("wifi_slot%d_lock" % i, "boolean", "false")]

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
                {"objID": oid(), "name": n, "type": t, "defaultValue": d,
                 "persistent": False, "native": True}
                for (n, t, d) in gvs
            ],
            "structures": [], "enums": [],
        },
        "actions": [
            {"objID": oid(), "name": a, "description": "wifi: " + a,
             "implementationType": "native", "userProperties": []}
            for a in (["scan_start", "wifi_connect", "chk_remember",
                       "panel_cancel"] +
                      ["wifi_pick_%d" % i for i in range(N_SLOTS)])
        ],
        "userPages": [page], "userWidgets": [],
        "lvglStyles": {"objID": oid(), "styles": [], "defaultStyles": {}},
        "lvglGroups": {"objID": oid(), "groups": []},
        "fonts": [font_entry(FONT_NAME, 14,
                              "黑体子集 14px（WiFi 演示静态文案）")],
        "bitmaps": [], "colors": [],
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
