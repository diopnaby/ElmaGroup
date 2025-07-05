#!/usr/bin/env python3
"""
Professional WSGI application entry point for ELMA Group
Optimized for production deployment on AWS Elastic Beanstalk
"""
import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

# Create application instance
application = create_app()

# Configure for production
if __name__ != "__main__":
    # Production configuration
    application.config['DEBUG'] = False
    application.config['TESTING'] = False

if __name__ == "__main__":
    # Local development
    port = int(os.environ.get('PORT', 5000))
    application.run(host='0.0.0.0', port=port, debug=False)
