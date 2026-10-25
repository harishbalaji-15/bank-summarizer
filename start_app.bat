@echo off
title Bank Statement Summarizer
echo ========================================================
echo   Launching Offline Bank Statement Summarizer...
echo ========================================================
echo.
echo Starting Local Backend (FastAPI on http://localhost:8000)...
start "Bank Summarizer Backend" cmd /c "cd /d "%~dp0backend" && python main.py"

timeout /t 2 /nobreak >nul

echo Starting Local Frontend (React + Vite on http://localhost:5173)...
start "Bank Summarizer Frontend" cmd /c "cd /d "%~dp0frontend" && npm run dev"

timeout /t 2 /nobreak >nul

echo Opening browser...
start http://localhost:5173

echo.
echo ========================================================
echo   Both services are running!
echo   Web App : http://localhost:5173
echo   API Docs: http://localhost:8000/docs
echo ========================================================
echo Press any key to exit this launcher (services will keep running).
pause >nul
