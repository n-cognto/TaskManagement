import re
import html
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseBadRequest

class RequestSanitizationMiddleware(MiddlewareMixin):
    """
    Middleware to sanitize request inputs to prevent XSS and other injection attacks
    """
    def process_request(self, request):
        # Only process POST, PUT, and PATCH requests
        if request.method not in ('POST', 'PUT', 'PATCH'):
            return None
            
        # Clean POST data
        if hasattr(request, 'POST') and request.POST:
            self._sanitize_data(request.POST)
            
        return None
    
    def _sanitize_data(self, data):
        """Sanitize the data in-place"""
        for key in data.keys():
            if isinstance(data[key], str):
                # HTML escape the values to prevent XSS
                data[key] = html.escape(data[key])

class RequestValidationMiddleware(MiddlewareMixin):
    """
    Middleware to validate incoming requests to prevent security issues
    """
    # Patterns for common malicious inputs
    SUSPICIOUS_PATTERNS = [
        # SQL Injection
        r"['\"]\s*OR\s+['\"]\s*['\"]\s*=\s*['\"]",
        r";\s*DROP\s+TABLE",
        r";\s*DELETE\s+FROM",
        # XSS
        r"<script>",
        r"javascript:",
        # Path traversal
        r"\.\.\/",
    ]
    
    def process_request(self, request):
        # Only validate POST, PUT, and PATCH requests
        if request.method not in ('POST', 'PUT', 'PATCH'):
            return None
            
        # Check POST data
        if hasattr(request, 'POST') and request.POST:
            for key, value in request.POST.items():
                if isinstance(value, str) and self._is_suspicious(value):
                    return HttpResponseBadRequest("Invalid input detected")
                    
        return None
    
    def _is_suspicious(self, value):
        """Check if a value matches any suspicious patterns"""
        for pattern in self.SUSPICIOUS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False