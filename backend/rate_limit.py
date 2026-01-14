# Rate limiting middleware for FastAPI
import time
from collections import defaultdict
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware"""
    
    def __init__(self, app, calls=100, period=60):
        super().__init__(app)
        self.calls = calls  # Max calls per period
        self.period = period  # Period in seconds
        self.clients = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host
        
        # Clean old requests
        now = time.time()
        self.clients[client_ip] = [
            req_time for req_time in self.clients[client_ip]
            if now - req_time < self.period
        ]
        
        # Check rate limit
        if len(self.clients[client_ip]) >= self.calls:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Add current request
        self.clients[client_ip].append(now)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, self.calls - len(self.clients[client_ip]))
        )
        response.headers["X-RateLimit-Reset"] = str(
            int(now + self.period)
        )
        
        return response

# Add to main.py:
# app.add_middleware(RateLimitMiddleware, calls=60, period=60)
