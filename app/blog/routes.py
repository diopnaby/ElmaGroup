from flask import render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from app.blog import bp
from app.models import Post, Comment, Category, Tag, User
from app.extensions import db
from datetime import datetime
from sqlalchemy import desc, asc, func
import re

@bp.route('/')
@bp.route('/index')
def index():
    """Blog homepage with posts listing"""
    page = request.args.get('page', 1, type=int)
    
    # Base query for published posts
    query = Post.query.filter_by(published=True)
    
    # Apply sorting
    query = query.order_by(desc(Post.published_at))
    
    # Paginate results
    posts = query.paginate(
        page=page, 
        per_page=current_app.config.get('POSTS_PER_PAGE', 10),
        error_out=False
    )
    
    # Featured/pinned posts for top of page
    featured_posts = Post.query.filter_by(
        published=True, 
        is_featured=True
    ).order_by(desc(Post.published_at)).limit(3).all()
    
    # Get categories for sidebar
    categories = Category.query.all()
    
    # Get popular posts for sidebar (by views)
    popular_posts = Post.query.filter_by(published=True).order_by(desc(Post.views)).limit(3).all()
    
    return render_template('blog/index.html',
                         posts=posts,
                         featured_posts=featured_posts,
                         categories=categories,
                         popular_posts=popular_posts)

@bp.route('/post/<slug>')
def post_detail(slug):
    """Individual post page"""
    post = Post.query.filter_by(slug=slug, published=True).first_or_404()
    
    # Increment view count
    post.views += 1
    db.session.commit()
    
    # Get approved comments
    comments = Comment.query.filter_by(
        post=post, 
        approved=True, 
        parent_id=None  # Top-level comments only
    ).order_by(Comment.created_at.asc()).all()
    
    # Get related posts (same category, excluding current post)
    related_posts = []
    if post.category:
        related_posts = Post.query.filter(
            Post.category == post.category,
            Post.published == True,
            Post.id != post.id
        ).order_by(desc(Post.published_at)).limit(4).all()
    
    # Get categories for sidebar
    categories = Category.query.all()
    
    return render_template('blog/post.html',
                         post=post,
                         comments=comments,
                         related_posts=related_posts,
                         categories=categories)

@bp.route('/post/<slug>/comment', methods=['POST'])
def add_comment(slug):
    """Add a comment to a blog post"""
    post = Post.query.filter_by(slug=slug, published=True).first_or_404()
    
    if not post.allow_comments:
        flash('Les commentaires sont désactivés pour cet article.', 'warning')
        return redirect(url_for('blog.post_detail', slug=slug))
    
    # Get form data
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    website = request.form.get('website', '').strip()
    content = request.form.get('content', '').strip()
    
    # Validation
    if not name or not email or not content:
        flash('Veuillez remplir tous les champs obligatoires.', 'error')
        return redirect(url_for('blog.post_detail', slug=slug))
    
    # Create comment
    comment = Comment(
        content=content,
        name=name,
        email=email,
        website=website if website else None,
        post=post,
        author=current_user if current_user.is_authenticated else None,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        approved=True  # Auto-approve comments (admin can delete later)
    )
    
    try:
        db.session.add(comment)
        db.session.commit()
        flash('Votre commentaire a été publié avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Une erreur est survenue lors de l\'envoi de votre commentaire.', 'error')
    
    return redirect(url_for('blog.post_detail', slug=slug))

@bp.route('/category/<slug>')
def category(slug):
    """Posts by category"""
    category = Category.query.filter_by(slug=slug).first_or_404()
    page = request.args.get('page', 1, type=int)
    
    posts = Post.query.filter_by(
        category=category, 
        published=True
    ).order_by(desc(Post.published_at)).paginate(
        page=page, 
        per_page=current_app.config.get('POSTS_PER_PAGE', 10),
        error_out=False
    )
    
    return render_template('blog/category.html',
                         category=category,
                         posts=posts)

@bp.route('/search')
def search():
    """Search blog posts"""
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    
    if not query:
        return redirect(url_for('blog.index'))
    
    # Search in title and content
    search_results = Post.query.filter(
        Post.published == True,
        db.or_(
            Post.title.contains(query),
            Post.content.contains(query),
            Post.excerpt.contains(query)
        )
    ).order_by(desc(Post.published_at)).paginate(
        page=page,
        per_page=current_app.config.get('POSTS_PER_PAGE', 10),
        error_out=False
    )
    
    return render_template('blog/search.html',
                         query=query,
                         posts=search_results)

# Template filters for blog
@bp.app_template_filter('excerpt')
def excerpt_filter(text, length=150):
    """Create excerpt from text"""
    if len(text) <= length:
        return text
    return text[:length].rsplit(' ', 1)[0] + '...'

@bp.app_template_filter('reading_time')
def reading_time_filter(text):
    """Estimate reading time for text"""
    words = len(text.split())
    minutes = max(1, round(words / 200))  # Assume 200 words per minute
    return f"{minutes} min de lecture"
