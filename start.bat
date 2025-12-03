@echo off
REM Startup script for LLM Inference System (Windows)

echo ================================================================================
echo LLM INFERENCE SYSTEM - STARTUP
echo ================================================================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then run: venv\Scripts\activate
    echo Then run: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
echo [1/3] Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if .env exists
if not exist ".env" (
    echo.
    echo [WARNING] .env file not found!
    echo Copying .env.example to .env...
    copy .env.example .env
    echo.
    echo Please edit .env file with your settings, then run this script again.
    pause
    exit /b 1
)

echo [2/3] Starting Celery worker...
echo.
echo Opening new window for Celery worker...
start "Celery Worker" cmd /k "venv\Scripts\activate.bat && celery -A app.celery_app worker --loglevel=info --pool=solo"

REM Wait a bit for worker to start
timeout /t 3 /nobreak > nul

echo.
echo [3/3] Starting FastAPI server...
echo.
echo Server will start at: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
