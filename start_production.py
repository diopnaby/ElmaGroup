#!/usr/bin/env python3
"""
ELMA Group Admin Dashboard - Production Startup
"""
import subprocess
import sys
import os

def main():
    print("🚀 Starting ELMA Group Admin Dashboard (Production)")
    print("=" * 50)
    
    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Set production environment
    os.environ['FLASK_ENV'] = 'production'
    os.environ['FLASK_DEBUG'] = '0'
    
    # Install dependencies
    print("📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return
    
    # Initialize database if needed
    if not os.path.exists("elma_app.db"):
        print("🗄️  Initializing database...")
        try:
            subprocess.run([sys.executable, "run_elma_app.py", "--init"], check=True)
            print("✅ Database initialized")
        except subprocess.CalledProcessError:
            print("❌ Database initialization failed")
            return
    
    # Start application with Gunicorn (if available)
    print("🌐 Starting production server...")
    print("📋 Admin credentials: admin / admin123")
    print("🔗 Access: http://localhost:50500")
    print("=" * 50)
    
    try:
        # Try Gunicorn first
        subprocess.run(["gunicorn", "--bind", "0.0.0.0:5050", "--workers", "4", "run_elma_app:app"], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Gunicorn not available, using Flask development server")
        subprocess.run([sys.executable, "run_elma_app.py"], check=True)

if __name__ == "__main__":
    main()
