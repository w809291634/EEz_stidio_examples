# -*- coding: utf-8 -*-
"""按需精确复核：把 UI 换进 P4 模板做 IDF 工程最终链接，写入 design/esp32_size.json。

默认资源账不跑本脚本（用 design/esp32_estimate.py 只编译估算）；
只有用户点名“用 IDF 工程编译”时才跑，得到与 idf.py size 一致的精确值。

用法：python design/esp32_size.py [--template DIR] [--no-restore-build]
"""
import argparse
import glob
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
UI = os.path.join(ROOT, "src", "ui")

sys.path.insert(0, HERE)
import esp32_estimate as est      # noqa: E402  native UI 文件清单的唯一实现

DEFAULT_TEMPLATE = (r"D:\esp32_8266_files\esp-idf-v5.5.5_ol\examples"
                    r"\idf_v555_my_exps\p4_touch_lcd4_3_exp\lvgl_demo_template_no_flow")
DEFAULT_IDF = r"D:\esp32_8266_files\esp-idf-v5.5.5_ol"
DEFAULT_TOOLS = r"D:\esp32_8266_files\esp-idf-tools_for_idf_v5_5_5"
IDF_PY_ENV = "idf5.5_py3.11_env"
RISCV_DIR = r"tools\riscv32-esp-elf\esp-14.2.0_20260121\riscv32-esp-elf\bin"
NINJA_DIR = r"tools\ninja\1.12.1"
CMAKE_DIR = r"tools\cmake\3.30.2\bin"

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass


def ui_hash():
    files = (sorted(glob.glob(os.path.join(UI, "**", "*.c"), recursive=True)) +
             sorted(glob.glob(os.path.join(UI, "**", "*.h"), recursive=True)) +
             est.native_sources() +
             sorted(glob.glob(os.path.join(ROOT, "src", "native", "**", "*.h"),
                              recursive=True)))
    h = hashlib.sha256()
    for f in files:
        h.update(os.path.relpath(f, ROOT).replace(os.sep, "/").encode())
        h.update(open(f, "rb").read())
    return h.hexdigest()


def run(cmd, cwd, log):
    with io.open(log, "a", encoding="utf-8", errors="replace") as f:
        f.write("\n$ %s\n" % " ".join(cmd))
        r = subprocess.run(cmd, cwd=cwd, stdout=f, stderr=subprocess.STDOUT)
    return r.returncode


def write_bat(path, template, idf, tools, action):
    lines = [
        "@echo off",
        "set MSYSTEM=",
        "set IDF_PATH=%s" % idf,
        "set IDF_TOOLS_PATH=%s" % tools,
        "set IDF_PYTHON_ENV_PATH=%s\\python_env\\%s" % (tools, IDF_PY_ENV),
        ("set PATH=%s\\%s;%s\\%s;%s\\%s;%s\\python_env\\%s\\Scripts;%%PATH%%"
         % (tools, RISCV_DIR, tools, NINJA_DIR, tools, CMAKE_DIR, tools, IDF_PY_ENV)),
        "cd /d %s" % template,
        ('"%s\\python_env\\%s\\Scripts\\python.exe" "%s\\tools\\idf.py" --no-hints %s'
         % (tools, IDF_PY_ENV, idf, action)),
        "exit /b %errorlevel%",
    ]
    io.open(path, "w", encoding="ascii", newline="\r\n").write("\r\n".join(lines) + "\r\n")


def parse_size_json(py, template, build, project):
    mp = os.path.join(build, project + ".map")
    r = subprocess.run([py, "-m", "esp_idf_size", "--files", "--format", "json", mp],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError("esp_idf_size 失败：%s" % r.stderr[-400:])
    return json.loads(r.stdout)


def app_partition_size(template):
    csv = os.path.join(template, "partitions.csv")

    def num(s):
        s = s.strip()
        if s[-1:].lower() == "m":
            return int(s[:-1], 0) * 1024 * 1024
        if s[-1:].lower() == "k":
            return int(s[:-1], 0) * 1024
        return int(s, 0)

    if os.path.isfile(csv):
        for line in io.open(csv, encoding="utf-8", errors="replace"):
            p = [x.strip() for x in line.split(",")]
            if len(p) >= 5 and p[1] == "app":
                try:
                    return num(p[4])
                except ValueError:
                    pass
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", default=os.environ.get("W78_ESP32_TEMPLATE", DEFAULT_TEMPLATE))
    ap.add_argument("--idf", default=os.environ.get("W78_IDF_PATH", DEFAULT_IDF))
    ap.add_argument("--tools", default=os.environ.get("W78_IDF_TOOLS", DEFAULT_TOOLS))
    ap.add_argument("--no-restore-build", action="store_true")
    a = ap.parse_args()

    template = os.path.abspath(a.template)
    idf, tools = os.path.abspath(a.idf), os.path.abspath(a.tools)
    py = os.path.join(tools, "python_env", IDF_PY_ENV, "Scripts", "python.exe")
    eez = os.path.join(template, "eez-test", "src")
    ui_dst, native_dst = os.path.join(eez, "ui"), os.path.join(eez, "native")
    bak_root = os.path.join(template, "eez-test", "__w78_measure_backup__")
    ui_bak, native_bak = os.path.join(bak_root, "ui"), os.path.join(bak_root, "native")
    build = os.path.join(template, "build")
    name = json.load(io.open(os.path.join(build, "project_description.json"), encoding="utf-8"))["project_name"]

    for p, what in ((template, "模板目录"), (py, "IDF python"), (ui_dst, "模板 ui"), (native_dst, "模板 native")):
        if not os.path.exists(p):
            print("[esp32] 缺少%s：%s" % (what, p))
            return 2
    for p in (ui_bak, native_bak):
        if os.path.exists(p):
            print("[esp32] 备份槽已占用（上次未还原？）：%s" % p)
            return 2

    tmp = os.path.join(ROOT, "tmp", "esp32_measure")
    os.makedirs(tmp, exist_ok=True)
    log = os.path.join(tmp, "build.log")
    bat = os.path.join(tmp, "build.bat")
    h = ui_hash()
    print("[esp32] 模板：%s" % template)
    print("[esp32] UI 哈希：%s" % h[:16])

    ok = False
    try:
        os.makedirs(bak_root, exist_ok=True)
        shutil.copytree(ui_dst, ui_bak)
        shutil.copytree(native_dst, native_bak)
        shutil.rmtree(ui_dst)
        shutil.copytree(UI, ui_dst)
        shutil.copy2(os.path.join(ui_bak, "CMakeLists.txt"), os.path.join(ui_dst, "CMakeLists.txt"))
        # 拷贝保留原 mtime，可能比模板上次构建产物旧 -> ninja 不重编，必须 touch
        for p in glob.glob(os.path.join(ui_dst, "**", "*.*"), recursive=True):
            if p.endswith((".c", ".h", ".cpp")):
                os.utime(p, None)
        shutil.rmtree(native_dst)
        os.makedirs(native_dst)
        io.open(os.path.join(native_dst, "CMakeLists.txt"), "w", encoding="ascii", newline="\n").write(
            'idf_component_register(SRCS "stub.c"\n'
            '    INCLUDE_DIRS "." "${CMAKE_CURRENT_LIST_DIR}/../ui"\n'
            '    REQUIRES lvgl)\n')
        io.open(os.path.join(native_dst, "stub.c"), "w", encoding="ascii", newline="\n").write(
            "void watch_anim_init(void) {}\n")

        write_bat(bat, template, idf, tools, "reconfigure build")
        if run(["cmd", "/c", bat], template, log) != 0:
            raise RuntimeError("模板构建失败，日志：%s" % log)

        data = parse_size_json(py, template, build, name)
        files = []
        for k, v in data.items():
            if k.startswith("libui.a:"):
                obj = k.split(":", 1)[1][:-4]
                files.append({"name": obj, "flash": v.get("flash_total", 0), "ram": v.get("ram_st_total", 0)})
        srcs = sorted(os.path.basename(p) for p in glob.glob(os.path.join(UI, "**", "*.c"), recursive=True))
        seen = {f["name"] for f in files}
        for s in srcs:
            if s not in seen:
                files.append({"name": s, "flash": 0, "ram": 0, "note": "未被引用，链接期丢弃"})
        files.sort(key=lambda x: -x["flash"])

        ui_flash = sum(f["flash"] for f in files)
        ui_ram = sum(f["ram"] for f in files)
        fonts_flash = sum(f["flash"] for f in files if f["name"].startswith("ui_font_"))
        binp = os.path.join(build, name + ".bin")
        out = {
            "measured_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "target": "esp32p4",
            "idf_version": "5.5.5",
            "board_template": os.path.basename(template),
            "ui_hash": h,
            "ui_flash": ui_flash,
            "ui_ram": ui_ram,
            "fonts_flash": fonts_flash,
            "files": files,
            "app_bin": os.path.getsize(binp) if os.path.isfile(binp) else 0,
            "app_partition": app_partition_size(template),
            "internal_ram": sum(v.get("ram_st_total", 0) for v in data.values()),
        }
        json.dump(out, io.open(os.path.join(HERE, "esp32_size.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print("[esp32] EEZ UI  Flash %.1fKB（字体 %.1fKB） / RAM %.1fKB；app.bin %.2fMB"
              % (ui_flash / 1024.0, fonts_flash / 1024.0, ui_ram / 1024.0, out["app_bin"] / 1048576.0))
        print("[esp32] 已写入 design/esp32_size.json（含逐文件字节数）")
        ok = True
    finally:
        if os.path.isdir(ui_bak):
            shutil.rmtree(ui_dst, ignore_errors=True)
            shutil.move(ui_bak, ui_dst)
        if os.path.isdir(native_bak):
            shutil.rmtree(native_dst, ignore_errors=True)
            shutil.move(native_bak, native_dst)
        shutil.rmtree(bak_root, ignore_errors=True)
        # 还原的源文件 mtime 可能比上次构建产物旧，touch 后再 configure
        for p in glob.glob(os.path.join(eez, "**", "*.c"), recursive=True) + \
                glob.glob(os.path.join(eez, "**", "*.h"), recursive=True):
            os.utime(p, None)
        if not a.no_restore_build:
            write_bat(bat, template, idf, tools, "reconfigure build")
            rc = run(["cmd", "/c", bat], template, log)
            print("[esp32] 模板已还原%s" % ("并重建成功" if rc == 0 else "（重建失败，见 %s）" % log))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
