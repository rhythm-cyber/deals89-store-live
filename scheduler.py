import schedule
import time
import logging
from datetime import datetime, timedelta, timezone
import os
import shutil
from models import Deal, BlogArticle, BlogCategory, db
from app import app

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_blog_categories():
    """Create default blog categories if they don't exist"""
    with app.app_context():
        categories = [
            {'name': 'Electronics', 'slug': 'electronics', 'description': 'Latest electronics deals and reviews'},
            {'name': 'Fashion', 'slug': 'fashion', 'description': 'Fashion trends and clothing deals'},
            {'name': 'Home & Kitchen', 'slug': 'home-kitchen', 'description': 'Home appliances and kitchen essentials'},
            {'name': 'Books', 'slug': 'books', 'description': 'Book reviews and reading recommendations'},
            {'name': 'Health & Beauty', 'slug': 'health-beauty', 'description': 'Health products and beauty essentials'},
            {'name': 'Deals & Offers', 'slug': 'deals-offers', 'description': 'Best deals and special offers'},
        ]
        
        for cat_data in categories:
            existing = BlogCategory.query.filter_by(slug=cat_data['slug']).first()
            if not existing:
                category = BlogCategory(
                    name=cat_data['name'],
                    slug=cat_data['slug'],
                    description=cat_data['description']
                )
                db.session.add(category)
        
        db.session.commit()
        logger.info("Blog categories created/updated successfully")

def generate_daily_blog_content():
    """Generate daily blog articles"""
    try:
        with app.app_context():
            from blog_generator import generate_daily_content
            
            logger.info("Starting daily blog content generation...")
            
            # Ensure categories exist
            create_blog_categories()
            
            # Generate content
            articles_created = generate_daily_content()
            
            if articles_created:
                logger.info(f"Successfully generated {len(articles_created)} blog articles")
                for article in articles_created:
                    logger.info(f"Created article: {article.title}")
                return len(articles_created)
            else:
                logger.warning("No articles were generated")
                return 0
                
    except Exception as e:
        logger.error(f"Error generating daily blog content: {str(e)}")
        return 0

def daily_social_media_posting():
    """Post daily deals to social media"""
    try:
        logger.info("Daily social media posting - placeholder function")
        return "Social media posting completed"
    except Exception as e:
        logger.error(f"Error in social media posting: {e}")
        return None

def send_daily_newsletter():
    """Send daily newsletter"""
    try:
        logger.info("Daily newsletter sending - placeholder function")
        return "Newsletter sent"
    except Exception as e:
        logger.error(f"Error sending newsletter: {e}")
        return None

def cleanup_expired_deals():
    """Delete deals older than 7 days"""
    with app.app_context():
        try:
            # Calculate cutoff date (7 days ago)
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
            
            # Find expired deals
            expired_deals = Deal.query.filter(Deal.pub_date < cutoff_date).all()
            
            count = len(expired_deals)
            
            # Delete expired deals
            for deal in expired_deals:
                db.session.delete(deal)
            
            db.session.commit()
            
            logger.info(f"Cleanup completed: Deleted {count} expired deals")
            return count
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            db.session.rollback()
            return 0

def mark_expired_deals():
    """Mark deals as expired if they're older than 3 days"""
    with app.app_context():
        try:
            # Calculate cutoff date (3 days ago)
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=3)
            
            # Find deals to mark as expired
            deals_to_expire = Deal.query.filter(
                Deal.pub_date < cutoff_date,
                Deal.is_expired == False
            ).all()
            
            count = len(deals_to_expire)
            
            # Mark as expired
            for deal in deals_to_expire:
                deal.is_expired = True
            
            db.session.commit()
            
            logger.info(f"Marked {count} deals as expired")
            return count
            
        except Exception as e:
            logger.error(f"Error marking deals as expired: {e}")
            db.session.rollback()
            return 0

def daily_social_media_posting():
    """Post daily deals to social media"""
    with app.app_context():
        try:
            result = post_daily_deals()
            logger.info(f"Daily social media posting completed: {result}")
            return result
        except Exception as e:
            logger.error(f"Error during daily posting: {e}")
            return {'telegram_posts': 0, 'facebook_posts': 0, 'total_posts': 0}

def backup_database():
    """Create a backup of the database"""
    with app.app_context():
        try:
            import shutil
            from pathlib import Path
            
            # Create backup directory if it doesn't exist
            backup_dir = Path('backups')
            backup_dir.mkdir(exist_ok=True)
            
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"deals_{timestamp}.db"
            backup_path = backup_dir / backup_filename
            
            # Copy database file
            db_path = Path('instance/deals.db')
            if db_path.exists():
                shutil.copy2(db_path, backup_path)
                logger.info(f"Database backup created: {backup_path}")
                
                # Keep only last 7 backups
                backups = sorted(backup_dir.glob('deals_*.db'), key=os.path.getmtime, reverse=True)
                for old_backup in backups[7:]:
                    old_backup.unlink()
                    logger.info(f"Removed old backup: {old_backup}")
                
                return str(backup_path)
            else:
                logger.warning("Database file not found for backup")
                return None
                
        except Exception as e:
            logger.error(f"Error during database backup: {e}")
            return None

def health_check():
    """Basic health check and statistics"""
    with app.app_context():
        try:
            total_deals = Deal.query.count()
            active_deals = Deal.query.filter(Deal.is_expired == False, Deal.price <= 1000).count()
            expired_deals = Deal.query.filter(Deal.is_expired == True).count()
            
            # Check for deals posted in last 24 hours
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            recent_deals = Deal.query.filter(Deal.pub_date >= yesterday).count()
            
            health_data = {
                'total_deals': total_deals,
                'active_deals': active_deals,
                'expired_deals': expired_deals,
                'recent_deals': recent_deals,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Health Check - Total: {total_deals}, Active: {active_deals}, "
                       f"Expired: {expired_deals}, Recent (24h): {recent_deals}")
            
            # Alert if no recent deals
            if recent_deals == 0:
                logger.warning("No deals added in the last 24 hours!")
            
            return health_data
            
        except Exception as e:
            logger.error(f"Error during health check: {e}")
            return None

def setup_scheduler():
    """Setup all scheduled jobs"""
    
    # Daily blog content generation at 7:00 AM
    schedule.every().day.at("07:00").do(generate_daily_blog_content)
    
    # Daily social media posting at 9:00 AM
    schedule.every().day.at("09:00").do(daily_social_media_posting)
    
    # Daily newsletter at 8:00 AM
    schedule.every().day.at("08:00").do(send_daily_newsletter)
    
    # Cleanup expired deals at 3:00 AM
    schedule.every().day.at("03:00").do(cleanup_expired_deals)
    
    # Mark deals as expired at 2:00 AM
    schedule.every().day.at("02:00").do(mark_expired_deals)
    
    # Database backup at 1:00 AM
    schedule.every().day.at("01:00").do(backup_database)
    
    # Health check every 6 hours
    schedule.every(6).hours.do(health_check)
    
    logger.info("Scheduler setup complete:")
    logger.info("- Daily blog content generation: 7:00 AM")
    logger.info("- Daily social media posting: 9:00 AM")
    logger.info("- Daily newsletter: 8:00 AM")
    logger.info("- Database backup: 1:00 AM")
    logger.info("- Mark expired deals: 2:00 AM")
    logger.info("- Cleanup old deals: 3:00 AM")
    logger.info("- Health check: Every 6 hours")

def run_scheduler():
    """Run the scheduler continuously"""
    setup_scheduler()
    
    logger.info("Scheduler started. Press Ctrl+C to stop.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user.")
    except Exception as e:
        logger.error(f"Scheduler error: {e}")
        raise

# Manual execution functions for testing
def run_cleanup():
    """Manually run cleanup"""
    return cleanup_expired_deals()

def run_expire_marking():
    """Manually run expire marking"""
    return mark_expired_deals()

def run_social_posting():
    """Manually run social media posting"""
    return daily_social_media_posting()

def run_health_check():
    """Manually run health check"""
    return health_check()

def run_backup():
    """Manually run database backup"""
    return backup_database()

def run_blog_generation():
    """Manually run blog content generation"""
    return generate_daily_blog_content()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "cleanup":
            result = run_cleanup()
            print(f"Cleanup result: {result} deals deleted")
        
        elif command == "expire":
            result = run_expire_marking()
            print(f"Expire marking result: {result} deals marked as expired")
        
        elif command == "post":
            result = run_social_posting()
            print(f"Social posting result: {result}")
        
        elif command == "health":
            result = run_health_check()
            print(f"Health check result: {result}")
        
        elif command == "backup":
            result = run_backup()
            print(f"Backup result: {result}")
        
        elif command == "blog":
            result = run_blog_generation()
            print(f"Blog generation result: {result} articles created")
        
        elif command == "run":
            run_scheduler()
        
        else:
            print("Usage: python scheduler.py [cleanup|expire|post|health|backup|blog|run]")
            print("  cleanup - Delete expired deals")
            print("  expire  - Mark old deals as expired")
            print("  post    - Post deals to social media")
            print("  health  - Run health check")
            print("  backup  - Create database backup")
            print("  blog    - Generate daily blog content")
            print("  run     - Start continuous scheduler")
    
    else:
        print("Starting scheduler...")
        run_scheduler()