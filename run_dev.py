#!/usr/bin/env python3
"""
Development server runner
Starts both FastAPI and Celery worker
"""
import subprocess
import sys
import time
import signal
import os
from multiprocessing import Process
from app.core.config import settings

def run_fastapi():
    """Run FastAPI development server"""
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "app.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000", 
        "--reload",
        "--log-level", "debug"
    ])


def run_celery():
    """Run Celery worker"""
    subprocess.run([
        sys.executable, "-m", "celery", 
        "-A", "app.tasks.celery_app", 
        "worker", 
        "--loglevel=info",
        "--concurrency=1",
        "--pool=solo"
    ])


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\nShutting down servers...")
    sys.exit(0)


if __name__ == "__main__":
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    print("Starting Furu AI Backend Development Servers...")
    print(f"FastAPI: {settings.backend_url}")
    print(f"API Docs: {settings.backend_url}/docs")
    print("Press Ctrl+C to stop")
    
    # # Start Celery worker in background
    # celery_process = Process(target=run_celery)
    # celery_process.start()
    
    # Give Celery time to start
    time.sleep(2)
    
    try:
        # Run FastAPI in foreground
        run_fastapi()
    except KeyboardInterrupt:
        print("\nShutting down...")
        celery_process.terminate()
        celery_process.join()
        sys.exit(0)