@echo off
title AI Second Brain Launcher
echo Starting AI Second Brain Application...
echo Installing/verifying dependencies using python -m pip...
python -m pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [Notice] Standard pip failed, trying python -m pip install --user...
    python -m pip install -r requirements.txt --user
)
python app.py
pause
