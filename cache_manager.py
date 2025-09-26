#!/usr/bin/env python3
"""
Cache manager for storing successful metadata fetches
"""

import json
import time
import hashlib
import os
from pathlib import Path
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder for Decimal objects"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

class MetadataCache:
    def __init__(self, cache_dir="cache", cache_duration=3600):  # 1 hour default
        self.cache_dir = Path(cache_dir)
        self.cache_duration = cache_duration
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_key(self, url):
        """Generate a cache key from URL"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def _get_cache_file(self, cache_key):
        """Get cache file path"""
        return self.cache_dir / f"{cache_key}.json"
    
    def get(self, url):
        """Get cached metadata for URL"""
        cache_key = self._get_cache_key(url)
        cache_file = self._get_cache_file(cache_key)
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Check if cache is still valid
            if time.time() - cache_data.get('timestamp', 0) > self.cache_duration:
                # Cache expired, remove file
                cache_file.unlink()
                return None
            
            return cache_data.get('metadata')
        
        except (json.JSONDecodeError, IOError):
            # Corrupted cache file, remove it
            try:
                cache_file.unlink()
            except:
                pass
            return None
    
    def set(self, url, metadata):
        """Cache metadata for URL"""
        if not metadata or not metadata.get('title') or metadata.get('title') in [
            'No title found', 'Error fetching title', 'Unable to fetch title (all methods failed)'
        ]:
            return  # Don't cache failed fetches
        
        cache_key = self._get_cache_key(url)
        cache_file = self._get_cache_file(cache_key)
        
        cache_data = {
            'url': url,
            'metadata': metadata,
            'timestamp': time.time()
        }
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False, cls=DecimalEncoder)
        except IOError as e:
            print(f"Failed to write cache: {e}")
    
    def clear_expired(self):
        """Clear expired cache entries"""
        current_time = time.time()
        cleared_count = 0
        
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                if current_time - cache_data.get('timestamp', 0) > self.cache_duration:
                    cache_file.unlink()
                    cleared_count += 1
            
            except (json.JSONDecodeError, IOError):
                # Corrupted file, remove it
                try:
                    cache_file.unlink()
                    cleared_count += 1
                except:
                    pass
        
        return cleared_count
    
    def clear_all(self):
        """Clear all cache entries"""
        cleared_count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                cleared_count += 1
            except:
                pass
        return cleared_count
    
    def get_stats(self):
        """Get cache statistics"""
        cache_files = list(self.cache_dir.glob("*.json"))
        total_files = len(cache_files)
        valid_files = 0
        expired_files = 0
        current_time = time.time()
        
        for cache_file in cache_files:
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                if current_time - cache_data.get('timestamp', 0) <= self.cache_duration:
                    valid_files += 1
                else:
                    expired_files += 1
            except:
                expired_files += 1
        
        return {
            'total_files': total_files,
            'valid_files': valid_files,
            'expired_files': expired_files,
            'cache_duration': self.cache_duration
        }

# Global cache instance
_cache_instance = None

def get_cache():
    """Get global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = MetadataCache()
    return _cache_instance

if __name__ == "__main__":
    # Test the cache
    cache = MetadataCache()
    
    # Test data
    test_url = "https://example.com/product"
    test_metadata = {
        'title': 'Test Product',
        'description': 'Test Description',
        'image_url': 'https://example.com/image.jpg',
        'price': 999
    }
    
    # Test set and get
    cache.set(test_url, test_metadata)
    cached_data = cache.get(test_url)
    
    print("Cache test:")
    print(f"Original: {test_metadata}")
    print(f"Cached: {cached_data}")
    print(f"Match: {test_metadata == cached_data}")
    
    # Test stats
    stats = cache.get_stats()
    print(f"Cache stats: {stats}")