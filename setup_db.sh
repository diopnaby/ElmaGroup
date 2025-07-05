#!/bin/bash

# This script runs on deployment to set up the database
echo "Setting up database..."

# Create database tables
python -c "
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print('Database tables created successfully!')
"

echo "Database setup complete!"
