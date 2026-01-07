@echo off
echo ========================================
echo Stirling Chatbot System Startup
echo ========================================
echo.

echo Checking prerequisites...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    pause
    exit /b 1
)

echo Prerequisites OK!
echo.

echo Starting Backend Server...
echo.
start "Stirling Backend" cmd /k "cd backend && python main.py"

timeout /t 3 /nobreak >nul

echo Starting Frontend Server...
echo.
start "Stirling Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo System Starting!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo Docs:     http://localhost:8000/docs
echo.
echo Press any key to open browser...
pause >nul

start http://localhost:3000

echo.
echo System is running!
echo Close this window to keep servers running.
echo.
pause
