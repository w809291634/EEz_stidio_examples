/*
 * native_vars.h — native 变量桥声明（EEZ 生成的 vars.h 也会声明；此处供内部引用）。
 * ★ 必须包 extern "C"，否则 C 侧链接报 undefined reference。
 */
#pragma once
#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

int32_t get_var_scan_state(void);
void    set_var_scan_state(int32_t v);
int32_t get_var_ap_gen(void);
void    set_var_ap_gen(int32_t v);
const char *get_var_scan_status(void);
void        set_var_scan_status(const char *s);

#ifdef __cplusplus
}
#endif
