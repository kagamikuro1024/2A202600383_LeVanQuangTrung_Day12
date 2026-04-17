"""
Cost Guard — Budget Protection for LLM API Calls

Tracks token usage and spending per user
- Daily budget per user: $1.00
- Global daily budget: $10.00
- Warns at 80% usage
- Blocks at 100% (402 Payment Required)
"""
import time
import logging
from dataclasses import dataclass, field
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Token pricing (GPT-4o-mini rates, in USD)
PRICE_PER_1K_INPUT_TOKENS = 0.00015    # $0.15 per 1M input tokens
PRICE_PER_1K_OUTPUT_TOKENS = 0.0006    # $0.60 per 1M output tokens


@dataclass
class UsageRecord:
    """Track usage per user per day."""
    user_id: str
    input_tokens: int = 0
    output_tokens: int = 0
    request_count: int = 0
    day: str = field(default_factory=lambda: time.strftime("%Y-%m-%d"))

    @property
    def total_cost_usd(self) -> float:
        """Calculate total cost in USD."""
        input_cost = (self.input_tokens / 1000) * PRICE_PER_1K_INPUT_TOKENS
        output_cost = (self.output_tokens / 1000) * PRICE_PER_1K_OUTPUT_TOKENS
        return round(input_cost + output_cost, 6)


class CostGuard:
    """In-memory cost tracking (for production: use Redis/DB)."""
    
    def __init__(
        self,
        daily_budget_usd: float = 1.0,        # $1 per user per day
        global_daily_budget_usd: float = 10.0, # $10 total per day
        warn_at_pct: float = 0.8,             # Warn at 80%
    ):
        self.daily_budget_usd = daily_budget_usd
        self.global_daily_budget_usd = global_daily_budget_usd
        self.warn_at_pct = warn_at_pct
        self._records: dict[str, UsageRecord] = {}
        self._global_today = time.strftime("%Y-%m-%d")
        self._global_cost = 0.0

    def _get_record(self, user_id: str) -> UsageRecord:
        """Get or create usage record for user (reset daily)."""
        today = time.strftime("%Y-%m-%d")
        
        # Reset global cost at midnight
        if today != self._global_today:
            self._global_today = today
            self._global_cost = 0.0
        
        record = self._records.get(user_id)
        if not record or record.day != today:
            self._records[user_id] = UsageRecord(user_id=user_id, day=today)
        
        return self._records[user_id]

    def check_budget(self, user_id: str) -> None:
        """Check if user can make another request (raise 402 if exceeded)."""
        record = self._get_record(user_id)

        # Global budget check
        if self._global_cost >= self.global_daily_budget_usd:
            logger.critical(f"GLOBAL BUDGET EXCEEDED: ${self._global_cost:.4f}")
            raise HTTPException(
                status_code=503,
                detail="Service temporarily unavailable - daily budget exhausted",
            )

        # Per-user budget check
        if record.total_cost_usd >= self.daily_budget_usd:
            raise HTTPException(
                status_code=402,  # Payment Required
                detail={
                    "error": "Daily budget exceeded",
                    "user_budget": self.daily_budget_usd,
                    "spent_today": record.total_cost_usd,
                    "reset_at": f"{record.day} 23:59:59",
                },
            )

        # Warning at 80%
        pct_used = record.total_cost_usd / self.daily_budget_usd
        if pct_used >= self.warn_at_pct:
            logger.warning(
                f"User {user_id} approaching budget: "
                f"${record.total_cost_usd:.4f}/${self.daily_budget_usd:.2f} ({pct_used*100:.0f}%)"
            )

    def record_usage(self, user_id: str, input_tokens: int, output_tokens: int) -> dict:
        """Record token usage after successful request."""
        record = self._get_record(user_id)
        record.input_tokens += input_tokens
        record.output_tokens += output_tokens
        record.request_count += 1
        
        cost = record.total_cost_usd
        self._global_cost += cost
        
        return {
            "cost_usd": cost,
            "spent_today": record.total_cost_usd,
            "budget_remaining": max(0, self.daily_budget_usd - record.total_cost_usd),
            "request_count": record.request_count,
        }

    def get_stats(self, user_id: str) -> dict:
        """Get usage stats for user."""
        record = self._get_record(user_id)
        spent = record.total_cost_usd
        remaining = max(0, self.daily_budget_usd - spent)
        pct = (spent / self.daily_budget_usd * 100) if self.daily_budget_usd > 0 else 0
        
        return {
            "spent_today_usd": spent,
            "budget_usd": self.daily_budget_usd,
            "remaining_usd": remaining,
            "usage_percent": round(pct, 1),
            "requests_today": record.request_count,
            "input_tokens": record.input_tokens,
            "output_tokens": record.output_tokens,
        }


# Global instance
cost_guard = CostGuard(
    daily_budget_usd=1.0,
    global_daily_budget_usd=10.0,
    warn_at_pct=0.8,
)
