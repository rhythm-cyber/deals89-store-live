import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import re
import os
from decimal import Decimal

def canonicalize_url(url):
    """Remove tracking parameters and affiliate tags to get canonical URL"""
    parsed = urlparse(url)
    
    # Parameters to remove for canonicalization
    params_to_remove = [
        'tag', 'affid', 'ref', 'utm_source', 'utm_medium', 'utm_campaign',
        'utm_term', 'utm_content', 'gclid', 'fbclid', 'msclkid'
    ]
    
    query_params = parse_qs(parsed.query)
    
    # Remove tracking parameters
    for param in params_to_remove:
        query_params.pop(param, None)
    
    # Rebuild query string
    new_query = urlencode(query_params, doseq=True)
    
    # Return canonical URL
    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        ''  # Remove fragment
    ))

def add_affiliate_tag(url):
    """Add affiliate tag to URL if missing"""
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    
    # Amazon affiliate tag
    if 'amazon.' in parsed.netloc.lower():
        if 'tag' not in query_params:
            query_params['tag'] = [os.getenv('AMAZON_AFFILIATE_TAG', 'deals89-21')]
    
    # Flipkart affiliate tag
    elif 'flipkart.' in parsed.netloc.lower():
        if 'affid' not in query_params:
            query_params['affid'] = [os.getenv('FLIPKART_AFFILIATE_ID', 'deals89')]
    
    # Rebuild URL with affiliate tag
    new_query = urlencode(query_params, doseq=True)
    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))

def fetch_metadata(url):
    """Fetch title, description, image, and price from URL with enhanced anti-bot measures and caching"""
    # Check cache first
    try:
        from cache_manager import get_cache
        cache = get_cache()
        cached_result = cache.get(url)
        if cached_result:
            print(f"Using cached metadata for: {url}")
            return cached_result
    except ImportError:
        print("Cache manager not available")
    except Exception as e:
        print(f"Cache error: {e}")
    
    try:
        # Enhanced user agents with more realistic browser fingerprints
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0'
        ]
        
        import random
        import time
        
        # Create a session for cookie persistence
        session = requests.Session()
        
        for attempt in range(len(user_agents)):
            try:
                # Enhanced headers with more realistic browser behavior
                headers = {
                    'User-Agent': user_agents[attempt],
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'cross-site',
                    'Sec-Fetch-User': '?1',
                    'Cache-Control': 'max-age=0',
                    'Referer': 'https://www.google.com/',
                    'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
                    'Sec-Ch-Ua-Mobile': '?0',
                    'Sec-Ch-Ua-Platform': '"Windows"'
                }
                
                # Add random delay with exponential backoff
                if attempt > 0:
                    delay = random.uniform(2, 5) * (attempt + 1)
                    time.sleep(delay)
                
                # Make request with session for cookie persistence
                response = session.get(url, headers=headers, timeout=30, allow_redirects=True)
                response.raise_for_status()
                
                # Enhanced bot detection checks
                content_length = len(response.content)
                response_text = response.text.lower()
                
                # Check for various bot detection indicators
                bot_indicators = [
                    "robot", "captcha", "blocked", "access denied", 
                    "forbidden", "rate limit", "too many requests",
                    "security check", "verify you are human", "cloudflare"
                ]
                
                is_blocked = (
                    content_length < 5000 or  # Very small response
                    any(indicator in response_text for indicator in bot_indicators) or
                    response.status_code in [403, 429, 503] or
                    "text/html" not in response.headers.get('content-type', '').lower()
                )
                
                if is_blocked and attempt < len(user_agents) - 1:
                    print(f"Attempt {attempt + 1} blocked, trying next user agent...")
                    continue  # Try next user agent
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract title with multiple fallbacks
                title = None
                title_selectors = [
                    'meta[property="og:title"]',
                    'meta[name="twitter:title"]',
                    'title',
                    'h1',
                    '#productTitle',
                    '.product-title'
                ]
                
                for selector in title_selectors:
                    element = soup.select_one(selector)
                    if element:
                        if element.name == 'meta':
                            title = element.get('content')
                        else:
                            title = element.get_text().strip()
                        if title and len(title) > 5 and title.lower() not in ['amazon.in', 'flipkart']:
                            break
                
                # Extract description with multiple fallbacks
                description = None
                desc_selectors = [
                    'meta[property="og:description"]',
                    'meta[name="description"]',
                    'meta[name="twitter:description"]',
                    '.product-description',
                    '#feature-bullets'
                ]
                
                for selector in desc_selectors:
                    element = soup.select_one(selector)
                    if element:
                        if element.name == 'meta':
                            description = element.get('content')
                        else:
                            description = element.get_text().strip()
                        if description and len(description) > 10:
                            break
                
                # Extract image with enhanced selectors
                image_url = None
                image_selectors = [
                    'meta[property="og:image"]',
                    'meta[name="twitter:image"]',
                    'img[data-old-hires]',
                    'img[data-a-dynamic-image]',
                    '#landingImage',
                    '.a-dynamic-image',
                    '.product-image img',
                    '.main-image img'
                ]
                
                for selector in image_selectors:
                    img_element = soup.select_one(selector)
                    if img_element:
                        if img_element.name == 'meta':
                            image_url = img_element.get('content')
                        else:
                            image_url = (img_element.get('src') or 
                                       img_element.get('data-old-hires') or 
                                       img_element.get('data-a-dynamic-image') or
                                       img_element.get('data-src'))
                        if image_url:
                            # Handle relative URLs
                            if image_url.startswith('//'):
                                image_url = 'https:' + image_url
                            elif image_url.startswith('/'):
                                from urllib.parse import urljoin
                                image_url = urljoin(url, image_url)
                            break
                
                # Extract price
                price = extract_price(soup, url)
                
                # If we got meaningful data, return it and cache it
                if title and title.lower() not in ['amazon.in', 'flipkart', 'error']:
                    result = {
                        'title': title or 'No title found',
                        'description': description or 'No description found',
                        'image_url': image_url,
                        'price': price
                    }
                    
                    # Cache successful result
                    try:
                        from cache_manager import get_cache
                        cache = get_cache()
                        cache.set(url, result)
                        print(f"Cached metadata for: {url}")
                    except Exception as e:
                        print(f"Failed to cache result: {e}")
                    
                    return result
                
            except requests.exceptions.RequestException as e:
                if attempt < len(user_agents) - 1:
                    continue  # Try next user agent
                else:
                    raise e
        
        # If all attempts failed, try Selenium as fallback
        try:
            from selenium_fetcher import fetch_with_selenium, extract_metadata_from_html
            print("Regular requests failed, trying Selenium fallback...")
            
            html_content = fetch_with_selenium(url)
            if html_content:
                 selenium_result = extract_metadata_from_html(html_content, url)
                 if selenium_result and selenium_result.get('title') != 'No title found':
                     print("Selenium fallback successful!")
                     
                     # Cache successful Selenium result
                     try:
                         from cache_manager import get_cache
                         cache = get_cache()
                         cache.set(url, selenium_result)
                         print(f"Cached Selenium result for: {url}")
                     except Exception as e:
                         print(f"Failed to cache Selenium result: {e}")
                     
                     return selenium_result
        except ImportError:
            print("Selenium not available, install with: pip install selenium")
        except Exception as e:
            print(f"Selenium fallback failed: {e}")
        
        # If all attempts failed, return error
        return {
            'title': 'Unable to fetch title (all methods failed)',
            'description': 'Unable to fetch description (all methods failed)',
            'image_url': None,
            'price': None
        }
        
    except Exception as e:
        print(f"Error fetching metadata: {e}")
        return {
            'title': 'Error fetching title',
            'description': 'Error fetching description',
            'image_url': None,
            'price': None
        }

def extract_price(soup, url):
    """Extract price from webpage"""
    price_patterns = [
        r'₹\s*(\d+(?:,\d+)*(?:\.\d+)?)',
        r'Rs\.?\s*(\d+(?:,\d+)*(?:\.\d+)?)',
        r'INR\s*(\d+(?:,\d+)*(?:\.\d+)?)',
        r'(\d+(?:,\d+)*(?:\.\d+)?)\s*₹'
    ]
    
    # Enhanced price selectors for Amazon and other sites
    price_selectors = [
        'meta[property="product:price:amount"]',
        'meta[property="og:price:amount"]',
        'meta[name="price"]',
        '.a-price-whole',
        '.a-price .a-offscreen',
        '.a-price-range .a-price .a-offscreen',
        '.a-price.a-text-price.a-size-medium.apexPriceToPay .a-offscreen',
        '.a-price-current .a-price-whole',
        '.a-price-current .a-offscreen',
        '[data-price]',
        '.price',
        '.notranslate',
        '#priceblock_dealprice',
        '#priceblock_ourprice',
        '.a-size-medium.a-color-price',
        '.a-price.a-text-price.a-size-medium.apexPriceToPay',
        '.a-price-symbol + .a-price-whole'
    ]
    
    # Check meta tags first
    for selector in price_selectors[:3]:
        meta_tag = soup.select_one(selector)
        if meta_tag:
            content = meta_tag.get('content') or meta_tag.get('value')
            if content:
                for pattern in price_patterns:
                    match = re.search(pattern, content)
                    if match:
                        price_str = match.group(1).replace(',', '')
                        try:
                            price = Decimal(price_str)
                            if 1 <= price <= 100000:  # Reasonable price range
                                return price
                        except:
                            continue
    
    # Check price elements
    for selector in price_selectors[3:]:
        elements = soup.select(selector)
        for element in elements:
            text = element.get_text().strip()
            if text:
                for pattern in price_patterns:
                    match = re.search(pattern, text)
                    if match:
                        price_str = match.group(1).replace(',', '')
                        try:
                            price = Decimal(price_str)
                            if 1 <= price <= 100000:  # Reasonable price range
                                return price
                        except:
                            continue
    
    # Search in entire page text as last resort
    page_text = soup.get_text()
    for pattern in price_patterns:
        matches = re.findall(pattern, page_text)
        if matches:
            # Take the first reasonable price found
            for match in matches:
                price_str = match.replace(',', '')
                try:
                    price = Decimal(price_str)
                    if 1 <= price <= 100000:  # Reasonable price range
                        return price
                except:
                    continue
    
    return None

def validate_price(price):
    """Validate that price is reasonable (between ₹1 and ₹200,000)"""
    if price is None:
        return False
    try:
        price_decimal = Decimal(str(price))
        return Decimal('1') <= price_decimal <= Decimal('200000')
    except:
        return False