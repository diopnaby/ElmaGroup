from flask import render_template, request, flash, redirect, url_for, jsonify, current_app
from app.blog import bp
from app.models import Post, Comment, Category, Tag, User
from app.extensions import db
from datetime import datetime, timedelta
from sqlalchemy import desc, asc, func
import re

@bp.route('/')
@bp.route('/index')
def index():
    """Blog homepage with posts listing"""
    page = request.args.get('page', 1, type=int)
    category_slug = request.args.get('category')
    tag_slug = request.args.get('tag')
    author_id = request.args.get('author', type=int)
    sort_by = request.args.get('sort', 'latest')  # latest, popular, oldest

    # Base query for published posts
    query = Post.query.filter_by(published=True)

    # Apply filters
    if category_slug:
        category = Category.query.filter_by(slug=category_slug).first_or_404()
        query = query.filter_by(category=category)

    if tag_slug:
        tag = Tag.query.filter_by(slug=tag_slug).first_or_404()
        query = query.filter(Post.tags.contains(tag))

    if author_id:
        author = User.query.get_or_404(author_id)
        query = query.filter_by(author=author)

    # Apply sorting
    if sort_by == 'popular':
        query = query.order_by(desc(Post.views))
    elif sort_by == 'oldest':
        query = query.order_by(asc(Post.published_at))
    else:  # latest (default)
        query = query.order_by(desc(Post.published_at))

    # Paginate results
    posts = query.paginate(
        page=page,
        per_page=current_app.config.get('POSTS_PER_PAGE', 10),
        error_out=False
    )

    # Get sidebar data
    sidebar_data = get_sidebar_data()

    # Featured/pinned posts for top of page
    featured_posts = Post.query.filter_by(
        published=True,
        is_featured=True
    ).order_by(desc(Post.published_at)).limit(3).all()

    # Popular posts this month
    one_month_ago = datetime.utcnow() - timedelta(days=30)
    popular_posts = Post.query.filter(
        Post.published == True,
        Post.created_at >= one_month_ago
    ).order_by(desc(Post.views)).limit(5).all()

    return render_template(
        'blog/index.html',
        posts=posts,
        sidebar_data=sidebar_data,
        featured_posts=featured_posts,
        popular_posts=popular_posts,
        current_category=category_slug,
        current_tag=tag_slug,
        current_author=author_id,
        current_sort=sort_by
    )

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

    # If not enough related posts, get recent posts
    if len(related_posts) < 4:
        additional_posts = Post.query.filter(
            Post.published == True,
            Post.id != post.id,
            ~Post.id.in_([p.id for p in related_posts])
        ).order_by(desc(Post.published_at)).limit(4 - len(related_posts)).all()
        related_posts.extend(additional_posts)

    # Get sidebar data
    sidebar_data = get_sidebar_data()

    # Previous and next posts
    prev_post = Post.query.filter(
        Post.published == True,
        Post.published_at < post.published_at
    ).order_by(desc(Post.published_at)).first()

    next_post = Post.query.filter(
        Post.published == True,
        Post.published_at > post.published_at
    ).order_by(asc(Post.published_at)).first()

    return render_template(
        'blog/post.html',
        post=post,
        comments=comments,
        related_posts=related_posts,
        sidebar_data=sidebar_data,
        prev_post=prev_post,
        next_post=next_post
    )

@bp.route('/post/<slug>/comment', methods=['POST'])
def add_comment(slug):
    """Add comment to a post"""
    post = Post.query.filter_by(slug=slug, published=True).first_or_404()

    if not post.allow_comments:
        flash('Les commentaires sont désactivés pour cet article.', 'error')
        return redirect(url_for('blog.post_detail', slug=slug))

    # Get form data
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    website = request.form.get('website', '').strip()
    content = request.form.get('content', '').strip()
    parent_id = request.form.get('parent_id', type=int)

    # Basic validation
    errors = []
    if not name:
        errors.append('Le nom est requis')
    if not email or not is_valid_email(email):
        errors.append('Une adresse email valide est requise')
    if not content:
        errors.append('Le commentaire ne peut pas être vide')
    if len(content) > 2000:
        errors.append('Le commentaire est trop long (maximum 2000 caractères)')

    # Check for spam patterns
    if is_likely_spam(content, name, email):
        errors.append('Votre commentaire a été marqué comme spam')

    if errors:
        for error in errors:
            flash(error, 'error')
        return redirect(url_for('blog.post_detail', slug=slug) + '#comment-form')

    # Create comment
    comment = Comment(
        post=post,
        name=name,
        email=email,
        website=website if website else None,
        content=content,
        parent_id=parent_id if parent_id else None,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        approved=False  # Require moderation
    )

    try:
        db.session.add(comment)
        db.session.commit()
        flash('Votre commentaire a été soumis et sera publié après modération.', 'success')
    except Exception as e:
        db.session.rollback()
        flash("Une erreur est survenue lors de l'ajout de votre commentaire.", 'error')

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

    sidebar_data = get_sidebar_data()

    return render_template(
        'blog/category.html',
        category=category,
        posts=posts,
        sidebar_data=sidebar_data
    )

@bp.route('/tag/<slug>')
def tag(slug):
    """Posts by tag"""
    tag = Tag.query.filter_by(slug=slug).first_or_404()
    page = request.args.get('page', 1, type=int)

    posts = Post.query.filter(
        Post.tags.contains(tag),
        Post.published == True
    ).order_by(desc(Post.published_at)).paginate(
        page=page,
        per_page=current_app.config.get('POSTS_PER_PAGE', 10),
        error_out=False
    )

    sidebar_data = get_sidebar_data()

    return render_template(
        'blog/tag.html',
        tag=tag,
        posts=posts,
        sidebar_data=sidebar_data
    )

@bp.route('/author/<int:author_id>')
def author(author_id):
    """Posts by author"""
    author = User.query.get_or_404(author_id)
    page = request.args.get('page', 1, type=int)

    posts = Post.query.filter_by(
        author=author,
        published=True
    ).order_by(desc(Post.published_at)).paginate(
        page=page,
        per_page=current_app.config.get('POSTS_PER_PAGE', 10),
        error_out=False
    )

    sidebar_data = get_sidebar_data()

    return render_template(
        'blog/author.html',
        author=author,
        posts=posts,
        sidebar_data=sidebar_data
    )

@bp.route('/archive')
def archive():
    """Archive view with posts grouped by month/year"""
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)

    # Get archive data
    archive_data = db.session.query(
        func.strftime('%Y', Post.published_at).label('year'),
        func.strftime('%m', Post.published_at).label('month'),
        func.count(Post.id).label('count')
    ).filter(
        Post.published == True,
        Post.published_at.isnot(None)
    ).group_by('year', 'month').order_by(desc('year'), desc('month')).all()

    # Filter posts if year/month specified
    query = Post.query.filter_by(published=True)

    if year:
        if month:
            # Specific month and year
            query = query.filter(
                func.strftime('%Y', Post.published_at) == str(year),
                func.strftime('%m', Post.published_at) == f'{month:02d}'
            )
        else:
            # Specific year only
            query = query.filter(
                func.strftime('%Y', Post.published_at) == str(year)
            )

    page = request.args.get('page', 1, type=int)
    posts = query.order_by(desc(Post.published_at)).paginate(
        page=page,
        per_page=current_app.config.get('POSTS_PER_PAGE', 10),
        error_out=False
    )

    sidebar_data = get_sidebar_data()

    return render_template(
        'blog/archive.html',
        posts=posts,
        archive_data=archive_data,
        sidebar_data=sidebar_data,
        current_year=year,
        current_month=month
    )

@bp.route('/search')
def search():
    """Blog search"""
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)

    posts = None
    if query and len(query) >= 2:
        posts = Post.query.filter(
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

    sidebar_data = get_sidebar_data()

    return render_template(
        'blog/search.html',
        query=query,
        posts=posts,
        sidebar_data=sidebar_data
    )

@bp.route('/rss.xml')
def rss():
    """RSS feed for blog posts"""
    from flask import Response

    posts = Post.query.filter_by(published=True).order_by(
        desc(Post.published_at)
    ).limit(20).all()

    rss_xml = render_template('blog/rss.xml', posts=posts)
    return Response(rss_xml, mimetype='application/rss+xml')

def get_sidebar_data():
    """Get common sidebar data for blog pages"""
    # Recent posts
    recent_posts = Post.query.filter_by(published=True).order_by(
        desc(Post.published_at)
    ).limit(5).all()

    # Categories with post counts
    categories = db.session.query(
        Category, func.count(Post.id).label('post_count')
    ).outerjoin(Post).filter(
        Post.published == True
    ).group_by(Category.id).order_by(Category.name).all()

    # Popular tags
    popular_tags = db.session.query(
        Tag, func.count(Post.id).label('post_count')
    ).join(Post.tags).filter(
        Post.published == True
    ).group_by(Tag.id).order_by(
        desc('post_count')
    ).limit(10).all()

    # Archive links (last 12 months)
    archive_months = db.session.query(
        func.strftime('%Y-%m', Post.published_at).label('month'),
        func.count(Post.id).label('count')
    ).filter(
        Post.published == True,
        Post.published_at.isnot(None)
    ).group_by('month').order_by(desc('month')).limit(12).all()

    return {
        'recent_posts': recent_posts,
        'categories': categories,
        'popular_tags': popular_tags,
        'archive_months': archive_months
    }

def is_valid_email(email):
    """Simple email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_likely_spam(content, name, email):
    """Basic spam detection"""
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
    if len(words) > 10:
        unique_words = set(words)
        if len(unique_words) / len(words) < 0.3:  # Less than 30% unique words
            return True

    return False

# Blog-specific template filters
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