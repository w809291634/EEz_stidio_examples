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

BANNER = (
    "/*\n"
    " * Rxroller.c —— 由 design/port_rxroller.py 从上游 Rxroller.c.orig 生成，勿手改。\n"
    " * 上游 https://github.com/rxwind7/Rxroller (MIT)；改动 = LVGL v8 -> 9.4 的\n"
    " * user_data 访问器化（12 处，逐条见 diff）+ 内存 API 别名 + 一条缩放窗口参数化。\n"
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
     '/* RX-PORT-FEAT: 缩放衰减窗口，单位=行距。上游写死 1（只有中心行放大，\n'
     ' *  相邻行直接落到 edge_scale），参考图（桌面 Design Watch 的 AppList）是\n'
     ' *  好几行连续渐变，所以把窗口放宽到 3 个行距。取 1 即恢复上游行为。\n'
     ' *  这是**能力补丁**不是版本适配，diff 里单列一条。 */\n'
     '#ifndef RX_SCALE_SPAN_PITCHES\n#  define RX_SCALE_SPAN_PITCHES 3\n#endif\n',
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
     "        scale = 255;\n"
     "    } else if (distance >= span) {\n"
     "        scale = ctx->config.edge_scale;\n"
     "    } else {\n"
     "        int32_t v_data = (int32_t)((float)(span - distance)\n"
     "                         / (float)span\n"
     "                         * (float)(255 - ctx->config.edge_scale));\n"
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
