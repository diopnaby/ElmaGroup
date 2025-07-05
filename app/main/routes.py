from flask import render_template, request, flash, redirect, url_for, jsonify
from app.main import bp
from app.models import (
    Post, Book, Testimonial, Collection, Category, Tag, 
    ContactMessage, NewsletterSubscriber, Author, LibraryStats, PresidentMessage, CommunicationCompany
)
from app.extensions import db
from datetime import datetime
import re

@bp.route('/')
@bp.route('/index')
def index():
    """Homepage with featured content"""
    # Featured posts
    featured_posts = Post.query.filter_by(published=True, is_featured=True).order_by(Post.published_at.desc()).limit(3).all()
    
    # Recent posts if no featured posts
    if not featured_posts:
        featured_posts = Post.query.filter_by(published=True).order_by(Post.published_at.desc()).limit(3).all()
    
    # Featured books
    featured_books = Book.query.filter_by(is_published=True, is_featured=True).order_by(Book.created_at.desc()).limit(6).all()
    
    # Featured testimonials
    featured_testimonials = Testimonial.query.filter_by(
        is_active=True, 
        show_on_homepage=True
    ).order_by(Testimonial.created_at.desc()).limit(3).all()
    
    # Collections - Show all 6 collections
    featured_collections = Collection.query.order_by(Collection.sort_order).limit(6).all()
    
    # Stats for homepage
    stats = {
        'total_books': Book.query.filter_by(is_published=True).count(),
        'total_authors': Author.query.count(),
        'total_posts': Post.query.filter_by(published=True).count(),
        'total_collections': Collection.query.count()
    }
    
    # President's message
    president_message = PresidentMessage.get_active_message()
    
    return render_template('main/index.html',
                         featured_posts=featured_posts,
                         featured_books=featured_books,
                         featured_testimonials=featured_testimonials,
                         featured_collections=featured_collections,
                         stats=stats,
                         president_message=president_message)

@bp.route('/about')
def about():
    """About page"""
    # Get some statistics
    library_stats = LibraryStats.query.first()
    if not library_stats:
        library_stats = LibraryStats.update_stats()
    
    # Recent achievements or milestones
    recent_books = Book.query.filter_by(is_published=True).order_by(Book.created_at.desc()).limit(5).all()
    
    # President's message
    president_message = PresidentMessage.get_active_message()
    
    return render_template('main/about.html',
                         library_stats=library_stats,
                         recent_books=recent_books,
                         president_message=president_message)

@bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page with form handling"""
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        phone = request.form.get('phone', '').strip()
        company = request.form.get('company', '').strip()
        
        # Basic validation
        errors = []
        if not name:
            errors.append('Le nom est requis')
        if not email or not is_valid_email(email):
            errors.append('Une adresse email valide est requise')
        if not subject:
            errors.append('Le sujet est requis')
        if not message:
            errors.append('Le message est requis')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('main/contact.html')
        
        # Create contact message
        contact_message = ContactMessage(
            name=name,
            email=email,
            subject=subject,
            message=message,
            phone=phone,
            company=company,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        
        try:
            db.session.add(contact_message)
            db.session.commit()
            flash('Votre message a été envoyé avec succès! Nous vous répondrons bientôt.', 'success')
            return redirect(url_for('main.contact'))
        except Exception as e:
            db.session.rollback()
            flash('Une erreur est survenue lors de l\'envoi de votre message. Veuillez réessayer.', 'error')
    
    return render_template('main/contact.html')

@bp.route('/collections')
def collections():
    """Collections overview page"""
    # Get all collections with their book counts
    collections = Collection.query.order_by(Collection.sort_order, Collection.name).all()
    
    # Get featured collections
    featured_collections = Collection.query.filter_by(is_featured=True).order_by(Collection.sort_order).all()
    
    return render_template('main/collections.html',
                         collections=collections,
                         featured_collections=featured_collections)

@bp.route('/collection/<slug>')
def collection_detail(slug):
    """Individual collection page"""
    collection = Collection.query.filter_by(slug=slug).first_or_404()
    
    # Get books in this collection
    books = Book.query.filter(
        Book.collections.contains(collection),
        Book.is_published == True
    ).order_by(Book.created_at.desc()).all()
    
    # Get related posts that might mention this collection
    related_posts = Post.query.filter(
        Post.published == True,
        Post.content.contains(collection.name)
    ).order_by(Post.published_at.desc()).limit(3).all()
    
    return render_template('main/collection_detail.html',
                         collection=collection,
                         books=books,
                         related_posts=related_posts)

@bp.route('/president-message')
def president_message():
    """President's message page"""
    return render_template('main/mot_president.html')

@bp.route('/search')
def search():
    """Global search functionality"""
    query = request.args.get('q', '').strip()
    if not query:
        return redirect(url_for('main.index'))
    
    # Search in different content types
    results = {
        'posts': [],
        'books': [],
        'authors': [],
        'collections': []
    }
    
    if len(query) >= 2:  # Minimum search length
        # Search posts
        results['posts'] = Post.query.filter(
            Post.published == True,
            db.or_(
                Post.title.contains(query),
                Post.content.contains(query),
                Post.excerpt.contains(query)
            )
        ).order_by(Post.published_at.desc()).limit(10).all()
        
        # Search books
        results['books'] = Book.query.filter(
            Book.is_published == True,
            db.or_(
                Book.title.contains(query),
                Book.description.contains(query),
                Book.abstract.contains(query),
                Book.keywords.contains(query)
            )
        ).order_by(Book.created_at.desc()).limit(10).all()
        
        # Search authors
        results['authors'] = Author.query.filter(
            db.or_(
                Author.name.contains(query),
                Author.biography.contains(query)
            )
        ).limit(5).all()
        
        # Search collections
        results['collections'] = Collection.query.filter(
            db.or_(
                Collection.name.contains(query),
                Collection.description.contains(query)
            )
        ).limit(5).all()
    
    total_results = sum(len(results[key]) for key in results)
    
    return render_template('main/search_results.html',
                         query=query,
                         results=results,
                         total_results=total_results)

@bp.route('/newsletter/subscribe', methods=['POST'])
def newsletter_subscribe():
    """Newsletter subscription endpoint"""
    email = request.form.get('email', '').strip()
    name = request.form.get('name', '').strip()
    source = request.form.get('source', 'website')
    
    if not email or not is_valid_email(email):
        return jsonify({'success': False, 'message': 'Adresse email invalide'})
    
    # Check if already subscribed
    existing = NewsletterSubscriber.query.filter_by(email=email).first()
    if existing:
        if existing.subscribed:
            return jsonify({'success': False, 'message': 'Vous êtes déjà abonné à notre newsletter'})
        else:
            # Reactivate subscription
            existing.subscribed = True
            existing.unsubscribed_at = None
    else:
        # Create new subscription
        subscriber = NewsletterSubscriber(
            email=email,
            name=name,
            source=source,
            ip_address=request.remote_addr
        )
        db.session.add(subscriber)
    
    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Merci pour votre abonnement!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Une erreur est survenue'})

@bp.route('/sitemap.xml')
def sitemap():
    """Generate sitemap"""
    from flask import Response
    
    # Get all public URLs
    urls = []
    
    # Static pages
    static_pages = [
        ('main.index', '1.0', 'daily'),
        ('main.about', '0.8', 'monthly'),
        ('main.contact', '0.6', 'monthly'),
        ('main.collections', '0.8', 'weekly'),
        ('blog.index', '0.9', 'daily'),
        ('library.index', '0.9', 'weekly'),
        ('testimonials.index', '0.7', 'monthly')
    ]
    
    for route, priority, changefreq in static_pages:
        urls.append({
            'loc': url_for(route, _external=True),
            'priority': priority,
            'changefreq': changefreq,
            'lastmod': datetime.utcnow().strftime('%Y-%m-%d')
        })
    
    # Dynamic content
    # Blog posts
    posts = Post.query.filter_by(published=True).all()
    for post in posts:
        urls.append({
            'loc': url_for('blog.post_detail', slug=post.slug, _external=True),
            'priority': '0.7',
            'changefreq': 'monthly',
            'lastmod': post.updated_at.strftime('%Y-%m-%d') if post.updated_at else post.created_at.strftime('%Y-%m-%d')
        })
    
    # Books
    books = Book.query.filter_by(is_published=True).all()
    for book in books:
        urls.append({
            'loc': url_for('library.book_detail', slug=book.slug, _external=True),
            'priority': '0.8',
            'changefreq': 'monthly',
            'lastmod': book.updated_at.strftime('%Y-%m-%d') if book.updated_at else book.created_at.strftime('%Y-%m-%d')
        })
    
    # Collections
    collections = Collection.query.all()
    for collection in collections:
        urls.append({
            'loc': url_for('main.collection_detail', slug=collection.slug, _external=True),
            'priority': '0.7',
            'changefreq': 'monthly',
            'lastmod': collection.created_at.strftime('%Y-%m-%d')
        })
    
    # Generate XML
    xml = render_template('sitemap.xml', urls=urls)
    return Response(xml, mimetype='application/xml')

def is_valid_email(email):
    """Simple email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Error handlers
@bp.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500


@bp.route('/edition')
def edition():
    books = Book.query.filter_by(is_published=True).all()
    authors = Author.query.all()
    return render_template('main/edition.html', books=books, authors=authors)

@bp.route('/communication')
def communication():
    companies = CommunicationCompany.query.order_by(CommunicationCompany.date_accompanied.desc()).all()
    return render_template('main/communication.html', companies=companies)
