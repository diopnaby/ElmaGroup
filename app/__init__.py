from flask import Flask
from app.extensions import db, migrate, admin, login_manager
from app.config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Import models (this must be done after db initialization)
    from app.models import (
        User, Post, Comment, Category, Collection, Tag, ContactMessage, 
        NewsletterSubscriber, Author, Publisher, BookCategory, Book, 
        BookReview, Testimonial, LibraryStats
    )
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Custom Jinja filters
    @app.template_filter('batch')
    def batch_filter(iterable, count, fill_with=None):
        """Batch items into groups of specified count"""
        result = []
        items = list(iterable)
        for i in range(0, len(items), count):
            batch = items[i:i+count]
            if fill_with is not None:
                batch.extend([fill_with] * (count - len(batch)))
            result.append(batch)
        return result
    
    # Register blueprints
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.library import bp as library_bp
    app.register_blueprint(library_bp, url_prefix='/library')
    
    from app.testimonials import bp as testimonials_bp
    app.register_blueprint(testimonials_bp, url_prefix='/testimonials')
    
    from app.blog import bp as blog_bp
    app.register_blueprint(blog_bp, url_prefix='/blog')
    
    from app.admin_panel import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Setup admin panel
    try:
        from app.admin import setup_admin
        setup_admin(app)
        print("✅ Admin panel configured successfully")
    except ImportError as e:
        print(f"⚠️  Flask-Admin not available: {e}")
        print("   To enable admin panel: pip install Flask-Admin")
    
    return app
