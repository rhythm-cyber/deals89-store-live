from flask import Blueprint, jsonify, request
from models import Deal, db
from sqlalchemy import desc, func

bp = Blueprint('api', __name__)

@bp.route('/deals')
def get_deals():
    """Get latest deals (max 50)"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 50)
    
    deals = Deal.query.filter(
        Deal.price <= 100,
        Deal.is_expired == False
    ).order_by(desc(Deal.pub_date)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'deals': [deal.to_dict() for deal in deals.items],
        'total': deals.total,
        'pages': deals.pages,
        'current_page': deals.page,
        'has_next': deals.has_next,
        'has_prev': deals.has_prev
    })

@bp.route('/deals/category/<category_name>')
def get_deals_by_category(category_name):
    """Get deals by category"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 50)
    
    deals = Deal.query.filter(
        Deal.category == category_name,
        Deal.price <= 100,
        Deal.is_expired == False
    ).order_by(desc(Deal.pub_date)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'category': category_name,
        'deals': [deal.to_dict() for deal in deals.items],
        'total': deals.total,
        'pages': deals.pages,
        'current_page': deals.page,
        'has_next': deals.has_next,
        'has_prev': deals.has_prev
    })

@bp.route('/deals/search')
def search_deals():
    """Search deals"""
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 50)
    
    if not query:
        return jsonify({
            'query': query,
            'deals': [],
            'total': 0,
            'pages': 0,
            'current_page': 1,
            'has_next': False,
            'has_prev': False
        })
    
    deals = Deal.query.filter(
        (Deal.title.contains(query) | Deal.summary.contains(query)),
        Deal.price <= 100,
        Deal.is_expired == False
    ).order_by(desc(Deal.pub_date)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'query': query,
        'deals': [deal.to_dict() for deal in deals.items],
        'total': deals.total,
        'pages': deals.pages,
        'current_page': deals.page,
        'has_next': deals.has_next,
        'has_prev': deals.has_prev
    })

@bp.route('/categories')
def get_categories():
    """Get all categories with deal counts"""
    categories = db.session.query(
        Deal.category,
        func.count(Deal.id).label('count')
    ).filter(
        Deal.price <= 100,
        Deal.is_expired == False
    ).group_by(Deal.category).all()
    
    return jsonify({
        'categories': [
            {'name': cat.category, 'count': cat.count}
            for cat in categories
        ]
    })

@bp.route('/deal/<int:deal_id>')
def get_deal(deal_id):
    """Get single deal by ID"""
    deal = Deal.query.get_or_404(deal_id)
    return jsonify(deal.to_dict())

@bp.route('/stats')
def get_stats():
    """Get site statistics"""
    total_deals = Deal.query.filter(Deal.price <= 100).count()
    active_deals = Deal.query.filter(
        Deal.price <= 100,
        Deal.is_expired == False
    ).count()
    expired_deals = Deal.query.filter(
        Deal.price <= 100,
        Deal.is_expired == True
    ).count()
    
    return jsonify({
        'total_deals': total_deals,
        'active_deals': active_deals,
        'expired_deals': expired_deals
    })