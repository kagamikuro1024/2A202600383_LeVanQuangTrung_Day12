"""
Agent production-ready with API Security (Part 4)

Features:
  ✅ API Key authentication (X-API-Key header)
  ✅ Rate limiting (10 requests/minute)
  ✅ Cost guard (daily budget protection)
  ✅ Structured JSON logging
  ✅ Health & readiness checks
  ✅ Graceful shutdown
"""
import os
import time
import logging
import json
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from utils.mock_llm import ask
from auth import verify_api_key
from rate_limiter import rate_limiter_user
from cost_guard import cost_guard

logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

START_TIME = time.time()
is_ready = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    global is_ready
    logger.info("Starting agent...")
    time.sleep(0.1)  # simulate init
    is_ready = True
    logger.info("Agent ready")
    yield
    is_ready = False
    logger.info("Agent shutdown")


app = FastAPI(
    title="Agent (API Security)",
    version="2.0.0-security",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "app": "AI Agent",
        "version": "2.0.0-security",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "features": ["api-key-auth", "rate-limiting", "cost-guard"],
    }


@app.post("/ask")
async def ask_agent(request: Request):
    """
    Ask the agent a question.
    
    Security checks:
    1. API Key authentication
    2. Rate limiting (10 req/min)
    3. Budget check (cost guard)
    
    Response: {"answer": "..."}
    """
    # 1. Authenticate user via API Key
    user_id = verify_api_key(request)
    
    # 2. Check rate limit
    rate_limit_info = rate_limiter_user.check(user_id)
    
    # 3. Check budget (before processing)
    cost_guard.check_budget(user_id)
    
    # 4. Parse request
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON")
    
    question = body.get("question", "")
    if not question:
        raise HTTPException(422, "question required")
    
    # 5. Log request
    logger.info(json.dumps({
        "event": "request",
        "user": user_id,
        "q_len": len(question),
        "rate_limit_remaining": rate_limit_info["remaining"],
    }))
    
    # 6. Get answer (mock LLM)
    answer = ask(question)
    
    # 7. Record usage (for cost tracking)
    # Mock: estimate 50 input + 100 output tokens
    usage_info = cost_guard.record_usage(user_id, input_tokens=50, output_tokens=100)
    
    logger.info(json.dumps({
        "event": "response",
        "user": user_id,
        "cost_usd": usage_info["cost_usd"],
        "spent_today": usage_info["spent_today"],
    }))
    
    return {
        "answer": answer,
        "usage": {
            "cost_usd": usage_info["cost_usd"],
            "spent_today": usage_info["spent_today"],
            "budget_remaining": usage_info["budget_remaining"],
        },
        "rate_limit": {
            "limit": rate_limit_info["limit"],
            "remaining": rate_limit_info["remaining"],
            "reset_at": rate_limit_info["reset_at"],
        },
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "version": "2.0.0-security",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/ready")
def ready():
    if not is_ready:
        raise HTTPException(503, "not ready")
    return {"ready": True}


@app.get("/stats")
async def stats(request: Request):
    """Get usage statistics (requires auth)."""
    user_id = verify_api_key(request)
    
    rate_stats = rate_limiter_user.get_stats(user_id)
    cost_stats = cost_guard.get_stats(user_id)
    
    return {
        "user_id": user_id,
        "rate_limit": rate_stats,
        "cost_guard": cost_stats,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
