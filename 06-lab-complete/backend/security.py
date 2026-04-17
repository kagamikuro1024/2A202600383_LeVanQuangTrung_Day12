"""
Security Module — API Key Auth, Rate Limiting, Cost Guard
"""

import time
from collections import deque
from datetime import datetime, timedelta
import json
import os

# ===== RATE LIMITING =====
class RateLimiter:
    """Sliding window rate limiter"""
    
    def __init__(self, max_requests=20, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.user_requests = {}  # {user_id: deque of timestamps}
    
    def check(self, user_id: str) -> bool:
        """Check if user exceeded rate limit. Returns True if allowed."""
        now = time.time()
        
        if user_id not in self.user_requests:
            self.user_requests[user_id] = deque()
        
        # Remove old requests outside window
        while self.user_requests[user_id] and (now - self.user_requests[user_id][0]) > self.window_seconds:
            self.user_requests[user_id].popleft()
        
        # Check if exceeded
        if len(self.user_requests[user_id]) >= self.max_requests:
            return False
        
        # Add current request
        self.user_requests[user_id].append(now)
        return True
    
    def get_remaining(self, user_id: str) -> int:
        """Get remaining requests for user"""
        if user_id not in self.user_requests:
            return self.max_requests
        
        now = time.time()
        # Remove old requests
        while self.user_requests[user_id] and (now - self.user_requests[user_id][0]) > self.window_seconds:
            self.user_requests[user_id].popleft()
        
        return self.max_requests - len(self.user_requests[user_id])


# ===== COST GUARD =====
class CostGuard:
    """Track OpenAI API call costs"""
    
    # Token pricing for GPT-4o-mini (USD)
    INPUT_COST_PER_1M = 0.15
    OUTPUT_COST_PER_1M = 0.60
    
    def __init__(self, per_user_budget=1.0, global_budget=10.0):
        self.per_user_budget = per_user_budget
        self.global_budget = global_budget
        self.user_usage = {}  # {user_id: {date: {cost, tokens}}}
        self.global_usage = {}  # {date: {cost, tokens}}
    
    def _get_date_key(self):
        """Get today's date as key"""
        return datetime.utcnow().strftime("%Y-%m-%d")
    
    def record_usage(self, user_id: str, input_tokens: int, output_tokens: int):
        """Record token usage and calculate cost"""
        cost = (input_tokens * self.INPUT_COST_PER_1M + output_tokens * self.OUTPUT_COST_PER_1M) / 1_000_000
        date_key = self._get_date_key()
        
        # User usage
        if user_id not in self.user_usage:
            self.user_usage[user_id] = {}
        if date_key not in self.user_usage[user_id]:
            self.user_usage[user_id][date_key] = {"cost": 0, "tokens": 0}
        
        self.user_usage[user_id][date_key]["cost"] += cost
        self.user_usage[user_id][date_key]["tokens"] += input_tokens + output_tokens
        
        # Global usage
        if date_key not in self.global_usage:
            self.global_usage[date_key] = {"cost": 0, "tokens": 0}
        
        self.global_usage[date_key]["cost"] += cost
        self.global_usage[date_key]["tokens"] += input_tokens + output_tokens
    
    def get_user_cost(self, user_id: str) -> float:
        """Get today's cost for user"""
        date_key = self._get_date_key()
        if user_id in self.user_usage and date_key in self.user_usage[user_id]:
            return self.user_usage[user_id][date_key]["cost"]
        return 0.0
    
    def get_global_cost(self) -> float:
        """Get today's global cost"""
        date_key = self._get_date_key()
        if date_key in self.global_usage:
            return self.global_usage[date_key]["cost"]
        return 0.0
    
    def get_user_stats(self, user_id: str) -> dict:
        """Get user's daily stats"""
        date_key = self._get_date_key()
        cost = self.get_user_cost(user_id)
        remaining = max(0, self.per_user_budget - cost)
        
        return {
            "spent_today": cost,
            "budget": self.per_user_budget,
            "remaining": remaining,
            "usage_percent": (cost / self.per_user_budget * 100) if self.per_user_budget > 0 else 0,
            "reset_time": (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d 00:00:00 UTC")
        }
    
    def get_global_stats(self) -> dict:
        """Get global daily stats"""
        cost = self.get_global_cost()
        remaining = max(0, self.global_budget - cost)
        
        return {
            "spent_today": cost,
            "budget": self.global_budget,
            "remaining": remaining,
            "usage_percent": (cost / self.global_budget * 100) if self.global_budget > 0 else 0,
            "reset_time": (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d 00:00:00 UTC")
        }


# ===== HEALTH CHECK =====
class HealthMonitor:
    """Monitor app health"""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
    
    def record_request(self, success: bool = True):
        """Record a request"""
        self.request_count += 1
        if not success:
            self.error_count += 1
    
    def get_stats(self) -> dict:
        """Get health stats"""
        uptime = time.time() - self.start_time
        error_rate = (self.error_count / self.request_count * 100) if self.request_count > 0 else 0
        
        return {
            "status": "healthy" if error_rate < 5 else "degraded",
            "uptime_seconds": round(uptime, 2),
            "requests": self.request_count,
            "errors": self.error_count,
            "error_rate_percent": round(error_rate, 2),
            "timestamp": datetime.utcnow().isoformat()
        }
