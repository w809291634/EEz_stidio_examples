/*
 * wifi_text.h — 界面状态文案的唯一真值
 *
 * 平台层（假世界/真接口/真机）与 logic 都引用这里：换文案只改这一处，
 * 不会出现"假后端说正在扫描、真后端说扫描中"这种漂移。
 * 注意：这些中文会进字库子集审计（design/audit_chars.py），新增生僻字要先确认 cn14 有字形。
 */
#pragma once

#define WIFI_TXT_SCAN_HINT      "点击刷新开始扫描"
#define WIFI_TXT_SCANNING       "正在扫描…"
#define WIFI_TXT_FOUND          "已发现 %d 个网络"
#define WIFI_TXT_EMPTY          "未发现网络，请重新扫描"

#define WIFI_TXT_REFRESH        "刷 新"
#define WIFI_TXT_REFRESHING     "扫描中"

#define WIFI_TXT_CONNECTING     "正在连接 %s…"
#define WIFI_TXT_CONNECTED      "已连接 %s"
#define WIFI_TXT_CONNECT_FAIL   "连接失败 %s"

#define WIFI_TXT_DISCONNECTED   "已断开 %s"
#define WIFI_TXT_DROP_FAIL      "断开失败 %s"
#define WIFI_TXT_NOT_CONNECTED  "未连接 %s"

#define WIFI_TXT_NEED_PWD       "请输入密码"
#define WIFI_TXT_PWD_LEN        "密码需 8-64 位"
