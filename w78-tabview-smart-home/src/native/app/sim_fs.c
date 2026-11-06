/* sim_fs.c — PC 仿真文件系统（A: → 工程根）
 *
 * 目的：仿真里也能按 `A:/assets/xxx.png` 这类路径读写宿主文件，
 * 与真机的 SD/Flash 文件系统用法一致；路径里的前导 '/' 会被剥掉再拼工程根。
 * 工程根来自 run_sim.bat 注入的 SIM_TARGET_PROJ_DIR。
 * ESP32 目标上编译为空实现（真机由 FATFS/LittleFS 提供）。
 */
#include "sim_fs.h"

#ifdef ESP_PLATFORM

void sim_fs_init(void) {}

#else

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "lvgl.h"

static char g_base[512];

static void build_path(char *out, size_t n, const char *path)
{
    while (*path == '/' || *path == '\\') path++;
    snprintf(out, n, "%s/%s", g_base, path);
}

static bool fs_ready(lv_fs_drv_t *drv)
{
    LV_UNUSED(drv);
    return g_base[0] != '\0';
}

static void *fs_open(lv_fs_drv_t *drv, const char *path, lv_fs_mode_t mode)
{
    const char *flags = "";
    char buf[600];
    LV_UNUSED(drv);
    if (mode == LV_FS_MODE_WR) flags = "wb";
    else if (mode == LV_FS_MODE_RD) flags = "rb";
    else if (mode == (LV_FS_MODE_WR | LV_FS_MODE_RD)) flags = "rb+";
    build_path(buf, sizeof(buf), path);
    return fopen(buf, flags);
}

static lv_fs_res_t fs_close(lv_fs_drv_t *drv, void *file_p)
{
    LV_UNUSED(drv);
    return fclose((FILE *)file_p) == 0 ? LV_FS_RES_OK : LV_FS_RES_UNKNOWN;
}

static lv_fs_res_t fs_read(lv_fs_drv_t *drv, void *file_p, void *buf,
                           uint32_t btr, uint32_t *br)
{
    LV_UNUSED(drv);
    *br = (uint32_t)fread(buf, 1, btr, (FILE *)file_p);
    return LV_FS_RES_OK;
}

static lv_fs_res_t fs_write(lv_fs_drv_t *drv, void *file_p, const void *buf,
                            uint32_t btw, uint32_t *bw)
{
    LV_UNUSED(drv);
    *bw = (uint32_t)fwrite(buf, 1, btw, (FILE *)file_p);
    return (*bw == btw) ? LV_FS_RES_OK : LV_FS_RES_UNKNOWN;
}

static lv_fs_res_t fs_seek(lv_fs_drv_t *drv, void *file_p, uint32_t pos,
                           lv_fs_whence_t whence)
{
    int w = SEEK_SET;
    LV_UNUSED(drv);
    if (whence == LV_FS_SEEK_CUR) w = SEEK_CUR;
    else if (whence == LV_FS_SEEK_END) w = SEEK_END;
    return fseek((FILE *)file_p, (long)pos, w) == 0 ? LV_FS_RES_OK : LV_FS_RES_UNKNOWN;
}

static lv_fs_res_t fs_tell(lv_fs_drv_t *drv, void *file_p, uint32_t *pos_p)
{
    LV_UNUSED(drv);
    *pos_p = (uint32_t)ftell((FILE *)file_p);
    return LV_FS_RES_OK;
}

void sim_fs_init(void)
{
    const char *root = getenv("SIM_TARGET_PROJ_DIR");
    static lv_fs_drv_t drv;
    snprintf(g_base, sizeof(g_base), "%s", (root && *root) ? root : ".");
    lv_fs_drv_init(&drv);
    drv.letter = 'A';
    drv.cache_size = 0;
    drv.ready_cb = fs_ready;
    drv.open_cb = fs_open;
    drv.close_cb = fs_close;
    drv.read_cb = fs_read;
    drv.write_cb = fs_write;
    drv.seek_cb = fs_seek;
    drv.tell_cb = fs_tell;
    lv_fs_drv_register(&drv);
}

#endif /* !ESP_PLATFORM */
