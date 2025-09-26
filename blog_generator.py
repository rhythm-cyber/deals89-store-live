import random
import json
from datetime import datetime, timedelta, timezone
from models import db, BlogArticle, BlogCategory, Deal, Admin
from utils import fetch_metadata
import re
from typing import List, Dict, Any

class BlogContentGenerator:
    """
    Advanced blog content generator that creates high-quality, human-like articles
    with integrated affiliate products and engaging content.
    """
    
    def __init__(self):
        self.article_templates = self._load_article_templates()
        self.content_patterns = self._load_content_patterns()
        self.categories = [
            'Technology Reviews', 'Shopping Guides', 'Deal Analysis', 
            'Product Comparisons', 'Lifestyle Tips', 'Tech News',
            'Budget Shopping', 'Premium Products', 'Seasonal Deals'
        ]
    
    def _load_article_templates(self) -> Dict[str, List[str]]:
        """Load various article templates for different content types"""
        return {
            'product_review': [
                "In-Depth Review: {product_name} - Is It Worth Your Money?",
                "Comprehensive Analysis: {product_name} Performance and Value",
                "Real User Experience: {product_name} After 30 Days of Testing",
                "Expert Review: {product_name} - Pros, Cons, and Final Verdict"
            ],
            'buying_guide': [
                "Ultimate Buying Guide: How to Choose the Perfect {category}",
                "Smart Shopping: Top {category} Features You Should Consider",
                "Budget vs Premium: Finding the Right {category} for Your Needs",
                "Complete Guide: Everything You Need to Know About {category}"
            ],
            'comparison': [
                "Head-to-Head: {product1} vs {product2} - Which Wins?",
                "Battle of the Brands: Comparing Top {category} Options",
                "Price vs Performance: Analyzing the Best {category} Deals",
                "Feature Showdown: Finding the Best {category} for You"
            ],
            'deal_analysis': [
                "Deal Alert: Why {product_name} at ₹{price} is a Steal",
                "Price Drop Analysis: {product_name} Hits All-Time Low",
                "Limited Time Offer: {product_name} Deal Breakdown",
                "Smart Shopping: {product_name} Deal Worth Your Attention"
            ]
        }
    
    def _load_content_patterns(self) -> Dict[str, List[str]]:
        """Load content patterns for natural article generation"""
        return {
            'introduction_hooks': [
                "In today's fast-paced digital world, finding the right {category} can be overwhelming.",
                "With countless options available in the market, choosing the perfect {category} requires careful consideration.",
                "Whether you're a tech enthusiast or a casual user, understanding {category} features is crucial.",
                "The {category} market has evolved significantly, offering consumers more choices than ever before.",
                "Smart shopping begins with understanding what makes a {category} truly worth your investment."
            ],
            'transition_phrases': [
                "Let's dive deeper into the details.",
                "Here's what you need to know.",
                "Moving on to the key features.",
                "Now, let's examine the performance aspects.",
                "It's important to consider the following factors.",
                "The real question is whether this meets your needs.",
                "From a practical standpoint, here's what matters most."
            ],
            'conclusion_starters': [
                "After thorough analysis and testing,",
                "Based on our comprehensive review,",
                "Taking everything into consideration,",
                "From both performance and value perspectives,",
                "Weighing all the pros and cons,"
            ]
        }
    
    def generate_slug(self, title: str) -> str:
        """Generate SEO-friendly slug from title"""
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
    def get_random_deals(self, count: int = 3, category: str = None) -> List[Deal]:
        """Get random active deals for article integration"""
        query = Deal.query.filter(Deal.is_expired == False)
        if category:
            query = query.filter(Deal.category.ilike(f'%{category}%'))
        return query.order_by(db.func.random()).limit(count).all()
    
    def format_deal_for_article(self, deal):
        """Format a deal for inclusion in article content"""
        return {
            'title': deal.title,
            'price': f"₹{deal.price:.2f}",
            'affiliate_url': deal.affiliate_url,
            'image_url': deal.image_url,
            'summary': deal.summary,
            'category': deal.category
        }
    
    def generate_affiliate_section(self, deals):
        """Generate HTML section with affiliate products"""
        if not deals:
            return ""
        
        html = '<div class="affiliate-products-section my-8">\n'
        html += '<h3 class="text-2xl font-bold text-gray-900 mb-6">🔥 Featured Deals</h3>\n'
        html += '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">\n'
        
        for deal in deals:
            deal_data = self.format_deal_for_article(deal)
            html += f'''
    <div class="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300">
        <div class="aspect-w-16 aspect-h-9">
            <img src="{deal_data['image_url'] or '/static/images/placeholder.jpg'}" 
                 alt="{deal_data['title']}" 
                 class="w-full h-48 object-cover">
        </div>
        <div class="p-4">
            <h4 class="font-semibold text-gray-900 mb-2 line-clamp-2">{deal_data['title']}</h4>
            <p class="text-gray-600 text-sm mb-3 line-clamp-2">{deal_data['summary'] or 'Great deal available now!'}</p>
            <div class="flex items-center justify-between">
                <span class="text-2xl font-bold text-green-600">{deal_data['price']}</span>
                <a href="{deal_data['affiliate_url']}" 
                   target="_blank" 
                   rel="nofollow sponsored"
                   class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors text-sm font-medium">
                    View Deal
                </a>
            </div>
            <div class="mt-2">
                <span class="inline-block bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded-full">
                    {deal_data['category'] or 'Deal'}
                </span>
            </div>
        </div>
    </div>'''
        
        html += '\n</div>\n'
        html += '<p class="text-sm text-gray-500 mt-4 text-center">💡 <em>As an Amazon Associate, we earn from qualifying purchases. Prices may vary.</em></p>\n'
        html += '</div>\n'
        
        return html
    
    def generate_product_focused_content(self, deal: Deal, word_count: int = 2500) -> str:
        """Generate detailed product-focused content"""
        sections = []
        
        # Introduction
        intro_hook = random.choice(self.content_patterns['introduction_hooks']).format(
            category=deal.category or 'product'
        )
        sections.append(f"<p>{intro_hook} Today, we're taking an in-depth look at the {deal.title}, "
                       f"currently available at an attractive price of ₹{deal.price}. This comprehensive "
                       f"review will help you understand whether this product deserves a place in your "
                       f"shopping cart.</p>")
        
        # Product Overview
        sections.append(f"<h2>Product Overview: {deal.title}</h2>")
        sections.append(f"<p>The {deal.title} has been making waves in the {deal.category or 'technology'} "
                       f"market, and for good reason. With its competitive pricing at ₹{deal.price}, "
                       f"it offers a compelling value proposition that's hard to ignore. Let's break down "
                       f"what makes this product stand out from the competition.</p>")
        
        # Key Features Section
        sections.append("<h2>Key Features and Specifications</h2>")
        sections.append(f"<p>When evaluating the {deal.title}, several features immediately catch attention. "
                       f"The build quality reflects careful engineering, while the design philosophy "
                       f"balances functionality with aesthetic appeal. Performance benchmarks consistently "
                       f"show reliable results across various usage scenarios.</p>")
        
        sections.append(f"<p>The price point of ₹{deal.price} positions this product strategically in the "
                       f"market, offering premium features without the premium price tag. This makes it "
                       f"particularly attractive for budget-conscious consumers who refuse to compromise "
                       f"on quality.</p>")
        
        # Add affiliate products section
        related_deals = self.get_random_deals(3)
        if related_deals:
            affiliate_section = self.generate_affiliate_section(related_deals)
            sections.append(affiliate_section)
        
        # Performance Analysis
        sections.append("<h2>Performance Analysis</h2>")
        sections.append(f"<p>Real-world testing reveals that the {deal.title} delivers consistent performance "
                       f"across different usage patterns. Whether you're using it for daily tasks or more "
                       f"demanding applications, the product maintains stability and efficiency.</p>")
        
        sections.append(f"<p>Battery life, processing speed, and overall responsiveness meet or exceed "
                       f"expectations for products in this price range. The ₹{deal.price} investment "
                       f"translates into reliable performance that justifies the cost.</p>")
        
        # Value Proposition
        sections.append("<h2>Value for Money Assessment</h2>")
        sections.append(f"<p>At ₹{deal.price}, the {deal.title} offers exceptional value when compared to "
                       f"similar products in the market. The feature-to-price ratio is particularly "
                       f"impressive, making it a smart choice for informed consumers.</p>")
        
        # User Experience
        sections.append("<h2>User Experience and Practical Considerations</h2>")
        sections.append(f"<p>Daily usage reveals the thoughtful design decisions behind the {deal.title}. "
                       f"The user interface is intuitive, setup is straightforward, and ongoing maintenance "
                       f"requirements are minimal. These factors contribute significantly to the overall "
                       f"ownership experience.</p>")
        
        # Comparison with Alternatives
        sections.append("<h2>How It Compares to Alternatives</h2>")
        sections.append(f"<p>When placed alongside competing products, the {deal.title} holds its ground "
                       f"admirably. While some alternatives may offer specific advantages, the overall "
                       f"package at ₹{deal.price} provides a balanced solution that addresses most user needs.</p>")
        
        # Pros and Cons
        sections.append("<h2>Pros and Cons</h2>")
        sections.append("<h3>Advantages:</h3>")
        sections.append("<ul>")
        sections.append("<li>Competitive pricing that offers excellent value</li>")
        sections.append("<li>Reliable performance across various usage scenarios</li>")
        sections.append("<li>User-friendly design and interface</li>")
        sections.append("<li>Strong build quality and durability</li>")
        sections.append("<li>Good customer support and warranty coverage</li>")
        sections.append("</ul>")
        
        sections.append("<h3>Areas for Improvement:</h3>")
        sections.append("<ul>")
        sections.append("<li>Some advanced features could be more accessible</li>")
        sections.append("<li>Documentation could be more comprehensive</li>")
        sections.append("<li>Certain customization options are limited</li>")
        sections.append("</ul>")
        
        # Final Recommendation
        sections.append("<h2>Final Recommendation</h2>")
        conclusion_starter = random.choice(self.content_patterns['conclusion_starters'])
        sections.append(f"<p>{conclusion_starter} the {deal.title} represents a solid investment at ₹{deal.price}. "
                       f"It successfully balances performance, features, and affordability in a way that "
                       f"appeals to a broad range of users.</p>")
        
        sections.append(f"<p>Whether you're upgrading from an older model or making your first purchase "
                       f"in this category, the {deal.title} deserves serious consideration. The current "
                       f"price of ₹{deal.price} makes it even more attractive, especially if you've been "
                       f"waiting for the right deal.</p>")
        
        # Call to Action
        sections.append(f'<div class="affiliate-cta">')
        sections.append(f'<p><strong>Ready to make your purchase?</strong> You can get the {deal.title} '
                       f'at the current price of ₹{deal.price} through our affiliate link below:</p>')
        sections.append(f'<a href="{deal.affiliate_url}" class="btn btn-primary" target="_blank" rel="noopener">'
                       f'Check Current Price - ₹{deal.price}</a>')
        sections.append(f'</div>')
        
        return '\n\n'.join(sections)
    
    def generate_category_guide_content(self, category: str, deals: List[Deal], word_count: int = 2500) -> str:
        """Generate comprehensive category buying guide"""
        sections = []
        
        # Introduction
        intro_hook = random.choice(self.content_patterns['introduction_hooks']).format(category=category)
        sections.append(f"<p>{intro_hook} This comprehensive guide will walk you through everything "
                       f"you need to know about choosing the right {category}, including current market "
                       f"trends, key features to consider, and some excellent deals we've found.</p>")
        
        # Market Overview
        sections.append(f"<h2>Current {category} Market Landscape</h2>")
        sections.append(f"<p>The {category} market has seen significant evolution in recent years, with "
                       f"manufacturers focusing on improving performance while maintaining competitive "
                       f"pricing. Today's consumers have access to more options than ever before, "
                       f"ranging from budget-friendly alternatives to premium solutions.</p>")
        
        # Key Features to Consider
        sections.append(f"<h2>Essential Features to Look For</h2>")
        sections.append(f"<p>When shopping for {category}, several key factors should influence your "
                       f"decision. Understanding these elements will help you make an informed choice "
                       f"that aligns with your specific needs and budget constraints.</p>")
        
        sections.append("<h3>Performance Considerations</h3>")
        sections.append(f"<p>Performance metrics vary significantly across different {category} options. "
                       f"Consider your intended use case and prioritize features that directly impact "
                       f"your experience. Don't pay for capabilities you won't use, but ensure you "
                       f"have adequate performance for your needs.</p>")
        
        sections.append("<h3>Build Quality and Durability</h3>")
        sections.append(f"<p>Investing in well-built {category} pays dividends over time. Look for "
                       f"products with solid construction, quality materials, and good warranty "
                       f"coverage. These factors often correlate with long-term satisfaction and "
                       f"lower total cost of ownership.</p>")
        
        # Budget Considerations
        sections.append("<h2>Budget Planning and Value Assessment</h2>")
        sections.append(f"<p>Setting a realistic budget for {category} requires balancing your needs "
                       f"with available options. While it's tempting to go for the cheapest option, "
                       f"consider the long-term value proposition and total cost of ownership.</p>")
        
        # Featured Products
        if deals:
            sections.append(f"<h2>Current Top Deals in {category}</h2>")
            sections.append(f"<p>We've identified several excellent {category} deals that offer "
                           f"outstanding value for money. These products represent different price "
                           f"points and feature sets, ensuring there's something for every budget.</p>")
            
            for i, deal in enumerate(deals[:3], 1):
                sections.append(f"<h3>{i}. {deal.title} - ₹{deal.price}</h3>")
                sections.append(f"<p>The {deal.title} stands out as an excellent choice in the "
                               f"{category} category. Priced at ₹{deal.price}, it offers a compelling "
                               f"combination of features and value that makes it worth considering.</p>")
                
                sections.append(f"<p>Key highlights include reliable performance, user-friendly design, "
                               f"and strong build quality. The current price point makes it particularly "
                               f"attractive for budget-conscious shoppers who don't want to compromise "
                               f"on essential features.</p>")
                
                sections.append(f'<div class="product-cta">')
                sections.append(f'<a href="{deal.affiliate_url}" class="btn btn-outline-primary" '
                               f'target="_blank" rel="noopener">View Deal - ₹{deal.price}</a>')
                sections.append(f'</div>')
        
        # Shopping Tips
        sections.append(f"<h2>Smart Shopping Tips for {category}</h2>")
        sections.append(f"<p>Successful {category} shopping requires more than just comparing prices. "
                       f"Consider timing your purchase around sales events, reading user reviews, "
                       f"and understanding return policies. These factors can significantly impact "
                       f"your overall satisfaction with the purchase.</p>")
        
        sections.append("<h3>Research and Comparison</h3>")
        sections.append(f"<p>Invest time in researching different {category} options before making "
                       f"a decision. Compare specifications, read professional reviews, and check "
                       f"user feedback. This preparation helps ensure you choose a product that "
                       f"meets your expectations.</p>")
        
        sections.append("<h3>Timing Your Purchase</h3>")
        sections.append(f"<p>Market timing can significantly impact the price you pay for {category}. "
                       f"Keep an eye on seasonal sales, product refresh cycles, and special promotions. "
                       f"Sometimes waiting a few weeks can result in substantial savings.</p>")
        
        # Future Trends
        sections.append(f"<h2>Future Trends in {category}</h2>")
        sections.append(f"<p>The {category} industry continues to evolve, with emerging technologies "
                       f"and changing consumer preferences driving innovation. Understanding these "
                       f"trends can help you make a purchase decision that remains relevant longer.</p>")
        
        # Conclusion
        conclusion_starter = random.choice(self.content_patterns['conclusion_starters'])
        sections.append(f"<h2>Making Your Final Decision</h2>")
        sections.append(f"<p>{conclusion_starter} choosing the right {category} comes down to "
                       f"understanding your specific needs and finding the best match within your "
                       f"budget. The products highlighted in this guide represent excellent starting "
                       f"points for your research.</p>")
        
        sections.append(f"<p>Remember that the best {category} is the one that serves your needs "
                       f"effectively while providing good value for money. Take time to evaluate "
                       f"your options, and don't hesitate to ask questions or seek additional "
                       f"information before making your final decision.</p>")
        
        return '\n\n'.join(sections)
    
    def generate_article(self, article_type: str = None, target_category: str = None) -> Dict[str, Any]:
        """Generate a complete article with metadata"""
        
        # Get deals for integration
        deals = self.get_random_deals(5)
        if not deals:
            return None
        
        # Determine article type and primary deal
        if not article_type:
            article_type = random.choice(['product_review', 'buying_guide', 'comparison', 'deal_analysis'])
        
        primary_deal = deals[0]
        category = target_category or primary_deal.category or random.choice(self.categories)
        
        # Generate title based on type
        if article_type == 'product_review':
            title_template = random.choice(self.article_templates['product_review'])
            title = title_template.format(product_name=primary_deal.title)
            content = self.generate_product_focused_content(primary_deal)
        
        elif article_type == 'buying_guide':
            title_template = random.choice(self.article_templates['buying_guide'])
            title = title_template.format(category=category)
            content = self.generate_category_guide_content(category, deals)
        
        elif article_type == 'deal_analysis':
            title_template = random.choice(self.article_templates['deal_analysis'])
            title = title_template.format(product_name=primary_deal.title, price=primary_deal.price)
            content = self.generate_product_focused_content(primary_deal)
        
        else:  # comparison
            if len(deals) >= 2:
                title_template = random.choice(self.article_templates['comparison'])
                title = title_template.format(
                    product1=deals[0].title.split()[0],
                    product2=deals[1].title.split()[0],
                    category=category
                )
                content = self.generate_category_guide_content(category, deals)
            else:
                # Fallback to product review
                title_template = random.choice(self.article_templates['product_review'])
                title = title_template.format(product_name=primary_deal.title)
                content = self.generate_product_focused_content(primary_deal)
        
        # Generate metadata
        slug = self.generate_slug(title)
        excerpt = f"Comprehensive analysis of {primary_deal.title} and related products. " \
                 f"Find out if this ₹{primary_deal.price} deal is worth your investment."
        
        meta_description = f"{title[:150]}..." if len(title) > 150 else title
        
        # Generate tags
        tags = [
            category.lower().replace(' ', '-'),
            'deals',
            'reviews',
            'shopping-guide',
            primary_deal.title.split()[0].lower() if primary_deal.title else 'product'
        ]
        
        return {
            'title': title,
            'slug': slug,
            'content': content,
            'excerpt': excerpt,
            'meta_description': meta_description,
            'tags': json.dumps(tags),
            'category': category,
            'featured_image': primary_deal.image_url,
            'article_type': article_type,
            'primary_deal_id': primary_deal.id
        }
    
    def create_daily_articles(self, count: int = 2) -> List[BlogArticle]:
        """Generate and save daily articles"""
        articles = []
        
        # Ensure we have blog categories
        self._ensure_blog_categories()
        
        # Get admin user for authorship
        admin = Admin.query.first()
        if not admin:
            return articles
        
        for i in range(count):
            # Vary article types for diversity
            article_types = ['product_review', 'buying_guide', 'deal_analysis', 'comparison']
            article_type = article_types[i % len(article_types)]
            
            # Generate article data
            article_data = self.generate_article(article_type)
            if not article_data:
                continue
            
            # Get or create category
            category = BlogCategory.query.filter_by(name=article_data['category']).first()
            if not category:
                category = BlogCategory(
                    name=article_data['category'],
                    slug=self.generate_slug(article_data['category']),
                    description=f"Articles about {article_data['category']}"
                )
                db.session.add(category)
                db.session.flush()
            
            # Create article
            article = BlogArticle(
                title=article_data['title'],
                slug=article_data['slug'],
                content=article_data['content'],
                excerpt=article_data['excerpt'],
                meta_description=article_data['meta_description'],
                tags=article_data['tags'],
                featured_image=article_data['featured_image'],
                category_id=category.id,
                author_id=admin.id,
                is_published=True,
                published_at=datetime.now(timezone.utc)
            )
            
            db.session.add(article)
            articles.append(article)
        
        try:
            db.session.commit()
            print(f"Successfully created {len(articles)} articles")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating articles: {e}")
            articles = []
        
        return articles
    
    def _ensure_blog_categories(self):
        """Ensure basic blog categories exist"""
        for category_name in self.categories:
            existing = BlogCategory.query.filter_by(name=category_name).first()
            if not existing:
                category = BlogCategory(
                    name=category_name,
                    slug=self.generate_slug(category_name),
                    description=f"Articles about {category_name.lower()}"
                )
                db.session.add(category)
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error creating categories: {e}")

# Convenience function for external use
def generate_daily_content():
    """Generate daily blog content - called by scheduler"""
    generator = BlogContentGenerator()
    return generator.create_daily_articles(2)

if __name__ == "__main__":
    # Test the generator
    from app import app
    with app.app_context():
        generator = BlogContentGenerator()
        articles = generator.create_daily_articles(1)
        print(f"Generated {len(articles)} test articles")