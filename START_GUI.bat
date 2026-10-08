@echo off
REM YouTube Automation Suite - GUI Launcher

echo ================================================================================
echo      YouTube Automation Suite - GUI Version
echo ================================================================================
echo.
echo Starting the GUI application...
echo.

REM Locate Python interpreter (prefer virtual environment if present)
set "PYTHON_EXE=python"
if exist "venv\Scripts\python.exe" (
    set "PYTHON_EXE=venv\Scripts\python.exe"
) else if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
)

REM Verify Python interpreter
%PYTHON_EXE% --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org
    echo.
    pause
    exit /b 1
)

REM Check if src directory exists
if not exist "src\youtube_automation_gui.py" (
    echo ERROR: Cannot find src\youtube_automation_gui.py
    echo Please make sure you are running this from the project root directory.
    echo.
    pause
    exit /b 1
)

REM Run the GUI application
%PYTHON_EXE% src\youtube_automation_gui.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Application exited with error code %errorlevel%.
    pause
)
