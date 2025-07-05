from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from app.admin_panel import bp
from app.extensions import db, mail
from app.models import (
    User, Post, Comment, Category, Collection, Tag, ContactMessage, 
    NewsletterSubscriber, Author, Publisher, BookCategory, Book, 
    BookReview, Testimonial, LibraryStats, PresidentMessage, CommunicationCompany,
    AdminInviteToken, AdminActionLog
)
from datetime import datetime
import os
import uuid
from werkzeug.utils import secure_filename
from PIL import Image
from flask_mail import Message


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Accès refusé. Vous devez être administrateur.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


def general_manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_general_manager:
            flash('Accès refusé. Vous devez être General Manager.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not (current_user.is_manager or current_user.is_general_manager):
            flash('Accès refusé. Vous devez être Manager ou General Manager.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def save_image(file, folder_name):
    """Save uploaded image file and return the relative path"""
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{uuid.uuid4().hex}{ext}"
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], folder_name)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save the file
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # Resize image if it's too large (optional optimization)
        try:
            if ext.lower() in ['.jpg', '.jpeg', '.png']:
                with Image.open(file_path) as img:
                    # Resize if larger than 1200px width
                    if img.width > 1200:
                        ratio = 1200 / img.width
                        new_height = int(img.height * ratio)
                        img = img.resize((1200, new_height), Image.Resampling.LANCZOS)
                        img.save(file_path, optimize=True, quality=85)
        except Exception as e:
            print(f"Error resizing image: {e}")
        
        # Return relative path for database storage
        return f"/static/uploads/{folder_name}/{unique_filename}"
    return None


def delete_image(image_path):
    """Delete image file from filesystem"""
    if image_path:
        try:
            # Convert relative path to absolute path
            if image_path.startswith('/static/uploads/'):
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 
                                       image_path.replace('/static/uploads/', ''))
                if os.path.exists(file_path):
                    os.remove(file_path)
        except Exception as e:
            print(f"Error deleting image: {e}")


@bp.route('/')
@login_required
@admin_required
def dashboard():
    # Calculate statistics
    stats = {
        'total_books': Book.query.count(),
        'total_authors': Author.query.count(),
        'total_posts': Post.query.count(),
        'total_collections': Collection.query.count(),
        'total_users': User.query.count(),
        'total_testimonials': Testimonial.query.count(),
        'pending_testimonials': Testimonial.query.filter_by(is_active=False).count(),
        'contact_messages': ContactMessage.query.count(),
        'newsletter_subscribers': NewsletterSubscriber.query.count()
    }
    
    # Recent activity
    recent_books = Book.query.order_by(Book.created_at.desc()).limit(5).all()
    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
    recent_comments = Comment.query.order_by(Comment.created_at.desc()).limit(5).all()
    pending_testimonials = Testimonial.query.filter_by(is_active=False).order_by(Testimonial.created_at.desc()).limit(5).all()
    
    return render_template('admin_panel/dashboard.html',
                         stats=stats,
                         recent_books=recent_books,
                         recent_posts=recent_posts,
                         recent_comments=recent_comments,
                         pending_testimonials=pending_testimonials)


# Books Management
@bp.route('/books')
@login_required
@admin_required
def books():
    page = request.args.get('page', 1, type=int)
    books = Book.query.order_by(Book.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin_panel/books.html', books=books)


@bp.route('/books/new', methods=['GET', 'POST'])
@bp.route('/books/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_book():
    if request.method == 'POST':
        title = request.form.get('title')
        subtitle = request.form.get('subtitle')
        description = request.form.get('description')
        abstract = request.form.get('abstract')
        isbn_13 = request.form.get('isbn_13')
        isbn_10 = request.form.get('isbn_10')
        price = request.form.get('price', type=float)
        currency = request.form.get('currency', 'EUR')
        page_count = request.form.get('page_count', type=int)
        language = request.form.get('language', 'Français')
        publication_date = request.form.get('publication_date')
        publisher_id = request.form.get('publisher_id', type=int)
        book_category_id = request.form.get('book_category_id', type=int)
        author_ids = request.form.getlist('author_ids', type=int)
        collection_ids = request.form.getlist('collection_ids', type=int)
        
        try:
            # Handle cover image upload
            cover_image_path = None
            if 'cover_image' in request.files:
                cover_image_file = request.files['cover_image']
                if cover_image_file.filename:
                    cover_image_path = save_image(cover_image_file, 'books')
            
            # Create new book
            book = Book(
                title=title,
                subtitle=subtitle,
                description=description,
                abstract=abstract,
                isbn_13=isbn_13,
                isbn_10=isbn_10,
                price=price,
                currency=currency,
                page_count=page_count,
                language=language,
                publisher_id=publisher_id if publisher_id else None,
                book_category_id=book_category_id if book_category_id else None,
                cover_image=cover_image_path,
                availability_status='available',
                is_published=True,  # Automatically publish new books
                is_featured=True    # Automatically feature new books for homepage
            )
            
            if publication_date:
                book.publication_date = datetime.strptime(publication_date, '%Y-%m-%d').date()
            
            # Add authors
            for author_id in author_ids:
                author = Author.query.get(author_id)
                if author:
                    book.authors.append(author)
            
            # Add to collections
            for collection_id in collection_ids:
                collection = Collection.query.get(collection_id)
                if collection:
                    book.collections.append(collection)
            
            db.session.add(book)
            db.session.commit()
            
            flash(f'Livre "{title}" créé avec succès!', 'success')
            return redirect(url_for('admin_panel.books'))
            
        except Exception as e:
            db.session.rollback()
           
    
    # Get form data
    authors = Author.query.order_by(Author.name).all()
    publishers = Publisher.query.order_by(Publisher.name).all()
    categories = BookCategory.query.order_by(BookCategory.name).all()
    collections = Collection.query.order_by(Collection.name).all()
    
    return render_template('admin_panel/book_form.html',
                         authors=authors,
                         publishers=publishers,
                         categories=categories,
                         collections=collections)


@bp.route('/books/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_book(id):
    book = Book.query.get_or_404(id)
    
    if request.method == 'POST':
        book.title = request.form.get('title')
        book.subtitle = request.form.get('subtitle')
        book.description = request.form.get('description')
        book.abstract = request.form.get('abstract')
        book.isbn_13 = request.form.get('isbn_13')
        book.isbn_10 = request.form.get('isbn_10')
        book.price = request.form.get('price', type=float)
        book.currency = request.form.get('currency', 'EUR')
        book.page_count = request.form.get('page_count', type=int)
        book.language = request.form.get('language', 'Français')
        
        publication_date = request.form.get('publication_date')
        if publication_date:
            book.publication_date = datetime.strptime(publication_date, '%Y-%m-%d').date()
        
        book.publisher_id = request.form.get('publisher_id', type=int) or None
        book.book_category_id = request.form.get('book_category_id', type=int) or None
        
        # Handle cover image upload
        if 'cover_image' in request.files:
            cover_image_file = request.files['cover_image']
            if cover_image_file.filename:
                # Delete old image if exists
                if book.cover_image:
                    delete_image(book.cover_image)
                # Save new image
                book.cover_image = save_image(cover_image_file, 'books')
        
        # Update authors
        author_ids = request.form.getlist('author_ids', type=int)
        book.authors.clear()
        for author_id in author_ids:
            author = Author.query.get(author_id)
            if author:
                book.authors.append(author)
        
        # Update collections
        collection_ids = request.form.getlist('collection_ids', type=int)
        book.collections.clear()
        for collection_id in collection_ids:
            collection = Collection.query.get(collection_id)
            if collection:
                book.collections.append(collection)
        
        # Handle status flags
        book.is_featured = bool(request.form.get('is_featured'))
        book.is_published = bool(request.form.get('is_published', True))
        book.is_bestseller = bool(request.form.get('is_bestseller'))
        book.is_new_release = bool(request.form.get('is_new_release'))
        
        try:
            book.updated_at = datetime.utcnow()
            db.session.commit()
            flash(f'Livre "{book.title}" mis à jour avec succès!', 'success')
            return redirect(url_for('admin_panel.books'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la mise à jour: {str(e)}', 'danger')
    
    # Get form data
    authors = Author.query.order_by(Author.name).all()
    publishers = Publisher.query.order_by(Publisher.name).all()
    categories = BookCategory.query.order_by(BookCategory.name).all()
    collections = Collection.query.order_by(Collection.name).all()
    
    return render_template('admin_panel/book_form.html',
                         book=book,
                         authors=authors,
                         publishers=publishers,
                         categories=categories,
                         collections=collections)


@bp.route('/books/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_book(id):
    book = Book.query.get_or_404(id)
    title = book.title
    
    try:
        db.session.delete(book)
        db.session.commit()
        flash(f'Livre "{title}" supprimé avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression: {str(e)}', 'danger')
    
    return redirect(url_for('admin_panel.books'))


@bp.route('/featured-books')
@login_required
@admin_required
def featured_books():
    """Manage featured books for homepage carousel"""
    featured_books = Book.query.filter_by(
        is_published=True,
        is_featured=True
    ).order_by(Book.created_at.desc()).all()
    
    all_books = Book.query.filter_by(
        is_published=True
    ).order_by(Book.title).all()
    
    return render_template('admin_panel/featured_books.html',
                         featured_books=featured_books,
                         all_books=all_books)


@bp.route('/featured-books/update', methods=['POST'])
@login_required
@admin_required
def update_featured_books():
    """Update featured books selection"""
    try:
        # Get selected book IDs from form
        featured_book_ids = request.form.getlist('featured_books', type=int)
        if len(featured_book_ids) > 12:
            flash('Vous ne pouvez sélectionner que 12 livres vedettes au maximum.', 'danger')
            return redirect(url_for('admin_panel.featured_books'))
        # Remove featured status from all books
        Book.query.filter_by(is_featured=True).update({Book.is_featured: False})
        # Set featured status for selected books
        if featured_book_ids:
            Book.query.filter(Book.id.in_(featured_book_ids)).update(
                {Book.is_featured: True}, 
                synchronize_session=False
            )
        db.session.commit()
        flash(f'{len(featured_book_ids)} livres sélectionnés comme vedettes!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la mise à jour: {str(e)}', 'danger')
    return redirect(url_for('admin_panel.featured_books'))


# Authors Management
@bp.route('/authors')
@login_required
@admin_required
def authors():
    page = request.args.get('page', 1, type=int)
    authors = Author.query.order_by(Author.name).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin_panel/authors.html', authors=authors)


@bp.route('/authors/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_author():
    if request.method == 'POST':
        name = request.form.get('name')
        biography = request.form.get('biography')
        short_bio = request.form.get('short_bio')
        nationality = request.form.get('nationality')
        birth_date = request.form.get('birth_date')
        death_date = request.form.get('death_date')
        website = request.form.get('website')
        awards = request.form.get('awards')
        
        try:
            author = Author(
                name=name,
                biography=biography,
                short_bio=short_bio,
                nationality=nationality,
                website=website,
                awards=awards
            )
            
            if birth_date:
                author.birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
            if death_date:
                author.death_date = datetime.strptime(death_date, '%Y-%m-%d').date()
            
            db.session.add(author)
            db.session.commit()
            
            flash(f'Auteur "{name}" créé avec succès!', 'success')
            return redirect(url_for('admin_panel.authors'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création de l\'auteur: {str(e)}', 'danger')
    
    return render_template('admin_panel/author_form.html')


# Collections Management
@bp.route('/collections')
@login_required
@admin_required
def collections():
    collections = Collection.query.order_by(Collection.name).all()
    return render_template('admin_panel/collections.html', collections=collections)


@bp.route('/collections/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_collection():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        is_featured = bool(request.form.get('is_featured'))
        
        # Check if we already have 6 collections
        if Collection.query.count() >= 6:
            flash('Vous ne pouvez pas créer plus de 6 collections.', 'warning')
            return redirect(url_for('admin_panel.collections'))
        
        try:
            # Handle collection image upload
            image_path = None
            if 'image' in request.files:
                image_file = request.files['image']
                if image_file.filename:
                    image_path = save_image(image_file, 'collections')
            
            collection = Collection(
                name=name,
                description=description,
                is_featured=is_featured,
                image=image_path
            )
            
            db.session.add(collection)
            db.session.commit()
            
            flash(f'Collection "{name}" créée avec succès!', 'success')
            return redirect(url_for('admin_panel.collections'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création de la collection: {str(e)}', 'danger')
    
    return render_template('admin_panel/collection_form.html')


# Users Management  
@bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin_panel/users.html', users=users)


@bp.route('/users/<int:id>/toggle_admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('Vous ne pouvez pas modifier vos propres privilèges.', 'warning')
        return redirect(url_for('admin_panel.users'))
    old_status = user.is_admin
    user.is_admin = not user.is_admin
    db.session.commit()
    # Audit log
    action = 'promote_to_admin' if user.is_admin else 'demote_admin'
    log = AdminActionLog(
        action=action,
        performed_by_id=current_user.id,
        target_user_id=user.id,
        details=f"Admin status changed from {old_status} to {user.is_admin}"
    )
    db.session.add(log)
    db.session.commit()
    status = "accordé" if user.is_admin else "retiré"
    flash(f'Privilège administrateur {status} pour {user.full_name}.', 'success')
    return redirect(url_for('admin_panel.users'))


@bp.route('/users/<int:id>/toggle_manager', methods=['POST'])
@login_required
@admin_required
def toggle_manager(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('Vous ne pouvez pas modifier vos propres privilèges.', 'warning')
        return redirect(url_for('admin_panel.users'))
    old_status = user.is_manager
    user.is_manager = not user.is_manager
    db.session.commit()
    # Audit log
    action = 'promote_to_manager' if user.is_manager else 'demote_manager'
    log = AdminActionLog(
        action=action,
        performed_by_id=current_user.id,
        target_user_id=user.id,
        details=f"Manager status changed from {old_status} to {user.is_manager}"
    )
    db.session.add(log)
    db.session.commit()
    status = "accordé" if user.is_manager else "retiré"
    flash(f'Privilège manager {status} pour {user.full_name}.', 'success')
    return redirect(url_for('admin_panel.users'))


@bp.route('/users/<int:id>/toggle_general_manager', methods=['POST'])
@login_required
@general_manager_required
def toggle_general_manager(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('Vous ne pouvez pas modifier vos propres privilèges.', 'warning')
        return redirect(url_for('admin_panel.users'))
    old_status = user.is_general_manager
    user.is_general_manager = not user.is_general_manager
    db.session.commit()
    # Audit log
    action = 'promote_to_general_manager' if user.is_general_manager else 'demote_general_manager'
    log = AdminActionLog(
        action=action,
        performed_by_id=current_user.id,
        target_user_id=user.id,
        details=f"General Manager status changed from {old_status} to {user.is_general_manager}"
    )
    db.session.add(log)
    db.session.commit()
    status = "accordé" if user.is_general_manager else "retiré"
    flash(f'Privilège General Manager {status} pour {user.full_name}.', 'success')
    return redirect(url_for('admin_panel.users'))


@bp.route('/promote-user-to-admin', methods=['POST'])
@login_required
def promote_user_to_admin():
    if not current_user.is_general_manager:
        flash("Accès refusé. Seul le General Admin peut promouvoir un admin.", "danger")
        return redirect(url_for('admin_panel.dashboard'))
    email = request.form.get('email', '').strip().lower()
    if not email:
        flash("Veuillez fournir une adresse email.", "danger")
        return redirect(url_for('admin_panel.dashboard'))
    user = User.query.filter_by(email=email).first()
    if not user:
        flash("Aucun utilisateur trouvé avec cet email.", "danger")
        return redirect(url_for('admin_panel.dashboard'))
    if user.id == current_user.id:
        flash("Vous ne pouvez pas vous promouvoir vous-même.", "warning")
        return redirect(url_for('admin_panel.dashboard'))
    if user.is_admin:
        flash("Cet utilisateur est déjà administrateur.", "info")
        return redirect(url_for('admin_panel.dashboard'))
    user.is_admin = True
    db.session.commit()
    # Audit log
    log = AdminActionLog(
        action='promote_to_admin',
        performed_by_id=current_user.id,
        target_user_id=user.id,
        details=f"Promoted {user.email} to admin via promote_user_to_admin"
    )
    db.session.add(log)
    db.session.commit()
    flash(f"{user.full_name or user.email} est maintenant administrateur!", "success")
    return redirect(url_for('admin_panel.dashboard'))


# Testimonials Management
@bp.route('/testimonials')
@login_required
@admin_required
def testimonials():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')
    
    # Filter testimonials based on status
    if status == 'pending':
        query = Testimonial.query.filter_by(is_active=False)
    elif status == 'approved':
        query = Testimonial.query.filter_by(is_active=True)
    else:
        query = Testimonial.query
    
    testimonials = query.order_by(Testimonial.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Calculate counts for template
    all_count = Testimonial.query.count()
    pending_count = Testimonial.query.filter_by(is_active=False).count()
    approved_count = Testimonial.query.filter_by(is_active=True).count()
    
    return render_template('admin_panel/testimonials.html', 
                         testimonials=testimonials,
                         status=status,
                         all_count=all_count,
                         pending_count=pending_count,
                         approved_count=approved_count)


@bp.route('/testimonials/<int:id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_testimonial(id):
    testimonial = Testimonial.query.get_or_404(id)
    testimonial.is_active = True
    testimonial.approved_at = datetime.utcnow()
    db.session.commit()
    
    flash('Témoignage approuvé avec succès!', 'success')
    return redirect(url_for('admin_panel.testimonials'))


@bp.route('/testimonials/<int:id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_testimonial(id):
    testimonial = Testimonial.query.get_or_404(id)
    db.session.delete(testimonial)
    db.session.commit()
    
    flash('Témoignage rejeté et supprimé.', 'info')
    return redirect(url_for('admin_panel.testimonials'))


@bp.route('/testimonials/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_testimonial(id):
    testimonial = Testimonial.query.get_or_404(id)
    db.session.delete(testimonial)
    db.session.commit()
    
    flash('Témoignage supprimé avec succès!', 'success')
    return redirect(url_for('admin_panel.testimonials'))


@bp.route('/collections/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_collection(id):
    collection = Collection.query.get_or_404(id)
    collection_name = collection.name
    
    # Check if collection has books
    if collection.books:
        flash(f'Impossible de supprimer la collection "{collection_name}" : elle contient des livres.', 'warning')
        return redirect(url_for('admin_panel.collections'))
    
    db.session.delete(collection)
    db.session.commit()
    
    flash(f'Collection "{collection_name}" supprimée avec succès!', 'success')
    return redirect(url_for('admin_panel.collections'))


@bp.route('/authors/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_author(id):
    author = Author.query.get_or_404(id)
    author_name = author.name
    
    # Check if author has books
    if author.books:
        flash(f'Impossible de supprimer l\'auteur "{author_name}" : il/elle a des livres associés.', 'warning')
        return redirect(url_for('admin_panel.authors'))
    
    db.session.delete(author)
    db.session.commit()
    
    flash(f'Auteur "{author_name}" supprimé avec succès!', 'success')
    return redirect(url_for('admin_panel.authors'))


@bp.route('/collections/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_collection(id):
    collection = Collection.query.get_or_404(id)
    
    if request.method == 'POST':
        collection.name = request.form.get('name')
        collection.description = request.form.get('description')
        collection.is_featured = bool(request.form.get('is_featured'))
        
        # Handle collection image upload
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file.filename:
                # Delete old image if exists
                if collection.image:
                    delete_image(collection.image)
                # Save new image
                collection.image = save_image(image_file, 'collections')
        
        db.session.commit()
        flash(f'Collection "{collection.name}" mise à jour avec succès!', 'success')
        return redirect(url_for('admin_panel.collections'))
    
    return render_template('admin_panel/collection_form.html', collection=collection)


@bp.route('/authors/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_author(id):
    author = Author.query.get_or_404(id)
    
    if request.method == 'POST':
        author.name = request.form.get('name')
        author.biography = request.form.get('biography')
        author.nationality = request.form.get('nationality')
        author.website = request.form.get('website')
        author.photo = request.form.get('photo')
        
        birth_date = request.form.get('birth_date')
        if birth_date:
            author.birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
            
        death_date = request.form.get('death_date')
        if death_date:
            author.death_date = datetime.strptime(death_date, '%Y-%m-%d').date()
        
        db.session.commit()
        flash(f'Auteur "{author.name}" mis à jour avec succès!', 'success')
        return redirect(url_for('admin_panel.authors'))
    
    return render_template('admin_panel/author_form.html', author=author)


# Blog Management
@bp.route('/posts')
@login_required
@admin_required
def posts():
    """List all blog posts"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')
    
    # Filter posts based on status
    query = Post.query
    if status == 'published':
        query = query.filter_by(published=True)
    elif status == 'draft':
        query = query.filter_by(published=False)
    
    posts = query.order_by(Post.created_at.desc()).paginate(
        page=page,
        per_page=20,
        error_out=False
    )
    
    return render_template('admin_panel/posts.html', posts=posts, current_status=status)

@bp.route('/posts/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_post():
    """Create a new blog post"""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        excerpt = request.form.get('excerpt')
        category_id = request.form.get('category_id', type=int)
        published = bool(request.form.get('published'))
        is_featured = bool(request.form.get('is_featured'))
        allow_comments = bool(request.form.get('allow_comments', True))
        
        try:
            # Handle featured image upload
            featured_image_path = None
            if 'featured_image' in request.files:
                featured_image_file = request.files['featured_image']
                if featured_image_file.filename:
                    featured_image_path = save_image(featured_image_file, 'posts')
            
            # Create new post
            post = Post(
                title=title,
                content=content,
                excerpt=excerpt if excerpt else None,
                author=current_user,
                category_id=category_id if category_id else None,
                published=published,
                is_featured=is_featured,
                allow_comments=allow_comments,
                featured_image=featured_image_path,
                published_at=datetime.utcnow() if published else None
            )
            
            db.session.add(post)
            db.session.commit()
            
            flash(f'Article "{title}" créé avec succès!', 'success')
            return redirect(url_for('admin_panel.posts'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création de l\'article: {str(e)}', 'danger')
    
    # Get categories for form
    categories = Category.query.order_by(Category.name).all()
    
    return render_template('admin_panel/post_form.html', 
                         categories=categories)

@bp.route('/posts/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_post(id):
    """Edit a blog post"""
    post = Post.query.get_or_404(id)
    
    if request.method == 'POST':
        post.title = request.form.get('title')
        post.content = request.form.get('content')
        post.excerpt = request.form.get('excerpt')
        post.category_id = request.form.get('category_id', type=int) or None
        post.published = bool(request.form.get('published'))
        post.is_featured = bool(request.form.get('is_featured'))
        post.allow_comments = bool(request.form.get('allow_comments', True))
        
        # Handle featured image upload
        if 'featured_image' in request.files:
            featured_image_file = request.files['featured_image']
            if featured_image_file.filename:
                # Delete old image if exists
                if post.featured_image:
                    delete_image(post.featured_image)
                # Save new image
                post.featured_image = save_image(featured_image_file, 'posts')
        
        # Update published_at if publishing for the first time
        if post.published and not post.published_at:
            post.published_at = datetime.utcnow()
        
        try:
            post.updated_at = datetime.utcnow()
            db.session.commit()
            flash(f'Article "{post.title}" mis à jour avec succès!', 'success')
            return redirect(url_for('admin_panel.posts'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la mise à jour: {str(e)}', 'danger')
    
    # Get categories for form
    categories = Category.query.order_by(Category.name).all()
    
    return render_template('admin_panel/post_form.html',
                         post=post,
                         categories=categories)

@bp.route('/posts/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_post(id):
    """Delete a blog post"""
    post = Post.query.get_or_404(id)
    
    try:
        # Delete associated image if exists
        if post.featured_image:
            delete_image(post.featured_image)
        
        # Delete associated comments
        Comment.query.filter_by(post_id=id).delete()
        
        db.session.delete(post)
        db.session.commit()
        flash(f'Article "{post.title}" supprimé avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression: {str(e)}', 'danger')
    
    return redirect(url_for('admin_panel.posts'))

@bp.route('/comments')
@login_required
@admin_required
def comments():
    """Manage blog comments"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')
    
    # Filter comments based on status
    query = Comment.query
    if status == 'pending':
        query = query.filter_by(approved=False, is_spam=False)
    elif status == 'approved':
        query = query.filter_by(approved=True)
    elif status == 'spam':
        query = query.filter_by(is_spam=True)
    
    comments = query.order_by(Comment.created_at.desc()).paginate(
        page=page,
        per_page=20,
        error_out=False
    )
    
    return render_template('admin_panel/comments.html', 
                         comments=comments, 
                         current_status=status)

@bp.route('/comments/<int:id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_comment(id):
    """Approve a comment"""
    comment = Comment.query.get_or_404(id)
    comment.approved = True
    comment.is_spam = False
    
    db.session.commit()
    flash('Commentaire approuvé avec succès!', 'success')
    return redirect(url_for('admin_panel.comments'))

@bp.route('/comments/<int:id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_comment(id):
    """Reject a comment (mark as spam)"""
    comment = Comment.query.get_or_404(id)
    comment.approved = False
    comment.is_spam = True
    
    db.session.commit()
    flash('Commentaire rejeté avec succès!', 'success')
    return redirect(url_for('admin_panel.comments'))

@bp.route('/comments/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_comment(id):
    """Delete a comment"""
    comment = Comment.query.get_or_404(id)
    
    try:
        db.session.delete(comment)
        db.session.commit()
        flash('Commentaire supprimé avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression: {str(e)}', 'danger')
    
    return redirect(url_for('admin_panel.comments'))

@bp.route('/president-message/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_president_message():
    """View and edit the President's Message"""
    message = PresidentMessage.query.first()
    if not message:
        # Create a default message if none exists
        message = PresidentMessage(content="", updated_at=datetime.utcnow())
        db.session.add(message)
        db.session.commit()

    if request.method == 'POST':
        content = request.form.get('content', '')
        message.content = content
        message.updated_at = datetime.utcnow()
        try:
            db.session.commit()
            flash("Message du Président mis à jour avec succès!", 'success')
            return redirect(url_for('admin_panel.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la mise à jour: {str(e)}", 'danger')

    return render_template('admin_panel/president_message_form.html', message=message)


# Communication Companies Management
@bp.route('/communication-companies')
@login_required
@admin_required
def communication_companies():
    companies = CommunicationCompany.query.order_by(CommunicationCompany.date_accompanied.desc()).all()
    return render_template('admin_panel/communication_companies.html', companies=companies)

@bp.route('/communication-company/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_communication_company():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        logo = request.form.get('logo', '').strip()
        description = request.form.get('description', '').strip()
        website = request.form.get('website', '').strip()
        date_accompanied = request.form.get('date_accompagned')
        if date_accompanied:
            from datetime import datetime
            date_accompagned = datetime.strptime(date_accompagned, '%Y-%m-%d').date()
        else:
            date_accompagned = None
        # TODO: handle file upload for logo if needed
        company = CommunicationCompany(
            name=name,
            logo=logo,
            description=description,
            website=website,
            date_accompagned=date_accompagned
        )
        db.session.add(company)
        db.session.commit()
        flash('Entreprise ajoutée avec succès!', 'success')
        return redirect(url_for('admin_panel.communication_companies'))
    return render_template('admin_panel/communication_company_form.html', company=None)

@bp.route('/communication-company/<int:company_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_communication_company(company_id):
    company = CommunicationCompany.query.get_or_404(company_id)
    if request.method == 'POST':
        company.name = request.form.get('name', '').strip()
        company.logo = request.form.get('logo', '').strip()
        company.description = request.form.get('description', '').strip()
        company.website = request.form.get('website', '').strip()
        date_accompagned = request.form.get('date_accompagned')
        if date_accompagned:
            from datetime import datetime
            company.date_accompagned = datetime.strptime(date_accompagned, '%Y-%m-%d').date()
        else:
            company.date_accompagned = None
        db.session.commit()
        flash('Entreprise modifiée avec succès!', 'success')
        return redirect(url_for('admin_panel.communication_companies'))
    return render_template('admin_panel/communication_company_form.html', company=company)

@bp.route('/communication-company/<int:company_id>/delete')
@login_required
@admin_required
def delete_communication_company(company_id):
    company = CommunicationCompany.query.get_or_404(company_id)
    db.session.delete(company)
    db.session.commit()
    flash('Entreprise supprimée avec succès!', 'success')
    return redirect(url_for('admin_panel.communication_companies'))

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
@admin_required
def profile():
    user = current_user
    if request.method == 'POST':
        # Update profile info
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        bio = request.form.get('bio', '').strip()
        avatar_file = request.files.get('avatar')
        password = request.form.get('password', '')
        password2 = request.form.get('password2', '')
        errors = []

        # Update first and last name
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        user.bio = bio

        # Handle avatar upload
        if avatar_file and avatar_file.filename:
            avatar_path = save_image(avatar_file, 'avatars')
            if avatar_path:
                # Delete old avatar if exists
                if user.avatar:
                    delete_image(user.avatar)
                user.avatar = avatar_path
            else:
                errors.append("Format d'image non autorisé.")

        # Handle password change
        if password or password2:
            if not password or not password2:
                errors.append("Veuillez remplir les deux champs de mot de passe.")
            elif password != password2:
                errors.append("Les mots de passe ne correspondent pas.")
            elif len(password) < 8:
                errors.append("Le mot de passe doit contenir au moins 8 caractères.")
            else:
                user.set_password(password)

        if errors:
            for error in errors:
                flash(error, 'danger')
        else:
            try:
                db.session.commit()
                flash("Profil mis à jour avec succès!", 'success')
                return redirect(url_for('admin_panel.profile'))
            except Exception as e:
                db.session.rollback()
                flash(f"Erreur lors de la mise à jour: {str(e)}", 'danger')

    return render_template('admin_panel/profile.html', user=user)


# Admin Tokens Management
@bp.route('/admin-tokens', methods=['GET', 'POST'])
@login_required
def admin_tokens():
    if not current_user.is_general_manager:
        flash("Accès refusé. Seul le General Admin peut générer des tokens.", "danger")
        return redirect(url_for('admin_panel.dashboard'))
    if request.method == 'POST':
        # Generate a new token
        token_obj = AdminInviteToken.generate_token()
        db.session.add(token_obj)
        db.session.commit()
        flash("Token généré avec succès!", "success")
        return redirect(url_for('admin_panel.admin_tokens'))
    # Show all valid tokens
    tokens = AdminInviteToken.query.order_by(AdminInviteToken.created_at.desc()).all()
    return render_template('admin_panel/admin_tokens.html', tokens=tokens)

@bp.route('/redeem-admin-token', methods=['GET', 'POST'])
@login_required
def redeem_admin_token():
    if current_user.is_admin:
        flash("Vous êtes déjà administrateur.", "info")
        return redirect(url_for('admin_panel.dashboard'))
    if request.method == 'POST':
        token_str = request.form.get('token', '').strip()
        token_obj = AdminInviteToken.query.filter_by(token=token_str).first()
        if not token_obj or not token_obj.is_valid():
            flash("Token invalide ou expiré.", "danger")
        else:
            token_obj.used = True
            token_obj.used_by = current_user.id
            current_user.is_admin = True
            db.session.commit()
            flash("Vous êtes maintenant administrateur!", "success")
            return redirect(url_for('admin_panel.dashboard'))
    return render_template('admin_panel/redeem_admin_token.html')

@bp.route('/send-admin-invite', methods=['POST'])
@login_required
def send_admin_invite():
    if not current_user.is_general_manager:
        flash("Accès refusé. Seul le General Admin peut inviter un admin.", "danger")
        return redirect(url_for('admin_panel.dashboard'))
    email = request.form.get('email', '').strip()
    from app.main.routes import is_valid_email
    if not email or not is_valid_email(email):
        flash("Adresse email invalide.", "danger")
        return redirect(url_for('admin_panel.dashboard'))
    # Generate token
    token_obj = AdminInviteToken.generate_token()
    db.session.add(token_obj)
    db.session.commit()
    # Send email
    try:
        invite_url = url_for('admin_panel.redeem_admin_token', _external=True)
        msg = Message(
            subject="Invitation à devenir administrateur ELMA Group",
            recipients=[email],
            body=f"Bonjour,\n\nVous avez été invité à devenir administrateur sur ELMA Group.\n\nUtilisez ce token : {token_obj.token}\nOu cliquez sur ce lien : {invite_url}\n\nCe token est valable 24h et utilisable une seule fois.\n\nCordialement,\nL'équipe ELMA Group"
        )
        mail.send(msg)
        flash(f"Invitation envoyée à {email}.", "success")
    except Exception as e:
        flash(f"Erreur lors de l'envoi de l'email: {str(e)}", "danger")
    return redirect(url_for('admin_panel.dashboard'))

@bp.route('/admin-logs')
@login_required
def admin_logs():
    if not current_user.is_general_manager:
        flash("Accès refusé. Seul le General Admin peut voir le journal des actions.", "danger")
        return redirect(url_for('admin_panel.dashboard'))
    page = request.args.get('page', 1, type=int)
    logs = AdminActionLog.query.order_by(AdminActionLog.timestamp.desc()).paginate(page=page, per_page=30, error_out=False)
    return render_template('admin_panel/admin_logs.html', logs=logs)
