from django.core.cache import cache
from django.conf import settings
from django.utils.encoding import force_str
import hashlib
import time

def generate_cache_key(prefix, args=None, kwargs=None):
    """Generate a unique cache key based on the prefix and arguments"""
    h = hashlib.md5()
    
    # Add prefix to key
    key_parts = [prefix]
    
    # Add args to key if provided
    if args:
        for arg in args:
            key_parts.append(force_str(arg))
    
    # Add kwargs to key if provided
    if kwargs:
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={force_str(v)}")
    
    key_string = ":".join(key_parts)
    h.update(key_string.encode('utf-8'))
    
    # Add version to the key
    version = getattr(settings, 'CACHE_VERSION', 1)
    return f"{prefix}:{h.hexdigest()}:{version}"

def cache_result(timeout=300, prefix=None):
    """Decorator for caching function results"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate a unique cache key
            cache_prefix = prefix or f"cache:{func.__module__}:{func.__name__}"
            cache_key = generate_cache_key(cache_prefix, args, kwargs)
            
            # Try to get the result from cache
            result = cache.get(cache_key)
            
            # If not in cache, call the function and cache the result
            if result is None:
                result = func(*args, **kwargs)
                cache.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator

def invalidate_cache(prefix):
    """Invalidate all cache entries with the given prefix"""
    # This is a simplistic implementation - in production with Redis, 
    # you'd use pattern matching to find and delete keys
    if hasattr(cache, 'delete_pattern'):
        # Redis-specific implementation
        cache.delete_pattern(f"{prefix}:*")
    else:
        # Fallback for other cache backends - less efficient
        # For a real implementation, consider using a registry of keys
        pass

def task_cache_key(task_id):
    """Generate a cache key for a specific task"""
    return f"task:{task_id}:{settings.CACHE_VERSION}"

def project_cache_key(project_id):
    """Generate a cache key for a specific project"""
    return f"project:{project_id}:{settings.CACHE_VERSION}"

def user_tasks_cache_key(user_id):
    """Generate a cache key for a user's tasks"""
    return f"user:{user_id}:tasks:{settings.CACHE_VERSION}"