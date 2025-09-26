from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from models import db, BlogArticle, BlogCategory, BlogComment, Deal
from blog_generator import BlogContentGenerator
from datetime import datetime, timezone
import json
import re

bp = Blueprint('blog', __name__)

@bp.route('/')
def blog_index():
    """Blog home page with latest articles"""
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    articles = BlogArticle.query.filter_by(is_published=True)\
        .order_by(BlogArticle.published_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    # Get featured articles
    featured_articles = BlogArticle.query.filter_by(is_published=True, is_featured=True)\
        .order_by(BlogArticle.published_at.desc()).limit(3).all()
    
    # Get categories with article counts
    categories = db.session.query(BlogCategory, db.func.count(BlogArticle.id).label('article_count'))\
        .outerjoin(BlogArticle)\
        .filter(BlogArticle.is_published == True)\
        .group_by(BlogCategory.id)\
        .all()
    
    return render_template('blog/index.html', 
                         articles=articles,
                         featured_articles=featured_articles,
                         categories=categories)

@bp.route('/article/<slug>')
def article_detail(slug):
    """Individual article page"""
    article = BlogArticle.query.filter_by(slug=slug, is_published=True).first_or_404()
    
    # Increment view count
    article.view_count += 1
    db.session.commit()
    
    # Get approved comments
    comments = BlogComment.query.filter_by(article_id=article.id, is_approved=True, parent_id=None)\
        .order_by(BlogComment.created_at.asc()).all()
    
    # Get related articles
    related_articles = BlogArticle.query.filter(
        BlogArticle.category_id == article.category_id,
        BlogArticle.id != article.id,
        BlogArticle.is_published == True
    ).order_by(BlogArticle.published_at.desc()).limit(4).all()
    
    # Get related deals based on article tags
    related_deals = []
    if article.tags:
        try:
            tags = json.loads(article.tags)
            # Simple keyword matching with deals
            for tag in tags[:3]:  # Limit to first 3 tags
                deals = Deal.query.filter(
                    Deal.is_expired == False,
                    db.or_(
                        Deal.title.ilike(f'%{tag}%'),
                        Deal.category.ilike(f'%{tag}%')
                    )
                ).limit(2).all()
                related_deals.extend(deals)
            
            # Remove duplicates and limit
            seen_ids = set()
            unique_deals = []
            for deal in related_deals:
                if deal.id not in seen_ids:
                    unique_deals.append(deal)
                    seen_ids.add(deal.id)
                if len(unique_deals) >= 3:
                    break
            related_deals = unique_deals
        except:
            related_deals = Deal.query.filter_by(is_expired=False).limit(3).all()
    
    return render_template('blog/article_detail.html',
                         article=article,
                         comments=comments,
                         related_articles=related_articles,
                         related_deals=related_deals)

@bp.route('/category/<slug>')
def category_articles(slug):
    """Articles by category"""
    category = BlogCategory.query.filter_by(slug=slug).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    articles = BlogArticle.query.filter_by(category_id=category.id, is_published=True)\
        .order_by(BlogArticle.published_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('blog/category.html',
                         category=category,
                         articles=articles)

@bp.route('/search')
def search_articles():
    """Search articles"""
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    if not query:
        return redirect(url_for('blog.blog_index'))
    
    # Search in title, content, and tags
    articles = BlogArticle.query.filter(
        BlogArticle.is_published == True,
        db.or_(
            BlogArticle.title.ilike(f'%{query}%'),
            BlogArticle.content.ilike(f'%{query}%'),
            BlogArticle.tags.ilike(f'%{query}%'),
            BlogArticle.excerpt.ilike(f'%{query}%')
        )
    ).order_by(BlogArticle.published_at.desc())\
     .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('blog/search.html',
                         articles=articles,
                         query=query)

@bp.route('/article/<int:article_id>/comment', methods=['POST'])
def add_comment(article_id):
    """Add comment to article"""
    article = BlogArticle.query.get_or_404(article_id)
    
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    website = request.form.get('website', '').strip()
    content = request.form.get('content', '').strip()
    parent_id = request.form.get('parent_id', type=int)
    
    # Basic validation
    if not all([name, email, content]):
        flash('Name, email, and comment are required.', 'error')
        return redirect(url_for('blog.article_detail', slug=article.slug))
    
    # Email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        flash('Please enter a valid email address.', 'error')
        return redirect(url_for('blog.article_detail', slug=article.slug))
    
    # Content length validation
    if len(content) < 10 or len(content) > 1000:
        flash('Comment must be between 10 and 1000 characters.', 'error')
        return redirect(url_for('blog.article_detail', slug=article.slug))
    
    # Create comment
    comment = BlogComment(
        article_id=article_id,
        name=name,
        email=email,
        website=website if website else None,
        content=content,
        parent_id=parent_id if parent_id else None,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        is_approved=True  # Auto-approve for now, can add moderation later
    )
    
    db.session.add(comment)
    db.session.commit()
    
    flash('Your comment has been added successfully!', 'success')
    return redirect(url_for('blog.article_detail', slug=article.slug) + f'#comment-{comment.id}')

@bp.route('/article/<int:article_id>/like', methods=['POST'])
def like_article(article_id):
    """Like an article (AJAX endpoint)"""
    article = BlogArticle.query.get_or_404(article_id)
    
    # Simple like increment (in production, you'd want to track user likes)
    article.like_count += 1
    db.session.commit()
    
    return jsonify({
        'success': True,
        'like_count': article.like_count
    })

@bp.route('/article/<int:article_id>/share', methods=['POST'])
def share_article(article_id):
    """Track article shares (AJAX endpoint)"""
    article = BlogArticle.query.get_or_404(article_id)
    
    article.share_count += 1
    db.session.commit()
    
    return jsonify({
        'success': True,
        'share_count': article.share_count
    })

# Admin routes for blog management
@bp.route('/admin')
@login_required
def admin_dashboard():
    """Blog admin dashboard"""
    total_articles = BlogArticle.query.count()
    published_articles = BlogArticle.query.filter_by(is_published=True).count()
    total_comments = BlogComment.query.count()
    pending_comments = BlogComment.query.filter_by(is_approved=False).count()
    
    recent_articles = BlogArticle.query.order_by(BlogArticle.created_at.desc()).limit(5).all()
    recent_comments = BlogComment.query.order_by(BlogComment.created_at.desc()).limit(5).all()
    
    return render_template('blog/admin/dashboard.html',
                         total_articles=total_articles,
                         published_articles=published_articles,
                         total_comments=total_comments,
                         pending_comments=pending_comments,
                         recent_articles=recent_articles,
                         recent_comments=recent_comments)

@bp.route('/admin/articles')
@login_required
def admin_articles():
    """Manage articles"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    articles = BlogArticle.query.order_by(BlogArticle.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('blog/admin/articles.html', articles=articles)

@bp.route('/admin/article/new', methods=['GET', 'POST'])
@login_required
def admin_new_article():
    """Create new article"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        excerpt = request.form.get('excerpt', '').strip()
        category_id = request.form.get('category_id', type=int)
        tags = request.form.get('tags', '').strip()
        is_published = request.form.get('is_published') == 'on'
        is_featured = request.form.get('is_featured') == 'on'
        
        if not all([title, content, category_id]):
            flash('Title, content, and category are required.', 'error')
            return render_template('blog/admin/article_form.html',
                                 categories=BlogCategory.query.all())
        
        # Generate slug
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[-\s]+', '-', slug).strip('-')
        
        # Ensure unique slug
        base_slug = slug
        counter = 1
        while BlogArticle.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        # Process tags
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            tags_json = json.dumps(tag_list)
        else:
            tags_json = '[]'
        
        article = BlogArticle(
            title=title,
            slug=slug,
            content=content,
            excerpt=excerpt,
            tags=tags_json,
            category_id=category_id,
            author_id=current_user.id,
            is_published=is_published,
            is_featured=is_featured,
            published_at=datetime.now(timezone.utc) if is_published else None
        )
        
        db.session.add(article)
        db.session.commit()
        
        flash('Article created successfully!', 'success')
        return redirect(url_for('blog.admin_articles'))
    
    categories = BlogCategory.query.all()
    return render_template('blog/admin/article_form.html', categories=categories)

@bp.route('/admin/article/<int:article_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_article(article_id):
    """Edit article"""
    article = BlogArticle.query.get_or_404(article_id)
    
    if request.method == 'POST':
        article.title = request.form.get('title', '').strip()
        article.content = request.form.get('content', '').strip()
        article.excerpt = request.form.get('excerpt', '').strip()
        article.category_id = request.form.get('category_id', type=int)
        
        tags = request.form.get('tags', '').strip()
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            article.tags = json.dumps(tag_list)
        else:
            article.tags = '[]'
        
        was_published = article.is_published
        article.is_published = request.form.get('is_published') == 'on'
        article.is_featured = request.form.get('is_featured') == 'on'
        
        # Set published_at if publishing for first time
        if article.is_published and not was_published:
            article.published_at = datetime.now(timezone.utc)
        
        article.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        flash('Article updated successfully!', 'success')
        return redirect(url_for('blog.admin_articles'))
    
    categories = BlogCategory.query.all()
    # Parse tags for display
    try:
        tags_list = json.loads(article.tags) if article.tags else []
        tags_string = ', '.join(tags_list)
    except:
        tags_string = ''
    
    return render_template('blog/admin/article_form.html',
                         article=article,
                         categories=categories,
                         tags_string=tags_string)

@bp.route('/admin/article/<int:article_id>/delete', methods=['POST'])
@login_required
def admin_delete_article(article_id):
    """Delete article"""
    article = BlogArticle.query.get_or_404(article_id)
    
    db.session.delete(article)
    db.session.commit()
    
    flash('Article deleted successfully!', 'success')
    return redirect(url_for('blog.admin_articles'))

@bp.route('/admin/generate-articles', methods=['POST'])
@login_required
def admin_generate_articles():
    """Generate articles using the content generator"""
    count = request.form.get('count', 2, type=int)
    count = min(max(count, 1), 5)  # Limit between 1 and 5
    
    try:
        generator = BlogContentGenerator()
        articles = generator.create_daily_articles(count)
        
        flash(f'Successfully generated {len(articles)} articles!', 'success')
    except Exception as e:
        flash(f'Error generating articles: {str(e)}', 'error')
    
    return redirect(url_for('blog.admin_articles'))

@bp.route('/admin/comments')
@login_required
def admin_comments():
    """Manage comments"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    comments = BlogComment.query.order_by(BlogComment.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('blog/admin/comments.html', comments=comments)

@bp.route('/admin/comment/<int:comment_id>/approve', methods=['POST'])
@login_required
def admin_approve_comment(comment_id):
    """Approve comment"""
    comment = BlogComment.query.get_or_404(comment_id)
    comment.is_approved = True
    db.session.commit()
    
    flash('Comment approved!', 'success')
    return redirect(url_for('blog.admin_comments'))

@bp.route('/admin/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def admin_delete_comment(comment_id):
    """Delete comment"""
    comment = BlogComment.query.get_or_404(comment_id)
    
    db.session.delete(comment)
    db.session.commit()
    
    flash('Comment deleted!', 'success')
    return redirect(url_for('blog.admin_comments'))

@bp.route('/admin/categories')
@login_required
def admin_categories():
    """Manage categories"""
    categories = BlogCategory.query.all()
    return render_template('blog/admin/categories.html', categories=categories)

@bp.route('/admin/category/new', methods=['GET', 'POST'])
@login_required
def admin_new_category():
    """Create new category"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        if not name:
            flash('Category name is required.', 'error')
            return render_template('blog/admin/category_form.html')
        
        # Generate slug
        slug = re.sub(r'[^\w\s-]', '', name.lower())
        slug = re.sub(r'[-\s]+', '-', slug).strip('-')
        
        # Ensure unique slug
        base_slug = slug
        counter = 1
        while BlogCategory.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        category = BlogCategory(
            name=name,
            slug=slug,
            description=description
        )
        
        db.session.add(category)
        db.session.commit()
        
        flash('Category created successfully!', 'success')
        return redirect(url_for('blog.admin_categories'))
    
    return render_template('blog/admin/category_form.html')

# RSS Feed
@bp.route('/feed.xml')
def rss_feed():
    """RSS feed for blog articles"""
    articles = BlogArticle.query.filter_by(is_published=True)\
        .order_by(BlogArticle.published_at.desc()).limit(20).all()
    
    return render_template('blog/feed.xml', articles=articles), 200, {
        'Content-Type': 'application/rss+xml; charset=utf-8'
    }