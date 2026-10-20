@echo off
rem Usage: study.cmd "C:\path\to\notes.pdf"  -> output\<name>\ with .md, .yaml and a clickable .html, then opens the .html
if "%~1"=="" (echo Usage: study.cmd "C:\path\to\file.pdf" & exit /b 1)
set "ROOT=%~dp0"
set "OUT=%ROOT%output\%~n1"
"%ROOT%.venv\Scripts\sa.exe" pdf "%~1" -o "%OUT%" -f study || exit /b 1
for %%Y in ("%OUT%\*.yaml") do (
  "%ROOT%.venv\Scripts\python.exe" "%ROOT%make_html.py" "%%Y" || exit /b 1
  start "" "%%~dpnY.html"
)
