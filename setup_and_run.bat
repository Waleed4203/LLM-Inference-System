@echo off
echo ========================================
echo LLM Inference System Setup
echo ========================================
echo.

echo Step 1: Checking Docker...
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop and run this script again.
    pause
    exit /b 1
)
echo Docker is running!
echo.

echo Step 2: Starting Redis...
docker-compose up -d redis
if %errorlevel% neq 0 (
    echo ERROR: Failed to start Redis
    pause
    exit /b 1
)
echo Redis started successfully!
echo.

echo Step 3: Waiting for Redis to be ready...
timeout /t 3 /nobreak >nul
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To run the system, open TWO separate terminals:
echo.
echo Terminal 1 - Start Celery Worker:
echo   celery -A app.celery_app worker --loglevel=info --pool=solo
echo.
echo Terminal 2 - Start FastAPI Server:
echo   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
echo.
echo Then visit: http://localhost:8000/docs
echo.
pause
