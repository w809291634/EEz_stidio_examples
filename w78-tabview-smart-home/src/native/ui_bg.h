#ifndef UI_BG_H
#define UI_BG_H

#ifdef __cplusplus
extern "C" {
#endif

/* 从文件系统加载固定背景图，套到全部业务屏（A: → 工程根 / 真机存储）。
 * 默认路径 A:/assets/ui_bg.png，可在编译时用 -DUI_BG_PATH="..." 覆盖。 */
void ui_bg_apply(void);

#ifdef __cplusplus
}
#endif

#endif
