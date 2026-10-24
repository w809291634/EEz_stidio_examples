#ifndef WATCH_VIEW_H
#define WATCH_VIEW_H

/* model/platform 快照到 EEZ objects.* 的唯一业务刷新入口。 */
void watch_view_render_all(void);
void watch_view_render_watchface(void);
void watch_view_render_sport(void);
void watch_view_render_spo2(void);
void watch_view_render_messages(void);
void watch_view_render_music(void);
void watch_view_render_alarm(void);
void watch_view_render_stopwatch(void);
void watch_view_render_timer(void);
void watch_view_render_calc(void);
void watch_view_render_editor(void);
void watch_view_render_face_picker(void);
void watch_view_render_find_phone(void);
void watch_view_render_settings(void);
void watch_view_apply_face_theme(void);

#endif /* WATCH_VIEW_H */
