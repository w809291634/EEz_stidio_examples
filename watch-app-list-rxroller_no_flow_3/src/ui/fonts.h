#ifndef EEZ_LVGL_UI_FONTS_H
#define EEZ_LVGL_UI_FONTS_H

#include <lvgl.h>

#ifdef __cplusplus
extern "C" {
#endif

extern const lv_font_t ui_font_cn14;
extern const lv_font_t ui_font_cn16;
extern const lv_font_t ui_font_cn18;
extern const lv_font_t ui_font_cn20;
extern const lv_font_t ui_font_cn22;
extern const lv_font_t ui_font_cn26;
extern const lv_font_t ui_font_cn30;
extern const lv_font_t ui_font_cn44;
extern const lv_font_t ui_font_cn52;
extern const lv_font_t ui_font_cn64;
extern const lv_font_t ui_font_cn76;

#ifndef EXT_FONT_DESC_T
#define EXT_FONT_DESC_T
typedef struct _ext_font_desc_t {
    const char *name;
    const void *font_ptr;
} ext_font_desc_t;
#endif

extern ext_font_desc_t fonts[];

#ifdef __cplusplus
}
#endif

#endif /*EEZ_LVGL_UI_FONTS_H*/