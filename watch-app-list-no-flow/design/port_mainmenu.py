# -*- coding: utf-8 -*-
"""从 SiFli SDK 逐字拷入 app_mainmenu.c，再做**最小**接线改造。

跑法：python design/port_mainmenu.py   （只在移植源变更时需要重跑）
产物：src/native/watch_app_list.c

设计口径：算法本体（蜂窝布局 / 穹顶缩放 / 甩动吸附 / 逐帧 transform）
**一行都不重写**，只替换依赖层与生命周期。每处改动都带 PORT: 注释，
diff 出来的量就是"移植到底动了什么"的账单。
"""
import io
import os
import sys

SRC = r"D:\temp_d\SiFli-SDK\example\multimedia\lvgl\watch_v9\src\gui_apps\main\app_mainmenu.c"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "src", "native", "watch_app_list.c")

if not os.path.exists(SRC):
    sys.exit("找不到移植源：%s" % SRC)

text = io.open(SRC, encoding="utf-8", errors="replace").read()


def replace_once(old, new, tag):
    global text
    if old not in text:
        sys.exit("锚点没命中：%s" % tag)
    if text.count(old) > 1 and not tag.startswith("allow-multi"):
        sys.exit("锚点不唯一（%d 处）：%s" % (text.count(old), tag))
    text = text.replace(old, new, 1)
    print("patched: %s" % tag)


def cut_between(start, end, new, tag):
    """把 [start, end) 整段换掉（end 保留）"""
    global text
    i = text.index(start)
    j = text.index(end, i + len(start))
    text = text[:i] + new + text[j:]
    print("cut: %s（%d 字符）" % (tag, j - i))


# ---------- 1. 版权头改成本工程口径，出处保留 ----------
cut_between("/*\n * SPDX-FileCopyrightText: 2019-2026 SiFli",
            "/*********************",
            '/*\n'
            ' * watch_app_list.c —— 手表蜂窝缩放应用列表（移植件）\n'
            ' *\n'
            ' * 逐字来自 SiFli SDK example/multimedia/lvgl/watch_v9/\n'
            ' *   src/gui_apps/main/app_mainmenu.c\n'
            ' *   SPDX-FileCopyrightText: 2019-2026 SiFli Technologies(Nanjing) Co., Ltd\n'
            ' *   SPDX-License-Identifier: Apache-2.0\n'
            ' *\n'
            ' * 移植改动全部标了 "PORT:"，算法本体未改写。\n'
            ' * 依赖替身见 sifli_compat.h；穹顶曲线复算见 watch_icon_transform.c。\n'
            ' */\n'
            '\n',
            "banner")

# ---------- 2. 依赖层换成 compat 单头 ----------
cut_between("#include <rtthread.h>",
            "/*------------------------------------mainmenu_layout_celluar",
            '#include "sifli_compat.h"   /* PORT: RT-Thread / GUI 框架 / 私有头 全在这一层 */\n'
            '#include "watch_app_list.h"  /* PORT: 本工程对外的三个入口 */\n'
            '\n'
            '/* PORT: 宿主容器（EEZ 生成的 objects.list_host）由 watch_app_list_create 注入；\n'
            ' *        必须声明在这里——mainmenu_cell_ui_init 比创建入口先被编译到。 */\n'
            'static lv_obj_t *s_host = NULL;\n'
            '\n'
            '/* PORT: 原文件在这里 LV_IMG_DECLARE 了 26 个图标；本工程的图标由\n'
            ' *        design/gen_icons.py 生成、经 sifli_compat.c 的应用表提供。 */\n'
            '\n',
            "includes+imgdecl")

# ---------- 3. 中段重复的框架头 / 遗留 include / 输入代理分支 ----------
replace_once('#include "gui_app_fwk.h"\n#define _MODULE_NAME_ "mainmenu"',
             '/* PORT: 框架头与调试 TAG 宏随依赖层一起去掉 */',
             "gui_app_fwk-2nd")

# 布局段的 lv_math.h 在 cut#2 的锚点之后，单独摘掉（9.4 的 lvgl.h 已带）
replace_once('#include "lv_math.h"\n', '', "lv_math-include")

# monkey_mode() 是 SiFli 输入代理（随机点击演示）专用，本工程没有该后端；
# 留着会让"依赖残留清零"这条门禁只能放宽成文本级，所以直接摘掉。
replace_once("    bool monkey = false;\n"
             "#if defined (BSP_USING_LVGL_INPUT_AGENT)\n"
             "    monkey = (0 != monkey_mode()) ? true : false;\n"
             "#endif\n",
             "    /* PORT: 原文件这里读 SiFli 输入代理的 monkey_mode()（随机点击演示），\n"
             "     *       PC 仿真无该后端，去掉后判定条件等价于 !scroll_actived。 */\n",
             "monkey-decl")
replace_once("             && (monkey || !p_menu_cell->scroll_actived))",
             "             && !p_menu_cell->scroll_actived)", "monkey-cond")
replace_once('        LOG_I("app mainmenu icon clickd: monkey %d \\n", monkey);\n',
             '        LOG_I("app mainmenu icon clicked\\n");\n', "monkey-log")
replace_once("        ready_to_jump = monkey ? true : ready_to_jump;\n",
             "", "monkey-jump")

# ---------- 4. 动态加载应用（DL_APP）这条分支不要 ----------
cut_between("        while (1)\n        {\n            //Fix 1st icon for clock\n"
            "            p_builtin_app = gui_script_app_list_get_next",
            "        gui_builtin_app_list_close(p_builtin_app);",
            "", "dl-app-loop")

# ---------- 5. demo 用的 52 个填充图标整段删掉 ----------
cut_between("#if 1//for demo, full fill screen",
            "static void mainmenu_cell_redraw_app",
            "    /* PORT: 原文件这里再塞 52 个假图标把屏铺满；本工程只留真应用表，\n"
            "     *       蜂窝环带自然向外扩展，铺不铺满由 MAX_APP_*_NUM 决定。 */\n"
            "}\n\n",
            "dummy-icons")

# ---------- 6. 页面挂到 EEZ 生成的宿主容器上，不再自建全屏 ----------
replace_once("    lv_obj_t *page = lv_obj_create(lv_scr_act());\n",
             "    /* PORT: 原来 lv_obj_create(lv_scr_act()) 自建全屏页；本工程挂到 EEZ\n"
             "     *       生成的 objects.list_host 上（它已经是整屏 368x448，\n"
             "       所以屏心与 get_icon_transform_param 用的屏心是同一个点）。 */\n"
             "    lv_obj_t *page = lv_obj_create(s_host);\n",
             "ui-init-parent")

replace_once("    lv_obj_align(page, LV_ALIGN_CENTER, 0, 0);\n",
             "    lv_obj_align(page, LV_ALIGN_TOP_LEFT, 0, 0);   /* PORT: 宿主就是视口，不再居中 */\n",
             "ui-init-align")

# ---------- 7. 生命周期尾部换成显式创建入口 ----------
cut_between("static void on_start(void)",
            "#if 1\nstatic int32_t keypad_handler(lv_key_t key, lv_indev_state_t event)",
            "/*==================== PORT: 生命周期 ====================*/\n"
            "/* 原文件靠 GUI 框架的 msg_handler 分发 ONSTART/ONRESUME/ONPAUSE/ONSTOP；\n"
            " * 本工程没有框架，改成一次性的显式创建：create == on_start + on_resume。\n"
            " * （s_host 声明在文件顶部，ui_init 那段要用） */\n"
            "void watch_app_list_create(lv_obj_t *host, lv_obj_t *status_label)\n"
            "{\n"
            "    uint16_t max_icons;\n"
            "\n"
            "    RT_ASSERT(host);\n"
            "    s_host = host;\n"
            "    watch_app_list_bind_status(status_label);\n"
            "\n"
            "    p_menu_cell = (mainmenu_cell_t *)rt_calloc(1, sizeof(mainmenu_cell_t));\n"
            "    RT_ASSERT(p_menu_cell);\n"
            "    p_menu_cell->zoom = 1;\n"
            "    p_menu_cell->target_zoom = 1;\n"
            "\n"
            "    max_icons = MAX_APP_COL_NUM * MAX_APP_ROW_NUM;\n"
            "    p_menu_cell->list = rt_calloc(1, max_icons * sizeof(lv_obj_t *));\n"
            "    RT_ASSERT(p_menu_cell->list);\n"
            "    p_menu_cell->icon_pivot = rt_calloc(1, max_icons * sizeof(lv_point_t));\n"
            "    RT_ASSERT(p_menu_cell->icon_pivot);\n"
            "\n"
            "    mainmenu_cell_ui_init(NULL);\n"
            "    mainmenu_cell_redraw_app(p_menu_cell->pg_obj);\n"
            "    mainmainmenu_cell_transform(true);\n"
            "    lv_obj_send_event(p_menu_cell->pg_obj, LV_EVENT_SCROLL, NULL);\n"
            "}\n"
            "\n"
            "/* 验收夹具要合成滑动，给它页面对象（未创建返回 NULL） */\n"
            "lv_obj_t *watch_app_list_page(void)\n"
            "{\n"
            "    return p_menu_cell ? p_menu_cell->pg_obj : NULL;\n"
            "}\n"
            "\n"
            "/* 自证钩子：把\"穹顶\"量化成可核对的数字（design/preflight.py 与\n"
            " * design/sim_cmake/main.c 的 WATCH_AUTOTEST 都读这条输出） */\n"
            "void watch_app_list_dump(const char *tag)\n"
            "{\n"
            "    uint8_t row_idx, col_idx;\n"
            "    int visible = 0, max_scale = 0, min_scale = 65536;\n"
            "    const char *center = \"-\";\n"
            "\n"
            "    if (NULL == p_menu_cell) {\n"
            "        printf(\"[LIST] %s 未创建\\n\", tag);\n"
            "        return;\n"
            "    }\n"
            "    for (row_idx = 0; row_idx < MAX_APP_ROW_NUM; row_idx++) {\n"
            "        for (col_idx = 0; col_idx < MAX_APP_COL_NUM; col_idx++) {\n"
            "            lv_obj_t *o = *mainmenu_cell_get_icon_obj(row_idx, col_idx);\n"
            "            int s;\n"
            "            if (NULL == o || lv_obj_has_flag(o, LV_OBJ_FLAG_HIDDEN))\n"
            "                continue;\n"
            "            s = (int)lv_image_get_scale(o);\n"
            "            visible++;\n"
            "            if (s > max_scale) max_scale = s;\n"
            "            if (s < min_scale) min_scale = s;\n"
            "        }\n"
            "    }\n"
            "    if (p_menu_cell->cicon) {\n"
            "        char *cmd = (char *)lv_obj_get_user_data(p_menu_cell->cicon);\n"
            "        center = cmd ? cmd : \"?\";\n"
            "    }\n"
            "    printf(\"[LIST] %-9s scroll=(%4d,%4d) visible=%2d scale=%5d..%5d center=%s\\n\",\n"
            "           tag,\n"
            "           (int)lv_obj_get_scroll_x(p_menu_cell->pg_obj),\n"
            "           (int)lv_obj_get_scroll_y(p_menu_cell->pg_obj),\n"
            "           visible, min_scale == 65536 ? 0 : min_scale, max_scale, center);\n"
            "}\n"
            "\n",
            "lifecycle")

# ---------- 8. 文件尾的框架导出删掉 ----------
i = text.index("static void msg_handler(gui_app_msg_type_t msg, void *param)")
text = text[:i].rstrip() + "\n"
print("cut: msg_handler + BUILTIN_APP_EXPORT 尾部")

# ---------- 9. 头部加 dump 前置声明（定义在后面，但 main.c 只认头文件） ----------
io.open(OUT, "w", encoding="utf-8", newline="\n").write(text)
print("written: %s (%d bytes, %d 行)"
      % (OUT, os.path.getsize(OUT), text.count(chr(10)) + 1))
