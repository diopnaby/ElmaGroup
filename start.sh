#!/bin/bash
# Startup script for deployment

echo "🚀 Starting ELMA Group deployment..."

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run database initialization
echo "🗄️ Setting up database..."
python -c "
from app import create_app
from app.extensions import db

app = create_app()
with app.app_context():
    db.create_all()
    print('✅ Database initialized')
"

# Start the application
echo "🌐 Starting web server..."
python run_elma_app.py
