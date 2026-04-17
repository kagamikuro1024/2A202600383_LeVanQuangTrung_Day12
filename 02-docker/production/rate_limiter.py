"""
Rate Limiter — Sliding Window Algorithm

Limits: 10 requests per 60 seconds per user
Algorithm: Sliding window counter using in-memory deque
"""
import time
from collections import defaultdict, deque
from fastapi import HTTPException


class RateLimiter:
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        """
        Args:
            max_requests: Max requests per window (default: 10/min)
            window_seconds: Time window in seconds (default: 60)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._windows: dict[str, deque] = defaultdict(deque)

    def check(self, user_id: str) -> dict:
        """
        Check if user exceeded rate limit.
        Raises: HTTPException 429 if exceeded
        Returns: dict with remaining requests and reset time
        """
        now = time.time()
        window = self._windows[user_id]

        # Remove old timestamps outside window
        while window and window[0] < now - self.window_seconds:
            window.popleft()

        remaining = self.max_requests - len(window)
        reset_at = int(now + self.window_seconds)

        if len(window) >= self.max_requests:
            oldest = window[0]
            retry_after = int(oldest + self.window_seconds - now) + 1
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "limit": self.max_requests,
                    "window_seconds": self.window_seconds,
                    "retry_after_seconds": retry_after,
                },
                headers={
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_at),
                    "Retry-After": str(retry_after),
                },
            )

        # Record this request
        window.append(now)

        return {
            "limit": self.max_requests,
            "remaining": remaining - 1,
            "reset_at": reset_at,
            "window_seconds": self.window_seconds,
        }

    def get_stats(self, user_id: str) -> dict:
        """Get usage stats for user (non-blocking)."""
        now = time.time()
        window = self._windows[user_id]
        active = sum(1 for t in window if t >= now - self.window_seconds)
        return {
            "requests_in_window": active,
            "limit": self.max_requests,
            "remaining": self.max_requests - active,
        }


# Global instances
rate_limiter_user = RateLimiter(max_requests=10, window_seconds=60)    # 10 req/min
rate_limiter_admin = RateLimiter(max_requests=100, window_seconds=60)  # 100 req/min
