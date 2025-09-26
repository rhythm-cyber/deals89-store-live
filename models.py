from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from sqlalchemy import Numeric

# Create db instance that will be initialized in app.py
db = SQLAlchemy()

class Deal(db.Model):
    __tablename__ = 'deals'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    affiliate_url = db.Column(db.Text, nullable=False)
    original_url = db.Column(db.Text, nullable=False)
    canonical_url = db.Column(db.Text, nullable=False)
    price = db.Column(Numeric(10, 2), nullable=False)
    image_url = db.Column(db.Text)
    summary = db.Column(db.Text)
    category = db.Column(db.String(100))
    pub_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_expired = db.Column(db.Boolean, default=False)
    telegram_posted = db.Column(db.Boolean, default=False)
    facebook_posted = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Deal {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'affiliate_url': self.affiliate_url,
            'original_url': self.original_url,
            'canonical_url': self.canonical_url,
            'price': float(self.price) if self.price else 0.0,
            'image_url': self.image_url,
            'summary': self.summary,
            'category': self.category,
            'pub_date': self.pub_date.isoformat() if self.pub_date else None,
            'is_expired': self.is_expired
        }

class Admin(UserMixin, db.Model):
    __tablename__ = 'admin'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<Admin {self.username}>'

class Newsletter(db.Model):
    __tablename__ = 'newsletter'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    subscribed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True)
    verification_token = db.Column(db.String(100))
    is_verified = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Newsletter {self.email}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'subscribed_at': self.subscribed_at.isoformat() if self.subscribed_at else None,
            'is_active': self.is_active,
            'is_verified': self.is_verified
        }

class BlogCategory(db.Model):
    __tablename__ = 'blog_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationship with articles
    articles = db.relationship('BlogArticle', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<BlogCategory {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class BlogArticle(db.Model):
    __tablename__ = 'blog_articles'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.Text)
    featured_image = db.Column(db.Text)
    meta_description = db.Column(db.String(160))
    tags = db.Column(db.Text)  # JSON string of tags
    
    # SEO and engagement
    view_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)
    share_count = db.Column(db.Integer, default=0)
    
    # Publishing
    is_published = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    published_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Foreign keys
    category_id = db.Column(db.Integer, db.ForeignKey('blog_categories.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    
    # Relationships
    comments = db.relationship('BlogComment', backref='article', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<BlogArticle {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'content': self.content,
            'excerpt': self.excerpt,
            'featured_image': self.featured_image,
            'meta_description': self.meta_description,
            'tags': self.tags,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'share_count': self.share_count,
            'is_published': self.is_published,
            'is_featured': self.is_featured,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'category_id': self.category_id,
            'author_id': self.author_id
        }

class BlogComment(db.Model):
    __tablename__ = 'blog_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    website = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    
    # Moderation
    is_approved = db.Column(db.Boolean, default=False)
    is_spam = db.Column(db.Boolean, default=False)
    
    # Metadata
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Foreign keys
    article_id = db.Column(db.Integer, db.ForeignKey('blog_articles.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('blog_comments.id'))  # For replies
    
    # Self-referential relationship for replies
    replies = db.relationship('BlogComment', backref=db.backref('parent', remote_side=[id]), lazy=True)
    
    def __repr__(self):
        return f'<BlogComment by {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'website': self.website,
            'content': self.content,
            'is_approved': self.is_approved,
            'is_spam': self.is_spam,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'article_id': self.article_id,
            'parent_id': self.parent_id
        }