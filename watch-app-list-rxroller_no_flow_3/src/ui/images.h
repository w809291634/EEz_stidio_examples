#ifndef EEZ_LVGL_UI_IMAGES_H
#define EEZ_LVGL_UI_IMAGES_H

#include <lvgl.h>

#ifdef __cplusplus
extern "C" {
#endif

extern const lv_img_dsc_t img_ic_0;
extern const lv_img_dsc_t img_ic_1;
extern const lv_img_dsc_t img_ic_2;
extern const lv_img_dsc_t img_ic_3;
extern const lv_img_dsc_t img_ic_4;
extern const lv_img_dsc_t img_ic_5;
extern const lv_img_dsc_t img_ic_6;
extern const lv_img_dsc_t img_ic_7;
extern const lv_img_dsc_t img_ic_8;
extern const lv_img_dsc_t img_ic_9;
extern const lv_img_dsc_t img_ic_10;
extern const lv_img_dsc_t img_ic_11;
extern const lv_img_dsc_t img_ic_12;
extern const lv_img_dsc_t img_ic_13;

#ifndef EXT_IMG_DESC_T
#define EXT_IMG_DESC_T
typedef struct _ext_img_desc_t {
    const char *name;
    const lv_img_dsc_t *img_dsc;
} ext_img_desc_t;
#endif

extern const ext_img_desc_t images[14];

#ifdef __cplusplus
}
#endif

#endif /*EEZ_LVGL_UI_IMAGES_H*/