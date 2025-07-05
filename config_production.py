"""
Professional production configuration for ELMA Group
Optimized for AWS EC2 deployment
"""
import os
from datetime import timedelta

class ProductionConfig:
    """Professional production configuration"""
    
    # Basic Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'elma-group-production-secret-key-2024'
    DEBUG = False
    TESTING = False
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://elmagroup:elma_secure_password_2024@localhost/elmagroup_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 300,
        'pool_pre_ping': True
    }
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Security configuration
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    
    # File upload configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = '/var/www/elmagroup/app/static/uploads'
    
    # Email configuration (for professional notifications)
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@elmagroup.com'
    
    # Professional logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = '/var/log/elmagroup/application.log'
    
    # Performance optimization
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 year cache for static files
    
    # Professional admin settings
    ADMIN_EMAIL = 'admin@elmagroup.com'
    COMPANY_NAME = 'ELMA Group'
    COMPANY_URL = 'https://elmagroup.com'
