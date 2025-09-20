@echo off
REM Furu AI Backend Development Startup Script for Windows

echo 🚀 Starting Furu AI Backend Development Environment...

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing dependencies...
pip install -r requirements.txt

REM Check if .env exists
if not exist ".env" (
    echo ⚙️  Creating .env file from template...
    copy env.example .env
    echo ⚠️  Please edit .env file with your database and email settings before continuing!
    echo    Required: DATABASE_URL, REDIS_URL, SECRET_KEY, SMTP_USERNAME, SMTP_PASSWORD
    pause
    exit /b 1
)

REM Check if PostgreSQL is running
echo 🗄️  Checking PostgreSQL connection...
python -c "import psycopg2; from app.core.config import settings; conn = psycopg2.connect(settings.database_url); conn.close(); print('✅ PostgreSQL connection successful')" 2>nul
if errorlevel 1 (
    echo ❌ PostgreSQL connection failed
    echo Please make sure PostgreSQL is running and database exists
    pause
    exit /b 1
)

REM Check if Redis is running
echo 🔴 Checking Redis connection...
python -c "import redis; from app.core.config import settings; r = redis.from_url(settings.redis_url); r.ping(); print('✅ Redis connection successful')" 2>nul
if errorlevel 1 (
    echo ❌ Redis connection failed
    echo Please make sure Redis is running
    pause
    exit /b 1
)



echo 🎉 Setup complete! Starting servers...

REM Start Celery worker in background
echo 🔄 Starting Celery worker...
start "Celery Worker" cmd /c "celery -A app.tasks.celery_app worker --loglevel=info --concurrency=1 --pool=solo"

REM Wait a moment for Celery to start
timeout /t 3 /nobreak >nul

REM Start FastAPI server
echo 🌐 Starting FastAPI server...
echo    Press Ctrl+C to stop all services

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug