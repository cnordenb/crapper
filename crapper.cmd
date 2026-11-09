@echo off
rem Run the CRAP tool on Windows, creating a local virtualenv on first use.
rem A .cmd runs from cmd and PowerShell alike, whatever the execution policy.
setlocal
set "ROOT=%~dp0"
set "PY=%ROOT%.venv\Scripts\python.exe"
if not exist "%PY%" (
  py -3 -m venv "%ROOT%.venv" 2>nul || python -m venv "%ROOT%.venv" || exit /b 1
  "%PY%" -m pip install -e "%ROOT%." || exit /b 1
)
"%PY%" -m crapper %*
exit /b %ERRORLEVEL%
