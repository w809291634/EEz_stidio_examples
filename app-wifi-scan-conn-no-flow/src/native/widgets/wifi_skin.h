/*
 * wifi_skin.h — 这套 WiFi 控件的"皮肤参数"（唯一真值）
 *
 * 换成另一个设计时，只改这里：行高与行内配色、遮罩/转圈、眼睛尺寸与配色。
 * 几何里唯一写死的值是行高——列表行是 native 画的，EEZ 侧没有对应控件可对齐。
 * 其余尺寸都跟随 EEZ 控件（半页动画取 sheet 实际高度，眼睛跟随 pwd_ta 矩形）。
 */
#pragma once

/******************** 列表行 ********************/

#define ROW_H        44          /* 行高（与设计图一致） */
#define C_BAR_ON     0x5B8CFF    /* 信号条：亮 */
#define C_BAR_OFF    0x2A3550    /* 信号条：暗 */
#define C_CONN       0x3DDC97    /* 「已连接」文字/描边 */
#define C_SAVED      0x9DB8FF    /* 「已保存」文字 */
#define C_OPEN       0x5C6A85    /* 「无需密码」文字 */
#define C_ROW_BG     0x101A28    /* 行底色 */
#define C_ROW_EDGE   0x26314A    /* 行描边/分隔 */
#define C_TEXT1      0xF0F4FC    /* 主文字 */
#define C_TEXT2      0x8A99B3    /* 次要文字 */

/******************** 连接中遮罩 ********************/

#define C_MASK       0x05070D    /* 遮罩底色（与对话框遮罩同色） */
#define MASK_OPA     204         /* 遮罩不透明度 0~255（LV_OPA_80） */
#define C_PRI        0x5B8CFF    /* 主色：转圈高亮、按住高亮 */
#define BUSY_SPIN_SIZE  64       /* 转圈直径 */
#define BUSY_SPIN_ARC   30       /* 弧长（度）：lv_spinner 是"伸缩+旋转"，别给大值 */
#define BUSY_SPIN_W     6        /* 线宽 */
#define BUSY_SPIN_MS    1000     /* 一圈时长 */

/******************** 密码框眼睛 ********************/

#define EYE_W        26
#define EYE_H        26
#define EYE_PAD_R    36          /* 输入框右侧留给眼睛的宽度 */
#define C_IDLE       0x8A99B3    /* 平时：次要文字色 */
#define C_ACTIVE     0x5B8CFF    /* 按住：主色 */
