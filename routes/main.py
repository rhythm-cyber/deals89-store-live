from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import Deal, Newsletter, BlogArticle, db
from sqlalchemy import desc, or_
from datetime import timedelta
import re

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Homepage showing latest deals"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    deals = Deal.query.filter(
        Deal.is_expired == False
    ).order_by(desc(Deal.pub_date)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get latest blog articles for homepage
    latest_articles = BlogArticle.query.filter_by(is_published=True)\
        .order_by(BlogArticle.published_at.desc()).limit(3).all()
    
    return render_template('index.html', deals=deals, latest_articles=latest_articles)

@bp.route('/category/<category_name>')
def category(category_name):
    """Category page showing deals by category"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    deals = Deal.query.filter(
        Deal.category == category_name,
        Deal.is_expired == False
    ).order_by(desc(Deal.pub_date)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('category.html', deals=deals, category=category_name)

@bp.route('/search')
def search():
    """Search deals"""
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    if query:
        # Search in title and summary
        deals = Deal.query.filter(
            or_(
                Deal.title.contains(query),
                Deal.summary.contains(query)
            ),
            Deal.is_expired == False
        ).order_by(desc(Deal.pub_date)).paginate(
            page=page, per_page=per_page, error_out=False
        )
    else:
        deals = Deal.query.filter(
            Deal.is_expired == False
        ).order_by(desc(Deal.pub_date)).paginate(
            page=page, per_page=per_page, error_out=False
        )
    
    return render_template('search.html', deals=deals, query=query)

@bp.route('/deal/<int:deal_id>')
def deal_detail(deal_id):
    """Deal detail page"""
    deal = Deal.query.get_or_404(deal_id)
    
    # Get related deals from same category
    related_deals = Deal.query.filter(
        Deal.category == deal.category,
        Deal.id != deal.id,
        Deal.is_expired == False
    ).limit(4).all()
    
    return render_template('deal_detail.html', deal=deal, related_deals=related_deals, timedelta=timedelta)

@bp.route('/sitemap.xml')
def sitemap():
    """Generate sitemap.xml"""
    from datetime import datetime, timezone
    
    deals = Deal.query.filter(
        Deal.price <= 1000,
        Deal.is_expired == False
    ).all()
    
    current_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    return render_template('sitemap.xml', deals=deals, current_date=current_date), 200, {'Content-Type': 'application/xml'}

@bp.route('/robots.txt')
def robots():
    """Serve robots.txt from static folder"""
    from flask import send_from_directory
    return send_from_directory('static', 'robots.txt', mimetype='text/plain')

@bp.route('/newsletter/subscribe', methods=['POST'])
def newsletter_subscribe():
    """Handle newsletter subscription"""
    try:
        email = request.form.get('email', '').strip().lower()
        
        # Validate email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not email or not re.match(email_pattern, email):
            return jsonify({'success': False, 'message': 'Please enter a valid email address'})
        
        # Check if email already exists
        existing_subscription = Newsletter.query.filter_by(email=email).first()
        if existing_subscription:
            if existing_subscription.is_active:
                return jsonify({'success': False, 'message': 'This email is already subscribed'})
            else:
                # Reactivate subscription
                existing_subscription.is_active = True
                db.session.commit()
                return jsonify({'success': True, 'message': 'Welcome back! Your subscription has been reactivated'})
        
        # Create new subscription
        import secrets
        verification_token = secrets.token_urlsafe(32)
        
        newsletter = Newsletter(
            email=email,
            verification_token=verification_token,
            is_verified=True  # For now, auto-verify. Can add email verification later
        )
        
        db.session.add(newsletter)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Successfully subscribed! You\'ll receive daily deals in your inbox'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred. Please try again later'})

@bp.route('/newsletter/unsubscribe/<token>')
def newsletter_unsubscribe(token):
    """Handle newsletter unsubscription"""
    newsletter = Newsletter.query.filter_by(verification_token=token).first()
    if newsletter:
        newsletter.is_active = False
        db.session.commit()
        flash('You have been successfully unsubscribed from our newsletter', 'success')
    else:
        flash('Invalid unsubscribe link', 'error')
    
    return redirect(url_for('main.index'))