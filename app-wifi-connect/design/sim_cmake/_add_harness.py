# -*- coding: utf-8 -*-
"""补丁：main.c 真模式加 WIFI_TEST_SSID/WIFI_TEST_PWD 自动测试钩子
（密码仅经环境变量传入内存，不写文件、不打印）"""
import io

f = "design/sim_cmake/main.c"
s = io.open(f, encoding="utf-8").read()

old = '''        if (getenv("WIFI_AUTOEXIT") && demo_scan_fired &&
                get_var_scan_state() == 2) {'''
new = '''        /* ★ 自动联网测试钩子（env 注入，密码不落盘不打印）：
         * WIFI_TEST_SSID → 扫完自动选中该网络；WIFI_TEST_PWD → 填入密码框；
         * 然后自动点"连 接"。 */
        {
            const char *tssid = getenv("WIFI_TEST_SSID");
            if (tssid && demo_scan_fired && get_var_scan_state() == 2 &&
                    !demo_pick_fired) {
                int idx = 0;
                for (const wifi_ap_t *p = wifi_ap_first(); p; p = p->next, idx++) {
                    if (strcmp(p->ssid, tssid) == 0) {
                        printf("[TEST] tap row %d for '%s'\\n", idx, tssid);
                        demo_tap(240, 40 + 2 + idx * 34 + 15);
                        demo_pick_fired = true;
                        break;
                    }
                }
                if (!demo_pick_fired)
                    printf("[TEST] SSID '%s' not in scan list\\n", tssid);
            }
            if (tssid && demo_pick_fired && !demo_connect_fired &&
                    strcmp(get_var_pick_ssid(), tssid) == 0) {
                static int w3 = 0;
                if (++w3 == 2) {
                    const char *pw = getenv("WIFI_TEST_PWD");
                    lv_textarea_set_text(objects.pwd_ta, pw ? pw : "");
                    printf("[TEST] password injected (len=%d), tap connect\\n",
                           (int)strlen(pw ? pw : ""));
                }
                if (w3 >= 4) {
                    demo_tap(40 + 30 + 85, 20 + 252 + 12);   /* 连接按钮 */
                    demo_connect_fired = true;
                }
            }
        }
        if (getenv("WIFI_AUTOEXIT") && demo_scan_fired &&
                get_var_scan_state() == 2) {'''
assert old in s, "anchor not found"
s = s.replace(old, new, 1)
io.open(f, "w", encoding="utf-8").write(s)
print("test harness added")
