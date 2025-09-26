#!/usr/bin/env python3
"""
Selenium-based web scraper for fetching deal metadata when regular requests fail
"""

import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
import os

def create_driver():
    """Create a Chrome WebDriver with stealth options"""
    chrome_options = Options()
    
    # Stealth options to avoid detection
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-plugins')
    chrome_options.add_argument('--disable-images')  # Faster loading
    chrome_options.add_argument('--disable-javascript')  # Disable JS for faster loading
    
    # Random window size to avoid fingerprinting
    window_sizes = ['1920,1080', '1366,768', '1440,900', '1536,864']
    chrome_options.add_argument(f'--window-size={random.choice(window_sizes)}')
    
    # User agent rotation
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    ]
    chrome_options.add_argument(f'--user-agent={random.choice(user_agents)}')
    
    # Run headless for production
    if os.getenv('ENVIRONMENT') == 'production':
        chrome_options.add_argument('--headless')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # Execute script to remove webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    except Exception as e:
        print(f"Failed to create Chrome driver: {e}")
        return None

def fetch_with_selenium(url, max_retries=2):
    """Fetch page content using Selenium as fallback"""
    driver = None
    
    for attempt in range(max_retries):
        try:
            driver = create_driver()
            if not driver:
                continue
                
            # Add random delay before request
            time.sleep(random.uniform(1, 3))
            
            # Navigate to URL
            driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Additional wait for dynamic content
            time.sleep(random.uniform(2, 4))
            
            # Get page source
            page_source = driver.page_source
            
            # Check if we got meaningful content
            if len(page_source) > 5000 and "captcha" not in page_source.lower():
                return page_source
                
        except (TimeoutException, WebDriverException) as e:
            print(f"Selenium attempt {attempt + 1} failed: {e}")
            
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
                driver = None
                
        # Wait before retry
        if attempt < max_retries - 1:
            time.sleep(random.uniform(3, 6))
    
    return None

def extract_metadata_from_html(html_content, url):
    """Extract metadata from HTML content"""
    if not html_content:
        return None
        
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Import extract_price from utils
    try:
        from utils import extract_price
    except ImportError:
        def extract_price(soup, url):
            return None
    
    # Extract title
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
            if title and len(title) > 5:
                break
    
    # Extract description
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
    
    # Extract image
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
    
    return {
        'title': title or 'No title found',
        'description': description or 'No description found',
        'image_url': image_url,
        'price': price
    }

if __name__ == "__main__":
    # Test the selenium fetcher
    test_url = "https://www.amazon.in/dp/B08N5WRWNW"
    print(f"Testing Selenium fetcher with: {test_url}")
    
    html = fetch_with_selenium(test_url)
    if html:
        metadata = extract_metadata_from_html(html, test_url)
        print("Extracted metadata:", metadata)
    else:
        print("Failed to fetch content with Selenium")