from flask import render_template, request, redirect, url_for, flash, current_app
from app.library import bp
from app.models import Book, Author, Publisher, BookCategory, Collection, BookReview, Tag
from app.extensions import db
from datetime import datetime
from sqlalchemy import desc, asc, func

@bp.route('/')
@bp.route('/index')
def index():
    """Library homepage"""
    page = request.args.get('page', 1, type=int)
    
    # Base query for published books
    query = Book.query.filter_by(is_published=True)
    
    # Apply sorting
    query = query.order_by(desc(Book.created_at))
    
    # Paginate results
    books = query.paginate(
        page=page,
        per_page=current_app.config.get('BOOKS_PER_PAGE', 12),
        error_out=False
    )
    
    # Featured books for carousel (up to 12 books for 3 slides with 4 books each)
    featured_books = Book.query.filter_by(
        is_published=True,
        is_featured=True
    ).order_by(desc(Book.created_at)).limit(12).all()
    
    return render_template('library/index.html',
                         books=books,
                         featured_books=featured_books)

@bp.route('/book/<slug>')
def book_detail(slug):
    """Individual book page"""
    book = Book.query.filter_by(slug=slug, is_published=True).first_or_404()
    
    # Increment view count
    book.views += 1
    db.session.commit()
    
    # Get approved reviews
    reviews = BookReview.query.filter_by(
        book=book,
        is_approved=True
    ).order_by(desc(BookReview.created_at)).all()
    
    # Get related books (same category or authors)
    related_books = []
    
    # Books in same category
    if book.book_category:
        related_books = Book.query.filter(
            Book.book_category == book.book_category,
            Book.is_published == True,
            Book.id != book.id
        ).order_by(desc(Book.created_at)).limit(4).all()
    
    return render_template('library/book_detail.html',
                         book=book,
                         reviews=reviews,
                         related_books=related_books)

@bp.route('/authors')
def authors():
    """Authors listing page"""
    page = request.args.get('page', 1, type=int)
    
    # Base query
    query = Author.query
    
    # Apply sorting
    query = query.order_by(Author.name)
    
    authors = query.paginate(
        page=page,
        per_page=20,
        error_out=False
    )
    
    return render_template('library/authors.html',
                         authors=authors)

@bp.route('/author/<slug>')
def author_detail(slug):
    """Individual author page"""
    author = Author.query.filter_by(slug=slug).first_or_404()
    
    # Increment profile views
    author.profile_views += 1
    db.session.commit()
    
    # Get author's books
    books = Book.query.filter(
        Book.authors.contains(author),
        Book.is_published == True
    ).order_by(desc(Book.publication_date)).all()
    
    return render_template('library/author_detail.html',
                         author=author,
                         books=books)

@bp.route('/categories')
def categories():
    """Book categories listing"""
    categories = BookCategory.query.order_by(BookCategory.sort_order, BookCategory.name).all()
    
    return render_template('library/categories.html',
                         categories=categories)

@bp.route('/search')
def search():
    """Library search"""
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    
    results = {'books': None, 'authors': None}
    
    if query and len(query) >= 2:
        # Search books
        books_query = Book.query.filter(
            Book.is_published == True,
            db.or_(
                Book.title.contains(query),
                Book.description.contains(query)
            )
        ).order_by(desc(Book.created_at))
        
        results['books'] = books_query.paginate(
            page=page,
            per_page=current_app.config.get('BOOKS_PER_PAGE', 12),
            error_out=False
        )
        
        # Search authors
        results['authors'] = Author.query.filter(
            db.or_(
                Author.name.contains(query),
                Author.biography.contains(query)
            )
        ).order_by(Author.name).limit(6).all()
    
    return render_template('library/search.html',
                         query=query,
                         results=results)

# Library-specific template filters
@bp.app_template_filter('format_price')
def format_price_filter(price, currency='XOF'):
    """Format price with currency"""
    if price:
        return f"{price:,.0f} {currency}"
    return "Prix sur demande"

@bp.app_template_filter('star_rating')
def star_rating_filter(rating, max_stars=5):
    """Generate star rating HTML"""
    if not rating:
        rating = 0
    
    stars_html = ''
    for i in range(1, max_stars + 1):
        if i <= rating:
            stars_html += '<i class="fas fa-star text-warning"></i>'
        elif i - 0.5 <= rating:
            stars_html += '<i class="fas fa-star-half-alt text-warning"></i>'
        else:
            stars_html += '<i class="far fa-star text-muted"></i>'
    
    return stars_html
