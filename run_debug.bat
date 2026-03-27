@echo off
setlocal ENABLEDELAYEDEXPANSION
set LOG=run_debug.log
>"%LOG%" echo [RUN] %DATE% %TIME%

REM 1) pick a python
set PY=
for %%P in (py.exe python.exe python3.exe) do (
  where %%P >nul 2>nul && set PY=%%P && goto :found
)
:found
if "%PY%"=="" (
  echo [ERR] No Python found in PATH. >> "%LOG%"
  echo ??? Python????????: py -V ?? Python ??? PATH?
  exit /b 1
)

REM 2) print version
"%PY%" -V >> "%LOG%" 2>&1

REM 3) compile sanity
"%PY%" -m py_compile novel_generator\vectorstore_utils.py novel_generator\chapter.py prompt_definitions.py >> "%LOG%" 2>&1
if errorlevel 1 (
  echo [ERR] py_compile failed, see %LOG% for details.
  type "%LOG%"
  exit /b 1
)

REM 4) run app
"%PY%" main.py >> "%LOG%" 2>&1
exit /b %ERRORLEVEL%
