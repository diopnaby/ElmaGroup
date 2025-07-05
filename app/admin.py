from flask import url_for, redirect, request, flash, current_app
from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import Select2Widget
from wtforms import SelectField, TextAreaField, BooleanField
from wtforms.widgets import TextArea
from datetime import datetime, timedelta
from app.extensions import db
from app.models import (
    User, Post, Comment, Category, Collection, Tag, ContactMessage, 
    NewsletterSubscriber, Author, Publisher, BookCategory, Book, 
    BookReview, Testimonial, LibraryStats
)

class CKTextAreaWidget(TextArea):
    def __call__(self, field, **kwargs):
        if kwargs.get('class'):
            kwargs['class'] += ' ckeditor'
        else:
            kwargs.setdefault('class', 'ckeditor')
        return super(CKTextAreaWidget, self).__call__(field, **kwargs)

class CKTextAreaField(TextAreaField):
    widget = CKTextAreaWidget()

class SecureModelView(ModelView):
    def is_accessible(self):
        # For development, allow access to all. In production, add authentication check
        return True
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin.index'))

class DashboardView(AdminIndexView):
    @expose('/')
    def index(self):
        # Blog Statistics
        total_posts = Post.query.count()
        published_posts = Post.query.filter_by(published=True).count()
        draft_posts = Post.query.filter_by(published=False).count()
        total_comments = Comment.query.count()
        pending_comments = Comment.query.filter_by(approved=False).count()
        
        # Library Statistics
        total_books = Book.query.filter_by(is_published=True).count()
        total_authors = Author.query.count()
        total_reviews = BookReview.query.filter_by(is_approved=True).count()
        pending_reviews = BookReview.query.filter_by(is_approved=False).count()
        
        # General Statistics
        total_testimonials = Testimonial.query.filter_by(is_active=True).count()
        pending_testimonials = Testimonial.query.filter_by(is_active=False).count()
        total_messages = ContactMessage.query.filter_by(responded=False).count()
        total_subscribers = NewsletterSubscriber.query.filter_by(subscribed=True).count()
        
        # Recent Activity
        recent_posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
        recent_comments = Comment.query.order_by(Comment.created_at.desc()).limit(5).all()
        recent_books = Book.query.order_by(Book.created_at.desc()).limit(5).all()
        recent_messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(5).all()
        
        # Popular Content (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        popular_posts = Post.query.filter(
            Post.created_at >= thirty_days_ago
        ).order_by(Post.views.desc()).limit(5).all()
        
        popular_books = Book.query.filter(
            Book.created_at >= thirty_days_ago
        ).order_by(Book.views.desc()).limit(5).all()
        
        return self.render('admin/dashboard.html',
                         # Blog stats
                         total_posts=total_posts,
                         published_posts=published_posts,
                         draft_posts=draft_posts,
                         total_comments=total_comments,
                         pending_comments=pending_comments,
                         
                         # Library stats
                         total_books=total_books,
                         total_authors=total_authors,
                         total_reviews=total_reviews,
                         pending_reviews=pending_reviews,
                         
                         # General stats
                         total_testimonials=total_testimonials,
                         pending_testimonials=pending_testimonials,
                         total_messages=total_messages,
                         total_subscribers=total_subscribers,
                         
                         # Recent activity
                         recent_posts=recent_posts,
                         recent_comments=recent_comments,
                         recent_books=recent_books,
                         recent_messages=recent_messages,
                         
                         # Popular content
                         popular_posts=popular_posts,
                         popular_books=popular_books)

# Blog Management Views
class UserView(SecureModelView):
    column_list = ['username', 'email', 'full_name', 'is_admin', 'is_author', 'is_active', 'post_count', 'created_at']
    column_searchable_list = ['username', 'email', 'first_name', 'last_name']
    column_filters = ['is_admin', 'is_author', 'is_active', 'created_at']
    form_columns = ['username', 'email', 'first_name', 'last_name', 'bio', 'website', 
                   'is_admin', 'is_author', 'is_active']
    form_overrides = {
        'bio': CKTextAreaField
    }
    column_labels = {
        'post_count': 'Articles publiés',
        'is_admin': 'Administrateur',
        'is_author': 'Auteur',
        'is_active': 'Actif',
        'created_at': 'Créé le'
    }

class PostView(SecureModelView):
    column_list = ['title', 'author_id', 'category_id', 'published', 'is_featured', 'views', 'comment_count', 'created_at']
    column_searchable_list = ['title', 'content', 'excerpt']
    column_filters = ['published', 'is_featured', 'is_pinned', 'category_id', 'author_id', 'created_at']
    column_editable_list = ['published', 'is_featured', 'is_pinned']
    
    form_columns = ['title', 'author_id', 'category_id', 'content', 'excerpt', 'meta_title', 
                   'meta_description', 'featured_image', 'tags', 'published', 'is_featured', 
                   'is_pinned', 'allow_comments']
    
    form_overrides = {
        'content': CKTextAreaField,
        'excerpt': CKTextAreaField,
        'meta_description': TextAreaField
    }
    
    column_labels = {
        'author_id': 'Auteur',
        'category_id': 'Catégorie',
        'published': 'Publié',
        'is_featured': 'À la une',
        'is_pinned': 'Épinglé',
        'views': 'Vues',
        'comment_count': 'Commentaires',
        'created_at': 'Créé le',
        'allow_comments': 'Autoriser commentaires'
    }
    
    def create_model(self, form):
        """Override to set published_at when publishing"""
        model = super().create_model(form)
        if model and model.published and not model.published_at:
            model.published_at = datetime.utcnow()
            db.session.commit()
        return model
    
    def update_model(self, form, model):
        """Override to set published_at when publishing"""
        result = super().update_model(form, model)
        if result and model.published and not model.published_at:
            model.published_at = datetime.utcnow()
            db.session.commit()
        elif result and not model.published:
            model.published_at = None
            db.session.commit()
        return result

class CommentView(SecureModelView):
    column_list = ['post', 'commenter_name', 'content', 'approved', 'is_spam', 'created_at']
    column_searchable_list = ['content', 'name', 'email']
    column_filters = ['approved', 'is_spam', 'created_at', 'post']
    column_editable_list = ['approved', 'is_spam']
    
    form_columns = ['post', 'author', 'name', 'email', 'website', 'content', 
                   'approved', 'is_spam', 'parent']
    
    form_overrides = {
        'content': CKTextAreaField
    }
    
    column_labels = {
        'post': 'Article',
        'commenter_name': 'Commentateur',
        'content': 'Commentaire',
        'approved': 'Approuvé',
        'is_spam': 'Spam',
        'created_at': 'Créé le',
        'parent': 'Réponse à'
    }
    
    def create_model(self, form):
        """Auto-approve if needed"""
        model = super().create_model(form)
        # You can add auto-approval logic here
        return model

class CategoryView(SecureModelView):
    column_list = ['name', 'post_count', 'is_featured', 'color', 'sort_order', 'created_at']
    column_searchable_list = ['name', 'description']
    column_filters = ['is_featured', 'created_at']
    column_editable_list = ['sort_order', 'is_featured', 'color']
    
    form_columns = ['name', 'description', 'color', 'icon', 'is_featured', 'sort_order']
    
    form_overrides = {
        'description': CKTextAreaField
    }
    
    column_labels = {
        'name': 'Nom',
        'post_count': 'Articles',
        'is_featured': 'À la une',
        'color': 'Couleur',
        'sort_order': 'Ordre',
        'created_at': 'Créé le',
        'icon': 'Icône'
    }

class TagView(SecureModelView):
    column_list = ['name', 'post_count', 'book_count', 'color', 'created_at']
    column_searchable_list = ['name', 'description']
    column_filters = ['created_at']
    
    form_columns = ['name', 'description', 'color']
    
    form_overrides = {
        'description': TextAreaField
    }
    
    column_labels = {
        'name': 'Nom',
        'post_count': 'Articles',
        'book_count': 'Livres',
        'color': 'Couleur',
        'created_at': 'Créé le'
    }

# Analytics and Reports View
class AnalyticsView(BaseView):
    @expose('/')
    def index(self):
        # Blog Analytics
        blog_stats = {
            'total_posts': Post.query.count(),
            'published_posts': Post.query.filter_by(published=True).count(),
            'total_views': db.session.query(db.func.sum(Post.views)).scalar() or 0,
            'total_comments': Comment.query.filter_by(approved=True).count(),
            'avg_comments_per_post': Comment.query.filter_by(approved=True).count() / max(1, Post.query.filter_by(published=True).count())
        }
        
        # Top performing posts
        top_posts = Post.query.filter_by(published=True).order_by(Post.views.desc()).limit(10).all()
        
        # Recent activity
        recent_activity = []
        
        # Recent posts
        for post in Post.query.order_by(Post.created_at.desc()).limit(5).all():
            recent_activity.append({
                'type': 'post',
                'title': f'Nouvel article: {post.title}',
                'date': post.created_at,
                'url': url_for('blog.post_detail', slug=post.slug)
            })
        
        # Recent comments
        for comment in Comment.query.order_by(Comment.created_at.desc()).limit(5).all():
            recent_activity.append({
                'type': 'comment',
                'title': f'Nouveau commentaire sur: {comment.post.title}',
                'date': comment.created_at,
                'url': url_for('blog.post_detail', slug=comment.post.slug)
            })
        
        # Sort by date
        recent_activity.sort(key=lambda x: x['date'], reverse=True)
        recent_activity = recent_activity[:10]
        
        return self.render('admin/analytics.html',
                         blog_stats=blog_stats,
                         top_posts=top_posts,
                         recent_activity=recent_activity)

# Content Management Tools
class ContentToolsView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/content_tools.html')
    
    @expose('/bulk-publish', methods=['POST'])
    def bulk_publish(self):
        """Bulk publish selected posts"""
        post_ids = request.form.getlist('post_ids')
        if post_ids:
            posts = Post.query.filter(Post.id.in_(post_ids)).all()
            for post in posts:
                if not post.published:
                    post.publish()
            db.session.commit()
            flash(f'{len(posts)} articles publiés avec succès!', 'success')
        return redirect(url_for('.index'))
    
    @expose('/bulk-unpublish', methods=['POST'])
    def bulk_unpublish(self):
        """Bulk unpublish selected posts"""
        post_ids = request.form.getlist('post_ids')
        if post_ids:
            posts = Post.query.filter(Post.id.in_(post_ids)).all()
            for post in posts:
                if post.published:
                    post.unpublish()
            db.session.commit()
            flash(f'{len(posts)} articles dépubliés avec succès!', 'success')
        return redirect(url_for('.index'))

# Library Admin Views (from previous implementation)
class AuthorView(SecureModelView):
    column_list = ['name', 'nationality', 'book_count', 'profile_views', 'created_at']
    column_searchable_list = ['name', 'nationality']
    column_filters = ['nationality', 'created_at']
    form_columns = ['name', 'photo', 'nationality', 'birth_date', 'death_date', 
                   'short_bio', 'biography', 'website', 'awards', 'education']
    form_overrides = {
        'biography': CKTextAreaField,
        'short_bio': CKTextAreaField
    }

class PublisherView(SecureModelView):
    column_list = ['name', 'website', 'book_count', 'is_active', 'created_at']
    column_searchable_list = ['name', 'email']
    column_filters = ['is_active', 'founded_year']
    form_overrides = {
        'description': CKTextAreaField
    }

class BookCategoryView(SecureModelView):
    column_list = ['name', 'book_count', 'sort_order', 'created_at']
    column_searchable_list = ['name']
    column_editable_list = ['sort_order']
    form_overrides = {
        'description': CKTextAreaField
    }

class BookView(SecureModelView):
    column_list = ['title', 'author_names', 'book_category', 'publisher', 
                  'is_published', 'is_featured', 'views', 'created_at']
    column_searchable_list = ['title', 'isbn_13', 'keywords']
    column_filters = ['is_published', 'is_featured', 'is_bestseller', 
                     'is_new_release', 'book_category', 'publisher', 'authors']
    form_columns = ['title', 'subtitle', 'authors', 'publisher', 'book_category',
                   'isbn_13', 'isbn_10', 'description', 'abstract', 'excerpt',
                   'cover_image', 'publication_date', 'page_count', 'format_type',
                   'language', 'edition', 'price', 'sale_price', 'currency',
                   'availability_status', 'stock_quantity', 'table_of_contents',
                   'target_audience', 'keywords', 'meta_title', 'meta_description',
                   'is_published', 'is_featured', 'is_bestseller', 'is_new_release',
                   'is_award_winner', 'allow_reviews', 'collections', 'tags']
    form_overrides = {
        'description': CKTextAreaField,
        'abstract': CKTextAreaField,
        'excerpt': CKTextAreaField,
        'table_of_contents': CKTextAreaField,
        'availability_status': SelectField
    }
    form_args = {
        'availability_status': {
            'choices': [('available', 'Available'), ('out_of_stock', 'Out of Stock'), 
                       ('pre_order', 'Pre-order')]
        }
    }

class BookReviewView(SecureModelView):
    column_list = ['book', 'reviewer_name', 'rating', 'is_approved', 
                  'is_featured', 'created_at']
    column_searchable_list = ['reviewer_name', 'reviewer_email', 'content']
    column_filters = ['rating', 'is_approved', 'is_featured', 'is_verified_purchase']
    form_columns = ['book', 'reviewer_name', 'reviewer_email', 'reviewer_location',
                   'title', 'content', 'rating', 'pros', 'cons', 'is_approved',
                   'is_featured', 'is_verified_purchase']
    form_overrides = {
        'content': CKTextAreaField
    }

class TestimonialView(SecureModelView):
    column_list = ['display_name', 'category', 'is_active', 'is_featured', 
                  'is_verified', 'created_at']
    column_searchable_list = ['display_name', 'quote', 'email']
    column_filters = ['category', 'is_active', 'is_featured', 'is_verified', 
                     'show_on_homepage']
    form_columns = ['quote', 'display_name', 'display_title', 'company', 
                   'location', 'photo', 'email', 'phone', 'category', 'context',
                   'rating', 'book', 'collection', 'is_active', 'is_featured',
                   'is_verified', 'show_on_homepage', 'can_use_name', 
                   'can_use_title', 'can_use_photo']
    form_overrides = {
        'quote': CKTextAreaField
    }

class ContactMessageView(SecureModelView):
    column_list = ['name', 'email', 'subject', 'priority', 'responded', 'created_at']
    column_searchable_list = ['name', 'email', 'subject', 'message']
    column_filters = ['responded', 'priority', 'is_spam', 'created_at']
    column_editable_list = ['responded', 'priority']
    can_create = False
    form_columns = ['name', 'email', 'subject', 'message', 'phone', 'company',
                   'responded', 'priority', 'is_spam']
    
    form_args = {
        'priority': {
            'choices': [('low', 'Faible'), ('normal', 'Normal'), 
                       ('high', 'Élevée'), ('urgent', 'Urgent')]
        }
    }

class NewsletterSubscriberView(SecureModelView):
    column_list = ['email', 'name', 'subscribed', 'confirmed', 'source', 'created_at']
    column_searchable_list = ['email', 'name']
    column_filters = ['subscribed', 'confirmed', 'source', 'created_at']
    column_editable_list = ['subscribed', 'confirmed']

def setup_admin(app):
    admin = Admin(
        app, 
        name='ELMA Admin', 
        template_mode='bootstrap4',
        index_view=DashboardView()
    )
    
    # Blog Management
    admin.add_view(PostView(Post, db.session, name='Articles', category='Blog'))
    admin.add_view(CommentView(Comment, db.session, name='Commentaires', category='Blog'))
    admin.add_view(CategoryView(Category, db.session, name='Catégories', category='Blog'))
    admin.add_view(TagView(Tag, db.session, name='Tags', category='Blog'))
    admin.add_view(UserView(User, db.session, name='Utilisateurs', category='Blog'))
    
    # Content Tools
    admin.add_view(AnalyticsView(name='Analytics', category='Outils'))
    admin.add_view(ContentToolsView(name='Outils de contenu', category='Outils'))
    
    # Library Management
    admin.add_view(AuthorView(Author, db.session, name='Auteurs', category='Bibliothèque'))
    admin.add_view(PublisherView(Publisher, db.session, name='Éditeurs', category='Bibliothèque'))
    admin.add_view(BookCategoryView(BookCategory, db.session, name='Catégories de livres', category='Bibliothèque'))
    admin.add_view(BookView(Book, db.session, name='Livres', category='Bibliothèque'))
    admin.add_view(BookReviewView(BookReview, db.session, name='Avis de livres', category='Bibliothèque'))
    admin.add_view(ModelView(Collection, db.session, name='Collections', category='Bibliothèque'))
    
    # Testimonials
    admin.add_view(TestimonialView(Testimonial, db.session, name='Témoignages', category='Communications'))
    
    # Communications
    admin.add_view(ContactMessageView(ContactMessage, db.session, name='Messages', category='Communications'))
    admin.add_view(NewsletterSubscriberView(NewsletterSubscriber, db.session, name='Newsletter', category='Communications'))
    
    return admin
