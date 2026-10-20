@echo off
rem One-time setup: Python environment, the app's packages, and your .env with the model key.
setlocal
cd /d "%~dp0"

where py >nul 2>nul && (set "PY=py -3") || (set "PY=python")
%PY% -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>nul
if errorlevel 1 (
  echo Python 3.10 or newer is needed. Install it from https://www.python.org/downloads/ ^(tick "Add python.exe to PATH"^), then run setup.cmd again.
  pause & exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating the Python environment in .venv ...
  %PY% -m venv .venv || (echo Could not create .venv & pause & exit /b 1)
)

echo Installing the app's packages ^(a minute or two^) ...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
".venv\Scripts\python.exe" -m pip install -e ".[pdf,web]" || (echo Package install failed. & pause & exit /b 1)

if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo.
  echo Created .env. Notepad will open it now: paste your free Groq key after SKILL_ANYTHING_API_KEY=, save and close.
  echo Get a key at https://console.groq.com/keys
  notepad ".env"
) else (
  echo .env already exists, left as it is.
)

echo.
echo Setup complete. Double-click StudyApp.cmd to open the app.
pause
