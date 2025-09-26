import os
import requests
import json
from datetime import datetime
from models import Deal, db
import facebook

class TelegramBot:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.channel_id = os.getenv('TELEGRAM_CHANNEL_ID')
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def send_deal(self, deal):
        """Send a single deal to Telegram channel"""
        if not self.bot_token or not self.channel_id:
            print("Telegram credentials not configured")
            return False
        
        try:
            # Format message
            message = self._format_deal_message(deal)
            
            # Send message with photo if available
            if deal.image_url:
                success = self._send_photo_message(message, deal.image_url)
            else:
                success = self._send_text_message(message)
            
            if success:
                # Mark as posted
                deal.posted_telegram = True
                db.session.commit()
                print(f"Successfully posted deal {deal.id} to Telegram")
                return True
            
        except Exception as e:
            print(f"Error posting to Telegram: {e}")
        
        return False
    
    def send_daily_deals(self, deals):
        """Send multiple deals to Telegram channel"""
        success_count = 0
        
        for deal in deals:
            if self.send_deal(deal):
                success_count += 1
        
        return success_count
    
    def _format_deal_message(self, deal):
        """Format deal for Telegram message"""
        message = f"🔥 <b>{deal.title}</b>\n\n"
        message += f"💰 <b>Price: ₹{deal.price:.0f}</b>\n"
        
        if deal.summary:
            # Limit summary length
            summary = deal.summary[:200] + "..." if len(deal.summary) > 200 else deal.summary
            message += f"📝 {summary}\n\n"
        
        if deal.category:
            message += f"🏷️ Category: {deal.category}\n"
        
        message += f"🛒 <a href='{deal.affiliate_url}'>Buy Now</a>\n"
        message += f"📱 <a href='{os.getenv('SITE_URL', 'http://localhost:5000')}/deal/{deal.id}'>View Details</a>\n\n"
        message += "💡 <i>Under ₹1000 Deals Daily!</i>"
        
        return message
    
    def _send_photo_message(self, caption, photo_url):
        """Send message with photo"""
        url = f"{self.base_url}/sendPhoto"
        data = {
            'chat_id': self.channel_id,
            'photo': photo_url,
            'caption': caption,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, data=data)
        return response.status_code == 200
    
    def _send_text_message(self, text):
        """Send text message"""
        url = f"{self.base_url}/sendMessage"
        data = {
            'chat_id': self.channel_id,
            'text': text,
            'parse_mode': 'HTML',
            'disable_web_page_preview': False
        }
        
        response = requests.post(url, data=data)
        return response.status_code == 200

class FacebookPoster:
    def __init__(self):
        self.page_access_token = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN')
        self.page_id = os.getenv('FACEBOOK_PAGE_ID')
        self.app_id = os.getenv('FACEBOOK_APP_ID')
        self.app_secret = os.getenv('FACEBOOK_APP_SECRET')
    
    def post_deal(self, deal):
        """Post a single deal to Facebook page"""
        if not self.page_access_token or not self.page_id:
            print("Facebook credentials not configured")
            return False
        
        try:
            graph = facebook.GraphAPI(access_token=self.page_access_token)
            
            # Format message
            message = self._format_deal_message(deal)
            
            # Post with image if available
            if deal.image_url:
                success = self._post_with_image(graph, message, deal.image_url, deal.affiliate_url)
            else:
                success = self._post_text(graph, message, deal.affiliate_url)
            
            if success:
                # Mark as posted
                deal.posted_facebook = True
                db.session.commit()
                print(f"Successfully posted deal {deal.id} to Facebook")
                return True
                
        except facebook.GraphAPIError as e:
            print(f"Facebook API Error: {e}")
            # Handle specific Facebook errors
            if e.code == 190:  # Invalid access token
                print("Facebook access token expired or invalid")
            elif e.code == 100:  # Invalid parameter
                print("Invalid parameter in Facebook post")
            return False
        except Exception as e:
            print(f"Error posting to Facebook: {e}")
        
        return False
    
    def post_daily_deals(self, deals):
        """Post multiple deals to Facebook page"""
        success_count = 0
        
        for deal in deals:
            if self.post_deal(deal):
                success_count += 1
        
        return success_count
    
    def get_page_insights(self):
        """Get Facebook page insights and analytics"""
        if not self.page_access_token or not self.page_id:
            return None
        
        try:
            graph = facebook.GraphAPI(access_token=self.page_access_token)
            
            # Get page insights for the last 7 days
            insights = graph.get_object(
                id=f"{self.page_id}/insights",
                metric="page_impressions,page_reach,page_engaged_users,page_post_engagements",
                period="day",
                since="7 days ago"
            )
            
            return insights
            
        except Exception as e:
            print(f"Error getting Facebook insights: {e}")
            return None
    
    def schedule_post(self, deal, scheduled_time):
        """Schedule a post for later (requires Facebook approval for this feature)"""
        if not self.page_access_token or not self.page_id:
            print("Facebook credentials not configured")
            return False
        
        try:
            graph = facebook.GraphAPI(access_token=self.page_access_token)
            
            # Format message
            message = self._format_deal_message(deal)
            
            # Convert scheduled_time to Unix timestamp
            import time
            scheduled_timestamp = int(time.mktime(scheduled_time.timetuple()))
            
            post_data = {
                'message': message,
                'link': deal.affiliate_url,
                'scheduled_publish_time': scheduled_timestamp,
                'published': False  # This makes it scheduled
            }
            
            if deal.image_url:
                post_data['picture'] = deal.image_url
            
            result = graph.put_object(parent_object=self.page_id, connection_name='feed', **post_data)
            
            if 'id' in result:
                print(f"Successfully scheduled Facebook post for deal {deal.id}")
                return True
                
        except Exception as e:
            print(f"Error scheduling Facebook post: {e}")
        
        return False
    
    def _format_deal_message(self, deal):
        """Format deal for Facebook post"""
        message = f"🔥 {deal.title}\n\n"
        message += f"💰 Special Price: ₹{deal.price:.0f}\n"
        
        if deal.summary:
            # Limit summary length for Facebook
            summary = deal.summary[:300] + "..." if len(deal.summary) > 300 else deal.summary
            message += f"📝 {summary}\n\n"
        
        if deal.category:
            message += f"🏷️ #{deal.category.replace(' ', '')}\n"
        
        message += f"🛒 Get it now before it's gone!\n\n"
        message += "#Deals #Under1000 #Shopping #Offers #Discount"
        
        return message
    
    def _post_with_image(self, graph, message, image_url, link_url):
        """Post with image"""
        try:
            # Post as link with image
            post_data = {
                'message': message,
                'link': link_url,
                'picture': image_url
            }
            
            result = graph.put_object(parent_object=self.page_id, connection_name='feed', **post_data)
            return 'id' in result
            
        except Exception as e:
            print(f"Error posting image to Facebook: {e}")
            return False
    
    def _post_text(self, graph, message, link_url):
        """Post text with link"""
        try:
            post_data = {
                'message': f"{message}\n\n{link_url}"
            }
            
            result = graph.put_object(parent_object=self.page_id, connection_name='feed', **post_data)
            return 'id' in result
            
        except Exception as e:
            print(f"Error posting text to Facebook: {e}")
            return False

def post_daily_deals():
    """Post daily deals to both Telegram and Facebook"""
    # Get unposted deals from last 24 hours
    from datetime import datetime, timedelta, timezone
    
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    
    # Get deals that haven't been posted yet
    telegram_deals = Deal.query.filter(
        Deal.posted_telegram == False,
        Deal.is_expired == False,
        Deal.price <= 1000,
        Deal.pub_date >= yesterday
    ).order_by(Deal.pub_date.desc()).limit(10).all()
    
    facebook_deals = Deal.query.filter(
        Deal.posted_facebook == False,
        Deal.is_expired == False,
        Deal.price <= 1000,
        Deal.pub_date >= yesterday
    ).order_by(Deal.pub_date.desc()).limit(5).all()  # Facebook posts less frequently
    
    # Initialize social media clients
    telegram_bot = TelegramBot()
    facebook_poster = FacebookPoster()
    
    # Post to Telegram
    telegram_count = 0
    if telegram_deals:
        telegram_count = telegram_bot.send_daily_deals(telegram_deals)
        print(f"Posted {telegram_count} deals to Telegram")
    
    # Post to Facebook
    facebook_count = 0
    if facebook_deals:
        facebook_count = facebook_poster.post_daily_deals(facebook_deals)
        print(f"Posted {facebook_count} deals to Facebook")
    
    return {
        'telegram_posts': telegram_count,
        'facebook_posts': facebook_count,
        'total_posts': telegram_count + facebook_count
    }

if __name__ == "__main__":
    # Test posting
    from app import app
    with app.app_context():
        result = post_daily_deals()
        print(f"Daily posting complete: {result}")