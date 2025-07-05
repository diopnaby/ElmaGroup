from datetime import datetime, timedelta
import secrets
from app.extensions import db
from slugify import slugify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# Association tables for many-to-many relationships
book_authors = db.Table('book_authors',
    db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True),
    db.Column('author_id', db.Integer, db.ForeignKey('author.id'), primary_key=True)
)

book_tags = db.Table('book_tags',
    db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

book_collections = db.Table('book_collections',
    db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True),
    db.Column('collection_id', db.Integer, db.ForeignKey('collection.id'), primary_key=True)
)

post_tags = db.Table('post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    bio = db.Column(db.Text)
    avatar = db.Column(db.String(255))
    website = db.Column(db.String(255))
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    is_author = db.Column(db.Boolean, default=False)
    is_general_manager = db.Column(db.Boolean, default=False)
    is_manager = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    posts = db.relationship('Post', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    @property
    def post_count(self):
        return self.posts.filter_by(published=True).count()
    
    def __repr__(self):
        return f'<User {self.username}>'

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    slug = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#007bff')  # Hex color
    icon = db.Column(db.String(50))  # FontAwesome icon class
    is_featured = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    posts = db.relationship('Post', backref='category', lazy='dynamic')
    
    def __init__(self, **kwargs):
        super(Category, self).__init__(**kwargs)
        if not self.slug:
            self.slug = slugify(self.name)
    
    @property
    def post_count(self):
        return self.posts.filter_by(published=True).count()
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Collection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    slug = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    image = db.Column(db.String(255))
    is_featured = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, **kwargs):
        super(Collection, self).__init__(**kwargs)
        if not self.slug:
            self.slug = slugify(self.name)
    
    @property
    def book_count(self):
        return len(self.books)
    
    def __repr__(self):
        return f'<Collection {self.name}>'

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    slug = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#6c757d')  # Hex color
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, **kwargs):
        super(Tag, self).__init__(**kwargs)
        if not self.slug:
            self.slug = slugify(self.name)
    
    @property
    def post_count(self):
        return len(self.posts)
    
    @property
    def book_count(self):
        return len(self.books)
    
    def __repr__(self):
        return f'<Tag {self.name}>'

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), nullable=False, unique=True)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.Text)
    meta_title = db.Column(db.String(200))
    meta_description = db.Column(db.String(500))
    featured_image = db.Column(db.String(255))
    reading_time = db.Column(db.Integer)  # in minutes
    
    # Status and visibility
    published = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    is_pinned = db.Column(db.Boolean, default=False)
    allow_comments = db.Column(db.Boolean, default=True)
    
    # Analytics
    views = db.Column(db.Integer, default=0)
    likes = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime)
    
    # Foreign Keys
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    
    # Relationships
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    tags = db.relationship('Tag', secondary=post_tags, backref='posts')
    
    def __init__(self, **kwargs):
        super(Post, self).__init__(**kwargs)
        if not self.slug:
            self.slug = slugify(self.title)
        if not self.excerpt and self.content:
            # Auto-generate excerpt from content (first 200 chars)
            self.excerpt = self.content[:200] + '...' if len(self.content) > 200 else self.content
        if not self.reading_time and self.content:
            # Estimate reading time (average 200 words per minute)
            word_count = len(self.content.split())
            self.reading_time = max(1, round(word_count / 200))
    
    @property
    def comment_count(self):
        return self.comments.filter_by(approved=True).count()
    
    @property
    def tag_names(self):
        return [tag.name for tag in self.tags]
    
    @property
    def formatted_date(self):
        date_to_use = self.published_at if self.published_at else self.created_at
        return date_to_use.strftime('%d %B %Y')
    
    @property
    def reading_time_text(self):
        if self.reading_time:
            return f"{self.reading_time} min de lecture"
        return "< 1 min de lecture"
    
    def publish(self):
        if not self.published:
            self.published = True
            self.published_at = datetime.utcnow()
    
    def unpublish(self):
        self.published = False
        self.published_at = None
    
    def __init__(self, **kwargs):
        super(Post, self).__init__(**kwargs)
        if not self.slug and self.title:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Post.query.filter_by(slug=slug).first():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
    
    def __repr__(self):
        return f'<Post {self.title}>'

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    name = db.Column(db.String(100))  # For anonymous comments
    email = db.Column(db.String(120))  # For anonymous comments
    website = db.Column(db.String(255))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    
    # Status
    approved = db.Column(db.Boolean, default=False)
    is_spam = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # For registered users
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'))  # For replies
    
    # Relationships
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    
    @property
    def commenter_name(self):
        if self.author:
            return self.author.full_name
        return self.name or 'Anonyme'
    
    @property
    def commenter_avatar(self):
        if self.author and self.author.avatar:
            return self.author.avatar
        return None
    
    def approve(self):
        self.approved = True
    
    def mark_as_spam(self):
        self.is_spam = True
        self.approved = False
    
    def __repr__(self):
        return f'<Comment by {self.commenter_name}>'

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    phone = db.Column(db.String(50))
    company = db.Column(db.String(100))
    
    # Status
    responded = db.Column(db.Boolean, default=False)
    is_spam = db.Column(db.Boolean, default=False)
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, urgent
    
    # Tracking
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    responded_at = db.Column(db.DateTime)
    
    def mark_as_responded(self):
        self.responded = True
        self.responded_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<ContactMessage from {self.name}>'

class NewsletterSubscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    name = db.Column(db.String(100))
    subscribed = db.Column(db.Boolean, default=True)
    confirmed = db.Column(db.Boolean, default=False)
    interests = db.Column(db.JSON)  # Store as JSON array
    
    # Tracking
    ip_address = db.Column(db.String(45))
    source = db.Column(db.String(100))  # Where they subscribed from
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime)
    unsubscribed_at = db.Column(db.DateTime)
    
    def confirm_subscription(self):
        self.confirmed = True
        self.confirmed_at = datetime.utcnow()
    
    def unsubscribe(self):
        self.subscribed = False
        self.unsubscribed_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<NewsletterSubscriber {self.email}>'

# Library Models (from previous implementation)
class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), nullable=False, unique=True)
    photo = db.Column(db.String(255))
    nationality = db.Column(db.String(100))
    birth_date = db.Column(db.Date)
    death_date = db.Column(db.Date)
    biography = db.Column(db.Text)
    short_bio = db.Column(db.Text)
    website = db.Column(db.String(255))
    social_media = db.Column(db.JSON)
    awards = db.Column(db.Text)
    education = db.Column(db.Text)
    profile_views = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    books = db.relationship('Book', secondary=book_authors, back_populates='authors')
    
    def __init__(self, **kwargs):
        super(Author, self).__init__(**kwargs)
        if not self.slug:
            self.slug = slugify(self.name)
    
    @property
    def book_count(self):
        return len(self.books)
    
    @property
    def is_alive(self):
        return self.death_date is None

class Publisher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    slug = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.Text)
    logo = db.Column(db.String(255))
    website = db.Column(db.String(255))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(50))
    address = db.Column(db.Text)
    founded_year = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    books = db.relationship('Book', backref='publisher', lazy='dynamic')
    
    def __init__(self, **kwargs):
        super(Publisher, self).__init__(**kwargs)
        if not self.slug:
            self.slug = slugify(self.name)
    
    @property
    def book_count(self):
        return self.books.count()

class BookCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    slug = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    icon = db.Column(db.String(100))
    color = db.Column(db.String(7))
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    books = db.relationship('Book', backref='book_category', lazy='dynamic')
    
    def __init__(self, **kwargs):
        super(BookCategory, self).__init__(**kwargs)
        if not self.slug:
            self.slug = slugify(self.name)
    
    @property
    def book_count(self):
        return self.books.count()

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    subtitle = db.Column(db.String(300))
    slug = db.Column(db.String(300), nullable=False, unique=True)
    isbn_13 = db.Column(db.String(17), unique=True)
    isbn_10 = db.Column(db.String(13), unique=True)
    description = db.Column(db.Text)
    abstract = db.Column(db.Text)
    excerpt = db.Column(db.Text)
    cover_image = db.Column(db.String(255))
    
    # Publication details
    publication_date = db.Column(db.Date)
    page_count = db.Column(db.Integer)
    format_type = db.Column(db.String(50))
    language = db.Column(db.String(50), default='French')
    edition = db.Column(db.String(50))
    
    # Physical details
    dimensions = db.Column(db.String(100))
    weight = db.Column(db.Float)
    
    # Pricing
    price = db.Column(db.Float)
    sale_price = db.Column(db.Float)
    currency = db.Column(db.String(3), default='XOF')
    
    # Availability
    availability_status = db.Column(db.String(50), default='available')
    stock_quantity = db.Column(db.Integer, default=0)
    
    # Digital content
    ebook_file = db.Column(db.String(255))
    audiobook_file = db.Column(db.String(255))
    sample_pdf = db.Column(db.String(255))
    
    # Metadata
    table_of_contents = db.Column(db.Text)
    target_audience = db.Column(db.String(100))
    keywords = db.Column(db.String(500))
    meta_title = db.Column(db.String(300))
    meta_description = db.Column(db.String(500))
    
    # Status flags
    is_published = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    is_bestseller = db.Column(db.Boolean, default=False)
    is_new_release = db.Column(db.Boolean, default=False)
    is_award_winner = db.Column(db.Boolean, default=False)
    allow_reviews = db.Column(db.Boolean, default=True)
    
    # Analytics
    views = db.Column(db.Integer, default=0)
    download_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    publisher_id = db.Column(db.Integer, db.ForeignKey('publisher.id'))
    book_category_id = db.Column(db.Integer, db.ForeignKey('book_category.id'))
    
    # Relationships
    authors = db.relationship('Author', secondary=book_authors, back_populates='books')
    tags = db.relationship('Tag', secondary=book_tags, backref='books')
    collections = db.relationship('Collection', secondary=book_collections, backref='books')
    reviews = db.relationship('BookReview', backref='book', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super(Book, self).__init__(**kwargs)
        if not self.slug:
            self.slug = slugify(self.title)
    
    @property
    def current_price(self):
        return self.sale_price if self.sale_price else self.price
    
    @property
    def is_on_sale(self):
        return self.sale_price is not None and self.sale_price < self.price
    
    @property
    def formatted_price(self):
        if self.current_price:
            return f"{self.current_price:,.0f} {self.currency}"
        return "Prix sur demande"
    
    @property
    def author_names(self):
        return ", ".join([author.name for author in self.authors])
    
    @property
    def average_rating(self):
        if self.reviews.count() == 0:
            return 0
        return sum([review.rating for review in self.reviews if review.is_approved]) / self.reviews.filter_by(is_approved=True).count()
    
    @property
    def review_count(self):
        return self.reviews.filter_by(is_approved=True).count()
    
    @property
    def reading_time_estimate(self):
        if self.page_count:
            words = self.page_count * 250
            minutes = words / 200
            hours = int(minutes // 60)
            remaining_minutes = int(minutes % 60)
            if hours > 0:
                return f"{hours}h {remaining_minutes}min"
            else:
                return f"{remaining_minutes}min"
        return None

class BookReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reviewer_name = db.Column(db.String(100), nullable=False)
    reviewer_email = db.Column(db.String(120), nullable=False)
    reviewer_location = db.Column(db.String(100))
    reviewer_occupation = db.Column(db.String(100))
    
    title = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    pros = db.Column(db.Text)
    cons = db.Column(db.Text)
    
    is_approved = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    is_verified_purchase = db.Column(db.Boolean, default=False)
    helpful_votes = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime)
    
    # Foreign Keys
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)

class Testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quote = db.Column(db.Text, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    display_title = db.Column(db.String(150))
    company = db.Column(db.String(150))
    location = db.Column(db.String(100))
    photo = db.Column(db.String(255))
    
    # Contact details (private)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(50))
    
    # Testimonial metadata
    category = db.Column(db.String(100))
    context = db.Column(db.String(200))
    rating = db.Column(db.Integer)
    
    # Status and permissions
    is_active = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    show_on_homepage = db.Column(db.Boolean, default=False)
    can_use_name = db.Column(db.Boolean, default=True)
    can_use_title = db.Column(db.Boolean, default=True)
    can_use_photo = db.Column(db.Boolean, default=False)
    
    # Relations (optional)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    collection_id = db.Column(db.Integer, db.ForeignKey('collection.id'))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime)
    
    # Relationships
    book = db.relationship('Book', backref='testimonials')
    collection = db.relationship('Collection', backref='testimonials')
    
    @property
    def short_quote(self):
        if len(self.quote) > 150:
            return self.quote[:150] + "..."
        return self.quote

class LibraryStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total_books = db.Column(db.Integer, default=0)
    total_authors = db.Column(db.Integer, default=0)
    total_publishers = db.Column(db.Integer, default=0)
    total_categories = db.Column(db.Integer, default=0)
    total_reviews = db.Column(db.Integer, default=0)
    total_views = db.Column(db.Integer, default=0)
    average_rating = db.Column(db.Float, default=0.0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def update_stats(cls):
        """Update library statistics"""
        stats = cls.query.first()
        if not stats:
            stats = cls()
            db.session.add(stats)
        
        stats.total_books = Book.query.filter_by(is_published=True).count()
        stats.total_authors = Author.query.count()
        stats.total_publishers = Publisher.query.filter_by(is_active=True).count()
        stats.total_categories = BookCategory.query.count()
        stats.total_reviews = BookReview.query.filter_by(is_approved=True).count()
        stats.total_views = db.session.query(db.func.sum(Book.views)).scalar() or 0
        
        # Calculate average rating
        avg_rating = db.session.query(db.func.avg(BookReview.rating)).filter_by(is_approved=True).scalar()
        stats.average_rating = float(avg_rating) if avg_rating else 0.0
        
        stats.updated_at = datetime.utcnow()
        db.session.commit()
        return stats


class PresidentMessage(db.Model):
    """Model for President's message content"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, default="Un mot du président fondateur")
    content = db.Column(db.Text, nullable=False)
    president_name = db.Column(db.String(100), nullable=False, default="El Hadji Omar Massaly")
    president_title = db.Column(db.String(200), default="Président fondateur, ELMA Group")
    president_photo = db.Column(db.String(255), default="omar.jpg")
    
    # Display settings
    show_on_homepage = db.Column(db.Boolean, default=True)
    show_on_about = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f'<PresidentMessage {self.title}>'
    
    @classmethod
    def get_active_message(cls):
        """Get the active president's message"""
        return cls.query.filter_by(is_active=True).first()

class CommunicationCompany(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    logo = db.Column(db.String(255))
    description = db.Column(db.Text)
    website = db.Column(db.String(255))
    date_accompanied = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<CommunicationCompany {self.name}>'

class AdminInviteToken(db.Model):
    __tablename__ = 'admin_invite_tokens'
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    used_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    @staticmethod
    def generate_token(expiry_hours=24):
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)
        return AdminInviteToken(token=token, expires_at=expires_at)

    def is_valid(self):
        return not self.used and self.expires_at > datetime.utcnow()

class AdminActionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(64), nullable=False)  # e.g., 'promote_to_admin', 'demote_manager', etc.
    performed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    target_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    details = db.Column(db.Text)

    performed_by = db.relationship('User', foreign_keys=[performed_by_id], backref='admin_actions_performed')
    target_user = db.relationship('User', foreign_keys=[target_user_id], backref='admin_actions_received')

    def __repr__(self):
        return f'<AdminActionLog {self.action} by {self.performed_by_id} on {self.target_user_id}>'

