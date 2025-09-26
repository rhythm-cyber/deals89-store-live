from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from models import Deal, Admin, Newsletter, db
from utils import canonicalize_url, add_affiliate_tag, fetch_metadata, validate_price
from decimal import Decimal
import os

bp = Blueprint('admin', __name__)

@bp.route('/')
@login_required
def admin_root():
    """Admin root - redirect to dashboard"""
    return redirect(url_for('admin.dashboard'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login"""
    if request.method == 'POST':
        password = request.form.get('password')
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        
        if password == admin_password:
            # Create or get admin user
            admin = Admin.query.first()
            if not admin:
                admin = Admin(username='admin')
                admin.set_password(admin_password)
                db.session.add(admin)
                db.session.commit()
            
            login_user(admin)
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid password', 'error')
    
    return render_template('admin/login.html')

@bp.route('/logout')
@login_required
def logout():
    """Admin logout"""
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/dashboard')
@login_required
def dashboard():
    """Admin dashboard"""
    total_deals = Deal.query.count()
    active_deals = Deal.query.filter(Deal.is_expired == False).count()
    recent_deals = Deal.query.order_by(Deal.pub_date.desc()).limit(10).all()
    
    # Newsletter stats
    total_subscribers = Newsletter.query.count()
    active_subscribers = Newsletter.query.filter(
        Newsletter.is_active == True,
        Newsletter.is_verified == True
    ).count()
    
    return render_template('admin/dashboard.html', 
                         total_deals=total_deals,
                         active_deals=active_deals,
                         recent_deals=recent_deals,
                         total_subscribers=total_subscribers,
                         active_subscribers=active_subscribers)

@bp.route('/add-deal', methods=['GET', 'POST'])
@login_required
def add_deal():
    """Add new deal"""
    if request.method == 'POST':
        try:
            # Get form data
            affiliate_url = request.form.get('affiliate_url', '').strip()
            title = request.form.get('title', '').strip()
            summary = request.form.get('summary', '').strip()
            image_url = request.form.get('image_url', '').strip()
            category = request.form.get('category', '').strip()
            manual_price = request.form.get('price', '').strip()
            
            if not affiliate_url:
                flash('Affiliate URL is required', 'error')
                return render_template('admin/add_deal.html')
            
            # Canonicalize URL for deduplication
            canonical_url = canonicalize_url(affiliate_url)
            
            # Check for duplicates
            existing_deal = Deal.query.filter_by(canonical_url=canonical_url).first()
            if existing_deal:
                flash('Deal already exists with this URL', 'error')
                return render_template('admin/add_deal.html')
            
            # Add affiliate tag if missing
            affiliate_url = add_affiliate_tag(affiliate_url)
            
            # Fetch metadata if not provided
            metadata = fetch_metadata(canonical_url)
            
            # Use manual data or fallback to fetched metadata
            final_title = title or metadata.get('title', 'No title')
            final_summary = summary or metadata.get('description', 'No description')
            final_image_url = image_url or metadata.get('image_url')
            
            # Determine price
            final_price = None
            if manual_price:
                try:
                    final_price = Decimal(manual_price)
                except:
                    flash('Invalid price format', 'error')
                    return render_template('admin/add_deal.html')
            else:
                final_price = metadata.get('price')
            
            if final_price is None:
                flash('Price could not be determined. Please enter manually.', 'error')
                return render_template('admin/add_deal.html')
            
            # Validate price (must be reasonable)
            if not validate_price(final_price):
                flash(f'Price ₹{final_price} is not valid. Please enter a price between ₹1 and ₹200,000', 'error')
                return render_template('admin/add_deal.html')
            
            # Create new deal
            deal = Deal(
                title=final_title,
                affiliate_url=affiliate_url,
                original_url=canonical_url,  # Use canonical_url as original_url
                canonical_url=canonical_url,
                image_url=final_image_url,
                summary=final_summary,
                price=final_price,
                category=category or 'General'
            )
            
            db.session.add(deal)
            db.session.commit()
            
            flash(f'Deal "{final_title}" added successfully!', 'success')
            return redirect(url_for('admin.dashboard'))
            
        except Exception as e:
            flash(f'Error adding deal: {str(e)}', 'error')
            db.session.rollback()
    
    return render_template('admin/add_deal.html')

@bp.route('/deals')
@login_required
def manage_deals():
    """Manage deals with filtering and pagination"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    status = request.args.get('status', '')
    
    # Build query
    query = Deal.query
    
    # Apply filters
    if search:
        query = query.filter(Deal.title.contains(search) | Deal.summary.contains(search))
    
    if category:
        query = query.filter(Deal.category == category)
    
    if status == 'active':
        query = query.filter(Deal.is_expired == False)
    elif status == 'expired':
        query = query.filter(Deal.is_expired == True)
    
    # Order by newest first
    query = query.order_by(Deal.pub_date.desc())
    
    # Paginate
    deals = query.paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get all categories for filter dropdown
    categories = db.session.query(Deal.category).filter(Deal.category.isnot(None)).distinct().all()
    categories = [cat[0] for cat in categories]
    
    return render_template('admin/manage_deals.html', deals=deals, categories=categories)

@bp.route('/deal/<int:deal_id>/toggle-expired')
@login_required
def toggle_expired(deal_id):
    """Toggle deal expiration status"""
    deal = Deal.query.get_or_404(deal_id)
    deal.is_expired = not deal.is_expired
    db.session.commit()
    
    status = 'expired' if deal.is_expired else 'active'
    flash(f'Deal marked as {status}', 'success')
    return redirect(url_for('admin.manage_deals'))

@bp.route('/newsletter')
@login_required
def newsletter_management():
    """Newsletter management page"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    subscribers = Newsletter.query.order_by(Newsletter.subscribed_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    stats = {
        'total': Newsletter.query.count(),
        'active': Newsletter.query.filter(
            Newsletter.is_active == True,
            Newsletter.is_verified == True
        ).count(),
        'unverified': Newsletter.query.filter(
            Newsletter.is_verified == False
        ).count(),
        'inactive': Newsletter.query.filter(
            Newsletter.is_active == False
        ).count()
    }
    
    return render_template('admin/newsletter.html', 
                         subscribers=subscribers,
                         stats=stats)

@bp.route('/newsletter/export')
@login_required
def export_subscribers():
    """Export active subscribers as CSV"""
    from flask import Response
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Email', 'Subscribed Date', 'Status', 'Verified'])
    
    # Write subscriber data
    subscribers = Newsletter.query.filter(
        Newsletter.is_active == True,
        Newsletter.is_verified == True
    ).all()
    
    for subscriber in subscribers:
        writer.writerow([
            subscriber.email,
            subscriber.subscribed_at.strftime('%Y-%m-%d %H:%M:%S'),
            'Active' if subscriber.is_active else 'Inactive',
            'Yes' if subscriber.is_verified else 'No'
        ])
    
    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=subscribers.csv'}
    )

@bp.route('/delete_deal/<int:deal_id>', methods=['POST'])
@login_required
def delete_deal(deal_id):
    deal = Deal.query.get_or_404(deal_id)
    db.session.delete(deal)
    db.session.commit()
    flash('Deal deleted successfully!', 'success')
    return redirect(url_for('admin.manage_deals'))

@bp.route('/bulk_action', methods=['POST'])
@login_required
def bulk_action():
    action = request.form.get('action')
    deal_ids = request.form.getlist('deal_ids')
    
    if not action or not deal_ids:
        flash('Please select an action and at least one deal.', 'error')
        return redirect(url_for('admin.manage_deals'))
    
    try:
        deal_ids = [int(id) for id in deal_ids]
        deals = Deal.query.filter(Deal.id.in_(deal_ids)).all()
        
        if action == 'expire':
            for deal in deals:
                deal.is_expired = True
            db.session.commit()
            flash(f'Marked {len(deals)} deals as expired.', 'success')
        
        elif action == 'activate':
            for deal in deals:
                deal.is_expired = False
            db.session.commit()
            flash(f'Marked {len(deals)} deals as active.', 'success')
        
        elif action == 'delete':
            for deal in deals:
                db.session.delete(deal)
            db.session.commit()
            flash(f'Deleted {len(deals)} deals.', 'success')
        
        else:
            flash('Invalid action selected.', 'error')
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error performing bulk action: {str(e)}', 'error')
    
    return redirect(url_for('admin.manage_deals'))