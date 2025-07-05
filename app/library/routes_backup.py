from flask import render_template, request, redirect, url_for, flash, current_app, jsonify
from app.library import bp
from app.models import Book, Author, Publisher, BookCategory, Collection, BookReview, Tag
from app.extensions import db
from datetime import datetime
from sqlalchemy import desc, asc, func

@bp.route('/')
@bp.route('/index')
def index():
    """Library homepage"""
    # Get filter parameters
    category_slug = request.args.get('category')
    collection_slug = request.args.get('collection')
    author_slug = request.args.get('author')
    publisher_slug = request.args.get('publisher')
    sort_by = request.args.get('sort', 'newest')  # newest, oldest, popular, rating
    search_query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)

    # Base query for published books
    query = Book.query.filter_by(is_published=True)

    # Apply filters
    if category_slug:
        category = BookCategory.query.filter_by(slug=category_slug).first_or_404()
        query = query.filter_by(book_category=category)

    if collection_slug:
        collection = Collection.query.filter_by(slug=collection_slug).first_or_404()
        query = query.filter(Book.collections.contains(collection))

    if author_slug:
        author = Author.query.filter_by(slug=author_slug).first_or_404()
        query = query.filter(Book.authors.contains(author))

    if publisher_slug:
        publisher = Publisher.query.filter_by(slug=publisher_slug).first_or_404()
        query = query.filter_by(publisher=publisher)

    if search_query:
        query = query.filter(
            db.or_(
                Book.title.contains(search_query),
                Book.description.contains(search_query),
                Book.abstract.contains(search_query),
                Book.keywords.contains(search_query)
            )
        )

    # Apply sorting
    if sort_by == 'oldest':
        query = query.order_by(asc(Book.publication_date))
    elif sort_by == 'popular':
        query = query.order_by(desc(Book.views))
    elif sort_by == 'rating':
        # Sort by average rating (books with reviews first)
        query = query.outerjoin(BookReview).group_by(Book.id).order_by(
            desc(func.avg(BookReview.rating).label('avg_rating'))
        )
    else:  # newest (default)
        query = query.order_by(desc(Book.created_at))

    # Paginate results
    books = query.paginate(
        page=page,
        per_page=current_app.config.get('BOOKS_PER_PAGE', 12),
        error_out=False
    )

    # Get sidebar data
    sidebar_data = get_library_sidebar_data()

    # Featured books for top of page
    featured_books = Book.query.filter_by(
        is_published=True,
        is_featured=True
    ).order_by(desc(Book.created_at)).limit(6).all()

    # New releases
    new_releases = Book.query.filter_by(
        is_published=True,
        is_new_release=True
    ).order_by(desc(Book.created_at)).limit(4).all()

    # Bestsellers
    bestsellers = Book.query.filter_by(
        is_published=True,
        is_bestseller=True
    ).order_by(desc(Book.views)).limit(4).all()

    return render_template(
        'library/index.html',
        books=books,
        sidebar_data=sidebar_data,
        featured_books=featured_books,
        new_releases=new_releases,
        bestsellers=bestsellers,
        current_category=category_slug,
        current_collection=collection_slug,
        current_author=author_slug,
        current_publisher=publisher_slug,
        current_sort=sort_by,
        search_query=search_query
    )

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

    # Calculate rating breakdown
    rating_breakdown = {}
    if reviews:
        for i in range(1, 6):
            count = len([r for r in reviews if r.rating == i])
            rating_breakdown[i] = {
                'count': count,
                'percentage': (count / len(reviews)) * 100 if reviews else 0
            }

    # Get related books (same category or authors)
    related_books = []
    # Books in same category
    if book.book_category:
        related_books = Book.query.filter(
            Book.book_category == book.book_category,
            Book.is_published == True,
            Book.id != book.id
        ).order_by(desc(Book.created_at)).limit(4).all()

    # If not enough, get books by same authors
    if len(related_books) < 4 and book.authors:
        author_books = Book.query.filter(
            Book.authors.any(Author.id.in_([a.id for a in book.authors])),
            Book.is_published == True,
            Book.id != book.id,
            ~Book.id.in_([b.id for b in related_books])
        ).order_by(desc(Book.created_at)).limit(4 - len(related_books)).all()
        related_books.extend(author_books)

    # If still not enough, get recent books
    if len(related_books) < 4:
        recent_books = Book.query.filter(
            Book.is_published == True,
            Book.id != book.id,
            ~Book.id.in_([b.id for b in related_books])
        ).order_by(desc(Book.created_at)).limit(4 - len(related_books)).all()
        related_books.extend(recent_books)

    # Get books in same collections
    collection_books = []
    for collection in book.collections:
        collection_books.extend([
            b for b in collection.books
            if b.is_published and b.id != book.id
        ])
    # Remove duplicates and limit
    collection_books = list(set(collection_books))[:4]

    return render_template(
        'library/book_detail.html',
        book=book,
        reviews=reviews,
        rating_breakdown=rating_breakdown,
        related_books=related_books,
        collection_books=collection_books
    )

@bp.route('/book/<slug>/review', methods=['POST'])
def add_review(slug):
    """Add review to a book"""
    book = Book.query.filter_by(slug=slug, is_published=True).first_or_404()

    if not book.allow_reviews:
        flash('Les avis sont désactivés pour ce livre.', 'error')
        return redirect(url_for('library.book_detail', slug=slug))

    # Get form data
    reviewer_name = request.form.get('reviewer_name', '').strip()
    reviewer_email = request.form.get('reviewer_email', '').strip()
    reviewer_location = request.form.get('reviewer_location', '').strip()
    reviewer_occupation = request.form.get('reviewer_occupation', '').strip()
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    rating = request.form.get('rating', type=int)
    pros = request.form.get('pros', '').strip()
    cons = request.form.get('cons', '').strip()

    # Basic validation
    errors = []
    if not reviewer_name:
        errors.append('Le nom est requis')
    if not reviewer_email:
        errors.append("L'email est requis")
    if not content:
        errors.append("Le contenu de l'avis est requis")
    if not rating or rating < 1 or rating > 5:
        errors.append('Une note entre 1 et 5 étoiles est requise')

    if errors:
        for error in errors:
            flash(error, 'error')
        return redirect(url_for('library.book_detail', slug=slug) + '#review-form')

    # Check if user already reviewed this book
    existing_review = BookReview.query.filter_by(
        book=book,
        reviewer_email=reviewer_email
    ).first()

    if existing_review:
        flash('Vous avez déjà donné votre avis sur ce livre.', 'error')
        return redirect(url_for('library.book_detail', slug=slug))

    # Create review
    review = BookReview(
        book=book,
        reviewer_name=reviewer_name,
        reviewer_email=reviewer_email,
        reviewer_location=reviewer_location,
        reviewer_occupation=reviewer_occupation,
        title=title,
        content=content,
        rating=rating,
        pros=pros,
        cons=cons,
        is_approved=False  # Require moderation
    )

    try:
        db.session.add(review)
        db.session.commit()
        flash('Votre avis a été soumis et sera publié après modération.', 'success')
    except Exception as e:
        db.session.rollback()
        flash("Une erreur est survenue lors de l'ajout de votre avis.", 'error')

    return redirect(url_for('library.book_detail', slug=slug))

@bp.route('/authors')
def authors():
    """Authors listing page"""
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '').strip()
    nationality = request.args.get('nationality')
    sort_by = request.args.get('sort', 'name')  # name, books, popular

    # Base query
    query = Author.query

    # Apply filters
    if search_query:
        query = query.filter(
            db.or_(
                Author.name.contains(search_query),
                Author.biography.contains(search_query)
            )
        )

    if nationality:
        query = query.filter_by(nationality=nationality)

    # Apply sorting
    if sort_by == 'books':
        # Sort by number of books (requires subquery)
        query = query.outerjoin(Author.books).group_by(Author.id).order_by(
            desc(func.count(Book.id))
        )
    elif sort_by == 'popular':
        query = query.order_by(desc(Author.profile_views))
    else:  # name (default)
        query = query.order_by(Author.name)

    authors = query.paginate(
        page=page,
        per_page=20,
        error_out=False
    )

    # Get nationality list for filter
    nationalities = db.session.query(Author.nationality).filter(
        Author.nationality.isnot(None)
    ).distinct().order_by(Author.nationality).all()
    nationality_list = [n[0] for n in nationalities if n[0]]

    return render_template(
        'library/authors.html',
        authors=authors,
        nationality_list=nationality_list,
        search_query=search_query,
        current_nationality=nationality,
        current_sort=sort_by
    )

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

    # Get book statistics
    total_books = len(books)
    total_views = sum(book.views for book in books)
    total_reviews = sum(book.review_count for book in books)
    avg_rating = sum(book.average_rating for book in books if book.average_rating) / max(1, len([b for b in books if b.average_rating]))

    # Get related authors (same nationality or similar works)
    related_authors = Author.query.filter(
        Author.nationality == author.nationality,
        Author.id != author.id
    ).limit(4).all()

    return render_template(
        'library/author_detail.html',
        author=author,
        books=books,
        stats={
            'total_books': total_books,
            'total_views': total_views,
            'total_reviews': total_reviews,
            'avg_rating': round(avg_rating, 1) if avg_rating else 0
        },
        related_authors=related_authors
    )

@bp.route('/categories')
def categories():
    """Book categories listing"""
    categories = BookCategory.query.order_by(BookCategory.sort_order, BookCategory.name).all()

    # Add book counts to categories
    category_data = []
    for category in categories:
        book_count = Book.query.filter_by(
            book_category=category,
            is_published=True
        ).count()

        recent_books = Book.query.filter_by(
            book_category=category,
            is_published=True
        ).order_by(desc(Book.created_at)).limit(3).all()

        category_data.append({
            'category': category,
            'book_count': book_count,
            'recent_books': recent_books
        })

    return render_template(
        'library/categories.html',
        category_data=category_data
    )

@bp.route('/search')
def search():
    """Library search"""
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all')  # all, books, authors
    page = request.args.get('page', 1, type=int)

    results = {'books': None, 'authors': None}

    if query and len(query) >= 2:
        if search_type in ['all', 'books']:
            books_query = Book.query.filter(
                Book.is_published == True,
                db.or_(
                    Book.title.contains(query),
                    Book.description.contains(query),
                    Book.abstract.contains(query),
                    Book.keywords.contains(query)
                )
            ).order_by(desc(Book.created_at))

            if search_type == 'books':
                results['books'] = books_query.paginate(
                    page=page,
                    per_page=current_app.config.get('BOOKS_PER_PAGE', 12),
                    error_out=False
                )
            else:
                results['books'] = books_query.limit(6).all()

        if search_type in ['all', 'authors']:
            authors_query = Author.query.filter(
                db.or_(
                    Author.name.contains(query),
                    Author.biography.contains(query)
                )
            ).order_by(Author.name)

            if search_type == 'authors':
                results['authors'] = authors_query.paginate(
                    page=page,
                    per_page=20,
                    error_out=False
                )
            else:
                results['authors'] = authors_query.limit(6).all()

    return render_template(
        'library/search.html',
        query=query,
        search_type=search_type,
        results=results
    )

def get_library_sidebar_data():
    """Get common sidebar data for library pages"""
    # Categories with book counts
    categories = db.session.query(
        BookCategory, func.count(Book.id).label('book_count')
    ).outerjoin(Book).filter(
        Book.is_published == True
    ).group_by(BookCategory.id).order_by(BookCategory.name).all()

    # Collections
    collections = Collection.query.order_by(Collection.sort_order, Collection.name).all()

    # Popular authors (by book views)
    popular_authors = db.session.query(
        Author, func.sum(Book.views).label('total_views')
    ).join(Book.authors).filter(
        Book.is_published == True
    ).group_by(Author.id).order_by(
        desc('total_views')
    ).limit(5).all()

    # Recent books
    recent_books = Book.query.filter_by(is_published=True).order_by(
        desc(Book.created_at)
    ).limit(5).all()

    # Publishers
    publishers = Publisher.query.filter_by(is_active=True).order_by(Publisher.name).all()

    return {
        'categories': categories,
        'collections': collections,
        'popular_authors': popular_authors,
        'recent_books': recent_books,
        'publishers': publishers
    }

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