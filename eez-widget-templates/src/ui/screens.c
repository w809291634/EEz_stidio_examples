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

screen_spangroup_state_t screen_spangroup_state;

//
// Event handlers
//

lv_obj_t *tick_value_change_obj;

//
// Screens
//

void create_screen_label() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.label = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_label_create(parent_obj);
            lv_obj_set_pos(obj, 360, 224);
            lv_obj_set_size(obj, LV_SIZE_CONTENT, LV_SIZE_CONTENT);
            lv_label_set_text_static(obj, "Text");
        }
    }
    
    tick_screen_label();
}

void tick_screen_label() {
}

void create_screen_button() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.button = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_button_create(parent_obj);
            lv_obj_set_pos(obj, 350, 215);
            lv_obj_set_size(obj, 100, 50);
            {
                lv_obj_t *parent_obj = obj;
                {
                    lv_obj_t *obj = lv_label_create(parent_obj);
                    lv_obj_set_pos(obj, 0, 0);
                    lv_obj_set_size(obj, LV_SIZE_CONTENT, LV_SIZE_CONTENT);
                    lv_obj_set_style_align(obj, LV_ALIGN_CENTER, LV_PART_MAIN | LV_STATE_DEFAULT);
                    lv_label_set_text_static(obj, "Button");
                }
            }
        }
    }
    
    tick_screen_button();
}

void tick_screen_button() {
}

void create_screen_switch() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.switch = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_switch_create(parent_obj);
            lv_obj_set_pos(obj, 375, 228);
            lv_obj_set_size(obj, 50, 25);
        }
    }
    
    tick_screen_switch();
}

void tick_screen_switch() {
}

void create_screen_arc() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.arc = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_arc_create(parent_obj);
            lv_obj_set_pos(obj, 325, 165);
            lv_obj_set_size(obj, 150, 150);
            lv_arc_set_value(obj, 25);
        }
    }
    
    tick_screen_arc();
}

void tick_screen_arc() {
}

void create_screen_bar() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.bar = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_bar_create(parent_obj);
            lv_obj_set_pos(obj, 325, 235);
            lv_obj_set_size(obj, 150, 10);
            lv_bar_set_value(obj, 25, LV_ANIM_OFF);
        }
    }
    
    tick_screen_bar();
}

void tick_screen_bar() {
}

void create_screen_chart() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.chart = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_chart_create(parent_obj);
            lv_obj_set_pos(obj, 310, 190);
            lv_obj_set_size(obj, 180, 100);
        }
    }
    
    tick_screen_chart();
}

void tick_screen_chart() {
}

void create_screen_checkbox() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.checkbox = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_checkbox_create(parent_obj);
            lv_obj_set_pos(obj, 348, 230);
            lv_obj_set_size(obj, LV_SIZE_CONTENT, LV_SIZE_CONTENT);
            lv_checkbox_set_text_static(obj, "Checkbox");
        }
    }
    
    tick_screen_checkbox();
}

void tick_screen_checkbox() {
}

void create_screen_container() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.container = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_obj_create(parent_obj);
            lv_obj_set_pos(obj, 250, 140);
            lv_obj_set_size(obj, 300, 200);
            lv_obj_set_style_pad_left(obj, 0, LV_PART_MAIN | LV_STATE_DEFAULT);
            lv_obj_set_style_pad_top(obj, 0, LV_PART_MAIN | LV_STATE_DEFAULT);
            lv_obj_set_style_pad_right(obj, 0, LV_PART_MAIN | LV_STATE_DEFAULT);
            lv_obj_set_style_pad_bottom(obj, 0, LV_PART_MAIN | LV_STATE_DEFAULT);
            lv_obj_set_style_bg_opa(obj, 0, LV_PART_MAIN | LV_STATE_DEFAULT);
            lv_obj_set_style_border_width(obj, 0, LV_PART_MAIN | LV_STATE_DEFAULT);
            lv_obj_set_style_radius(obj, 0, LV_PART_MAIN | LV_STATE_DEFAULT);
        }
    }
    
    tick_screen_container();
}

void tick_screen_container() {
}

void create_screen_dropdown() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.dropdown = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_dropdown_create(parent_obj);
            lv_obj_set_pos(obj, 325, 224);
            lv_obj_set_size(obj, 150, LV_SIZE_CONTENT);
            lv_dropdown_set_options_static(obj, "Option 1\nOption 2\nOption 3");
            lv_dropdown_set_selected(obj, 0);
        }
    }
    
    tick_screen_dropdown();
}

void tick_screen_dropdown() {
}

void create_screen_keyboard() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.keyboard = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_keyboard_create(parent_obj);
            lv_obj_set_pos(obj, 250, 180);
            lv_obj_set_size(obj, 300, 120);
            lv_obj_set_style_align(obj, LV_ALIGN_DEFAULT, LV_PART_MAIN | LV_STATE_DEFAULT);
        }
    }
    
    tick_screen_keyboard();
}

void tick_screen_keyboard() {
}

void create_screen_led() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.led = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_led_create(parent_obj);
            objects.obj0 = obj;
            lv_obj_set_pos(obj, 384, 224);
            lv_obj_set_size(obj, 32, 32);
            lv_led_set_color(obj, lv_color_hex(0x0000ff));
            lv_led_set_brightness(obj, 255);
        }
    }
    
    tick_screen_led();
}

void tick_screen_led() {
}

void create_screen_list() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.list = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_list_create(parent_obj);
            lv_obj_set_pos(obj, 310, 190);
            lv_obj_set_size(obj, 180, 100);
        }
    }
    
    tick_screen_list();
}

void tick_screen_list() {
}

void create_screen_panel() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.panel = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_obj_create(parent_obj);
            lv_obj_set_pos(obj, 250, 140);
            lv_obj_set_size(obj, 300, 200);
        }
    }
    
    tick_screen_panel();
}

void tick_screen_panel() {
}

void create_screen_roller() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.roller = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_roller_create(parent_obj);
            lv_obj_set_pos(obj, 360, 190);
            lv_obj_set_size(obj, 80, 100);
            lv_roller_set_options(obj, "Option 1\nOption 2\nOption 3", LV_ROLLER_MODE_NORMAL);
        }
    }
    
    tick_screen_roller();
}

void tick_screen_roller() {
}

void create_screen_scale() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.scale = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_scale_create(parent_obj);
            objects.obj1 = obj;
            lv_obj_set_pos(obj, 280, 220);
            lv_obj_set_size(obj, 240, 40);
            lv_scale_set_mode(obj, LV_SCALE_MODE_HORIZONTAL_BOTTOM);
            lv_scale_set_range(obj, 10, 40);
            lv_scale_set_angle_range(obj, 270);
            lv_scale_set_rotation(obj, 135);
            lv_scale_set_total_tick_count(obj, 31);
            lv_scale_set_major_tick_every(obj, 5);
            lv_scale_set_label_show(obj, true);
        }
    }
    
    tick_screen_scale();
}

void tick_screen_scale() {
}

void create_screen_slider() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.slider = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_slider_create(parent_obj);
            lv_obj_set_pos(obj, 325, 235);
            lv_obj_set_size(obj, 150, 10);
            lv_slider_set_value(obj, 25, LV_ANIM_OFF);
        }
    }
    
    tick_screen_slider();
}

void tick_screen_slider() {
}

void create_screen_spinner() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.spinner = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_spinner_create(parent_obj);
            lv_obj_set_pos(obj, 360, 200);
            lv_obj_set_size(obj, 80, 80);
        }
    }
    
    tick_screen_spinner();
}

void tick_screen_spinner() {
}

void create_screen_textarea() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.textarea = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_textarea_create(parent_obj);
            lv_obj_set_pos(obj, 325, 205);
            lv_obj_set_size(obj, 150, 70);
            lv_textarea_set_max_length(obj, 128);
            lv_textarea_set_one_line(obj, false);
            lv_textarea_set_password_mode(obj, false);
        }
    }
    
    tick_screen_textarea();
}

void tick_screen_textarea() {
}

void create_screen_button_matrix() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.button_matrix = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_buttonmatrix_create(parent_obj);
            lv_obj_set_pos(obj, 253, 92);
            lv_obj_set_size(obj, 240, 240);
            static const char *map[1] = {
                NULL,
            };
            lv_buttonmatrix_set_map(obj, map);
        }
    }
    
    tick_screen_button_matrix();
}

void tick_screen_button_matrix() {
}

void create_screen_tabview() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.tabview = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_tabview_create(parent_obj);
            lv_obj_set_pos(obj, 283, 162);
            lv_obj_set_size(obj, 180, 100);
            lv_tabview_set_tab_bar_position(obj, LV_DIR_TOP);
            lv_tabview_set_tab_bar_size(obj, 32);
            {
                lv_obj_t *parent_obj = obj;
                {
                    lv_obj_t *obj = lv_tabview_add_tab(parent_obj, "Tab");
                }
            }
        }
    }
    
    tick_screen_tabview();
}

void tick_screen_tabview() {
}

void create_screen_image() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.image = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_image_create(parent_obj);
            lv_obj_set_pos(obj, 323, 264);
            lv_obj_set_size(obj, LV_SIZE_CONTENT, LV_SIZE_CONTENT);
        }
    }
    
    tick_screen_image();
}

void tick_screen_image() {
}

void create_screen_menu() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.menu = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_menu_create(parent_obj);
            lv_obj_set_pos(obj, 283, 264);
            lv_obj_set_size(obj, 180, 100);
        }
    }
    
    tick_screen_menu();
}

void tick_screen_menu() {
}

void create_screen_message_box() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.message_box = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_msgbox_create(parent_obj);
            lv_obj_set_pos(obj, 283, 264);
            lv_obj_set_size(obj, 180, 100);
            lv_obj_set_style_align(obj, LV_ALIGN_DEFAULT, LV_PART_MAIN | LV_STATE_DEFAULT);
        }
    }
    
    tick_screen_message_box();
}

void tick_screen_message_box() {
}

void create_screen_qr_code() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.qr_code = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_qrcode_create(parent_obj);
            objects.obj2 = obj;
            lv_obj_set_pos(obj, 293, 240);
            lv_obj_set_size(obj, 160, 160);
            lv_qrcode_set_size(obj, 160);
            lv_qrcode_set_dark_color(obj, lv_color_hex(0x20429f));
            lv_qrcode_set_light_color(obj, lv_color_hex(0xe2f5fe));
            lv_qrcode_update(obj, "https://envox.eu/", 17);
            lv_obj_add_flag(obj, LV_OBJ_FLAG_CLICKABLE);
        }
    }
    
    tick_screen_qr_code();
}

void tick_screen_qr_code() {
}

void create_screen_spangroup() {
    screen_spangroup_state_t *state = &screen_spangroup_state;
    (void)state;
    lv_obj_t *obj = lv_obj_create(0);
    objects.spangroup = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_spangroup_create(parent_obj);
            lv_obj_set_pos(obj, 283, 264);
            lv_obj_set_size(obj, LV_SIZE_CONTENT, LV_SIZE_CONTENT);
            {
                state->span_0 = lv_spangroup_add_span(obj);
                lv_span_set_text_static(state->span_0, "Span");
            }
            lv_spangroup_refresh(obj);
        }
    }
    
    tick_screen_spangroup();
}

void tick_screen_spangroup() {
    screen_spangroup_state_t *state = &screen_spangroup_state;
    (void)state;
}

void create_screen_table() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.table = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_table_create(parent_obj);
            lv_obj_set_pos(obj, 283, 264);
            lv_obj_set_size(obj, 180, 100);
        }
    }
    
    tick_screen_table();
}

void tick_screen_table() {
}

void create_screen_tile_view() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.tile_view = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_tileview_create(parent_obj);
            lv_obj_set_pos(obj, 283, 264);
            lv_obj_set_size(obj, 180, 100);
        }
    }
    
    tick_screen_tile_view();
}

void tick_screen_tile_view() {
}

void create_screen_window() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.window = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_win_create(parent_obj);
            lv_obj_set_pos(obj, 283, 264);
            lv_obj_set_size(obj, 180, 100);
        }
    }
    
    tick_screen_window();
}

void tick_screen_window() {
}

void create_screen_calendar() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.calendar = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_calendar_create(parent_obj);
            lv_obj_set_pos(obj, 258, 194);
            lv_obj_set_size(obj, 230, 240);
            lv_calendar_add_header_arrow(obj);
            lv_calendar_set_today_date(obj, 2022, 11, 1);
            lv_calendar_set_month_shown(obj, 2022, 11);
        }
    }
    
    tick_screen_calendar();
}

void tick_screen_calendar() {
}

void create_screen_imgbutton() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.imgbutton = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_imagebutton_create(parent_obj);
            lv_obj_set_pos(obj, 336, 282);
            lv_obj_set_size(obj, LV_SIZE_CONTENT, 64);
        }
    }
    
    tick_screen_imgbutton();
}

void tick_screen_imgbutton() {
}

void create_screen_spinbox() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.spinbox = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_spinbox_create(parent_obj);
            lv_obj_set_pos(obj, 283, 264);
            lv_obj_set_size(obj, 180, 100);
            lv_spinbox_set_digit_format(obj, 5, 0);
            lv_spinbox_set_range(obj, -99999, 99999);
            lv_spinbox_set_rollover(obj, false);
            lv_spinbox_set_step(obj, 1);
            lv_spinbox_set_value(obj, 0);
        }
    }
    
    tick_screen_spinbox();
}

void tick_screen_spinbox() {
}

void create_screen_animation_image() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.animation_image = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_animimg_create(parent_obj);
            lv_obj_set_pos(obj, 283, 264);
            lv_obj_set_size(obj, 180, 100);
        }
    }
    
    tick_screen_animation_image();
}

void tick_screen_animation_image() {
}

void create_screen_canvas() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.canvas = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_canvas_create(parent_obj);
            lv_obj_set_pos(obj, 283, 264);
            lv_obj_set_size(obj, 180, 100);
        }
    }
    
    tick_screen_canvas();
}

void tick_screen_canvas() {
}

void create_screen_line() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.line = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_line_create(parent_obj);
            lv_obj_set_pos(obj, 273, 289);
            lv_obj_set_size(obj, LV_SIZE_CONTENT, LV_SIZE_CONTENT);
            static lv_point_precise_t line_points[] = {
                { 0, 0 },
                { 50, 50 },
                { 100, 0 },
                { 150, 50 },
                { 200, 0 }
            };
            lv_line_set_points(obj, line_points, 5);
        }
    }
    
    tick_screen_line();
}

void tick_screen_line() {
}

void create_screen_tabview0() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.tabview0 = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_tabview_create(parent_obj);
            lv_obj_set_pos(obj, 283, 264);
            lv_obj_set_size(obj, 180, 100);
            lv_tabview_set_tab_bar_position(obj, LV_DIR_TOP);
            lv_tabview_set_tab_bar_size(obj, 32);
        }
    }
    
    tick_screen_tabview0();
}

void tick_screen_tabview0() {
}

void create_screen_tabview1() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.tabview1 = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_tabview_create(parent_obj);
            lv_obj_set_pos(obj, 283, 264);
            lv_obj_set_size(obj, 180, 100);
            lv_tabview_set_tab_bar_position(obj, LV_DIR_TOP);
            lv_tabview_set_tab_bar_size(obj, 32);
            {
                lv_obj_t *parent_obj = obj;
                {
                    lv_obj_t *obj = lv_tabview_add_tab(parent_obj, "Tab");
                }
            }
        }
    }
    
    tick_screen_tabview1();
}

void tick_screen_tabview1() {
}

void create_screen_tabview2() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.tabview2 = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_tabview_create(parent_obj);
            lv_obj_set_pos(obj, 283, 264);
            lv_obj_set_size(obj, 180, 100);
            lv_tabview_set_tab_bar_position(obj, LV_DIR_TOP);
            lv_tabview_set_tab_bar_size(obj, 32);
            {
                lv_obj_t *parent_obj = obj;
                {
                    lv_obj_t *obj = lv_tabview_add_tab(parent_obj, "Tab");
                }
                {
                    lv_obj_t *obj = lv_tabview_add_tab(parent_obj, "Tab");
                }
            }
        }
    }
    
    tick_screen_tabview2();
}

void tick_screen_tabview2() {
}

void create_screen_tabview3() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.tabview3 = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_tabview_create(parent_obj);
            lv_obj_set_pos(obj, 283, 264);
            lv_obj_set_size(obj, 180, 100);
            lv_tabview_set_tab_bar_position(obj, LV_DIR_TOP);
            lv_tabview_set_tab_bar_size(obj, 32);
            {
                lv_obj_t *parent_obj = obj;
                {
                    lv_obj_t *obj = lv_tabview_add_tab(parent_obj, "Tab");
                }
                {
                    lv_obj_t *obj = lv_tabview_add_tab(parent_obj, "Tab");
                }
                {
                    lv_obj_t *obj = lv_tabview_add_tab(parent_obj, "Tab");
                }
            }
        }
    }
    
    tick_screen_tabview3();
}

void tick_screen_tabview3() {
}

void create_screen_lottie() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.lottie = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 800, 480);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_lottie_create(parent_obj);
            lv_obj_set_pos(obj, 283, 264);
            lv_obj_set_size(obj, 180, 100);
        }
    }
    
    tick_screen_lottie();
}

void tick_screen_lottie() {
}

typedef void (*tick_screen_func_t)();
tick_screen_func_t tick_screen_funcs[] = {
    tick_screen_label,
    tick_screen_button,
    tick_screen_switch,
    tick_screen_arc,
    tick_screen_bar,
    tick_screen_chart,
    tick_screen_checkbox,
    tick_screen_container,
    tick_screen_dropdown,
    tick_screen_keyboard,
    tick_screen_led,
    tick_screen_list,
    tick_screen_panel,
    tick_screen_roller,
    tick_screen_scale,
    tick_screen_slider,
    tick_screen_spinner,
    tick_screen_textarea,
    tick_screen_button_matrix,
    tick_screen_tabview,
    tick_screen_image,
    tick_screen_menu,
    tick_screen_message_box,
    tick_screen_qr_code,
    tick_screen_spangroup,
    tick_screen_table,
    tick_screen_tile_view,
    tick_screen_window,
    tick_screen_calendar,
    tick_screen_imgbutton,
    tick_screen_spinbox,
    tick_screen_animation_image,
    tick_screen_canvas,
    tick_screen_line,
    tick_screen_tabview0,
    tick_screen_tabview1,
    tick_screen_tabview2,
    tick_screen_tabview3,
    tick_screen_lottie,
};
void tick_screen(int screen_index) {
    if (screen_index >= 0 && screen_index < 39) {
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
    lv_theme_t *theme = lv_theme_default_init(dispp, lv_palette_main(LV_PALETTE_BLUE), lv_palette_main(LV_PALETTE_RED), false, LV_FONT_DEFAULT);
    lv_display_set_theme(dispp, theme);
    
    // Initialize screens
    // Create screens
    create_screen_label();
    create_screen_button();
    create_screen_switch();
    create_screen_arc();
    create_screen_bar();
    create_screen_chart();
    create_screen_checkbox();
    create_screen_container();
    create_screen_dropdown();
    create_screen_keyboard();
    create_screen_led();
    create_screen_list();
    create_screen_panel();
    create_screen_roller();
    create_screen_scale();
    create_screen_slider();
    create_screen_spinner();
    create_screen_textarea();
    create_screen_button_matrix();
    create_screen_tabview();
    create_screen_image();
    create_screen_menu();
    create_screen_message_box();
    create_screen_qr_code();
    create_screen_spangroup();
    create_screen_table();
    create_screen_tile_view();
    create_screen_window();
    create_screen_calendar();
    create_screen_imgbutton();
    create_screen_spinbox();
    create_screen_animation_image();
    create_screen_canvas();
    create_screen_line();
    create_screen_tabview0();
    create_screen_tabview1();
    create_screen_tabview2();
    create_screen_tabview3();
    create_screen_lottie();
}