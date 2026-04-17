#  Delivery Checklist — Day 12 Lab Submission

> **Student Name:** _________________________  
> **Student ID:** _________________________  
> **Date:** _________________________

---

##  Submission Requirements

Submit a **GitHub repository** containing:

### 1. Mission Answers (40 points)

Create a file `MISSION_ANSWERS.md` with your answers to all exercises:

```markdown
# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. **Hardcoded API Key:** Lộ thông tin nhạy cảm khi push lên Git.
2. **Fixed Port/Host:** Không linh hoạt khi chạy trên Docker/Cloud.
3. **Debug Mode:** Bật `debug=True` trong production gây tốn tài nguyên và lộ lỗi.
4. **No Health Check:** Hệ thống không biết khi nào app chết để restart.
5. **Print Logging:** Gây lỗi encoding (UnicodeError) và khó quản lý tập trung.
6. **No Graceful Shutdown:** Ngắt kết nối người dùng đột ngột khi tắt app.
7. **No Config Management:** Khó thay đổi thông số giữa các môi trường Dev/Prod.


### Exercise 1.3: Comparison table
| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| **Config** | Hardcode code | Env Vars (`.env`) | Bảo mật và linh hoạt giữa các môi trường. |
| **Port/Host** | localhost:8000 | 0.0.0.0:${PORT} | Cần thiết để Docker & Cloud có thể route traffic. |
| **Checks** | ❌ Không có | `/health`, `/ready` | Tự động giám sát và phục hồi ứng dụng. |
| **Logging** | `print()` | JSON Structured | Dễ parse và phân tích log ở quy mô lớn. |
| **Shutdown** | Đột ngột | Graceful | Hoàn thành request dở dang, đảm bảo UX. |

**1. Điều gì xảy ra nếu bạn push code với API key hardcode lên GitHub public?**
- **Bị lộ bí mật (Credential Leaks):** Các bot quét GitHub sẽ phát hiện ra key của bạn chỉ trong vài giây.
- **Mất tiền/Tài nguyên:** Người khác có thể dùng key đó để gọi API (OpenAI, AWS, v.v.), khiến bạn phải trả hóa đơn khổng lồ.
- **Nguy cơ bảo mật:** Nếu là key truy cập hệ thống (Database, Cloud provider), kẻ tấn công có thể chiếm quyền điều khiển hoặc đánh cắp dữ liệu.
- **Cơ chế thu hồi:** GitHub sẽ gửi cảnh báo, và bạn phải lập tức "revoke/rotate" key đó.

**2. Tại sao stateless quan trọng khi scale?**
- **Tính linh hoạt (Horizontal Scaling):** Khi app stateless (không lưu data người dùng trong RAM của server), Load Balancer có thể gửi request đến bất kỳ instance nào (A, B hoặc C) mà vẫn xử lý được.
- **Tính tin cậy:** Nếu một instance bị crash, người dùng chỉ cần gửi lại request và sẽ được phục vụ bởi instance khác mà không mất dữ liệu phiên làm việc (session).
- **Dễ quản lý:** Việc thêm/bớt instances trở nên cực kỳ đơn giản vì các instances hoàn toàn giống hệt nhau.

**3. 12-factor nói "dev/prod parity" — nghĩa là gì trong thực tế?**
- **Đồng nhất môi trường:** Giảm thiểu sự khác biệt giữa môi trường phát triển (Local) và môi trường thực tế (Cloud) về:
    - **Code:** Code chạy ở local và prod phải là một.
    - **Dependencies:** Dùng chung phiên bản thư viện (qua `requirements.txt` hoặc Docker).
    - **Backing services:** Nếu prod dùng Redis, local cũng nên dùng Redis (không dùng kiểu "local dùng RAM, prod dùng Redis").
- **Lợi ích:** Tránh tình trạng "it works on my machine" (chạy trên máy tôi ổn mà lên server lại lỗi).

## Part 2: Docker

### Exercise 2.1: Dockerfile questions

1. **Base image:** 
   - Basic: `python:3.11` (Full Python distribution ~1GB)
   - Production: `python:3.11-slim` (Lightweight, no build tools ~300MB)
   
2. **Working directory:** `/app`

3. **Tại sao COPY requirements.txt trước?**
   - Để tận dụng **Docker layer cache**
   - Nếu code thay đổi nhưng dependencies không, Docker sẽ dùng lại layer cũ → build cực nhanh
   - Nếu COPY code trước, mọi thay đổi code đều phải cài lại tất cả packages (lãng phí time)

4. **CMD vs ENTRYPOINT:**
   - `CMD`: Cung cấp lệnh mặc định (có thể ghi đè khi `docker run`)
   - `ENTRYPOINT`: Quy định executable chính (khó ghi đè, tham số từ CMD được truyền vào)
   - Best practice: Dùng ENTRYPOINT cho executable chính, CMD cho default args

### Exercise 2.2: Build & Run Results

**Build commands executed:**
```bash
# Develop (basic, single-stage)
docker build -f 02-docker/develop/Dockerfile -t agent-develop:latest .

# Production (advanced, multi-stage)
docker build -f 02-docker/production/Dockerfile -t agent-production:latest .
```

**Status:** ✅ Both images built successfully

### Exercise 2.3: Image size comparison

| Metric | Develop | Production | Difference |
|--------|---------|------------|-----------|
| **Image Size** | 424 MB | 56.6 MB | **86.6% nhỏ hơn** 🎉 |
| **Compressed Size** | 1.66 GB | 236 MB | **86.8% nhỏ hơn** |
| **Base Image** | python:3.11 (full) | python:3.11-slim | ~7x smaller |
| **Build Strategy** | Single-stage | Multi-stage | Builder stage discarded |
| **Non-root User** | ❌ root | ✅ appuser | Security improvement |
| **Build Tools** | ✅ Included | ❌ Not in final | Cleanup after build |

**Why multi-stage is better:**
- **Builder stage (Stage 1):** Contains gcc, build-essential, etc. needed to compile dependencies
- **Runtime stage (Stage 2):** Only copied compiled packages, no build tools → 86% smaller!
- **Security:** Non-root user (appuser) cannot escalate privileges
- **Performance:** Smaller images = faster pull/push, less bandwidth, less disk usage
- **Deployment:** Under 500MB limit ✅

### Exercise 2.4: Docker Compose Stack

**Services in stack:**
1. **agent** - FastAPI application (FastAPI on port 8000, 2 workers)
2. **redis** - In-memory cache for session & rate limiting (port 6379)
3. **qdrant** - Vector database for RAG (port 6333)
4. **nginx** - Load balancer & reverse proxy (port 80/443)

**Stack Architecture:**
```
Client → Nginx (port 80) → Agent (port 8000) → Redis (6379)
                                    ↓
                               Qdrant (6333)
```

**Services tested:**
- ✅ agent: Healthy (FastAPI with health check)
- ✅ redis: Healthy (redis-cli ping response)
- ✅ qdrant: Healthy (curl health endpoint)
- ✅ nginx: Active (reverse proxy forwarding)

## Part 3: Cloud Deployment

### Exercise 3.1: Render Deployment ✅

**Platform:** Render.com (Free tier)

**Public URL:**
```
https://twoa202600383-levanquangtrung-day12.onrender.com
```

**Deployment Process:**
1. ✅ Created production Dockerfile (multi-stage build)
2. ✅ Created render.yaml configuration
3. ✅ Pushed code to GitHub
4. ✅ Connected GitHub repo to Render
5. ✅ Render auto-deployed on git push
6. ✅ Service status: **LIVE** 🟢

**Build Information:**
- **Base Image:** python:3.11-slim (multi-stage)
- **Image Size:** ~56.6 MB (production optimized)
- **Build Time:** ~5-10 minutes (first deployment)
- **Deployment URL:** https://twoa202600383-levanquangtrung-day12.onrender.com
- **Deploy Status:** ✅ Success

### Exercise 3.2: Endpoint Testing ✅

**Test Results:**

```bash
# 1. Health Check Endpoint
GET /health
Response: 200 OK
{
  "status": "ok",
  "uptime_seconds": 21.4,
  "version": "2.0.0",
  "timestamp": "2026-04-17T08:41:50.247104"
}
✅ PASSED

# 2. Ask Endpoint (Agent Query)
POST /ask
Body: {"question": "Hello"}
Headers: X-API-Key: sk-test-part3-change-later
Response: 200 OK
{
  "answer": "Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé."
}
✅ PASSED

# 3. Ready Endpoint (Readiness Check)
GET /ready
Response: 200 OK
{"ready": true}
✅ PASSED
```

**Test Commands (for reproduction):**
```bash
# Health check
curl https://twoa202600383-levanquangtrung-day12.onrender.com/health

# Agent ask with API key
curl -X POST https://twoa202600383-levanquangtrung-day12.onrender.com/ask \
  -H "X-API-Key: sk-test-part3-change-later" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'

# Readiness check
curl https://twoa202600383-levanquangtrung-day12.onrender.com/ready
```

**Key Features Verified:**
- ✅ Health check endpoint responsive
- ✅ Agent endpoint accepting POST requests
- ✅ Mock LLM integration working
- ✅ Environment variables loaded (ENVIRONMENT=production)
- ✅ Multi-stage Docker build optimized
- ✅ Non-root user (appuser) running container
- ✅ CORS middleware configured
- ✅ JSON structured logging enabled

**Environment Variables Set on Render:**
| Variable | Value |
|----------|-------|
| ENVIRONMENT | production |
| LOG_LEVEL | info |
| AGENT_API_KEY | sk-test-part3-change-later |
| DEBUG | false |
| PORT | 8000 (auto-assigned by Render) |

**Files Deployed:**
- ✅ Dockerfile (multi-stage production build)
- ✅ render.yaml (Render deployment config)
- ✅ .env.example (environment template)
- ✅ 02-docker/production/main.py (FastAPI app)
- ✅ 02-docker/production/requirements.txt (dependencies)
- ✅ utils/mock_llm.py (mock LLM module)

**Summary:**
Part 3 completed successfully! Agent is deployed on Render cloud and responding to requests from a public URL. Multi-stage Docker optimization achieved 86.6% size reduction (56.6 MB), security best practices implemented (non-root user, env vars, no hardcoded secrets).

## Part 4: API Security

### Exercise 4.1-4.3: Test results
[Paste your test outputs]

### Exercise 4.4: Cost guard implementation
[Explain your approach]

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes
[Your explanations and test results]
```

---

### 2. Full Source Code - Lab 06 Complete (60 points)

Your final production-ready agent with all files:

```
your-repo/
├── app/
│   ├── main.py              # Main application
│   ├── config.py            # Configuration
│   ├── auth.py              # Authentication
│   ├── rate_limiter.py      # Rate limiting
│   └── cost_guard.py        # Cost protection
├── utils/
│   └── mock_llm.py          # Mock LLM (provided)
├── Dockerfile               # Multi-stage build
├── docker-compose.yml       # Full stack
├── requirements.txt         # Dependencies
├── .env.example             # Environment template
├── .dockerignore            # Docker ignore
├── railway.toml             # Railway config (or render.yaml)
└── README.md                # Setup instructions
```

**Requirements:**
-  All code runs without errors
-  Multi-stage Dockerfile (image < 500 MB)
-  API key authentication
-  Rate limiting (10 req/min)
-  Cost guard ($10/month)
-  Health + readiness checks
-  Graceful shutdown
-  Stateless design (Redis)
-  No hardcoded secrets

---

### 3. Service Domain Link

Create a file `DEPLOYMENT.md` with your deployed service information:

```markdown
# Deployment Information

## Public URL
https://your-agent.railway.app

## Platform
Railway / Render / Cloud Run

## Test Commands

### Health Check
```bash
curl https://your-agent.railway.app/health
# Expected: {"status": "ok"}
```

### API Test (with authentication)production
```bash
curl -X POST https://your-agent.railway.app/ask \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "question": "Hello"}'
```

## Environment Variables Set
- PORT
- REDIS_URL
- AGENT_API_KEY
- LOG_LEVEL

## Screenshots
- [Deployment dashboard](screenshots/dashboard.png)
- [Service running](screenshots/running.png)
- [Test results](screenshots/test.png)
```

##  Pre-Submission Checklist

- [ ] Repository is public (or instructor has access)
- [ ] `MISSION_ANSWERS.md` completed with all exercises
- [ ] `DEPLOYMENT.md` has working public URL
- [ ] All source code in `app/` directory
- [ ] `README.md` has clear setup instructions
- [ ] No `.env` file committed (only `.env.example`)
- [ ] No hardcoded secrets in code
- [ ] Public URL is accessible and working
- [ ] Screenshots included in `screenshots/` folder
- [ ] Repository has clear commit history

---

##  Self-Test

Before submitting, verify your deployment:

```bash
# 1. Health check
curl https://your-app.railway.app/health

# 2. Authentication required
curl https://your-app.railway.app/ask
# Should return 401

# 3. With API key works
curl -H "X-API-Key: YOUR_KEY" https://your-app.railway.app/ask \
  -X POST -d '{"user_id":"test","question":"Hello"}'
# Should return 200

# 4. Rate limiting
for i in {1..15}; do 
  curl -H "X-API-Key: YOUR_KEY" https://your-app.railway.app/ask \
    -X POST -d '{"user_id":"test","question":"test"}'; 
done
# Should eventually return 429
```

---

##  Submission

**Submit your GitHub repository URL:**

```
https://github.com/your-username/day12-agent-deployment
```

**Deadline:** 17/4/2026

---

##  Quick Tips

1.  Test your public URL from a different device
2.  Make sure repository is public or instructor has access
3.  Include screenshots of working deployment
4.  Write clear commit messages
5.  Test all commands in DEPLOYMENT.md work
6.  No secrets in code or commit history

---

##  Need Help?

- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Review [CODE_LAB.md](CODE_LAB.md)
- Ask in office hours
- Post in discussion forum

---

**Good luck! **
