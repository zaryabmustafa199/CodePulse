"""
In-Memory IP Rate Limiter Middleware for CodePulse API.
Enforces strict 3 requests per IP per 1-hour window rate limit per INTERFACES.md rules.
"""

import os
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import Dict, List
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

class IPRateLimiterMiddleware(BaseHTTPMiddleware):
    """FastAPI Middleware enforcing 3 analyses per hour per client IP address."""

    def __init__(self, app, max_requests: int = 3, window_seconds: int = 3600):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_history: Dict[str, List[datetime]] = defaultdict(list)

    def is_rate_limited(self, ip_address: str) -> bool:
        """Check if IP address has exceeded request limit within the sliding window."""
        # Bypass rate limiter during automated testing runs
        if os.getenv("TESTING") == "true":
            return False

        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=self.window_seconds)

        # Filter out requests older than sliding window (1 hour)
        valid_requests = [t for t in self.request_history[ip_address] if t > cutoff]
        self.request_history[ip_address] = valid_requests

        if len(valid_requests) >= self.max_requests:
            return True

        self.request_history[ip_address].append(now)
        return False

    async def dispatch(self, request: Request, call_next):
        """Intercept analyze POST requests and enforce rate limit."""
        if request.url.path.endswith("/analyze") and request.method == "POST":
            # Extract client IP (supporting X-Forwarded-For if behind proxy)
            forwarded_for = request.headers.get("x-forwarded-for")
            if forwarded_for:
                client_ip = forwarded_for.split(",")[0].strip()
            else:
                client_ip = request.client.host if request.client else "127.0.0.1"

            if self.is_rate_limited(client_ip):
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Please wait 60 minutes before submitting another analysis (Limit: 3 requests/hour)."}
                )

        return await call_next(request)
