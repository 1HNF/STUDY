@echo off
rem Opens the Study app so a phone on the same Wi-Fi can use it too. Keep this window open while you study.
if not exist "%~dp0.venv\Scripts\python.exe" (
  echo The app is not set up yet. Double-click setup.cmd first.
  pause & exit /b 1
)
"%~dp0.venv\Scripts\python.exe" "%~dp0app.py" --lan
pause
