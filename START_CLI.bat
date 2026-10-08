@echo off
REM YouTube Automation Suite - CLI Launcher

echo ================================================================================
echo      YouTube Automation Suite - CLI Version
echo ================================================================================
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
if not exist "src\youtube_automation_cli.py" (
    echo ERROR: Cannot find src\youtube_automation_cli.py
    echo Please make sure you are running this from the project root directory.
    echo.
    pause
    exit /b 1
)

REM Forward arguments or start interactive mode
if "%~1"=="" (
    %PYTHON_EXE% src\youtube_automation_cli.py
) else (
    %PYTHON_EXE% src\youtube_automation_cli.py %*
)

if %errorlevel% neq 0 (
    echo.
    echo Command exited with error code %errorlevel%.
    pause
)
