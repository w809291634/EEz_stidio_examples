# -*- coding: utf-8 -*-
"""生成 src/native/nav_bind_table.h：控件 identifier → 目标屏（或返回）。

真值：design/pages.py 的行为层 + design/nav_map.py 的目标表。
identifier 与 eez_gen 同规则（{页}_{码}{NN}，码表 pages.IO_CODE），逐页按行顺序编号。

用法：python design/nav_bind_gen.py
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import pages as pg            # noqa: E402
import nav_map as nm          # noqa: E402
import overview_pro as ov     # noqa: E402
from eez_gen import PAGE_IDS  # noqa: E402

OUT = os.path.join(ROOT, "src", "native", "nav_bind_table.h")


def screen_id(page):
    return "SCREEN_ID_" + PAGE_IDS[page].upper()


def main():
    entries = []
    for name, _f, _e, _x, rows in pg.PAGES:
        cnt = {}
        for r in rows:
            nm_, cat, act, behav, box = r
            io_k = ov.io_of(name, {"name": nm_, "behav": behav, "cat": cat})
            code = pg.IO_CODE[io_k]
            cnt[code] = cnt.get(code, 0) + 1
            ident = "%s_%s%02d" % (PAGE_IDS[name], code, cnt[code])
            if behav == "返回":
                entries.append((ident, name, None, 1))
            else:
                dst = nm.NAV_TARGETS.get((name, nm_))
                if dst:
                    entries.append((ident, name, dst, 0))
    lines = [
        "/* 由 design/nav_bind_gen.py 生成，勿手改。 */",
        "#ifndef NAV_BIND_TABLE_H",
        "#define NAV_BIND_TABLE_H",
        "",
        "#include \"screens.h\"",
        "",
        "#define NAV_PAGE_LIST(X) \\",
    ]
    for name, _f, _e, _x, _r in pg.PAGES:
        lines.append("    X(%s, %s) \\" % (screen_id(name), PAGE_IDS[name]))
    lines = lines[:-1] + [lines[-1].rstrip(" \\"), ""]
    lines += [
        "typedef struct {",
        "    lv_obj_t **obj;",
        "    int src;",
        "    int dst;",
        "    int back;   /* 1 = 返回来路 */",
        "} nav_bind_entry_t;",
        "",
        "static const nav_bind_entry_t NAV_BIND[] = {",
    ]
    for ident, src, dst, back in entries:
        lines.append("    { &objects.%s, %s, %s, %d },"
                     % (ident, screen_id(src),
                        "0" if back else screen_id(dst), back))
    lines += [
        "};",
        "#define NAV_BIND_COUNT ((int)(sizeof(NAV_BIND) / sizeof(NAV_BIND[0])))",
        "",
        "#endif",
        "",
    ]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
    print("[NAV_BIND] %d 条（静态 %d / 返回 %d）→ %s"
          % (len(entries), sum(1 for e in entries if not e[3]),
             sum(1 for e in entries if e[3]), OUT))


if __name__ == "__main__":
    main()
