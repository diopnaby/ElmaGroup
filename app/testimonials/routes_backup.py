from flask import render_template, request, flash, redirect, url_for, current_app
from app.testimonials import bp
from app.models import Testimonial, Book, Collection
from app.extensions import db
from datetime import datetime
import re


@bp.route('/')
@bp.route('/index')
def index():
    """Testimonials listing page"""
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category')

    # Base query for active testimonials
    query = Testimonial.query.filter_by(is_active=True)

    # Apply category filter
    if category:
        query = query.filter_by(category=category)

    # Order by featured first, then by creation date
    query = query.order_by(
        Testimonial.is_featured.desc(),
        Testimonial.created_at.desc()
    )

    testimonials = query.paginate(
        page=page,
        per_page=current_app.config.get('TESTIMONIALS_PER_PAGE', 9),
        error_out=False
    )

    # Get featured testimonials for top of page
    featured_testimonials = Testimonial.query.filter_by(
        is_active=True,
        is_featured=True
    ).order_by(Testimonial.created_at.desc()).limit(3).all()

    # Get available categories
    categories = db.session.query(Testimonial.category).filter(
        Testimonial.is_active == True,
        Testimonial.category.isnot(None)
    ).distinct().all()
    category_list = [c[0] for c in categories if c[0]]

    # Statistics
    stats = {
        'total_testimonials': Testimonial.query.filter_by(is_active=True).count(),
        'verified_testimonials': Testimonial.query.filter_by(is_active=True, is_verified=True).count(),
        'categories_count': len(category_list)
    }

    return render_template(
        'testimonials/index.html',
        testimonials=testimonials,
        featured_testimonials=featured_testimonials,
        category_list=category_list,
        current_category=category,
        stats=stats
    )


@bp.route('/submit', methods=['GET', 'POST'])
def submit():
    """Submit testimonial form"""
    if request.method == 'POST':
        # Get form data
        quote = request.form.get('quote', '').strip()
        display_name = request.form.get('display_name', '').strip()
        display_title = request.form.get('display_title', '').strip()
        company = request.form.get('company', '').strip()
        location = request.form.get('location', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        category = request.form.get('category', '').strip()
        context = request.form.get('context', '').strip()
        rating = request.form.get('rating', type=int)
        book_id = request.form.get('book_id', type=int) if request.form.get('book_id') else None
        collection_id = request.form.get('collection_id', type=int) if request.form.get('collection_id') else None

        # Permission checkboxes
        can_use_name = bool(request.form.get('can_use_name'))
        can_use_title = bool(request.form.get('can_use_title'))
        can_use_photo = bool(request.form.get('can_use_photo'))

        # Basic validation
        errors = []
        if not quote or len(quote) < 10:
            errors.append('Le témoignage doit contenir au moins 10 caractères')
        if len(quote) > 1000:
            errors.append('Le témoignage ne peut pas dépasser 1000 caractères')
        if not display_name:
            errors.append('Le nom est requis')
        if not email or not is_valid_email(email):
            errors.append('Une adresse email valide est requise')
        if not category:
            errors.append('Veuillez sélectionner une catégorie')
        if rating and (rating < 1 or rating > 5):
            errors.append('La note doit être entre 1 et 5 étoiles')

        # Check for spam
        if is_likely_spam(quote, display_name, email):
            errors.append('Votre témoignage a été marqué comme spam')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template(
                'testimonials/submit.html',
                books=get_books_for_select(),
                collections=get_collections_for_select(),
                form_data=request.form
            )

        # Create testimonial
        testimonial = Testimonial(
            quote=quote,
            display_name=display_name,
            display_title=display_title,
            company=company,
            location=location,
            email=email,
            phone=phone,
            category=category,
            context=context,
            rating=rating,
            book_id=book_id,
            collection_id=collection_id,
            can_use_name=can_use_name,
            can_use_title=can_use_title,
            can_use_photo=can_use_photo,
            is_active=False  # Require approval
        )

        try:
            db.session.add(testimonial)
            db.session.commit()
            flash('Votre témoignage a été soumis avec succès! Il sera publié après modération.', 'success')
            return redirect(url_for('testimonials.submit'))
        except Exception as e:
            db.session.rollback()
            flash("Une erreur est survenue lors de l'envoi de votre témoignage.", 'error')

    return render_template(
        'testimonials/submit.html',
        books=get_books_for_select(),
        collections=get_collections_for_select()
    )


@bp.route('/category/<category>')
def category(category):
    """Testimonials by category"""
    page = request.args.get('page', 1, type=int)

    testimonials = Testimonial.query.filter_by(
        is_active=True,
        category=category
    ).order_by(
        Testimonial.is_featured.desc(),
        Testimonial.created_at.desc()
    ).paginate(
        page=page,
        per_page=current_app.config.get('TESTIMONIALS_PER_PAGE', 9),
        error_out=False
    )

    # Get category statistics
    category_stats = {
        'total': Testimonial.query.filter_by(is_active=True, category=category).count(),
        'verified': Testimonial.query.filter_by(is_active=True, category=category, is_verified=True).count(),
        'featured': Testimonial.query.filter_by(is_active=True, category=category, is_featured=True).count()
    }

    # Get all categories for navigation
    categories = db.session.query(Testimonial.category).filter(
        Testimonial.is_active == True,
        Testimonial.category.isnot(None)
    ).distinct().all()
    category_list = [c[0] for c in categories if c[0]]

    return render_template(
        'testimonials/category.html',
        testimonials=testimonials,
        current_category=category,
        category_list=category_list,
        category_stats=category_stats
    )


@bp.route('/book/<int:book_id>')
def book_testimonials(book_id):
    """Testimonials for a specific book"""
    book = Book.query.get_or_404(book_id)
    page = request.args.get('page', 1, type=int)

    testimonials = Testimonial.query.filter_by(
        is_active=True,
        book_id=book_id
    ).order_by(
        Testimonial.is_featured.desc(),
        Testimonial.created_at.desc()
    ).paginate(
        page=page,
        per_page=current_app.config.get('TESTIMONIALS_PER_PAGE', 9),
        error_out=False
    )

    return render_template(
        'testimonials/book_testimonials.html',
        testimonials=testimonials,
        book=book
    )


@bp.route('/collection/<int:collection_id>')
def collection_testimonials(collection_id):
    """Testimonials for a specific collection"""
    collection = Collection.query.get_or_404(collection_id)
    page = request.args.get('page', 1, type=int)

    testimonials = Testimonial.query.filter_by(
        is_active=True,
        collection_id=collection_id
    ).order_by(
        Testimonial.is_featured.desc(),
        Testimonial.created_at.desc()
    ).paginate(
        page=page,
        per_page=current_app.config.get('TESTIMONIALS_PER_PAGE', 9),
        error_out=False
    )

    return render_template(
        'testimonials/collection_testimonials.html',
        testimonials=testimonials,
        collection=collection
    )


def get_books_for_select():
    """Get books for select dropdown"""
    return Book.query.filter_by(is_published=True).order_by(Book.title).all()


def get_collections_for_select():
    """Get collections for select dropdown"""
    return Collection.query.order_by(Collection.name).all()


def is_valid_email(email):
    """Simple email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_likely_spam(content, name, email):
    """Basic spam detection for testimonials"""
    spam_patterns = [
        r'\b(viagra|cialis|pharmacy|casino|poker|loan|mortgage)\b',
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
        r'\b\w+\.(com|net|org|ru|cn)\b',
    ]

    text_to_check = f"{content} {name} {email}".lower()

    for pattern in spam_patterns:
        if re.search(pattern, text_to_check, re.IGNORECASE):
            return True

    # Check for excessive repetition
    words = content.lower().split()
    if len(words) > 5:
        unique_words = set(words)
        if len(unique_words) / len(words) < 0.3:  # Less than 30% unique words
            return True

    return False


# Testimonials-specific template filters
@bp.app_template_filter('testimonial_excerpt')
def testimonial_excerpt_filter(text, length=100):
    """Create excerpt from testimonial"""
    if len(text) <= length:
        return text
    return text[:length].rsplit(' ', 1)[0] + '...'