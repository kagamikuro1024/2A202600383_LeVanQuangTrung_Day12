# 📋 Chi Tiết Lộ Trình Lab Day 12 - Deploy AI Agent

> **Deadline:** 17/4/2026  
> **Điểm tối đa:** 100 (40 từ exercises + 60 từ final project)  
> **Thời gian ước tính:** 3-4 giờ

---

## 🎯 Tổng Quan

Bạn sẽ biến một AI agent chạy trên laptop thành một service production-ready trên cloud. Quy trình:

```
Part 1: Hiểu vấn đề (Dev vs Prod)
   ↓
Part 2: Docker (Containerize)
   ↓
Part 3: Cloud (Deploy lên internet)
   ↓
Part 4: Security (Bảo mật + giới hạn chi phí)
   ↓
Part 5: Scalability (Chạy nhiều instances)
   ↓
Part 6: Final Project (Build từ đầu)
```

**Mục tiêu cuối cùng:** Một service trên cloud mà ai cũng có thể gọi qua URL công khai.

---

## 📦 CẢI ĐẶT TRƯỚC

Kiểm tra xem bạn đã có các công cụ này:

```bash
# 1. Python
python --version
# Cần: 3.11 hoặc cao hơn

# 2. Docker
docker --version
docker compose version
# Cần: Docker Desktop (hoặc Docker + Docker Compose)

# 3. Git
git --version

# 4. NPM (cho Railway CLI)
npm --version
```

**Nếu thiếu gì:** 
- Python: https://python.org/downloads
- Docker Desktop: https://www.docker.com/products/docker-desktop
- Git: https://git-scm.com/downloads
- Node.js: https://nodejs.org/

---

## 📚 PHẦN 1: Localhost vs Production (30 phút)

### Mục tiêu
Hiểu tại sao code hoạt động trên laptop nhưng fail khi deploy.

### Step 1.1: Phát hiện anti-patterns (10 phút)

```bash
# Mở thư mục
cd d:\gitHub\AI_20k\Day12\day12_ha-tang-cloud_va_deployment\01-localhost-vs-production\develop

# Đọc file app.py
# (Mở bằng VS Code hoặc text editor)
```

**Tìm và liệt kê 5+ vấn đề:**

Gợi ý tìm:
- ❌ API key được hardcode ở đâu?
- ❌ Port cố định là gì?
- ❌ Debug mode có bật không?
- ❌ Có health check endpoint không?
- ❌ Có xử lý shutdown gracefully không?
- ❌ Config có từ environment variables không?
- ❌ Logging dùng gì? (print vs JSON logging)

**Ghi vào file:** `MISSION_ANSWERS.md` 
```markdown
## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. Hardcoded API key (sk-123abc)
2. Port cố định là 8000 trong code
3. ...
```

### Step 1.2: Chạy basic version (8 phút)

```bash
# Cài dependencies
pip install -r requirements.txt

# Chạy app
python app.py

# Trong terminal khác, test
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'

# Dừng app (Ctrl+C)
```

**Quan sát:** Nó chạy! Nhưng có production-ready không?

### Step 1.3: So sánh với advanced version (12 phút)

```bash
# Chuyển sang production folder
cd ../production

# Copy .env.example thành .env
cp .env.example .env

# Cài dependencies
pip install -r requirements.txt

# Chạy app
python app.py

# Test (terminal khác)
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "What is production?"}'

# Dừng (Ctrl+C)
```

**So sánh app.py từ 2 folder:**

Điền vào bảng trong `MISSION_ANSWERS.md`:

```markdown
### Exercise 1.3: Comparison table

| Feature | Basic | Production | Tại sao quan trọng? |
|---------|-------|------------|---------------------|
| Config | Hardcode `api_key = "sk-123"` | Từ env vars: `api_key = os.getenv("OPENAI_API_KEY")` | Không để lộ secrets trong code, dễ thay đổi giữa environments |
| Port | Port 8000 cố định trong code | Port từ env: `port = int(os.getenv("PORT", 8000))` | Cloud platform quy định port, không thể hardcode |
| Health check | Không có | `@app.get("/health")` return 200 | Platform cần kiểm tra app còn sống không |
| Logging | `print()` | JSON structured logging | Dễ parse logs, search, analysis ở production |
| Shutdown | Đột ngột (SIGTERM ignore) | Signal handler graceful shutdown | Hoàn thành requests đang chạy trước khi tắt |
| ... | | | |
```

### ✅ Checkpoint 1
Bạn hiểu được:
- [ ] Tại sao hardcode secrets nguy hiểm
- [ ] Cách dùng environment variables
- [ ] Tầm quan trọng của health check
- [ ] Graceful shutdown là gì

---

## 🐳 PHẦN 2: Docker Containerization (45 phút)

### Mục tiêu
Đóng gói app + dependencies để chạy ở bất cứ đâu.

### Step 2.1: Dockerfile cơ bản (10 phút)

```bash
cd ../../02-docker/develop

# Đọc Dockerfile
# (Mở file Dockerfile)
```

**Trả lời những câu hỏi:**

1. Base image là gì? (FROM ...)
2. Working directory là gì? (WORKDIR ...)
3. Tại sao COPY requirements.txt trước COPY app.py?
4. CMD vs ENTRYPOINT khác nhau thế nào?

**Ghi vào `MISSION_ANSWERS.md`:**

```markdown
## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. Base image: python:3.11-slim (lightweight Python runtime)
2. Working directory: /app
3. COPY requirements.txt trước: Để tận dụng Docker layer cache. Nếu code thay đổi nhưng dependencies không, cache layer đó sẽ được dùng lại, không cần cài lại tất cả packages
4. CMD vs ENTRYPOINT: CMD có thể override khi run container, ENTRYPOINT thì không
```

### Step 2.2: Build & Run image (15 phút)

```bash
# Build image
docker build -t my-agent:develop .

# Xem image size
docker images my-agent:develop

# Run container
docker run -p 8000:8000 my-agent:develop

# Trong terminal khác, test
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Docker?"}'

# Dừng container (Ctrl+C)
```

**Ghi vào `MISSION_ANSWERS.md`:**

```markdown
### Exercise 2.2: Build & Run results

Build command:
docker build -t my-agent:develop .

Image size: 
[Paste output từ: docker images my-agent:develop]

Test result:
[Paste curl response]
```

### Step 2.3: Multi-stage build (10 phút)

```bash
cd ../production

# Đọc Dockerfile (có FROM ... as builder, rồi FROM ... tiếp)
```

**Trả lời:**
- Stage 1 (builder) làm gì?
- Stage 2 (runtime) làm gì?
- Tại sao image nhỏ hơn?

```bash
# Build
docker build -t my-agent:advanced .

# So sánh size
docker images | grep my-agent
```

**Ghi vào `MISSION_ANSWERS.md`:**

```markdown
### Exercise 2.3: Multi-stage build

Image sizes:
- Develop: [X] MB
- Production (multi-stage): [Y] MB  
- Tỷ lệ nhỏ hơn: [Z]%

Lợi ích multi-stage:
- Stage 1 (builder): Cài đủ dependencies để build
- Stage 2 (runtime): Copy chỉ cái cần chạy, bỏ cái build không cần
- Kết quả: Image nhỏ hơn, deploy nhanh hơn, bảo mật hơn
```

### Step 2.4: Docker Compose stack (10 phút)

```bash
# Vẫn ở production folder, đọc docker-compose.yml
```

**Trả lời:**
- Services nào? (agent, redis, nginx?)
- Chúng communicate thế nào?

```bash
# Start stack
docker compose up

# Trong terminal khác
# Health check
curl http://localhost/health

# Test API
curl http://localhost/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain Docker Compose"}'

# Xem logs
docker compose logs

# Dừng (Ctrl+C), cleanup
docker compose down
```

**Ghi vào `MISSION_ANSWERS.md`:**

```markdown
### Exercise 2.4: Docker Compose

Services:
- agent: FastAPI app on port 8000
- redis: In-memory store on port 6379
- nginx: Load balancer on port 80

Architecture:
Client → Nginx (port 80) → Agent (port 8000) → Redis (port 6379)

Test results:
[Paste curl outputs]
```

### ✅ Checkpoint 2
- [ ] Hiểu Dockerfile structure
- [ ] Biết multi-stage builds giúp giảm size
- [ ] Hiểu Docker Compose orchestration
- [ ] Biết cách debug container (docker logs, exec)

---

## ☁️ PHẦN 3: Cloud Deployment (45 phút)

### Mục tiêu
Deploy agent lên cloud để ai cũng có thể gọi qua URL công khai.

### Step 3.1: Deploy Railway (20 phút) ⭐ RECOMMENDED

```bash
cd ../../03-cloud-deployment/railway

# 1. Cài Railway CLI
npm i -g @railway/cli

# 2. Login (sẽ mở browser)
railway login

# 3. Init project
railway init
# Chọn: Create a new project
# Đặt tên: my-agent-deployment

# 4. Set environment variables
railway variables set PORT=8000
railway variables set AGENT_API_KEY=my-secret-key-12345

# 5. Deploy!
railway up

# 6. Lấy domain
railway domain
# Hoặc: railway open (mở dashboard)
```

**Kết quả:** Bạn được một URL công khai như:
```
https://student-agent-xxxxx.railway.app
```

**Test:**
```bash
# Thay YOUR_DOMAIN bằng domain thực tế
YOUR_DOMAIN="student-agent-xxxxx.railway.app"

# Health check
curl https://$YOUR_DOMAIN/health

# Test API
curl https://$YOUR_DOMAIN/ask -X POST \
  -H "X-API-Key: my-secret-key-12345" \
  -H "Content-Type: application/json" \
  -d '{"question": "Am I on the cloud?"}'
```

**Ghi vào `MISSION_ANSWERS.md`:**

```markdown
## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment

Public URL: https://student-agent-xxxxx.railway.app

Test results:
[Paste curl outputs]

Screenshots:
[Thêm link tới folder screenshots/]
```

### Step 3.2: Deploy Render (15 phút) - OPTIONAL

```bash
cd ../render

# 1. Tạo GitHub repo nếu chưa có
# Push code lên GitHub

# 2. Vào render.com → Sign up (free)

# 3. New → Blueprint
# Chọn GitHub repo

# 4. Render tự động đọc render.yaml

# 5. Set environment variables trong dashboard:
#    PORT=8000
#    AGENT_API_KEY=my-secret-key

# 6. Deploy
```

**Nếu thành công:**
```
https://student-agent-render.onrender.com
```

**Ghi vào `MISSION_ANSWERS.md`:**

```markdown
### Exercise 3.2: Render deployment (Optional)

Platform: Render
Public URL: https://student-agent-render.onrender.com
[hoặc: Skipped - chỉ deploy Railway]
```

### Step 3.3: Cloud Run GCP (Optional)

Bỏ qua nếu không có GCP account.

### ✅ Checkpoint 3
- [ ] Deploy thành công lên ít nhất 1 platform (Railway hoặc Render)
- [ ] Có public URL hoạt động
- [ ] Health check endpoint trả về 200
- [ ] Có thể gọi /ask endpoint qua curl

---

## 🔐 PHẦN 4: API Security (40 phút)

### Mục tiêu
Bảo vệ API khỏi bị abuse (ai cũng có thể gọi = hết tiền OpenAI).

### Step 4.1: API Key authentication (10 phút)

```bash
cd ../../04-api-gateway/develop

# Chạy app
python app.py

# Test không có key (phải fail)
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
# Expected: 401 Unauthorized

# Test có key (phải thành công)
curl http://localhost:8000/ask -X POST \
  -H "X-API-Key: secret-key-123" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
# Expected: 200 OK

# Dừng app (Ctrl+C)
```

**Ghi vào `MISSION_ANSWERS.md`:**

```markdown
## Part 4: API Security

### Exercise 4.1: API Key authentication

Test without key:
[Paste curl output - must be 401]

Test with key:
[Paste curl output - must be 200]

API Key header: X-API-Key
```

### Step 4.2: JWT authentication (Optional Advanced)

```bash
cd ../production

# Chạy app
python app.py

# 1. Lấy token
TOKEN=$(curl http://localhost:8000/token -X POST \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "secret"}' \
  | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

# 2. Dùng token
curl http://localhost:8000/ask -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain JWT"}'
# Expected: 200 OK

# Dừng (Ctrl+C)
```

**Ghi vào `MISSION_ANSWERS.md`:**

```markdown
### Exercise 4.2: JWT (Optional)

JWT flow:
1. Client POST /token với username/password
2. Server return access_token
3. Client dùng token trong Authorization header
4. Server verify token

Advantages:
- Không cần lưu session state ở server
- Stateless → dễ scale
```

### Step 4.3: Rate limiting (10 phút)

```bash
# Vẫn ở production folder
# App đang chạy từ bước trên

# Gửi 20 requests liên tiếp
for i in {1..20}; do
  echo "Request $i:"
  curl http://localhost:8000/ask -X POST \
    -H "X-API-Key: secret-key-123" \
    -H "Content-Type: application/json" \
    -d '{"question": "Test '$i'"}'
  echo ""
done

# Quan sát: Sau request thứ 10, phải có 429 Too Many Requests
```

**Ghi vào `MISSION_ANSWERS.md`:**

```markdown
### Exercise 4.3: Rate limiting

Rate limit: 10 requests/minute per user

Test results:
[Paste output - shows 429 after 10th request]

Algorithm: Sliding window / Token bucket
```

### Step 4.4: Cost guard (10 phút)

**File:** `app/cost_guard.py`

```bash
# Đọc code để hiểu logic
```

**Implement:**

```python
# cost_guard.py
import redis
from datetime import datetime

r = redis.Redis()

def check_budget(user_id: str, estimated_cost: float) -> bool:
    """
    Return True nếu còn budget, False nếu vượt.
    - Monthly limit: $10 per user
    - Track trong Redis
    - Reset đầu tháng
    """
    month_key = datetime.now().strftime("%Y-%m")
    redis_key = f"budget:{user_id}:{month_key}"
    
    # Get current spending
    current_spending = float(r.get(redis_key) or 0)
    
    # Check if exceeds
    if current_spending + estimated_cost > 10.0:
        return False
    
    # Add cost
    r.incrbyfloat(redis_key, estimated_cost)
    r.expire(redis_key, 32 * 24 * 3600)  # 32 days
    
    return True
```

**Test:**
```bash
# Gọi API liên tục để vượt $10
curl http://localhost:8000/ask -X POST \
  -H "X-API-Key: secret-key-123" \
  -H "Content-Type: application/json" \
  -d '{"question": "..." }'
# Khi vượt $10: 402 Payment Required
```

**Ghi vào `MISSION_ANSWERS.md`:**

```markdown
### Exercise 4.4: Cost guard

Monthly budget: $10 per user

Implementation:
- Track spending trong Redis
- Key format: budget:{user_id}:{YYYY-MM}
- Reset đầu tháng (TTL 32 days)
- Return 402 nếu vượt

Test result:
[Paste output showing 402 when over budget]
```

### ✅ Checkpoint 4
- [ ] API key authentication hoạt động
- [ ] Rate limiting (10 req/min) hoạt động
- [ ] Cost guard ($10/month) hoạt động
- [ ] Tất cả trả về đúng HTTP status codes

---

## 📈 PHẦN 5: Scaling & Reliability (40 phút)

### Mục tiêu
Làm app có thể chạy nhiều instances cùng lúc mà không bị conflict.

### Step 5.1: Health checks (10 phút)

```bash
cd ../../05-scaling-reliability/develop

# Implement 2 endpoints (nếu chưa có)
```

**Code:**

```python
# app.py
import redis
from fastapi import FastAPI, HTTPException, status

app = FastAPI()
r = redis.Redis()

@app.get("/health")
def health():
    """Liveness probe - container còn sống không?"""
    return {"status": "ok", "timestamp": datetime.now()}

@app.get("/ready")
def ready():
    """Readiness probe - sẵn sàn nhận traffic không?"""
    try:
        # Check Redis
        r.ping()
        return {"status": "ready"}
    except:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Not ready"
        )
```

**Test:**
```bash
python app.py

# Terminal khác
curl http://localhost:8000/health  # Must return 200

curl http://localhost:8000/ready   # Must return 200 (if Redis running)
```

### Step 5.2: Graceful shutdown (10 phút)

**Code:**

```python
# app.py
import signal
import sys

shutdown_event = False

def shutdown_handler(signum, frame):
    global shutdown_event
    print("[SHUTDOWN] Received SIGTERM, shutting down gracefully...")
    shutdown_event = True
    
    # Give time to finish current requests
    import time
    time.sleep(2)
    
    print("[SHUTDOWN] Goodbye!")
    sys.exit(0)

# Register handler
signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)
```

**Test:**
```bash
python app.py &
PID=$!

# Gửi request dài
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Long task"}' &

# Ngay lập tức kill
sleep 1
kill -TERM $PID

# Quan sát: Request có hoàn thành không?
```

### Step 5.3: Stateless design (10 phút)

**Anti-pattern (Stateful):**
```python
# ❌ WRONG - State in memory
conversation_history = {}  # Global variable

@app.post("/ask")
def ask(user_id: str, question: str):
    history = conversation_history.get(user_id, [])
    # ...
    conversation_history[user_id] = history
```

**Problem:** Nếu scale ra 3 instances:
- Request 1 → Instance A (history lưu ở A)
- Request 2 → Instance B (không thấy history từ A)
- Request 3 → Instance C (không thấy history)

**Correct (Stateless):**
```python
# ✅ CORRECT - State in Redis
import redis
r = redis.Redis()

@app.post("/ask")
def ask(user_id: str, question: str):
    # Get from Redis
    history = r.lrange(f"history:{user_id}", 0, -1)
    
    # Process
    # ...
    
    # Save to Redis
    r.rpush(f"history:{user_id}", response)
    r.expire(f"history:{user_id}", 30 * 24 * 3600)  # 30 days
```

**Refactor code:**
```bash
cd ../production

# Kiểm tra: Có state trong memory không?
# Nếu có, move to Redis
```

### Step 5.4: Load balancing (5 phút)

```bash
# Vẫn ở production folder

# Start 3 agent instances + Nginx load balancer
docker compose up --scale agent=3

# Test
for i in {1..10}; do
  curl http://localhost/ask -X POST \
    -H "Content-Type: application/json" \
    -d '{"question": "Request '$i'"}'
  echo "---"
done

# Check logs - requests phân tán giữa 3 instances
docker compose logs agent | grep "Request"
```

### Step 5.5: Test stateless (5 phút)

```bash
python test_stateless.py

# Script này:
# 1. Tạo conversation
# 2. Kill 1 instance
# 3. Tiếp tục gọi API
# 4. Check: conversation vẫn còn không?
```

### ✅ Checkpoint 5
- [ ] /health endpoint hoạt động
- [ ] /ready endpoint hoạt động
- [ ] Graceful shutdown hoạt động
- [ ] Code refactored to stateless (state trong Redis)
- [ ] Load balancer phân tán traffic
- [ ] Test stateless passed

---

## 🏆 PHẦN 6: Final Project - Build từ đầu (60 phút)

### Mục tiêu
Kết hợp TẤT CẢ concepts để build một production-ready agent.

### Architecture

```
┌──────────────────────────────────────────┐
│         Client Requests                  │
└──────────────┬───────────────────────────┘
               │
               ▼
       ┌───────────────┐
       │  Nginx (LB)   │  Port 80
       └───────┬───────┘
               │
        ┌──────┼──────┐
        │      │      │
        ▼      ▼      ▼
    ┌─────┐┌─────┐┌─────┐
    │Ag.1 ││Ag.2 ││Ag.3 │  Port 8000 each
    └─────┘└─────┘└─────┘
        │      │      │
        └──────┼──────┘
               │
               ▼
         ┌──────────┐
         │  Redis   │  Port 6379
         └──────────┘
```

### Checklist Yêu cầu

**Functional:**
- [ ] Agent trả lời câu hỏi qua POST /ask
- [ ] Có conversation history
- [ ] Error handling graceful

**Non-functional:**
- [ ] Multi-stage Dockerfile (image < 500 MB)
- [ ] Config từ environment variables
- [ ] API key authentication (X-API-Key header)
- [ ] Rate limiting (10 req/min per user)
- [ ] Cost guard ($10/month per user)
- [ ] Health check endpoint (/health)
- [ ] Readiness check endpoint (/ready)
- [ ] Graceful shutdown (SIGTERM handler)
- [ ] Stateless design (state in Redis)
- [ ] Structured JSON logging
- [ ] docker-compose.yml với Redis + Nginx
- [ ] Deploy lên Railway hoặc Render
- [ ] No hardcoded secrets

### Step-by-step Implementation

#### 6.1: Project Setup (5 phút)

Sử dụng folder `06-lab-complete` làm template hoặc tạo mới:

```bash
cd ../06-lab-complete

# Kiểm tra structure
ls -la
# Cần có:
# - app/
#   - main.py
#   - config.py
#   - auth.py
#   - rate_limiter.py
#   - cost_guard.py
# - Dockerfile
# - docker-compose.yml
# - requirements.txt
# - .env.example
# - .dockerignore
# - README.md
```

#### 6.2: config.py (5 phút)

```python
# app/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Server
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    
    # Security
    AGENT_API_KEY: str
    
    # Database
    REDIS_URL: str = "redis://localhost:6379"
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 10
    
    # Cost guard
    MONTHLY_BUDGET_USD: float = 10.0
    
    class Config:
        env_file = ".env"

settings = Settings()
```

#### 6.3: auth.py (5 phút)

```python
# app/auth.py
from fastapi import Header, HTTPException

def verify_api_key(x_api_key: str = Header(...)) -> str:
    """Verify API key from header"""
    from .config import settings
    
    if x_api_key != settings.AGENT_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return "user_" + x_api_key[:8]  # Return user_id
```

#### 6.4: rate_limiter.py (5 phút)

```python
# app/rate_limiter.py
import redis
from fastapi import HTTPException
from datetime import datetime

def get_rate_limiter():
    from .config import settings
    return redis.from_url(settings.REDIS_URL)

def check_rate_limit(user_id: str) -> None:
    """Check if user exceeded rate limit"""
    from .config import settings
    
    r = get_rate_limiter()
    
    now = datetime.now()
    minute_key = f"ratelimit:{user_id}:{now.strftime('%Y%m%d%H%M')}"
    
    count = r.incr(minute_key)
    r.expire(minute_key, 120)
    
    if count > settings.RATE_LIMIT_PER_MINUTE:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
```

#### 6.5: cost_guard.py (5 phút)

```python
# app/cost_guard.py
import redis
from datetime import datetime
from fastapi import HTTPException

def check_budget(user_id: str, estimated_cost: float = 0.01) -> None:
    """Check if user exceeded monthly budget"""
    from .config import settings
    
    r = redis.from_url(settings.REDIS_URL)
    
    month_key = datetime.now().strftime("%Y-%m")
    budget_key = f"budget:{user_id}:{month_key}"
    
    current = float(r.get(budget_key) or 0)
    if current + estimated_cost > settings.MONTHLY_BUDGET_USD:
        raise HTTPException(status_code=402, detail="Budget exceeded")
    
    r.incrbyfloat(budget_key, estimated_cost)
    r.expire(budget_key, 32 * 24 * 3600)
```

#### 6.6: main.py (20 phút)

```python
# app/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
import signal
import sys
import redis
import logging
from datetime import datetime
import json

from .config import settings
from .auth import verify_api_key
from .rate_limiter import check_rate_limit
from .cost_guard import check_budget

# Setup logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Agent")

# Redis connection
r = redis.from_url(settings.REDIS_URL)

# Graceful shutdown
shutdown = False

def shutdown_handler(signum, frame):
    global shutdown
    logger.info("Received SIGTERM, shutting down gracefully...")
    shutdown = True
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

# ========== ENDPOINTS ==========

@app.get("/health")
def health():
    """Liveness probe"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/ready")
def ready():
    """Readiness probe"""
    try:
        r.ping()
        return {"status": "ready"}
    except:
        return JSONResponse(
            status_code=503,
            content={"status": "not ready"}
        )

@app.post("/ask")
def ask(
    question: str,
    user_id: str = Depends(verify_api_key),
    _rate_check: None = Depends(check_rate_limit),
    _budget_check: None = Depends(check_budget)
):
    """Ask the AI agent a question"""
    
    if shutdown:
        raise HTTPException(status_code=503, detail="Server shutting down")
    
    try:
        # Get conversation history from Redis
        history_key = f"history:{user_id}"
        history = r.lrange(history_key, 0, -1)
        history = [json.loads(h.decode()) for h in history]
        
        # Call mock LLM
        from ..utils.mock_llm import call_llm
        response = call_llm(question, history)
        
        # Save to history
        r.rpush(history_key, json.dumps({
            "role": "assistant",
            "content": response
        }))
        r.expire(history_key, 30 * 24 * 3600)
        
        # Log
        logger.info(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "question": question,
            "response_length": len(response)
        }))
        
        return {
            "question": question,
            "answer": response,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.on_event("startup")
async def startup():
    logger.info("Application started")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown")
```

#### 6.7: requirements.txt

```
fastapi==0.104.0
uvicorn==0.24.0
pydantic-settings==2.1.0
redis==5.0.0
python-dotenv==1.0.0
```

#### 6.8: Dockerfile (Multi-stage)

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Copy only necessary files
COPY --from=builder /root/.local /root/.local
COPY app/ ./app/
COPY utils/ ./utils/

# Create non-root user
RUN useradd -m appuser
USER appuser

# Make scripts in .local usable
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 6.9: docker-compose.yml

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    networks:
      - app-network

  agent:
    build: .
    ports:
      - "8000:8000"
    environment:
      REDIS_URL: redis://redis:6379
      AGENT_API_KEY: ${AGENT_API_KEY:-my-secret-key}
      PORT: 8000
      LOG_LEVEL: INFO
    depends_on:
      redis:
        condition: service_healthy
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 3s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - agent
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
```

#### 6.10: nginx.conf

```
events {
    worker_connections 1024;
}

http {
    upstream agent {
        least_conn;
        server agent:8000 max_fails=3 fail_timeout=30s;
    }

    server {
        listen 80;
        server_name _;

        location / {
            proxy_pass http://agent;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }
}
```

#### 6.11: .env.example

```
AGENT_API_KEY=my-secret-key-change-this
REDIS_URL=redis://redis:6379
PORT=8000
LOG_LEVEL=INFO
RATE_LIMIT_PER_MINUTE=10
MONTHLY_BUDGET_USD=10.0
```

#### 6.12: .dockerignore

```
__pycache__
*.pyc
*.pyo
.Python
env/
venv/
.venv
.git
.gitignore
.dockerignore
.env
*.md
!README.md
.vscode/
.idea/
*.log
.DS_Store
test_*.py
```

#### 6.13: railway.toml (cho Railway)

```toml
[build]
builder = "dockerfile"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
```

#### 6.14: Test locally

```bash
# Create .env
cp .env.example .env
# Edit: AGENT_API_KEY=test-key-123

# Build & start
docker compose up --build

# In another terminal, test
curl http://localhost/health
curl -X POST http://localhost/ask \
  -H "X-API-Key: test-key-123" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
```

#### 6.15: Deploy to Railway

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Init
railway init

# Set env vars
railway variables set AGENT_API_KEY=production-key-secure
railway variables set REDIS_URL=<Railway Redis URL>
railway variables set PORT=8000

# Deploy
railway up
```

### ✅ Final Checklist

Before submitting:

- [ ] Code chạy không có error
- [ ] Docker image build thành công (< 500 MB)
- [ ] docker-compose up chạy tất cả services
- [ ] Health check: curl /health → 200
- [ ] Ready check: curl /ready → 200  
- [ ] Auth: curl /ask without key → 401
- [ ] Auth: curl /ask with key → 200
- [ ] Rate limit: 10+ requests liên tiếp → 429
- [ ] Cost guard: Nhiều requests → 402 khi vượt $10
- [ ] Deploy lên Railway/Render thành công
- [ ] Public URL hoạt động
- [ ] No hardcoded secrets
- [ ] .env file không được commit
- [ ] Graceful shutdown hoạt động

---

## 📝 CẦN NỘP NHỮNG GÌ

### 1. File: MISSION_ANSWERS.md (40 điểm)

**Nội dung:**
```markdown
# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production
### Exercise 1.1: Anti-patterns found
1. ...
2. ...
...

### Exercise 1.3: Comparison table
| Feature | Develop | Production | Why Important? |
| ... | ... | ... | ... |

## Part 2: Docker
### Exercise 2.1: Dockerfile questions
1. Base image: ...
...

### Exercise 2.3: Image size
- Develop: X MB
- Production: Y MB

## Part 3: Cloud Deployment
### Exercise 3.1: Railway deployment
- URL: https://...
- Screenshots: [link]

## Part 4: API Security
### Exercise 4.1-4.4: Test results
[Paste test outputs]

## Part 5: Scaling & Reliability
### Exercise 5.1-5.5
[Paste implementation notes and test results]
```

### 2. Full Source Code - Lab 06 (60 điểm)

**Tất cả files:**
- ✅ app/main.py
- ✅ app/config.py
- ✅ app/auth.py
- ✅ app/rate_limiter.py
- ✅ app/cost_guard.py
- ✅ Dockerfile (multi-stage)
- ✅ docker-compose.yml
- ✅ requirements.txt
- ✅ .env.example (không .env!)
- ✅ .dockerignore
- ✅ railway.toml (hoặc render.yaml)
- ✅ README.md (setup instructions)

### 3. File: DEPLOYMENT.md

```markdown
# Deployment Information

## Public URL
https://your-agent-xxxxx.railway.app

## Platform
Railway / Render

## Test Commands

### Health Check
curl https://your-agent-xxxxx.railway.app/health

### API Test
curl -X POST https://your-agent-xxxxx.railway.app/ask \
  -H "X-API-Key: YOUR_KEY" \
  -d '{"question": "Hello"}'

## Screenshots
- [Dashboard](screenshots/dashboard.png)
- [Deployment success](screenshots/success.png)
- [Test results](screenshots/test.png)
```

### 4. GitHub Repository

**Yêu cầu:**
- [ ] Công khai (public)
- [ ] MISSION_ANSWERS.md ✓
- [ ] DEPLOYMENT.md ✓
- [ ] Tất cả source code ✓
- [ ] README.md rõ ràng ✓
- [ ] Không có .env, không có secrets ✓
- [ ] Commit history rõ ràng ✓
- [ ] screenshots/ folder ✓

---

## 🎬 CÁCH LÀM

1. **Đọc file này** ← Bạn đang ở đây
2. **Làm từng phần** theo Step-by-step
3. **Ghi lại answers** vào MISSION_ANSWERS.md
4. **Build Part 6** từ đầu
5. **Deploy** lên Railway/Render
6. **Nộp:**
   - MISSION_ANSWERS.md
   - DEPLOYMENT.md  
   - Source code (GitHub repo)

---

## ⏱️ TIME ESTIMATE

| Phần | Thời gian | Ghi chú |
|------|-----------|--------|
| Part 1 | 30 phút | Đọc, so sánh, trả lời |
| Part 2 | 45 phút | Docker, build, compose |
| Part 3 | 45 phút | Deploy Railway/Render |
| Part 4 | 40 phút | Auth, rate limit, cost guard |
| Part 5 | 40 phút | Health check, graceful shutdown |
| Part 6 | 60 phút | Build full project |
| **TOTAL** | **4 giờ** | Nếu làm không dừng |

💡 **Pro tip:** Part 1-5 là learning, Part 6 là actual building. Có thể làm Part 6 từ đầu nếu bạn đã hiểu concepts.

---

## ✅ SUCCESS CRITERIA

Bạn thành công khi:

1. ✅ Tất cả code chạy không error
2. ✅ Docker image build < 500 MB
3. ✅ Deploy lên cloud với public URL
4. ✅ Public URL trả lời câu hỏi qua API
5. ✅ Authentication hoạt động (401 without key, 200 with key)
6. ✅ Rate limiting hoạt động (429 after 10 requests)
7. ✅ Cost guard hoạt động (402 after $10)
8. ✅ Health check hoạt động (/health → 200)
9. ✅ Nộp đủ cả 3 file (MISSION_ANSWERS.md, DEPLOYMENT.md, GitHub repo)

---

## 🆘 NẾU GẶP LỖI

1. **Xem TROUBLESHOOTING.md** trong project
2. **Google error message**
3. **Hỏi classmates hoặc instructor**

---

## 📌 NOTES

- **Deadline:** 17/4/2026
- **No API key needed** - dùng mock LLM
- **Không có points** nếu không submit MISSION_ANSWERS.md
- **Không có points** nếu không có public URL hoạt động
- **Secrets không được hardcode** - dùng environment variables
