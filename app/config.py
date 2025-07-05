import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Basic Flask config
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'elma-group-secret-key-dev-2024'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, '..', 'elma_app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload settings
    UPLOAD_FOLDER = os.path.join(basedir, 'static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Pagination
    POSTS_PER_PAGE = 10
    BOOKS_PER_PAGE = 12
    TESTIMONIALS_PER_PAGE = 9
    COMMENTS_PER_PAGE = 20
    
    # Flask-Admin settings
    FLASK_ADMIN_SWATCH = 'cosmo'
    
    # File upload settings
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
    
    # Email settings (for contact forms, newsletters, etc.)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Application settings
    COMPANY_NAME = 'ELMA Group'
    COMPANY_EMAIL = 'contact@elmagroup.com'
    COMPANY_PHONE = '+221 XX XXX XX XX'
    COMPANY_ADDRESS = 'Dakar, Sénégal'
    
    # Blog settings
    BLOG_TITLE = 'ELMA Group Blog'
    BLOG_SUBTITLE = 'Actualités, analyses et perspectives sur la littérature africaine'
    BLOG_DESCRIPTION = 'Le blog officiel d\'ELMA Group avec des articles sur la littérature africaine, l\'édition et la culture.'
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    
class ProductionConfig(Config):
    DEBUG = False
    
    # Professional PostgreSQL database for production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://elmagroup:elma_secure_password_2024@localhost/elmagroup_db'
    
    # Production database settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'connect_args': {
            'sslmode': 'require',
            'connect_timeout': 10
        }
    }
    
    # Professional session settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Security settings
    WTF_CSRF_ENABLED = True
    
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
