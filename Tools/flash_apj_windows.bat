@echo off
REM Force flash .apj via Mission Planner uploader tool or bootloader
REM Usage: flash_apj_windows.bat COM11 path\to\ardurover.apj

set PORT=%1
set APJ=%2

if "%PORT%"=="" (
    echo Usage: flash_apj_windows.bat COMx path\to\ardurover.apj
    exit /b 1
)

if "%APJ%"=="" (
    set APJ=build\HDZERO_HALO\bin\ardurover.apj
)

if not exist "%APJ%" (
    echo Error: %APJ% not found
    exit /b 1
)

echo Flashing %APJ% to %PORT%...
echo.
echo Python uploader method (requires pyserial):
python -m pip install pyserial >nul 2>&1
python Tools\scripts\uploader.py --port %PORT% %APJ%

if errorlevel 1 (
    echo.
    echo Upload failed. Try DFU mode instead.
    exit /b 1
)

echo.
echo Flash complete! Reconnect Mission Planner.
