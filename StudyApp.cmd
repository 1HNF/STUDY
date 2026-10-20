@echo off
rem Double-click to open the Study app (no console window).
if not exist "%~dp0.venv\Scripts\pythonw.exe" (
  echo The app is not set up yet. Double-click setup.cmd first.
  pause & exit /b 1
)
start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0app.py"
