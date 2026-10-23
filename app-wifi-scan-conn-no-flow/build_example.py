# -*- coding: utf-8 -*-
"""app-wifi-scan-conn-no-flow —— WiFi 扫描列表（no-flow 变体：关 EEZ Flow 运行时）

本文件是工程唯一设计源：由它生成 .eez-project，请勿手改产物。
与 app-wifi-scan-flow 的唯一设计差异：settings.general.flowSupport=False、
settings.build.generateSourceCodeForEezFramework=False（见本文件 README）。

    python build_example.py        → app-wifi-scan-conn-no-flow.eez-project
    python design/cli_build.py     → src/ui/（EEZ CLI 生成，勿手改）
    python design/gen_font.py      → src/ui/fonts/ui_font_cn14.c

结构（单屏，480×320，深色）：
  main screen
    lbl_title   (16,14,200,24)   "Wi-Fi"                 #f0f4fc
    lbl_status  (16,40,372,16)   ""（C 侧写：已发现 N 个网络）  #8a99b3
    btn_refresh (400,14,64,26)   "刷 新"  CLICKED→action_scan_start
    list_box    (16,64,448,242)  滚动容器（bg 透明，scrollbar AUTO）
      row_1..row_10  (0, i*50, 448,44)  初始 HIDDEN，C 侧填值/显隐
        bar_N_1..4   信号条 3×5/8/11/14 @ x=14/20/26/32（底对齐 34）
        lbl_ssid_N   (44,6,230,16)   SSID        #f0f4fc
        lbl_meta_N   (44,24,250,16)  类型·dBm·频段 #8a99b3
        lbl_state_N  (310,14,120,16) 状态        #8a99b3

  变量：本工程 EEZ 不持有任何变量——扫描态/文案由 native 经 app_model 契约直驱，
        列表直接读 io 接口（wifi_ap_at/wifi_ap_count）；EEZ 仅提供静态外壳与行对象。

  动作（native，C 侧 action_scan_start(lv_event_t*)）：
    scan_start  刷新按钮 → io_scan_start()

  字体：cn14 = simhei.ttf 14px，GB2312 符号区+一二级汉字 + ASCII，
        经 TTF cmap 过滤（P-0125：缺字形会让 EEZ 提取报 extraction failed）

数据流：行内容全部由 src/native/wifi_ui_sync.cpp 直接写控件
        （不建 Flow 绑定、不投影变量）——EEZ 只提供外壳与 10 个行对象。
"""
import json
import os
import sys

# Windows 控制台默认 GBK：打印字体丢弃字符（如 U+30FB）或检查名里的符号
# 会 UnicodeEncodeError 把流程本身打断 —— 编不出的字符替换掉，不中断。
try:
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")
except (AttributeError, ValueError):
    pass
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_FILE = os.path.join(HERE, "app-wifi-scan-conn-no-flow.eez-project")

SCREEN_W, SCREEN_H = 480, 320
ROW_PITCH, ROW_H, ROW_COUNT = 50, 44, 10
LIST_X, LIST_Y, LIST_W, LIST_H = 16, 64, 448, 242

# ---- 设计令牌（与 design/mockups/ 的图同一套值，改这里重出图）----
BG        = "0x0b0f1a"   # 屏幕底
ROW_BG    = "0x101a28"   # 行底
ROW_EDGE  = "0x26314a"   # 行描边
BAR_DIM   = "0x2a3550"   # 信号条（未点亮）
ELEVATED  = "0x1c2440"   # 按钮底
TEXT1     = "0xf0f4fc"   # 主文字
TEXT2     = "0x8a99b3"   # 次文字
TEXT3     = "0x6b7791"   # 三级文字（占位/提示）
FAIL      = "0xff5b5b"   # 危险色
FAIL_BG   = "0x3a1618"   # 危险按钮底
SHEET_BG  = "0x1c2440"   # 半页/对话框底
PRI       = "0x5b8cff"   # 主行动按钮底（= 设计图 PRI）
PRI_TXT   = "0x0a1020"   # 主行动按钮文字

# ---- 顶部刷新按钮（设计图与本文件同值，preflight 对账）----
HEAD_BTN = (400, 14, 64, 26)

# ---- 连接半页几何（与 design/mockup_gen.py 同值，preflight 会对账）----
SHEET_Y, SHEET_H = 96, 224
SHEET_TA = (8, 43, 364, 36)          # 相对 sheet
SHEET_BTN = (396, 43, 76, 36)
SHEET_KB = (8, 92, 464, 132)
SHEET_KB_GAP = 4                     # 键间距；4 行 = (132-3*4)/4 = 30 px/行
# one-line 输入框的真实高度 = 行高 + 上下 pad（探针实测 cn14 行高 19，不是字号 14）
TA_LINE_H = 19
SHEET_TA_PAD = (SHEET_TA[3] - TA_LINE_H) // 2
SHEET_CLOSE = (436, 15, 28, 20)      # 相对 sheet

# ---- 忘记确认对话框（绝对坐标）----
DIALOG_BOX = (70, 90, 340, 140)
DIALOG_BTN_L = (90, 182, 140, 32)
DIALOG_BTN_R = (250, 182, 140, 32)

FONT_FILE = "fonts/simhei.ttf"   # 全量黑体（相对工程目录，P-0035）
FONT_NAME = "cn14"


def gb2312_charset():
    """GB2312 符号区 + 一二级汉字（~7445 字形），经 'gb2312' 编解码器
    映射到 Unicode。真机预算：14px bpp4 ≈ 750KB（KB 09 号作业卡）。"""
    chars = set()
    for hi in range(0xA1, 0xF8):
        for lo in range(0xA1, 0xFF):
            try:
                chars.add(bytes([hi, lo]).decode("gb2312"))
            except UnicodeDecodeError:
                pass
    return "".join(sorted(chars))


_RAW_CHARS = (gb2312_charset()
              + "".join(chr(c) for c in range(0x20, 0x7F)))
# ★ ASCII 0x20-0x7E 必须并入（P-0125：lvglRanges[0]=32-126），
#   漏 ASCII → 画布所有拉丁/数字豆腐


def _filter_by_font_cmap(chars, ttf_path):
    """按 TTF cmap 过滤：lvglRanges 里任何"字体没有的字"都会让 EEZ
    提取报 extraction failed（如 U+30FB 间隔号 simhei 没有）。

    ★ 硬失败而非静默降级：fontTools 缺失时**直接退出**，绝不把
    未过滤字符集写进工程——否则漏进去的缺字形字符会让 EEZ GUI
    字体提取必报 extraction failed（P-0169 反复踩的根因）。"""
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        sys.stderr.write(
            "FATAL: fontTools 未安装，无法按字体 cmap 过滤字符集。\n"
            "        请先执行：`python -m pip install fontTools`\n"
            "        未过滤的字符集会包含字体没有的字形（如 U+30FB ·），\n"
            "        导致 EEZ Studio 字体提取报 extraction failed。\n")
        sys.exit(2)
    f = TTFont(ttf_path, lazy=True)
    cmap = set(f.getBestCmap().keys())
    f.close()
    kept = [c for c in chars if ord(c) in cmap]
    dropped = [c for c in chars if ord(c) not in cmap]
    if dropped:
        print("font coverage: dropped %d chars not in TTF: %s"
              % (len(dropped), "".join(dropped[:40])))
    return "".join(kept)


FONT_CHARS = _filter_by_font_cmap(_RAW_CHARS, os.path.join(HERE, FONT_FILE))

ZERO_PAD = {
    "pad_top": 0, "pad_bottom": 0, "pad_left": 0, "pad_right": 0,
    "pad_row": 0, "pad_column": 0, "border_width": 0, "outline_width": 0,
}

DEFAULT_FLAGS = {
    "LVGLScreenWidget": "CLICKABLE|CLICK_FOCUSABLE|SCROLLABLE|SCROLL_MOMENTUM|SCROLL_ELASTIC|SNAPPABLE|SCROLL_CHAIN_VER",
    "LVGLLabelWidget": "GESTURE_BUBBLE|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER",
    "LVGLButtonWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_ON_FOCUS|SCROLL_WITH_ARROW|SNAPPABLE",
    "LVGLContainerWidget": "CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SNAPPABLE",
    "LVGLTextareaWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_WITH_ARROW|SNAPPABLE",
    "LVGLKeyboardWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLLABLE|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_WITH_ARROW|SNAPPABLE",
    # EEZ classInfo defaultFlags（lv_list 原生：CLICKABLE + SCROLLABLE + 全套 CHAIN
    # ——子项是 lv_button，滚动链路天然通；实测容器+自建行因 hit_test 要求
    # CLICKABLE 而全线失效，故改用 List 控件）
    "LVGLListWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLLABLE|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_WITH_ARROW|SNAPPABLE",
}

# 容器类默认不可滚动；需要滚动的显式传 flags
SCROLL_FLAGS = "SCROLLABLE|SCROLL_ELASTIC|SCROLL_MOMENTUM"


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
        "flagScrollbarMode": "AUTO" if flags == SCROLL_FLAGS else "OFF",
        "checkedStateType": "literal", "disabledStateType": "literal",
        "states": "",
        "localStyles": {"objID": oid(), "definition": local or {}},
        "groupIndex": 0,
    }
    if identifier:
        wd["identifier"] = identifier
    wd.update(extra)
    return wd


def label(x, y, w, h, text, color=TEXT1, identifier=None, font=FONT_NAME):
    """Label：显式清零 padding/border，文字色/字体按需覆盖。"""
    return widget(
        "LVGLLabelWidget", x, y, w, h,
        identifier=identifier,
        local={"MAIN": {"DEFAULT": dict(ZERO_PAD, text_color=color,
                                        text_font=font)}},
        text=text,
        textType="literal",
        longMode="WRAP",
        recolor=False,
        useStaticText=True,
    )


def bar(x, y, w, h, identifier):
    """信号条：3px 宽纯色小方块（EEZ 容器控件，零文字）。"""
    return widget(
        "LVGLContainerWidget", x, y, w, h,
        identifier=identifier,
        flags="",
        local={"MAIN": {"DEFAULT": dict(ZERO_PAD, bg_color=BAR_DIM,
                                        bg_opa=255, radius=2)}},
    )


def button(x, y, w, h, text, action, identifier, bg=ELEVATED,
           text_color="0xFFFFFF"):
    """按钮：子 label 用 EEZ 原生新建按钮形态（content 尺寸 + align
    CENTER，官方 defaultValue 逐字段一致——P-0164 坑 20 定论）。"""
    lbl = {
        "objID": oid(), "type": "LVGLLabelWidget",
        "left": 0, "top": 0, "width": 80, "height": 32,
        "widthUnit": "content", "heightUnit": "content",
        "text": text, "textType": "literal", "longMode": "WRAP",
        "recolor": False, "useStaticText": True,
        "localStyles": {"objID": oid(),
                        "definition": {"MAIN": {"DEFAULT": {
                            "align": "CENTER",
                            "text_color": text_color,
                            "text_font": FONT_NAME}}}},
    }
    return widget(
        "LVGLButtonWidget", x, y, w, h,
        identifier=identifier,
        local={"MAIN": {"DEFAULT": dict(ZERO_PAD, bg_color=bg,
                                        bg_opa=255, radius=8)}},
        children=[lbl],
        eventHandlers=[{"objID": oid(), "eventName": "CLICKED",
                        "handlerType": "action", "action": action,
                        "userData": 0}],
    )


def row_slot(i):
    """第 i 行（i 从 0 起）：容器 + 4 信号条 + 3 个 label，初始 HIDDEN。
    行内容由 C 侧 wifi_ui_sync.cpp 填（不在 EEZ 里绑变量）。"""
    y = i * ROW_PITCH
    kids = []
    for b, (bx, bh) in enumerate([(14, 5), (20, 8), (26, 11), (32, 14)]):
        kids.append(bar(bx, 34 - bh, 3, bh, "bar_%d_%d" % (i + 1, b + 1)))
    kids.append(label(44, 6, 230, 16, "", TEXT1, "lbl_ssid_%d" % (i + 1)))
    kids.append(label(44, 24, 250, 16, "", TEXT2, "lbl_meta_%d" % (i + 1)))
    kids.append(label(310, 14, 120, 16, "", TEXT2, "lbl_state_%d" % (i + 1)))
    return widget(
        "LVGLContainerWidget", 0, y, LIST_W, ROW_H,
        identifier="row_%d" % (i + 1),
        # ★ SCROLL_CHAIN_VER 必填：indev 从按下的对象沿父链找 scrollable，
        #   行本身不可滚 → 没有 CHAIN_VER 会 break，list_box 永远收不到
        #   滚动（实测"滑不动"根因，lv_indev_scroll.c:325）
        flags="SCROLL_CHAIN_VER",
        local={"MAIN": {"DEFAULT": dict(ZERO_PAD, bg_color=ROW_BG,
                                        bg_opa=255, radius=10,
                                        border_width=1,
                                        border_color=ROW_EDGE)}},
        children=kids,
        **{"hiddenFlag": True, "hiddenFlagType": "literal"},
    )


def page(name, screen_children, create_at_start=True):
    """一页 = 一个铺满屏幕的 LVGLScreenWidget + 其下挂的控件树。"""
    screen = widget("LVGLScreenWidget", 0, 0, SCREEN_W, SCREEN_H,
                    local={"MAIN": {"DEFAULT": dict(ZERO_PAD, bg_color=BG,
                                                    bg_opa=255, radius=0)}},
                    children=screen_children)
    return {
        "objID": oid(),
        "components": [screen],
        "connectionLines": [],
        "localVariables": [],
        "componentGroups": [],
        "userProperties": [],
        "name": name,
        "left": 0, "top": 0,
        "width": SCREEN_W, "height": SCREEN_H,
        "isUsedAsUserWidget": False,
        "createAtStart": create_at_start,
        "deleteOnScreenUnload": False,
    }


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
        "lvglGlyphs": {"objID": oid(), "encodings": encodings},
    }


def build_project():
    # ---------------- 头部 ----------------
    head = [
        label(16, 14, 200, 24, "Wi-Fi", TEXT1, "lbl_title"),
        label(16, 40, 372, 16, "", TEXT2, "lbl_status"),
        button(HEAD_BTN[0], HEAD_BTN[1], HEAD_BTN[2], HEAD_BTN[3],
               "刷 新", "scan_start", "btn_refresh"),
    ]

    # ---------------- 列表：EEZ List (LVGL) 控件 ----------------
    # lv_list 原生可滚动（SCROLLABLE + 全套 CHAIN + 子项 lv_button 带
    # CLICKABLE）；行由 C 侧 wifi_ui_sync.cpp 用 lv_list_add_text/add_button
    # 按 ap_cnt 动态填充——EEZ 只画这一个空 List。
    list_box = widget(
        "LVGLListWidget", LIST_X, LIST_Y, LIST_W, LIST_H,
        identifier="list_box",
        local={"MAIN": {"DEFAULT": dict(ZERO_PAD, bg_color=BG,
                                        bg_opa=0, radius=0)}},
        flagScrollbarMode="AUTO",       # 内容超高时显示滚动条
    )

    # ---------------- 连接半页（DESIGN.md §6.1 方案 C，默认隐藏）----------------
    # ★ overlay_root 挂 **screen 根**：放进容器会被父边界裁剪、坐标二次偏移（P-0007）。
    scrim = widget(
        "LVGLContainerWidget", 0, 0, SCREEN_W, SCREEN_H,
        identifier="scrim",
        flags="CLICKABLE",
        local={"MAIN": {"DEFAULT": dict(ZERO_PAD, bg_color="0x000000",
                                        bg_opa=115, radius=0)}},
        eventHandlers=[{"objID": oid(), "eventName": "CLICKED",
                        "handlerType": "action", "action": "pwd_cancel",
                        "userData": 0}],
    )
    sheet = widget(
        "LVGLContainerWidget", 0, SHEET_Y, SCREEN_W, SHEET_H,
        identifier="sheet",
        flags="CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK",
        local={"MAIN": {"DEFAULT": dict(ZERO_PAD, bg_color=SHEET_BG,
                                        bg_opa=255, radius=0)}},
        children=[
            widget("LVGLContainerWidget", (SCREEN_W - 32) // 2, 6, 32, 3,
                   identifier="sheet_handle", flags="",
                   local={"MAIN": {"DEFAULT": dict(ZERO_PAD, bg_color=ROW_EDGE,
                                                   bg_opa=255, radius=2)}}),
            label(16, 15, 400, 20, "", TEXT1, "lbl_pwd_ssid"),
            button(SHEET_CLOSE[0], SHEET_CLOSE[1], SHEET_CLOSE[2], SHEET_CLOSE[3],
                   "×", "pwd_cancel", "btn_pwd_close"),
            widget("LVGLTextareaWidget", SHEET_TA[0], SHEET_TA[1],
                   SHEET_TA[2], SHEET_TA[3],
                   identifier="pwd_ta",
                   # ★ oneLineMode 会把 height 强制成 LV_SIZE_CONTENT
                   #   （lv_textarea.c:557），36 的设计高度只能靠上下 pad 撑：
                   #   探针实测渲染高 = 行高 19 + 2×SHEET_TA_PAD。
                   local={"MAIN": {"DEFAULT": dict(
                       ZERO_PAD, pad_top=SHEET_TA_PAD,
                       pad_bottom=SHEET_TA_PAD,
                       bg_color=ROW_BG,
                       bg_opa=255, radius=8,
                       border_width=1, border_color=ROW_EDGE,
                       text_color=TEXT1,
                       text_font=FONT_NAME)}},
                   text="", textType="literal", placeholder="输入密码",
                   oneLineMode=True, passwordMode=True,
                   acceptedCharacters="", maxTextLength=64),
            button(SHEET_BTN[0], SHEET_BTN[1], SHEET_BTN[2], SHEET_BTN[3],
                   "连 接", "wifi_connect", "btn_connect",
                   bg=PRI, text_color=PRI_TXT),
            widget("LVGLKeyboardWidget", SHEET_KB[0], SHEET_KB[1],
                   SHEET_KB[2], SHEET_KB[3],
                   identifier="kb_main", textarea="pwd_ta", mode="TEXT_LOWER",
                   # ★ lv_keyboard 构造函数写死 lv_obj_align(BOTTOM_MID,0,0)，
                   #   不覆盖的话 set_pos 变成"相对底边中点的偏移"，
                   #   实测整块键盘下移 92px、只有第一行留在屏内。
                   #   改 TOP_LEFT 后 (8,92) 才是左上角坐标。
                   local={"MAIN": {"DEFAULT": {
                       "align": "TOP_LEFT",
                       "pad_top": 0, "pad_bottom": 0,
                       "pad_left": 0, "pad_right": 0,
                       "pad_row": SHEET_KB_GAP, "pad_column": SHEET_KB_GAP,
                       "border_width": 0, "outline_width": 0,
                       "bg_color": SHEET_BG, "bg_opa": 255, "radius": 0}}}),
        ],
    )
    overlay = widget(
        "LVGLContainerWidget", 0, 0, SCREEN_W, SCREEN_H,
        identifier="overlay_root", flags="",
        local={"MAIN": {"DEFAULT": dict(ZERO_PAD, bg_color=BG, bg_opa=0, radius=0)}},
        children=[scrim, sheet],
        hiddenFlag=True,
    )

    # ---------------- 忘记确认对话框（长按已保存行，默认隐藏）----------------
    dlg_scrim = widget(
        "LVGLContainerWidget", 0, 0, SCREEN_W, SCREEN_H,
        identifier="dlg_scrim",
        flags="CLICKABLE",
        local={"MAIN": {"DEFAULT": dict(ZERO_PAD, bg_color="0x000000",
                                        bg_opa=140, radius=0)}},
        eventHandlers=[{"objID": oid(), "eventName": "CLICKED",
                        "handlerType": "action", "action": "dlg_cancel",
                        "userData": 0}],
    )
    dlg_card = widget(
        "LVGLContainerWidget", DIALOG_BOX[0], DIALOG_BOX[1],
        DIALOG_BOX[2], DIALOG_BOX[3],
        identifier="dlg_card", flags="CLICKABLE|CLICK_FOCUSABLE",
        local={"MAIN": {"DEFAULT": dict(ZERO_PAD, bg_color=SHEET_BG,
                                        bg_opa=255, radius=14)}},
        children=[
            label(20, 18, 300, 20, "忘记此网络？", TEXT1, "lbl_dlg_title"),
            label(20, 40, 300, 16, "", TEXT2, "lbl_dlg_ssid"),
            label(20, 58, 300, 16, "将删除已保存的密码，下次连接需重新输入。",
                  TEXT2, "lbl_dlg_hint"),
            button(DIALOG_BTN_L[0] - DIALOG_BOX[0], DIALOG_BTN_L[1] - DIALOG_BOX[1],
                   DIALOG_BTN_L[2], DIALOG_BTN_L[3], "忘 记", "dlg_forget",
                   "btn_dlg_forget", bg=FAIL_BG),
            button(DIALOG_BTN_R[0] - DIALOG_BOX[0], DIALOG_BTN_R[1] - DIALOG_BOX[1],
                   DIALOG_BTN_R[2], DIALOG_BTN_R[3], "取 消", "dlg_cancel",
                   "btn_dlg_cancel"),
        ],
    )
    dlg = widget(
        "LVGLContainerWidget", 0, 0, SCREEN_W, SCREEN_H,
        identifier="dlg_root", flags="",
        local={"MAIN": {"DEFAULT": dict(ZERO_PAD, bg_color=BG, bg_opa=0, radius=0)}},
        children=[dlg_scrim, dlg_card],
        hiddenFlag=True,
    )

    screen_children = head + [list_box, overlay, dlg]

    gvs = []   # 本工程 EEZ 不持有任何变量：状态由 native 经 app_model 契约直驱

    # ---- 变量策略（v4 收口）----
    # EEZ 不持有任何变量：标量状态（扫描态/文案/内容代数）由 native 经 app_model 契约
    # 直驱、列表直接读 io 接口（wifi_ap_at/wifi_ap_count/wifi_ap_gen）。EEZ 只画静态
    # 外壳与空 lv_list，所有动态显示逻辑在 src/native/wifi_ui_sync.cpp 每帧比对后直写
    # LVGL——彻底无 Flow 变量桥（native_vars.* 已删）。
    flow_vars = []
    structures = []

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
                # ★ no-flow 变体开关①：关 Flow 总开关 → 不发射 eez-flow.cpp/h
                "flowSupport": False,
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
                # ★ no-flow 变体开关②：不为 EEZ 框架生成源码 → 不链 eez 运行时
                "generateSourceCodeForEezFramework": False,
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
            "globalVariables": (
                [{"objID": oid(), "name": n, "type": t, "defaultValue": d,
                  "persistent": False, "native": True}
                 for (n, t, d) in gvs] + flow_vars),
            "structures": structures, "enums": [],
        },
        "actions": [
            {"objID": oid(), "name": "scan_start",
             "description": "wifi: scan_start",
             "implementationType": "native", "userProperties": []},
            # 连接半页两个动作 + 忘记对话框两个动作（实现全在 native，EEZ 只出桩）
            {"objID": oid(), "name": "wifi_connect",
             "description": "wifi: connect(pwd_ta)", "implementationType": "native",
             "userProperties": []},
            {"objID": oid(), "name": "pwd_cancel",
             "description": "wifi: close password sheet", "implementationType": "native",
             "userProperties": []},
            {"objID": oid(), "name": "dlg_forget",
             "description": "wifi: forget saved network", "implementationType": "native",
             "userProperties": []},
            {"objID": oid(), "name": "dlg_cancel",
             "description": "wifi: close dialog", "implementationType": "native",
             "userProperties": []}
        ],
        "userPages": [page("Main", screen_children)],
        "userWidgets": [],
        "lvglStyles": {"objID": oid(), "styles": [], "defaultStyles": {}},
        "lvglGroups": {"objID": oid(), "groups": []},
        "fonts": [font_entry(FONT_NAME, 14,
                             "GB2312 符号区+一二级汉字 7445 字形 14px"
                             "（标准字库子集）")],
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


def main():
    data = build_project()
    with open(PROJECT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("written: %s (%d bytes)"
          % (PROJECT_FILE, os.path.getsize(PROJECT_FILE)))


if __name__ == "__main__":
    main()
