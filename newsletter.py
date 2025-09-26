#!/usr/bin/env python3
"""
Newsletter management system for sending daily deals to subscribers.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
from models import Newsletter, Deal, db
from app import app
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsletterManager:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_username)
        self.site_url = os.getenv('SITE_URL', 'https://deals89.store')
    
    def send_daily_newsletter(self):
        """Send daily newsletter to all active subscribers"""
        with app.app_context():
            try:
                # Get active subscribers
                subscribers = Newsletter.query.filter_by(
                    is_active=True,
                    is_verified=True
                ).all()
                
                if not subscribers:
                    logger.info("No active subscribers found")
                    return 0
                
                # Get today's deals
                today = datetime.now(timezone.utc).date()
                deals = Deal.query.filter(
                    Deal.price <= 1000,
                    Deal.is_expired == False,
                    Deal.pub_date >= today
                ).order_by(Deal.pub_date.desc()).limit(10).all()
                
                if not deals:
                    logger.info("No deals found for today")
                    return 0
                
                # Generate email content
                html_content = self._generate_email_html(deals)
                text_content = self._generate_email_text(deals)
                
                # Send emails
                sent_count = 0
                for subscriber in subscribers:
                    try:
                        if self._send_email(subscriber.email, html_content, text_content, subscriber.verification_token):
                            sent_count += 1
                    except Exception as e:
                        logger.error(f"Failed to send email to {subscriber.email}: {e}")
                
                logger.info(f"Newsletter sent to {sent_count}/{len(subscribers)} subscribers")
                return sent_count
                
            except Exception as e:
                logger.error(f"Error sending daily newsletter: {e}")
                return 0
    
    def _send_email(self, to_email, html_content, text_content, unsubscribe_token):
        """Send email to a single subscriber"""
        if not self.smtp_username or not self.smtp_password:
            logger.warning("SMTP credentials not configured")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Daily Deals Under ₹1000 - {datetime.now().strftime('%B %d, %Y')}"
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Add unsubscribe link to content
            unsubscribe_url = f"{self.site_url}/newsletter/unsubscribe/{unsubscribe_token}"
            html_content = html_content.replace('{{UNSUBSCRIBE_URL}}', unsubscribe_url)
            text_content = text_content.replace('{{UNSUBSCRIBE_URL}}', unsubscribe_url)
            
            # Attach parts
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            return False
    
    def _generate_email_html(self, deals):
        """Generate HTML email content"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Daily Deals - Deals89</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }}
                .deal {{ border-bottom: 1px solid #eee; padding: 20px; }}
                .deal:last-child {{ border-bottom: none; }}
                .deal-title {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #333; }}
                .deal-price {{ font-size: 24px; font-weight: bold; color: #e74c3c; margin-bottom: 10px; }}
                .deal-summary {{ color: #666; margin-bottom: 15px; line-height: 1.5; }}
                .deal-button {{ display: inline-block; background-color: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold; }}
                .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 12px; }}
                .unsubscribe {{ color: #999; text-decoration: none; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔥 Daily Deals Under ₹1000</h1>
                    <p>Amazing products at unbeatable prices!</p>
                </div>
        """
        
        for deal in deals:
            html += f"""
                <div class="deal">
                    <div class="deal-title">{deal.title}</div>
                    <div class="deal-price">₹{deal.price:.0f}</div>
                    {f'<div class="deal-summary">{deal.summary}</div>' if deal.summary else ''}
                    <a href="{deal.affiliate_url}" class="deal-button">Buy Now</a>
                </div>
            """
        
        html += f"""
                <div class="footer">
                    <p>© 2024 Deals89. All rights reserved.</p>
                    <p><a href="{{{{UNSUBSCRIBE_URL}}}}" class="unsubscribe">Unsubscribe</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_email_text(self, deals):
        """Generate plain text email content"""
        text = f"""
Daily Deals Under ₹1000 - {datetime.now().strftime('%B %d, %Y')}
================================================================

Amazing products at unbeatable prices!

"""
        
        for i, deal in enumerate(deals, 1):
            text += f"""
{i}. {deal.title}
   Price: ₹{deal.price:.0f}
   {deal.summary if deal.summary else ''}
   Buy Now: {deal.affiliate_url}

"""
        
        text += """
================================================================
© 2024 Deals89. All rights reserved.
Unsubscribe: {{UNSUBSCRIBE_URL}}
"""
        
        return text

def send_daily_newsletter():
    """Function to be called by scheduler"""
    newsletter_manager = NewsletterManager()
    return newsletter_manager.send_daily_newsletter()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "send":
        result = send_daily_newsletter()
        print(f"Newsletter sent to {result} subscribers")
    else:
        print("Usage: python newsletter.py send")