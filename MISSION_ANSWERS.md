# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found

Tìm được **7 vấn đề lớn** trong `01-localhost-vs-production/develop/app.py`:

1. **Hardcoded API Key** (`sk-hardcoded-fake-key-never-do-this`)
   - ❌ Nếu push lên GitHub → key bị lộ ngay lập tức
   - ❌ Ai cũng có thể sử dụng key đó
   - ✅ Solution: Đọc từ environment variable `OPENAI_API_KEY`

2. **Hardcoded Database URL** (`postgresql://admin:password123@localhost:5432/mydb`)
   - ❌ Database password để trong code
   - ❌ Giống như để chìa khóa nhà ngoài cửa
   - ✅ Solution: Dùng `DATABASE_URL` env var

3. **Không có Health Check Endpoint**
   - ❌ Cloud platform (Railway, Render) không biết app còn sống hay không
   - ❌ Nếu app crash, platform không thể restart tự động
   - ✅ Solution: Implement `/health` endpoint return 200 OK

4. **Port Cố Định trong Code** (`port=8000`)
   - ❌ Railway/Render quy định port thông qua `PORT` env var
   - ❌ Nếu port đã được dùng, app sẽ crash
   - ✅ Solution: `port = int(os.getenv("PORT", 8000))`

5. **Host Cố Định** (`host="localhost"`)
   - ❌ `localhost` chỉ chạy được trên máy cục bộ
   - ❌ Trong container, cần `0.0.0.0` để lắng nghe tất cả network interfaces
   - ✅ Solution: `host = os.getenv("HOST", "0.0.0.0")`

6. **Debug Mode Bật trong Production** (`debug=True`, `reload=True`)
   - ❌ Reload mode tạo process mới liên tục → tốn CPU
   - ❌ Debug mode leak thông tin nhạy cảm
   - ✅ Solution: `debug = os.getenv("DEBUG", "false").lower() == "true"`

7. **Logging không Structured** (`print()` thay vì proper logging)
   - ❌ Print output khó parse, khó search trong logs lớn
   - ❌ Log ra secret key (`OPENAI_API_KEY`)
   - ✅ Solution: JSON structured logging, không log secrets

---

### Exercise 1.2: Chạy basic version

**Commands:**
```bash
cd 01-localhost-vs-production/develop
pip install -r requirements.txt
python app.py
```

**Test (terminal khác):**
```bash
curl http://localhost:8000/
# Response: {"message": "Hello! Agent is running on my machine :)"}

curl -X POST http://localhost:8000/ask?question=Hello
# Response: {"answer": "I'm a mock LLM..."}
```

**Kết quả:**
- ✅ App chạy thành công trên localhost
- ✅ Endpoints hoạt động
- ⚠️ Nhưng KHÔNG production-ready (có tất cả 7 vấn đề ở trên)

**Quan sát:**
```
Port: 8000 (cứng → không flexible)
Host: localhost (chỉ local → không container-friendly)
Config: Hardcode trong code → không env-friendly
Logging: print() → không parse-friendly
Health check: ❌ không có → không tự động restart
Debug: True → không security-friendly
```

---

### Exercise 1.3: Comparison table

| Feature | Basic (Develop) | Advanced (Production) | Tại sao quan trọng? |
|---------|-----------------|----------------------|---------------------|
| **API Key** | Hardcoded `sk-hardcoded-...` | Env var `OPENAI_API_KEY` | Secrets không được hardcode, GitHub sẽ lộ ngay |
| **Database URL** | Hardcoded password | Env var `DATABASE_URL` | Tách config khỏi code → security |
| **Host** | `host="localhost"` | `host=os.getenv("HOST", "0.0.0.0")` | Container cần `0.0.0.0` để bind tất cả interfaces |
| **Port** | `port=8000` (fixed) | `port=int(os.getenv("PORT", 8000))` | Cloud platform inject PORT → flexibility |
| **Health Check** | ❌ không có | ✅ `/health` endpoint | Platform tự động restart nếu fail |
| **Readiness Check** | ❌ không có | ✅ `/ready` endpoint | Platform biết khi nào start nhận traffic |
| **Logging** | `print()` statements | JSON structured logging | Log aggregator parse dễ, không log secrets |
| **Debug Mode** | `debug=True` (always) | `os.getenv("DEBUG", "false")` | Dev=true, Prod=false → cost & security |
| **Reload** | `reload=True` (always) | Disabled in production | Dev=true for fast iteration, Prod=false for stability |
| **Graceful Shutdown** | ❌ không xử lý SIGTERM | ✅ Signal handler + lifespan context | Hoàn thành in-flight requests trước khi tắt |
| **CORS** | ❌ không có | ✅ Whitelist origins | Bảo vệ khỏi cross-origin attacks |
| **Config Management** | Hardcode everywhere | Centralized `config.py` | Dễ thay đổi env, fail fast nếu missing config |
| **Environment Awareness** | `environment` hardcode | `os.getenv("ENVIRONMENT")` | Dev/staging/prod cần khác config |

---

### Câu hỏi thảo luận



## Part 2: Docker

### Exercise 2.1: Dockerfile questions

1. **Base image là gì?**
   - Develop: `python:3.11` - Full Python distribution (~1GB)
   - Production: `python:3.11-slim` - Lightweight Python (~300MB)
   - Image là template chứa OS + runtime (Python) + base libraries

2. **Working directory là gì?**
   - Trong Dockerfile: `WORKDIR /app`
   - Tương đương `cd /app` - tất cả file được COPY/RUN sẽ ở `/app`
   - Khi start container: working directory mặc định là `/app`

3. **Tại sao COPY requirements.txt trước?**
   - **Docker layer cache:** Mỗi lệnh RUN/COPY tạo một layer
   - Nếu code thay đổi nhưng requirements.txt không → dùng lại cache từ lần trước (super fast!)
   - Nếu COPY code trước, mọi thay đổi code → phải cài lại tất cả packages (lãng phí)
   - **Pattern:** COPY dependencies → RUN pip install → COPY code

4. **CMD vs ENTRYPOINT - khác nhau gì?**
   - **CMD:** Cung cấp lệnh và tham số mặc định
     - Có thể override: `docker run image python app2.py` → chạy app2.py thay vì CMD
   - **ENTRYPOINT:** Quy định executable chính của container
     - Khó override, tham số từ CMD hoặc `docker run` được truyền vào ENTRYPOINT
   - **Ví dụ:**
     ```dockerfile
     ENTRYPOINT ["uvicorn"]
     CMD ["main:app", "--host", "0.0.0.0"]
     # → chạy: uvicorn main:app --host 0.0.0.0
     
     # override: docker run image --port 9000
     # → chạy: uvicorn --port 9000
     ```

### Exercise 2.2: Build & Run basic version

**Commands:**
```bash
docker build -f 02-docker/develop/Dockerfile -t agent-develop:latest .
docker run -p 8000:8000 agent-develop:latest
```

**Results:**
- ✅ Build successful
- ✅ Container starts without errors
- ✅ Agent responds to requests

**Test curl:**
```bash
curl http://localhost:8000/
# Response: {"message": "Agent is running in a Docker container!"}

curl -X POST "http://localhost:8000/ask?question=Hello"
# Response: {"answer": "I'm a mock LLM..."}

curl http://localhost:8000/health
# Response: {"status": "ok", "uptime_seconds": 5.2, "container": true}
```

### Exercise 2.3: Multi-stage build comparison

| Đặc điểm | Develop (Single) | Production (Multi) | Tại sao khác? |
|---------|------------------|-------------------|--------------|
| **Image Size** | 424 MB | 56.6 MB | Multi-stage loại bỏ build tools |
| **Compressed** | 1.66 GB | 236 MB | Builder stage không được ship |
| **Build Time** | ~25s | ~107s | Production phải build 2 stages |
| **Base Image** | python:3.11 | python:3.11-slim | slim = không có build tools |
| **Build Tools** | ✅ gcc, make, etc. | ❌ Chỉ ở stage 1 | Mỏng nhẹ = dễ deploy |
| **Non-root User** | ❌ Chạy as root | ✅ appuser | Bảo mật > không escalate privilege |
| **Healthcheck** | ❌ Không có | ✅ HTTP healthcheck | Docker tự restart nếu fail |

**Multi-stage build breakdown:**

```dockerfile
# STAGE 1: Builder (cài gcc, build deps)
FROM python:3.11-slim AS builder
RUN apt-get install gcc libpq-dev ...  # Build tools
RUN pip install --user -r requirements.txt  # Compile & install

# STAGE 2: Runtime (chỉ copy compiled packages)
FROM python:3.11-slim
COPY --from=builder /root/.local /home/appuser/.local
# Bây giờ image chỉ có compiled packages, không có gcc!
```

**Size reduction: (424 - 56.6) / 424 = 86.6% nhỏ hơn! 🎉**

**Why production < 500MB is important:**
- Cloud platforms (Railway, Render) giới hạn image size (thường 500MB-1GB)
- Nhỏ = pull nhanh = deploy nhanh = start nhanh
- Docker hub storage quota
- Network bandwidth = chi phí

### Exercise 2.4: Docker Compose stack test

**Stack có 4 services:**
1. **agent** - FastAPI app (2 workers) - port 8000
2. **redis** - Caching & session store - port 6379  
3. **qdrant** - Vector DB for RAG - port 6333
4. **nginx** - Load balancer - port 80

**Test commands:**
```bash
docker compose up -d

# Health check
curl http://localhost/health
# Expected: {"status": "ok"}

# Agent endpoint (qua Nginx)
curl -X POST http://localhost/ask?question=Hello \
  -H "Content-Type: application/json"
# Expected: {"answer": "...mock response..."}

# Check services
docker compose ps
# Status: all running ✅

docker compose logs agent
# Output: FastAPI startup logs

# Cleanup
docker compose down
```

**Architecture:**
```
[Client] 
   ↓
[Nginx - Port 80 - Load Balancer]
   ↓
[Agent Instance 1]  [Agent Instance 2]  [Agent Instance 3]
   ↓                   ↓                    ↓
[Redis - Port 6379] (shared cache)
[Qdrant - Port 6333] (shared vector DB)
```

**Quan sát:**
- ✅ Services communicate via Docker internal network (service_name:port)
- ✅ Nginx phân tán requests qua agents
- ✅ Redis/Qdrant dùng chung cho tất cả agents (stateless)
- ✅ Volumes persist data giữa restarts

---

## Part 3: Cloud Deployment

*(Sẽ update sau khi hoàn thành Part 3)*

---

## Part 4: API Security

*(Sẽ update sau khi hoàn thành Part 4)*

---

## Part 5: Scaling & Reliability

*(Sẽ update sau khi hoàn thành Part 5)*

