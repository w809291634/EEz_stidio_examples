@echo off
REM ============================================================================
REM  EEZ example -> PC simulator one-click build / run
REM ----------------------------------------------------------------------------
REM  Usage:
REM    run_sim.bat          build Release only  (output: PC_SIM\bin\main_rel.exe)
REM    run_sim.bat run      build AND run (GUI; swipe to verify gestures)
REM
REM  How it works:
REM    Inject this example's absolute path into SIM_TARGET_PROJ_DIR, then call
REM    PC_SIM\build.bat. PC_SIM\CMakeLists.txt reads that env var to locate the
REM    target project, so switching project = run the matching run_sim.bat.
REM    No need to touch PC_SIM / apl_lvgl_v9_4 source.
REM ============================================================================

REM %~dp0 is this script's dir = <project>\design\sim_cmake\ . PC_SIM's CMakeLists
REM appends /design/sim_cmake/<lv_conf.h|main.c> to SIM_TARGET_PROJ_DIR, so the
REM env var must be the PROJECT ROOT. This script sits two levels under the
REM project root (<project>\design\sim_cmake\), so go up two levels.
set "PROJ_DIR=%~dp0"
if "%PROJ_DIR:~-1%"=="\" set "PROJ_DIR=%PROJ_DIR:~0,-1%"
for %%I in ("%PROJ_DIR%") do set "PROJ_DIR=%%~dpI"
if "%PROJ_DIR:~-1%"=="\" set "PROJ_DIR=%PROJ_DIR:~0,-1%"
for %%I in ("%PROJ_DIR%") do set "SIM_TARGET_PROJ_DIR=%%~dpI"
if "%SIM_TARGET_PROJ_DIR:~-1%"=="\" set "SIM_TARGET_PROJ_DIR=%SIM_TARGET_PROJ_DIR:~0,-1%"

set "PC_SIM_DIR=C:\Users\yjt54\Desktop\EEz_stidio_examples\PC_SIM\lv_port_pc_vscode_v9.5"

REM ---------------------------------------------------------------------------
REM  Force reconfigure. PC_SIM's CMakeLists only reconfigures when its content
REM  changes; switching examples does NOT change it. Without deleting, the stale
REM  build_rel cache makes cmake skip reconfigure and keeps building the old
REM  project. We delete PC_SIM's GENERATED dirs (not source); ccache still
REM  reuses unchanged LVGL objects, so rebuild is fast.
REM ---------------------------------------------------------------------------
if exist "%PC_SIM_DIR%\build_rel" rmdir /s /q "%PC_SIM_DIR%\build_rel"
if exist "%PC_SIM_DIR%\build_dbg" rmdir /s /q "%PC_SIM_DIR%\build_dbg"

if /i "%~1"=="run" (
    call "%PC_SIM_DIR%\build.bat" run_rel
) else (
    call "%PC_SIM_DIR%\build.bat" build_rel
)
