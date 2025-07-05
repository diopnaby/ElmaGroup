#!/usr/bin/env python3
"""
ELMA Group Admin Dashboard - Development Startup
"""
import subprocess
import sys
import os

def main():
    print("🚀 Starting ELMA Group Admin Dashboard (Development)")
    print("=" * 50)
    
    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Install dependencies
    print("📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return
    
    # Initialize database if needed
    print("🗄️  Initializing database...")
    try:
        subprocess.run([sys.executable, "run_elma_app.py", "--init"], check=True)
        print("✅ Database initialized")
    except subprocess.CalledProcessError:
        print("⚠️  Database already exists or initialization failed")
    
    # Start application
    print("🌐 Starting web server...")
    print("📋 Admin credentials: admin / admin123")
    print("🔗 Access: http://localhost:5050")
    print("=" * 50)
    
    try:
        subprocess.run([sys.executable, "run_elma_app.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

if __name__ == "__main__":
    main()
