#ifndef VALUE_BIND_H
#define VALUE_BIND_H

#ifdef __cplusplus
extern "C" {
#endif

void value_bind_init(void);
/* 色温滑条值 → 开尔文（唯一映射，UI 读数与仿真页头共用） */
int value_bind_cct(int slider_value);

#ifdef __cplusplus
}
#endif

#endif
