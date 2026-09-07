@echo off
cd /d "%~dp0"
python --version
if errorlevel 1 goto fail
if not exist .venv\Scripts\python.exe python -m venv .venv
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m unittest discover -s tests -v
if errorlevel 1 goto fail
echo Setup complete. Double-click Run_Windows.bat to open the app.
pause
exit /b 0
:fail
echo Setup failed. Read the error above. Python 3.11 or 3.12 is recommended.
pause
exit /b 1
