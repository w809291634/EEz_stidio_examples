@echo off
REM ============================================================================
REM  EEZ example -> PC simulator one-click build / run
REM ----------------------------------------------------------------------------
REM  Usage:
REM    run_sim.bat          build AND launch simulator (default on double-click)
REM    run_sim.bat build    build only
REM
REM  How it works:
REM    1) Inject this example's absolute path into SIM_TARGET_PROJ_DIR.
REM       PC_SIM\CMakeLists.txt reads that env var to locate the target project,
REM       so switching project = run the matching run_sim.bat. PC_SIM and
REM       apl_lvgl_v9_4 source stay untouched.
REM    2) Build dir is <project>\tmp\sim_build_<project name> - one private
REM       build dir per example, named by project. Caches are never deleted
REM       and never clash between examples; the first build of each example
REM       compiles LVGL once (ccache speeds it up), later builds incremental.
REM ============================================================================
set "SIM_DIR=%~dp0"
if "%SIM_DIR:~-1%"=="\" set "SIM_DIR=%SIM_DIR:~0,-1%"

REM %~dp0 is <project>\design\sim_cmake\ . PC_SIM's CMakeLists appends
REM /design/sim_cmake/<lv_conf.h|main.c> to SIM_TARGET_PROJ_DIR, so the env var
REM must be the PROJECT ROOT - go up two levels from this script's dir.
set "PROJ_DIR=%SIM_DIR%"
for %%I in ("%PROJ_DIR%") do set "PROJ_DIR=%%~dpI"
if "%PROJ_DIR:~-1%"=="\" set "PROJ_DIR=%PROJ_DIR:~0,-1%"
for %%I in ("%PROJ_DIR%") do set "SIM_TARGET_PROJ_DIR=%%~dpI"
if "%SIM_TARGET_PROJ_DIR:~-1%"=="\" set "SIM_TARGET_PROJ_DIR=%SIM_TARGET_PROJ_DIR:~0,-1%"

set "PC_SIM_DIR=C:\Users\yjt54\Desktop\EEz_stidio_examples\PC_SIM\lv_port_pc_vscode_v9.5"
REM Per-project build dir: projects sharing this PC_SIM must never share tmp\build.
for %%I in ("%SIM_TARGET_PROJ_DIR%") do set "PROJ_NAME=%%~nxI"
set "BUILD_DIR=%SIM_TARGET_PROJ_DIR%\tmp\sim_build_%PROJ_NAME%"
REM Build dir and tmp\compile_cache are intentionally kept (user 2026-11-05):
REM deleting them forces a full LVGL/UI rebuild next time. Do not clean them in scripts.
REM Keep the exe PRIVATE to this project. PC_SIM\bin is shared by every
REM example: another project building later overwrites main.exe, and this
REM bat would then launch the wrong program. PC_SIM CMakeLists reads SIM_BIN_DIR.
set "SIM_BIN_DIR=%BUILD_DIR%\bin"

REM Toolchain PATH: mingw / cmake / sdl2. setup_env.bat deliberately has no
REM setlocal, so the PATH change propagates here.
call "%PC_SIM_DIR%\setup_env.bat" >nul
cd /d "%PC_SIM_DIR%"

set "GENERATOR=Ninja"
where ninja >nul 2>&1
if errorlevel 1 set "GENERATOR=MinGW Makefiles"

echo [run_sim] target    = %SIM_TARGET_PROJ_DIR%
echo [run_sim] build dir = %BUILD_DIR%
echo [run_sim] configuring...
cmake -S "%PC_SIM_DIR%" -B "%BUILD_DIR%" -G "%GENERATOR%" -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_STANDARD_LIBRARIES=-lwlanapi
if errorlevel 1 (
    echo [run_sim] configure FAILED.
    exit /b 1
)
echo [run_sim] building...
cmake --build "%BUILD_DIR%"
if errorlevel 1 (
    echo [run_sim] build FAILED.
    exit /b 1
)
echo [run_sim] build succeeded.
set "PYTHONIOENCODING=utf-8"
python "%SIM_TARGET_PROJ_DIR%\design\mem_report.py"
set "LOCAL_EXE=%SIM_BIN_DIR%\main.exe"
if not exist "%LOCAL_EXE%" (
    echo [run_sim] local exe not found: %LOCAL_EXE%
    echo            PC_SIM still writes to the shared bin dir; see SIM_BIN_DIR
    echo            branch in PC_SIM\CMakeLists.txt
    pause
    exit /b 1
)
echo [run_sim] exe = %LOCAL_EXE%
if /i "%~1"=="build" exit /b 0
if /i "%~1"=="test" (
    set "W78_AUTOTEST=1"
    set "SDL_VIDEODRIVER=dummy"
    echo [run_sim] headless nav autotest...
    start /b /wait "" "%LOCAL_EXE%"
    if errorlevel 1 (
        echo [run_sim] AUTOTEST FAILED
        pause
        exit /b 1
    )
    echo [run_sim] AUTOTEST PASS
    python "%SIM_TARGET_PROJ_DIR%\design\mem_report.py" --brief
    exit /b 0
)
if /i "%~1"=="wifitest" (
    set "W78_WIFI_TEST=1"
    set "SDL_VIDEODRIVER=dummy"
    cd /d "%SIM_TARGET_PROJ_DIR%"
    echo [run_sim] headless wifi scan test...
    start /b /wait "" "%LOCAL_EXE%"
    if errorlevel 1 (
        echo [run_sim] WIFITEST FAILED
        pause
        exit /b 1
    )
    exit /b 0
)
if /i "%~1"=="flowtest" (
    set "W78_WIFI_FLOW_TEST=1"
    set "WIFI_PC_FAKE=1"
    set "SDL_VIDEODRIVER=dummy"
    cd /d "%SIM_TARGET_PROJ_DIR%"
    echo [run_sim] headless wifi flow test - fake backend...
    start /b /wait "" "%LOCAL_EXE%"
    if errorlevel 1 (
        echo [run_sim] FLOWTEST FAILED
        pause
        exit /b 1
    )
    exit /b 0
)
if /i "%~1"=="shots" (
    set "W78_SHOT_ALL=1"
    set "WIFI_PC_FAKE=1"
    set "SDL_VIDEODRIVER=dummy"
    cd /d "%SIM_TARGET_PROJ_DIR%"
    echo [run_sim] per-screen shots...
    "%LOCAL_EXE%"
    exit /b 0
)
if /i "%~1"=="behaviortest" (
    set "W78_UI_BEHAVIOR_TEST=1"
    set "SDL_VIDEODRIVER=dummy"
    echo [run_sim] headless UI behavior test...
    start /b /wait "" "%LOCAL_EXE%"
    if errorlevel 1 (
        echo [run_sim] UI BEHAVIOR FAILED
        pause
        exit /b 1
    )
    echo [run_sim] UI BEHAVIOR PASS
    exit /b 0
)
if /i "%~1"=="uitest" (
    set "W78_WIFI_UI_TEST=1"
    set "WIFI_PC_FAKE=1"
    set "SDL_VIDEODRIVER=dummy"
    cd /d "%SIM_TARGET_PROJ_DIR%"
    echo [run_sim] headless wifi ui test...
    start /b /wait "" "%LOCAL_EXE%"
    if errorlevel 1 (
        echo [run_sim] UITEST FAILED
        pause
        exit /b 1
    )
    exit /b 0
)
if /i "%~1"=="quittest" (
    set "W78_QUIT_TEST=1"
    set "SDL_VIDEODRIVER=dummy"
    echo [run_sim] headless close-window test...
    start /b /wait "" "%LOCAL_EXE%"
    if errorlevel 1 (
        echo [run_sim] QUITTEST FAILED
        pause
        exit /b 1
    )
    echo [run_sim] QUITTEST PASS
    exit /b 0
)
echo [run_sim] launching simulator window...
"%LOCAL_EXE%"
exit /b 0
