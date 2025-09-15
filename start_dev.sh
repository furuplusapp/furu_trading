#!/bin/bash

# Furu AI Backend Development Startup Script

echo "🚀 Starting Furu AI Backend Development Environment..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please edit .env file with your database and email settings before continuing!"
    echo "   Required: DATABASE_URL, REDIS_URL, SECRET_KEY, SMTP_USERNAME, SMTP_PASSWORD"
    exit 1
fi

# Check if PostgreSQL is running
echo "🗄️  Checking PostgreSQL connection..."
python -c "
import psycopg2
from app.core.config import settings
try:
    conn = psycopg2.connect(settings.database_url)
    conn.close()
    print('✅ PostgreSQL connection successful')
except Exception as e:
    print(f'❌ PostgreSQL connection failed: {e}')
    print('Please make sure PostgreSQL is running and database exists')
    exit(1)
"

# Check if Redis is running
echo "🔴 Checking Redis connection..."
python -c "
import redis
from app.core.config import settings
try:
    r = redis.from_url(settings.redis_url)
    r.ping()
    print('✅ Redis connection successful')
except Exception as e:
    print(f'❌ Redis connection failed: {e}')
    print('Please make sure Redis is running')
    exit(1)
"

# Run database migrations
echo "🗃️  Running database migrations..."
alembic upgrade head

echo "🎉 Setup complete! Starting servers..."

# Start Celery worker in background
echo "🔄 Starting Celery worker..."
celery -A app.tasks.celery_app worker --loglevel=info &
CELERY_PID=$!

# Start FastAPI server
echo "🌐 Starting FastAPI server..."
echo "   API: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo "   Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo "🛑 Shutting down services..."
    kill $CELERY_PID 2>/dev/null
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Start FastAPI
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload