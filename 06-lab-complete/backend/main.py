"""
FastAPI Backend for TA Chatbot
Handles AI agent logic, RAG, escalation, and security
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
import logging

from agent import stream_chat
from utils.storage import get_metrics, update_metric, save_chat_session, load_chat_session
from utils.email_service import send_escalation_email
from security import RateLimiter, CostGuard, HealthMonitor

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TA Chatbot API",
    description="AI Teaching Assistant for C/C++",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize security
rate_limiter = RateLimiter(max_requests=20, window_seconds=60)
cost_guard = CostGuard(per_user_budget=1.0, global_budget=10.0)
health_monitor = HealthMonitor()

# Models
class ChatMessage(BaseModel):
    content: str
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    content: str
    cost: float
    remaining_budget: float
    warning: Optional[str] = None

class MetricsResponse(BaseModel):
    helpful: int
    unhelpful: int
    escalated: int
    total: int

class HealthResponse(BaseModel):
    status: str
    uptime_seconds: float
    total_requests: int
    error_count: int
    error_rate: float

# Routes
@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Process user chat message"""
    user_id = message.user_id or "anonymous"
    
    try:
        # Rate limit check
        if not rate_limiter.check(user_id):
            health_monitor.record_request(success=False)
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: 20 requests per 60 seconds"
            )
        
        # Budget check
        user_stats = cost_guard.get_user_stats(user_id)
        if user_stats['usage_percent'] >= 100:
            health_monitor.record_request(success=False)
            raise HTTPException(
                status_code=402,
                detail=f"Budget exceeded: ${user_stats['spent_today']:.2f} / ${user_stats['budget']:.2f}"
            )
        
        # Stream response
        response_chunks = []
        for chunk in stream_chat(message.content, []):
            response_chunks.append(chunk)
        
        full_response = "".join(response_chunks)
        
        # Track cost
        input_tokens = len(message.content) // 4
        output_tokens = len(full_response) // 4
        cost_guard.record_usage(user_id, input_tokens, output_tokens)
        
        # Update metrics
        update_metric("total", 1)
        
        # Get updated stats
        user_stats = cost_guard.get_user_stats(user_id)
        
        warning = None
        if user_stats['usage_percent'] > 80:
            warning = f"⚠️ Budget warning: {user_stats['usage_percent']:.1f}% used"
        
        health_monitor.record_request(success=True)
        
        return ChatResponse(
            content=full_response,
            cost=user_stats['spent_today'],
            remaining_budget=user_stats['remaining'],
            warning=warning
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        health_monitor.record_request(success=False)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/escalate")
async def escalate(data: Dict):
    """Escalate to human TA"""
    try:
        success = send_escalation_email(data)
        if success:
            update_metric("escalated", 1)
            health_monitor.record_request(success=True)
            return {"status": "success", "message": "Escalation email sent"}
        else:
            health_monitor.record_request(success=False)
            raise HTTPException(status_code=500, detail="Failed to send email")
    except Exception as e:
        health_monitor.record_request(success=False)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics", response_model=MetricsResponse)
async def metrics():
    """Get application metrics"""
    try:
        metrics_data = get_metrics()
        health_monitor.record_request(success=True)
        return MetricsResponse(**metrics_data)
    except Exception as e:
        logger.error(f"Metrics error: {str(e)}")
        health_monitor.record_request(success=False)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    stats = health_monitor.get_stats()
    return HealthResponse(**stats)

@app.post("/feedback")
async def feedback(data: Dict):
    """Record user feedback"""
    try:
        feedback_type = data.get("type")  # "helpful", "unhelpful", "escalate"
        if feedback_type in ["helpful", "unhelpful", "escalated"]:
            update_metric(feedback_type, 1)
            health_monitor.record_request(success=True)
            return {"status": "success"}
        else:
            raise ValueError(f"Invalid feedback type: {feedback_type}")
    except Exception as e:
        health_monitor.record_request(success=False)
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/")
async def root():
    """API info"""
    return {
        "name": "TA Chatbot API",
        "version": "1.0.0",
        "description": "AI Teaching Assistant Backend",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
