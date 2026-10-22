# -*- coding: utf-8 -*-
"""port_rxroller.py —— 把上游 Rxroller(v8) 打成 LVGL 9.4 可编的 Rxroller.c

上游：https://github.com/rxwind7/Rxroller  MIT，单文件 Rxroller.c/.h
上游原文**逐字保留**在 `src/native/rxroller/Rxroller.c.orig`（.orig 不被 CMake 的
*.c glob 收进去，所以不会重复定义符号）；本脚本只生成 `Rxroller.c`。

为什么补丁这么小：实测把上游原文件用仿真器同一套 gcc 参数编到 9.4，
**12 个错误全是同一类**——直接摸 `lv_obj_t::user_data` / `lv_event_t::user_data`。
v8 里 lv_obj_t 是公开完整结构体，v9 改成不透明指针，正规写法是
`lv_obj_get_user_data()` / `lv_obj_set_user_data()` / `lv_event_get_user_data()`。
其余 v8 名字（transform_zoom / lv_img_set_zoom / lv_anim_del / lv_obj_del_async /
lv_obj_get_child_cnt / lv_img_create）9.4 的 `src/lv_api_map_v8.h` 全都兜着，不用动。

跑法：python design/port_rxroller.py     （幂等：每次都从 .orig 重新生成）
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
UPSTREAM = os.path.join(ROOT, "src", "native", "rxroller", "Rxroller.c.orig")
OUT = os.path.join(ROOT, "src", "native", "rxroller", "Rxroller.c")

# ★ 上游补丁里那两个可调常数，唯一出处是 watch_list_config.h（改它就行，别改这里）
sys.path.insert(0, HERE)
from wconfig import wcfg  # noqa: E402

SPAN = wcfg("SCALE_SPAN_PITCHES")
CLICK_MAX = wcfg("CLICK_TRAVEL_MAX_PX")
SCALE_MAX = wcfg("SCALE_MAX")
ROW_PITCH = wcfg("ROW_PITCH")

BANNER = (
    "/*\n"
    " * Rxroller.c —— 由 design/port_rxroller.py 从上游 Rxroller.c.orig 生成，勿手改。\n"
    " * 上游 https://github.com/rxwind7/Rxroller (MIT)；改动 = LVGL v8 -> 9.4 的\n"
    " * user_data 访问器化（12 处，逐条见 diff）+ 内存 API 别名 + 两条缩放能力补丁\n"
    " *（衰减窗口 RX_SCALE_SPAN_PITCHES、中心满档 RXROLLER_SCALE_MAX，值均取自\n"
    " *  watch_list_config.h；各取 1 / 255 即逐字恢复上游行为）。\n"
    " * 完整账单与复核方法见工程根目录 PORTLOG.md。\n"
    " * 与上游的 diff 就是移植账单：diff Rxroller.c.orig Rxroller.c\n"
    " */\n"
)

# (上游原文, 替换文本, 期望命中次数)
PATCHES = [
    # LVGL 9 的内存 API 改名：lv_mem_alloc/lv_mem_free -> lv_malloc/lv_free
    # （src/stdlib/lv_mem.h:69/97）。上游 v8 写法只报"隐式声明"警告，链接期才炸，
    # 所以在这里补两个别名宏，上游正文照旧不动。
    ('#include "Rxroller.h"\n',
     '#include "Rxroller.h"\n'
     '/* RX-PORT: LVGL 9 内存 API 改名（lv_mem_alloc->lv_malloc, lv_mem_free->lv_free）*/\n'
     '#ifndef lv_mem_alloc\n#  define lv_mem_alloc(sz) lv_malloc(sz)\n#endif\n'
     '#ifndef lv_mem_free\n#  define lv_mem_free(p)   lv_free(p)\n#endif\n'
     '/* RX-PORT-FEAT: 缩放衰减窗口，单位=行距。上游写死 1 ⇒ 只有正中那行是大的，\n'
     ' *  紧邻行立刻落到 edge_scale（= "未选中就是最小"的口径）。\n'
     ' *  调大它才有"上下几行连续渐变"。值来自 watch_list_config.h 的\n'
     ' *  SCALE_SPAN_PITCHES，取 1 时与上游行为完全一致。\n'
     ' *  这是**能力补丁**不是版本适配，diff 里单列一条。 */\n'
     '#ifndef RX_SCALE_SPAN_PITCHES\n#  define RX_SCALE_SPAN_PITCHES %d\n#endif\n'
     '/* RX-PORT-FEAT: 中心档（满档）缩放。上游写死 255 ⇒ 中心最多只到位图原尺寸，\n'
     ' *  再想大就得放开它。256 = LVGL transform_zoom 的 100%%，值来自\n'
     ' *  watch_list_config.h 的 SCALE_CENTER_PCT。取 255 即恢复上游行为。 */\n'
     '#ifndef RXROLLER_SCALE_MAX\n#  define RXROLLER_SCALE_MAX %d\n#endif\n'
     % (SPAN, SCALE_MAX),
     1),
    # 衰减窗口参数化：三处 icon_distance 换成 span
    ("    int32_t distance = LV_ABS(item->distance);\n"
     "    uint16_t scale;\n"
     "\n"
     "    if (distance == 0) {\n"
     "        scale = 255;\n"
     "    } else if (distance >= (int32_t)ctx->config.icon_distance) {\n"
     "        scale = ctx->config.edge_scale;\n"
     "    } else {\n"
     "        int32_t v_data = (int32_t)((float)((int32_t)ctx->config.icon_distance - distance)\n"
     "                         / (float)ctx->config.icon_distance\n"
     "                         * (float)(255 - ctx->config.edge_scale));\n"
     "        scale = (uint16_t)(ctx->config.edge_scale + v_data);\n"
     "    }\n",
     "    int32_t distance = LV_ABS(item->distance);\n"
     "    /* RX-PORT-FEAT: 衰减窗口从 1 个行距放宽到 RX_SCALE_SPAN_PITCHES 个 */\n"
     "    int32_t span = (int32_t)ctx->config.icon_distance * RX_SCALE_SPAN_PITCHES;\n"
     "    uint16_t scale;\n"
     "\n"
     "    if (distance == 0) {\n"
     "        scale = RXROLLER_SCALE_MAX;   /* RX-PORT-FEAT: 上游写死 255=位图原尺寸，\n"
     "                                       *  想「中心比原图还大」必须放开它 */\n"
     "    } else if (distance >= span) {\n"
     "        scale = ctx->config.edge_scale;\n"
     "    } else {\n"
     "        int32_t v_data = (int32_t)((float)(span - distance)\n"
     "                         / (float)span\n"
     "                         * (float)(RXROLLER_SCALE_MAX - ctx->config.edge_scale));\n"
     "        scale = (uint16_t)(ctx->config.edge_scale + v_data);\n"
     "    }\n",
     1),
    ("    if (!wheel->user_data) {",
     "    if (!lv_obj_get_user_data(wheel)) {   /* RX-PORT: v8 直接摸 obj->user_data */",
     1),
    ("    return (rxroller_ctx_t *)wheel->user_data;",
     "    return (rxroller_ctx_t *)lv_obj_get_user_data(wheel);",
     1),
    ("    ctx->screen->user_data = NULL;",
     "    lv_obj_set_user_data(ctx->screen, NULL);",
     1),
    ("    rxroller_ctx_t *ctx = (rxroller_ctx_t *)parent->user_data;",
     "    rxroller_ctx_t *ctx = (rxroller_ctx_t *)lv_obj_get_user_data(parent);",
     3),
    ("    rxroller_item_t *item = (rxroller_item_t *)icon_obj->user_data;",
     "    rxroller_item_t *item = (rxroller_item_t *)lv_obj_get_user_data(icon_obj);",
     1),
    ("    if (parent && lv_obj_is_valid(parent) && parent->user_data) {",
     "    if (parent && lv_obj_is_valid(parent) && lv_obj_get_user_data(parent)) {",
     2),
    ("        item->obj->user_data = item;",
     "        lv_obj_set_user_data(item->obj, item);",
     1),
    ("    rxroller_ctx_t *ctx = (rxroller_ctx_t *)e->user_data;",
     "    rxroller_ctx_t *ctx = (rxroller_ctx_t *)lv_event_get_user_data(e);",
     1),
    ("    ctx->screen->user_data = ctx;",
     "    lv_obj_set_user_data(ctx->screen, ctx);",
     1),
    # ---- RX-PORT-FIX：上游"点击 vs 拖动"判定用错了量 ----
    # ctx->offset 每拍被覆写成"这一拍的增量"（pressing 里 point1 随即跟进），
    # 而 released 用 `offset == 0` 判点击 ⇒ 松手前只要停顿一拍，整段拖动就被
    # 判成点击，上游自己 rx_set_center(click_id) 把列表切到松手那一行
    # （现象："拖完自动回弹")。改成按整段手势累计位移判。
    ("    int32_t         offset;\n",
     "    int32_t         offset;\n"
     "    int32_t         drag_travel;  /* RX-PORT-FIX: 整段手势累计位移 */\n",
     1),
    ("        lv_indev_get_point(lv_indev_get_act(), &ctx->touch_point1);\n"
     "        ctx->touched = 1;\n"
     "        ctx->pending_anim_count = 0;\n"
     "        ctx->offset = 0;\n",
     "        lv_indev_get_point(lv_indev_get_act(), &ctx->touch_point1);\n"
     "        ctx->touched = 1;\n"
     "        ctx->pending_anim_count = 0;\n"
     "        ctx->offset = 0;\n"
     "        ctx->drag_travel = 0;      /* RX-PORT-FIX: 新手势清零 */\n",
     1),
    ("    } else {\n"
     "        ctx->offset = ctx->touch_point2.y - ctx->touch_point1.y;\n"
     "        ctx->touch_point1.y = ctx->touch_point2.y;\n"
     "    }\n",
     "    } else {\n"
     "        ctx->offset = ctx->touch_point2.y - ctx->touch_point1.y;\n"
     "        ctx->touch_point1.y = ctx->touch_point2.y;\n"
     "    }\n"
     "    ctx->drag_travel += LV_ABS(ctx->offset);   /* RX-PORT-FIX: 累计位移 */\n",
     1),
    ("    uint8_t is_click = (ctx->offset == 0 && ctx->pending_anim_count == 0 && target != ctx->screen);",
     "    /* RX-PORT-FIX: 原来用单拍 offset 判点击 ⇒ 松手前停一下就误判成点击，\n"
     "     *   列表被动画切回松手那一行（现象=拖完自动回弹）。改按累计位移判。 */\n"
     "    uint8_t is_click = (ctx->drag_travel <= RXROLLER_CLICK_TRAVEL_MAX\n"
     "                        && ctx->pending_anim_count == 0 && target != ctx->screen);",
     1),
    # 阈值定义（放在文件头，便于按屏/行距调）
    ('#include "Rxroller.h"\n',
     '#include "Rxroller.h"\n'
     '/* RX-PORT-FIX: 累计位移 <= 该值才算点击（px）。行距 %dpx，轻点抖动远小于它 */\n'
     '#ifndef RXROLLER_CLICK_TRAVEL_MAX\n'
     '#  define RXROLLER_CLICK_TRAVEL_MAX %d\n'
     '#endif\n' % (ROW_PITCH, CLICK_MAX),
     1),
]


def patched_text():
    """从上游原文算出补丁后的文本（preflight 用它做逐字节重放比对）"""
    if not os.path.exists(UPSTREAM):
        sys.exit("缺上游原文：%s" % UPSTREAM)
    with open(UPSTREAM, encoding="utf-8-sig") as f:
        text = f.read()

    for old, new, want in PATCHES:
        got = text.count(old)
        if got != want:
            sys.exit("锚点命中 %d 次（应为 %d）：%s" % (got, want, old.strip()))
        text = text.replace(old, new)

    # 收尾自检：lv 对象上的裸 user_data 必须清零。
    # 先剥注释与字符串字面量——否则本脚本自己写的 RX-PORT 注释、上游的
    # SW_LOG_ERROR("wheel->user_data is NULL") 都会被误判成残留。
    code = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    code = re.sub(r'"(?:[^"\\\n]|\\.)*"', '""', code)
    residue = [ln.strip() for ln in code.splitlines()
               if re.search(r"\b(wheel|parent|icon_obj|screen|e|obj)->user_data\b", ln)]
    if residue:
        sys.exit("还有未改的裸 user_data：\n  " + "\n  ".join(residue))

    return BANNER + text


def main():
    text = patched_text()
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("written: %s（12 处 user_data 访问器化 + 内存 API 别名 + 缩放窗口补丁，"
          "上游原文其余逐字未动）" % OUT)


if __name__ == "__main__":
    main()
