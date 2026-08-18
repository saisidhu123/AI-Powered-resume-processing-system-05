@echo off
echo =======================================================
echo Starting AI-Powered Resume Processing System (Web App)
echo =======================================================
echo.
echo Checking Python environment...
python --version
echo.
echo Starting FastAPI + React Server on http://127.0.0.1:8000 ...
start "" cmd /c "timeout /t 3 /nobreak >nul & start http://127.0.0.1:8000"
python -m uvicorn server:app --host 127.0.0.1 --port 8000 --reload
pause

