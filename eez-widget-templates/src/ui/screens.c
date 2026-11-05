#include <string.h>

#include "screens.h"
#include "images.h"
#include "fonts.h"
#include "actions.h"
#include "vars.h"
#include "styles.h"
#include "ui.h"

#include <string.h>

objects_t objects;

//
// Event handlers
//

lv_obj_t *tick_value_change_obj;

//
// Screens
//

void create_screen_tpl_label() {
    // tpl_screen
    lv_obj_t *obj = lv_obj_create(0);
    objects.tpl_label = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
    {
        lv_obj_t *parent_obj = obj;
        {
            // w_label
            lv_obj_t *obj = lv_label_create(parent_obj);
            objects.w_label = obj;
            lv_obj_set_pos(obj, 40, 60);
            lv_obj_set_size(obj, LV_SIZE_CONTENT, LV_SIZE_CONTENT);
            lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
            lv_label_set_text_static(obj, "Text");
        }
    }
    
    tick_screen_tpl_label();
}

void tick_screen_tpl_label() {
}

void create_screen_tpl_button() {
    // tpl_screen
    lv_obj_t *obj = lv_obj_create(0);
    objects.tpl_button = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
    {
        lv_obj_t *parent_obj = obj;
        {
            // w_button
            lv_obj_t *obj = lv_button_create(parent_obj);
            objects.w_button = obj;
            lv_obj_set_pos(obj, 40, 60);
            lv_obj_set_size(obj, 100, 50);
            lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
            {
                lv_obj_t *parent_obj = obj;
                {
                    // tpl_button_label
                    lv_obj_t *obj = lv_label_create(parent_obj);
                    objects.tpl_button_label = obj;
                    lv_obj_set_pos(obj, 0, 0);
                    lv_obj_set_size(obj, LV_SIZE_CONTENT, LV_SIZE_CONTENT);
                    lv_obj_set_style_align(obj, LV_ALIGN_CENTER, LV_PART_MAIN | LV_STATE_DEFAULT);
                    lv_label_set_text_static(obj, "Button");
                }
            }
        }
    }
    
    tick_screen_tpl_button();
}

void tick_screen_tpl_button() {
}

void create_screen_tpl_container() {
    // tpl_screen
    lv_obj_t *obj = lv_obj_create(0);
    objects.tpl_container = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
    {
        lv_obj_t *parent_obj = obj;
        {
            // w_container
            lv_obj_t *obj = lv_obj_create(parent_obj);
            objects.w_container = obj;
            lv_obj_set_pos(obj, 40, 60);
            lv_obj_set_size(obj, 300, 200);
            lv_obj_set_style_pad_left(obj, 0, LV_PART_MAIN | LV_STATE_DEFAULT);
            lv_obj_set_style_pad_top(obj, 0, LV_PART_MAIN | LV_STATE_DEFAULT);
            lv_obj_set_style_pad_right(obj, 0, LV_PART_MAIN | LV_STATE_DEFAULT);
            lv_obj_set_style_pad_bottom(obj, 0, LV_PART_MAIN | LV_STATE_DEFAULT);
            lv_obj_set_style_bg_opa(obj, 0, LV_PART_MAIN | LV_STATE_DEFAULT);
            lv_obj_set_style_border_width(obj, 0, LV_PART_MAIN | LV_STATE_DEFAULT);
            lv_obj_set_style_radius(obj, 0, LV_PART_MAIN | LV_STATE_DEFAULT);
            lv_obj_add_flag(obj, LV_OBJ_FLAG_SCROLL_ON_FOCUS);
            lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
        }
    }
    
    tick_screen_tpl_container();
}

void tick_screen_tpl_container() {
}

void create_screen_tpl_panel() {
    // tpl_screen
    lv_obj_t *obj = lv_obj_create(0);
    objects.tpl_panel = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
    {
        lv_obj_t *parent_obj = obj;
        {
            // w_panel
            lv_obj_t *obj = lv_obj_create(parent_obj);
            objects.w_panel = obj;
            lv_obj_set_pos(obj, 40, 60);
            lv_obj_set_size(obj, 300, 200);
            lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
        }
    }
    
    tick_screen_tpl_panel();
}

void tick_screen_tpl_panel() {
}

void create_screen_tpl_switch() {
    // tpl_screen
    lv_obj_t *obj = lv_obj_create(0);
    objects.tpl_switch = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
    {
        lv_obj_t *parent_obj = obj;
        {
            // w_switch
            lv_obj_t *obj = lv_switch_create(parent_obj);
            objects.w_switch = obj;
            lv_obj_set_pos(obj, 40, 60);
            lv_obj_set_size(obj, 50, 25);
            lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
        }
    }
    
    tick_screen_tpl_switch();
}

void tick_screen_tpl_switch() {
}

void create_screen_tpl_slider() {
    // tpl_screen
    lv_obj_t *obj = lv_obj_create(0);
    objects.tpl_slider = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
    {
        lv_obj_t *parent_obj = obj;
        {
            // w_slider
            lv_obj_t *obj = lv_slider_create(parent_obj);
            objects.w_slider = obj;
            lv_obj_set_pos(obj, 40, 60);
            lv_obj_set_size(obj, 150, 10);
            lv_slider_set_value(obj, 25, LV_ANIM_OFF);
            lv_obj_add_flag(obj, LV_OBJ_FLAG_SCROLLABLE|LV_OBJ_FLAG_SCROLL_CHAIN_HOR);
            lv_obj_remove_flag(obj, LV_OBJ_FLAG_SCROLL_ON_FOCUS);
            lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
        }
    }
    
    tick_screen_tpl_slider();
}

void tick_screen_tpl_slider() {
}

void create_screen_tpl_bar() {
    // tpl_screen
    lv_obj_t *obj = lv_obj_create(0);
    objects.tpl_bar = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
    {
        lv_obj_t *parent_obj = obj;
        {
            // w_bar
            lv_obj_t *obj = lv_bar_create(parent_obj);
            objects.w_bar = obj;
            lv_obj_set_pos(obj, 40, 60);
            lv_obj_set_size(obj, 150, 10);
            lv_bar_set_value(obj, 25, LV_ANIM_OFF);
            lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
        }
    }
    
    tick_screen_tpl_bar();
}

void tick_screen_tpl_bar() {
}

void create_screen_tpl_arc() {
    // tpl_screen
    lv_obj_t *obj = lv_obj_create(0);
    objects.tpl_arc = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
    {
        lv_obj_t *parent_obj = obj;
        {
            // w_arc
            lv_obj_t *obj = lv_arc_create(parent_obj);
            objects.w_arc = obj;
            lv_obj_set_pos(obj, 40, 60);
            lv_obj_set_size(obj, 150, 150);
            lv_arc_set_value(obj, 25);
            lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
        }
    }
    
    tick_screen_tpl_arc();
}

void tick_screen_tpl_arc() {
}

void create_screen_tpl_chart() {
    // tpl_screen
    lv_obj_t *obj = lv_obj_create(0);
    objects.tpl_chart = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
    {
        lv_obj_t *parent_obj = obj;
        {
            // w_chart
            lv_obj_t *obj = lv_chart_create(parent_obj);
            objects.w_chart = obj;
            lv_obj_set_pos(obj, 40, 60);
            lv_obj_set_size(obj, 180, 100);
            lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
        }
    }
    
    tick_screen_tpl_chart();
}

void tick_screen_tpl_chart() {
}

void create_screen_tpl_scale() {
    // tpl_screen
    lv_obj_t *obj = lv_obj_create(0);
    objects.tpl_scale = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
    {
        lv_obj_t *parent_obj = obj;
        {
            // w_scale
            lv_obj_t *obj = lv_scale_create(parent_obj);
            objects.w_scale = obj;
            lv_obj_set_pos(obj, 40, 60);
            lv_obj_set_size(obj, 240, 40);
            lv_scale_set_mode(obj, LV_SCALE_MODE_HORIZONTAL_BOTTOM);
            lv_scale_set_range(obj, 10, 40);
            lv_scale_set_angle_range(obj, 270);
            lv_scale_set_rotation(obj, 135);
            lv_scale_set_total_tick_count(obj, 31);
            lv_scale_set_major_tick_every(obj, 5);
            lv_scale_set_label_show(obj, true);
            lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
        }
    }
    
    tick_screen_tpl_scale();
}

void tick_screen_tpl_scale() {
}

void create_screen_tpl_led() {
    // tpl_screen
    lv_obj_t *obj = lv_obj_create(0);
    objects.tpl_led = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
    {
        lv_obj_t *parent_obj = obj;
        {
            // w_led
            lv_obj_t *obj = lv_led_create(parent_obj);
            objects.w_led = obj;
            lv_obj_set_pos(obj, 40, 60);
            lv_obj_set_size(obj, 32, 32);
            lv_led_set_color(obj, lv_color_hex(0x0000ff));
            lv_led_set_brightness(obj, 255);
            lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
        }
    }
    
    tick_screen_tpl_led();
}

void tick_screen_tpl_led() {
}

void create_screen_tpl_checkbox() {
    // tpl_screen
    lv_obj_t *obj = lv_obj_create(0);
    objects.tpl_checkbox = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
    {
        lv_obj_t *parent_obj = obj;
        {
            // w_checkbox
            lv_obj_t *obj = lv_checkbox_create(parent_obj);
            objects.w_checkbox = obj;
            lv_obj_set_pos(obj, 40, 60);
            lv_obj_set_size(obj, LV_SIZE_CONTENT, LV_SIZE_CONTENT);
            lv_checkbox_set_text_static(obj, "Checkbox");
            lv_obj_add_flag(obj, LV_OBJ_FLAG_ADV_HITTEST|LV_OBJ_FLAG_SCROLLABLE);
            lv_obj_remove_flag(obj, LV_OBJ_FLAG_CHECKABLE|LV_OBJ_FLAG_SCROLL_CHAIN_HOR|LV_OBJ_FLAG_SCROLL_CHAIN_VER|LV_OBJ_FLAG_SCROLL_ON_FOCUS);
            lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
        }
    }
    
    tick_screen_tpl_checkbox();
}

void tick_screen_tpl_checkbox() {
}

void create_screen_tpl_dropdown() {
    // tpl_screen
    lv_obj_t *obj = lv_obj_create(0);
    objects.tpl_dropdown = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
    {
        lv_obj_t *parent_obj = obj;
        {
            // w_dropdown
            lv_obj_t *obj = lv_dropdown_create(parent_obj);
            objects.w_dropdown = obj;
            lv_obj_set_pos(obj, 40, 60);
            lv_obj_set_size(obj, 150, LV_SIZE_CONTENT);
            lv_dropdown_set_options_static(obj, "Option 1\nOption 2\nOption 3");
            lv_dropdown_set_selected(obj, 0);
            lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
        }
    }
    
    tick_screen_tpl_dropdown();
}

void tick_screen_tpl_dropdown() {
}

void create_screen_tpl_roller() {
    // tpl_screen
    lv_obj_t *obj = lv_obj_create(0);
    objects.tpl_roller = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
    {
        lv_obj_t *parent_obj = obj;
        {
            // w_roller
            lv_obj_t *obj = lv_roller_create(parent_obj);
            objects.w_roller = obj;
            lv_obj_set_pos(obj, 40, 60);
            lv_obj_set_size(obj, 80, 100);
            lv_roller_set_options(obj, "Option 1\nOption 2\nOption 3", LV_ROLLER_MODE_NORMAL);
            lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
        }
    }
    
    tick_screen_tpl_roller();
}

void tick_screen_tpl_roller() {
}

void create_screen_tpl_textarea() {
    // tpl_screen
    lv_obj_t *obj = lv_obj_create(0);
    objects.tpl_textarea = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
    {
        lv_obj_t *parent_obj = obj;
        {
            // w_textarea
            lv_obj_t *obj = lv_textarea_create(parent_obj);
            objects.w_textarea = obj;
            lv_obj_set_pos(obj, 40, 60);
            lv_obj_set_size(obj, 150, 70);
            lv_textarea_set_max_length(obj, 128);
            lv_textarea_set_one_line(obj, false);
            lv_textarea_set_password_mode(obj, false);
            lv_obj_add_flag(obj, LV_OBJ_FLAG_SCROLL_ONE|LV_OBJ_FLAG_SCROLL_WITH_ARROW);
            lv_obj_remove_flag(obj, LV_OBJ_FLAG_SCROLL_ON_FOCUS);
            lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
        }
    }
    
    tick_screen_tpl_textarea();
}

void tick_screen_tpl_textarea() {
}

void create_screen_tpl_keyboard() {
    // tpl_screen
    lv_obj_t *obj = lv_obj_create(0);
    objects.tpl_keyboard = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
    {
        lv_obj_t *parent_obj = obj;
        {
            // w_keyboard
            lv_obj_t *obj = lv_keyboard_create(parent_obj);
            objects.w_keyboard = obj;
            lv_obj_set_pos(obj, 40, 60);
            lv_obj_set_size(obj, 300, 120);
            lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
            lv_obj_set_style_align(obj, LV_ALIGN_DEFAULT, LV_PART_MAIN | LV_STATE_DEFAULT);
        }
    }
    
    tick_screen_tpl_keyboard();
}

void tick_screen_tpl_keyboard() {
}

void create_screen_tpl_list() {
    // tpl_screen
    lv_obj_t *obj = lv_obj_create(0);
    objects.tpl_list = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
    {
        lv_obj_t *parent_obj = obj;
        {
            // w_list
            lv_obj_t *obj = lv_list_create(parent_obj);
            objects.w_list = obj;
            lv_obj_set_pos(obj, 40, 60);
            lv_obj_set_size(obj, 180, 100);
            lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_AUTO);
        }
    }
    
    tick_screen_tpl_list();
}

void tick_screen_tpl_list() {
}

void create_screen_tpl_spinner() {
    // tpl_screen
    lv_obj_t *obj = lv_obj_create(0);
    objects.tpl_spinner = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
    {
        lv_obj_t *parent_obj = obj;
        {
            // w_spinner
            lv_obj_t *obj = lv_spinner_create(parent_obj);
            objects.w_spinner = obj;
            lv_obj_set_pos(obj, 40, 60);
            lv_obj_set_size(obj, 80, 80);
            lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
        }
    }
    
    tick_screen_tpl_spinner();
}

void tick_screen_tpl_spinner() {
}

typedef void (*tick_screen_func_t)();
tick_screen_func_t tick_screen_funcs[] = {
    tick_screen_tpl_label,
    tick_screen_tpl_button,
    tick_screen_tpl_container,
    tick_screen_tpl_panel,
    tick_screen_tpl_switch,
    tick_screen_tpl_slider,
    tick_screen_tpl_bar,
    tick_screen_tpl_arc,
    tick_screen_tpl_chart,
    tick_screen_tpl_scale,
    tick_screen_tpl_led,
    tick_screen_tpl_checkbox,
    tick_screen_tpl_dropdown,
    tick_screen_tpl_roller,
    tick_screen_tpl_textarea,
    tick_screen_tpl_keyboard,
    tick_screen_tpl_list,
    tick_screen_tpl_spinner,
};
void tick_screen(int screen_index) {
    if (screen_index >= 0 && screen_index < 18) {
        tick_screen_funcs[screen_index]();
    }
}
void tick_screen_by_id(enum ScreensEnum screenId) {
    tick_screen(screenId - 1);
}

//
// Fonts
//

ext_font_desc_t fonts[] = {
#if LV_FONT_MONTSERRAT_8
    { "MONTSERRAT_8", &lv_font_montserrat_8 },
#endif
#if LV_FONT_MONTSERRAT_10
    { "MONTSERRAT_10", &lv_font_montserrat_10 },
#endif
#if LV_FONT_MONTSERRAT_12
    { "MONTSERRAT_12", &lv_font_montserrat_12 },
#endif
#if LV_FONT_MONTSERRAT_14
    { "MONTSERRAT_14", &lv_font_montserrat_14 },
#endif
#if LV_FONT_MONTSERRAT_16
    { "MONTSERRAT_16", &lv_font_montserrat_16 },
#endif
#if LV_FONT_MONTSERRAT_18
    { "MONTSERRAT_18", &lv_font_montserrat_18 },
#endif
#if LV_FONT_MONTSERRAT_20
    { "MONTSERRAT_20", &lv_font_montserrat_20 },
#endif
#if LV_FONT_MONTSERRAT_22
    { "MONTSERRAT_22", &lv_font_montserrat_22 },
#endif
#if LV_FONT_MONTSERRAT_24
    { "MONTSERRAT_24", &lv_font_montserrat_24 },
#endif
#if LV_FONT_MONTSERRAT_26
    { "MONTSERRAT_26", &lv_font_montserrat_26 },
#endif
#if LV_FONT_MONTSERRAT_28
    { "MONTSERRAT_28", &lv_font_montserrat_28 },
#endif
#if LV_FONT_MONTSERRAT_30
    { "MONTSERRAT_30", &lv_font_montserrat_30 },
#endif
#if LV_FONT_MONTSERRAT_32
    { "MONTSERRAT_32", &lv_font_montserrat_32 },
#endif
#if LV_FONT_MONTSERRAT_34
    { "MONTSERRAT_34", &lv_font_montserrat_34 },
#endif
#if LV_FONT_MONTSERRAT_36
    { "MONTSERRAT_36", &lv_font_montserrat_36 },
#endif
#if LV_FONT_MONTSERRAT_38
    { "MONTSERRAT_38", &lv_font_montserrat_38 },
#endif
#if LV_FONT_MONTSERRAT_40
    { "MONTSERRAT_40", &lv_font_montserrat_40 },
#endif
#if LV_FONT_MONTSERRAT_42
    { "MONTSERRAT_42", &lv_font_montserrat_42 },
#endif
#if LV_FONT_MONTSERRAT_44
    { "MONTSERRAT_44", &lv_font_montserrat_44 },
#endif
#if LV_FONT_MONTSERRAT_46
    { "MONTSERRAT_46", &lv_font_montserrat_46 },
#endif
#if LV_FONT_MONTSERRAT_48
    { "MONTSERRAT_48", &lv_font_montserrat_48 },
#endif
};

//
// Color themes
//

uint32_t active_theme_index = 0;

//
//
//

void create_screens() {

// Set default LVGL theme
    lv_display_t *dispp = lv_display_get_default();
    lv_theme_t *theme = lv_theme_default_init(dispp, lv_palette_main(LV_PALETTE_BLUE), lv_palette_main(LV_PALETTE_RED), true, LV_FONT_DEFAULT);
    lv_display_set_theme(dispp, theme);
    
    // Initialize screens
    // Create screens
    create_screen_tpl_label();
    create_screen_tpl_button();
    create_screen_tpl_container();
    create_screen_tpl_panel();
    create_screen_tpl_switch();
    create_screen_tpl_slider();
    create_screen_tpl_bar();
    create_screen_tpl_arc();
    create_screen_tpl_chart();
    create_screen_tpl_scale();
    create_screen_tpl_led();
    create_screen_tpl_checkbox();
    create_screen_tpl_dropdown();
    create_screen_tpl_roller();
    create_screen_tpl_textarea();
    create_screen_tpl_keyboard();
    create_screen_tpl_list();
    create_screen_tpl_spinner();
}