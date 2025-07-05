from flask import render_template, request, flash, redirect, url_for, current_app
from app.testimonials import bp
from app.models import Testimonial, Book, Collection
from app.extensions import db
from datetime import datetime
import re
import os
import uuid
from werkzeug.utils import secure_filename
from PIL import Image


def allowed_file(filename):
    """Check if the file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
                    # Resize if larger than 400px width for profile pictures
                    if img.width > 400:
                        ratio = 400 / img.width
                        new_height = int(img.height * ratio)
                        img = img.resize((400, new_height), Image.Resampling.LANCZOS)
                        img.save(file_path, optimize=True, quality=85)
        except Exception as e:
            print(f"Error resizing image: {e}")
        
        # Return relative path for database storage
        return f"/static/uploads/{folder_name}/{unique_filename}"
    return None

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
    
    return render_template('testimonials/index.html',
                         testimonials=testimonials,
                         featured_testimonials=featured_testimonials,
                         category_list=category_list,
                         current_category=category)

@bp.route('/submit', methods=['GET', 'POST'])
def submit():
    """Submit testimonial form"""
    if request.method == 'POST':
        # Get form data
        quote = request.form.get('quote', '').strip()
        display_name = request.form.get('display_name', '').strip()
        email = request.form.get('email', '').strip()
        category = request.form.get('category', '').strip()
        display_title = request.form.get('display_title', '').strip()
        company = request.form.get('company', '').strip()
        location = request.form.get('location', '').strip()
        context = request.form.get('context', '').strip()
        rating = request.form.get('rating', type=int)
        can_use_name = bool(request.form.get('can_use_name'))
        can_use_title = bool(request.form.get('can_use_title'))
        can_use_photo = bool(request.form.get('can_use_photo'))
        
        # Basic validation
        errors = []
        if not quote or len(quote) < 10:
            errors.append('Le témoignage doit contenir au moins 10 caractères')
        if not display_name:
            errors.append('Le nom est requis')
        if not email or not is_valid_email(email):
            errors.append('Une adresse email valide est requise')
        if not category:
            errors.append('Veuillez sélectionner une catégorie')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('testimonials/submit.html')
        
        # Handle photo upload
        photo_path = None
        if 'photo' in request.files:
            photo_file = request.files['photo']
            if photo_file.filename:
                photo_path = save_image(photo_file, 'testimonials')
        
        # Create testimonial
        testimonial = Testimonial(
            quote=quote,
            display_name=display_name,
            email=email,
            category=category,
            display_title=display_title if display_title else None,
            company=company if company else None,
            location=location if location else None,
            context=context if context else None,
            rating=rating if rating else None,
            photo=photo_path,
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
            flash('Une erreur est survenue lors de l\'envoi de votre témoignage.', 'error')
    
    return render_template('testimonials/submit.html')

def is_valid_email(email):
    """Simple email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Testimonials-specific template filters
@bp.app_template_filter('testimonial_excerpt')
def testimonial_excerpt_filter(text, length=100):
    """Create excerpt from testimonial"""
    if len(text) <= length:
        return text
    return text[:length].rsplit(' ', 1)[0] + '...'
