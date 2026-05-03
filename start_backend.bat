@echo off
setlocal
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set HTTP_PROXY=
set HTTPS_PROXY=
set ALL_PROXY=
set http_proxy=
set https_proxy=
set all_proxy=

if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" "scripts\start_backend.py" %*
) else (
  python "scripts\start_backend.py" %*
)
