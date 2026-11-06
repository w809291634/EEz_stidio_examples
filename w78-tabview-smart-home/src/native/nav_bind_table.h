/* 由 design/nav_bind_gen.py 生成，勿手改。 */
#ifndef NAV_BIND_TABLE_H
#define NAV_BIND_TABLE_H

#include "screens.h"

#define NAV_PAGE_LIST(X) \
    X(SCREEN_ID_MAIN, main) \
    X(SCREEN_ID_LIVING, living) \
    X(SCREEN_ID_MASTER, master) \
    X(SCREEN_ID_KITCHEN, kitchen) \
    X(SCREEN_ID_BATH, bath) \
    X(SCREEN_ID_DETAIL_LIGHT, detail_light) \
    X(SCREEN_ID_DETAIL_AC, detail_ac) \
    X(SCREEN_ID_DETAIL_CURTAIN, detail_curtain) \
    X(SCREEN_ID_DETAIL_SENSOR, detail_sensor) \
    X(SCREEN_ID_DETAIL_CAMERA, detail_camera) \
    X(SCREEN_ID_DETAIL_PLUG, detail_plug) \
    X(SCREEN_ID_NOTIFY, notify) \
    X(SCREEN_ID_ENERGY, energy) \
    X(SCREEN_ID_SETTINGS, settings) \
    X(SCREEN_ID_WIFI, wifi) \
    X(SCREEN_ID_DEVICES, devices) \
    X(SCREEN_ID_SECURITY, security) \
    X(SCREEN_ID_SCENE_DETAIL, scene_detail) \
    X(SCREEN_ID_ADD_TYPE, add_type) \
    X(SCREEN_ID_ADD_PAIRING, add_pairing) \
    X(SCREEN_ID_ADD_DONE, add_done) \
    X(SCREEN_ID_ABOUT, about) \
    X(SCREEN_ID_OFFLINE, offline) \
    X(SCREEN_ID_EMPTY_ROOM, empty_room)

typedef struct {
    lv_obj_t **obj;
    int src;
    int dst;
    int back;   /* 1 = 返回来路 */
} nav_bind_entry_t;

static const nav_bind_entry_t NAV_BIND[] = {
    { &objects.main_go01, SCREEN_ID_MAIN, SCREEN_ID_LIVING, 0 },
    { &objects.main_go02, SCREEN_ID_MAIN, SCREEN_ID_MASTER, 0 },
    { &objects.main_go03, SCREEN_ID_MAIN, SCREEN_ID_KITCHEN, 0 },
    { &objects.main_go04, SCREEN_ID_MAIN, SCREEN_ID_BATH, 0 },
    { &objects.main_go05, SCREEN_ID_MAIN, SCREEN_ID_DEVICES, 0 },
    { &objects.main_go06, SCREEN_ID_MAIN, SCREEN_ID_ENERGY, 0 },
    { &objects.main_go07, SCREEN_ID_MAIN, SCREEN_ID_NOTIFY, 0 },
    { &objects.main_go08, SCREEN_ID_MAIN, SCREEN_ID_SETTINGS, 0 },
    { &objects.main_go09, SCREEN_ID_MAIN, SCREEN_ID_SECURITY, 0 },
    { &objects.living_go01, SCREEN_ID_LIVING, SCREEN_ID_MAIN, 0 },
    { &objects.living_go02, SCREEN_ID_LIVING, SCREEN_ID_DETAIL_LIGHT, 0 },
    { &objects.living_go03, SCREEN_ID_LIVING, SCREEN_ID_DETAIL_LIGHT, 0 },
    { &objects.living_go04, SCREEN_ID_LIVING, SCREEN_ID_DETAIL_CURTAIN, 0 },
    { &objects.living_go05, SCREEN_ID_LIVING, SCREEN_ID_DETAIL_AC, 0 },
    { &objects.living_go06, SCREEN_ID_LIVING, SCREEN_ID_DETAIL_SENSOR, 0 },
    { &objects.living_go07, SCREEN_ID_LIVING, SCREEN_ID_DETAIL_CAMERA, 0 },
    { &objects.master_go01, SCREEN_ID_MASTER, SCREEN_ID_MAIN, 0 },
    { &objects.master_go02, SCREEN_ID_MASTER, SCREEN_ID_DETAIL_LIGHT, 0 },
    { &objects.master_go03, SCREEN_ID_MASTER, SCREEN_ID_DETAIL_LIGHT, 0 },
    { &objects.master_go04, SCREEN_ID_MASTER, SCREEN_ID_DETAIL_CURTAIN, 0 },
    { &objects.master_go05, SCREEN_ID_MASTER, SCREEN_ID_DETAIL_AC, 0 },
    { &objects.master_go06, SCREEN_ID_MASTER, SCREEN_ID_DETAIL_SENSOR, 0 },
    { &objects.master_go07, SCREEN_ID_MASTER, SCREEN_ID_SCENE_DETAIL, 0 },
    { &objects.kitchen_go01, SCREEN_ID_KITCHEN, SCREEN_ID_MAIN, 0 },
    { &objects.kitchen_go02, SCREEN_ID_KITCHEN, SCREEN_ID_DETAIL_LIGHT, 0 },
    { &objects.kitchen_go03, SCREEN_ID_KITCHEN, SCREEN_ID_DETAIL_PLUG, 0 },
    { &objects.kitchen_go04, SCREEN_ID_KITCHEN, SCREEN_ID_DETAIL_SENSOR, 0 },
    { &objects.bath_go01, SCREEN_ID_BATH, SCREEN_ID_MAIN, 0 },
    { &objects.bath_go02, SCREEN_ID_BATH, SCREEN_ID_DETAIL_LIGHT, 0 },
    { &objects.bath_go03, SCREEN_ID_BATH, SCREEN_ID_DETAIL_LIGHT, 0 },
    { &objects.bath_go04, SCREEN_ID_BATH, SCREEN_ID_DETAIL_SENSOR, 0 },
    { &objects.detail_light_go01, SCREEN_ID_DETAIL_LIGHT, 0, 1 },
    { &objects.detail_ac_go01, SCREEN_ID_DETAIL_AC, 0, 1 },
    { &objects.detail_curtain_go01, SCREEN_ID_DETAIL_CURTAIN, 0, 1 },
    { &objects.detail_sensor_go01, SCREEN_ID_DETAIL_SENSOR, 0, 1 },
    { &objects.detail_camera_go01, SCREEN_ID_DETAIL_CAMERA, 0, 1 },
    { &objects.detail_plug_go01, SCREEN_ID_DETAIL_PLUG, 0, 1 },
    { &objects.notify_go01, SCREEN_ID_NOTIFY, SCREEN_ID_MAIN, 0 },
    { &objects.energy_go01, SCREEN_ID_ENERGY, SCREEN_ID_MAIN, 0 },
    { &objects.settings_go01, SCREEN_ID_SETTINGS, SCREEN_ID_MAIN, 0 },
    { &objects.settings_go02, SCREEN_ID_SETTINGS, SCREEN_ID_WIFI, 0 },
    { &objects.settings_go03, SCREEN_ID_SETTINGS, SCREEN_ID_ABOUT, 0 },
    { &objects.wifi_go01, SCREEN_ID_WIFI, SCREEN_ID_SETTINGS, 0 },
    { &objects.devices_go01, SCREEN_ID_DEVICES, SCREEN_ID_MAIN, 0 },
    { &objects.devices_go02, SCREEN_ID_DEVICES, SCREEN_ID_ADD_TYPE, 0 },
    { &objects.security_go01, SCREEN_ID_SECURITY, SCREEN_ID_MAIN, 0 },
    { &objects.scene_detail_go01, SCREEN_ID_SCENE_DETAIL, SCREEN_ID_MAIN, 0 },
    { &objects.add_type_go01, SCREEN_ID_ADD_TYPE, SCREEN_ID_DEVICES, 0 },
    { &objects.add_type_go02, SCREEN_ID_ADD_TYPE, SCREEN_ID_ADD_PAIRING, 0 },
    { &objects.add_type_go03, SCREEN_ID_ADD_TYPE, SCREEN_ID_ADD_PAIRING, 0 },
    { &objects.add_type_go04, SCREEN_ID_ADD_TYPE, SCREEN_ID_ADD_PAIRING, 0 },
    { &objects.add_type_go05, SCREEN_ID_ADD_TYPE, SCREEN_ID_ADD_PAIRING, 0 },
    { &objects.add_type_go06, SCREEN_ID_ADD_TYPE, SCREEN_ID_ADD_PAIRING, 0 },
    { &objects.add_type_go07, SCREEN_ID_ADD_TYPE, SCREEN_ID_ADD_PAIRING, 0 },
    { &objects.add_pairing_go01, SCREEN_ID_ADD_PAIRING, SCREEN_ID_ADD_TYPE, 0 },
    { &objects.add_pairing_go02, SCREEN_ID_ADD_PAIRING, SCREEN_ID_DEVICES, 0 },
    { &objects.add_pairing_go03, SCREEN_ID_ADD_PAIRING, SCREEN_ID_ADD_DONE, 0 },
    { &objects.add_done_go01, SCREEN_ID_ADD_DONE, SCREEN_ID_DEVICES, 0 },
    { &objects.add_done_go02, SCREEN_ID_ADD_DONE, SCREEN_ID_DEVICES, 0 },
    { &objects.about_go01, SCREEN_ID_ABOUT, SCREEN_ID_SETTINGS, 0 },
    { &objects.offline_go01, SCREEN_ID_OFFLINE, SCREEN_ID_MAIN, 0 },
    { &objects.offline_go02, SCREEN_ID_OFFLINE, SCREEN_ID_WIFI, 0 },
    { &objects.empty_room_go01, SCREEN_ID_EMPTY_ROOM, 0, 1 },
    { &objects.empty_room_go02, SCREEN_ID_EMPTY_ROOM, SCREEN_ID_ADD_TYPE, 0 },
};
#define NAV_BIND_COUNT ((int)(sizeof(NAV_BIND) / sizeof(NAV_BIND[0])))

#endif
