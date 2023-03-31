@echo off
setlocal enabledelayedexpansion

rem Get the absolute path of the tool directory
for %%F in ("%~dp0.") do set "TOOL_DIR=%%~fF"

rem Change the current directory to the tool directory
cd /d "%TOOL_DIR%"

rem Create virtual environment if needed
if not exist "env" (
    python3 -m venv env
)

rem Activate virtual environment
call env\Scripts\activate.bat

rem Upgrade pip
if not exist env\Scripts\pip.exe (
    python3 -m ensurepip --upgrade
)

rem Install dependencies
pip install -r requirements.txt

rem Run the script
python3 start.py

rem Deactivate virtual environment
deactivate
