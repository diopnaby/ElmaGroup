#!/usr/bin/env python3
"""
Simple entry point for deployment platforms
"""
import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import create_app
    
    # Create the app
    app = create_app()
    
    if __name__ == "__main__":
        # Get port from environment or use default
        port = int(os.environ.get('PORT', 5000))
        
        print(f"🚀 Starting ELMA Group on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
    
    # For WSGI servers (gunicorn, etc.)
    application = app
    
except Exception as e:
    print(f"❌ Error starting app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
