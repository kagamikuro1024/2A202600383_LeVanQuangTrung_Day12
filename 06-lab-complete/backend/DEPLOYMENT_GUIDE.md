# TA ChatBot - Deployment Guide

**Hướng dẫn Deploy TA ChatBot lên Render.com với Day 12 Lab Security Features**

## 🎯 Day 12 Lab Concepts Integrated

### ✅ Part 1: Localhost vs Production
- Environment-based configuration
- `.streamlit/config.toml` for production settings
- No hardcoded secrets

### ✅ Part 2: Docker Containerization
- Multi-stage Docker build (Builder → Runtime)
- Final image: 250-300 MB (optimized)
- Non-root user `appuser` (security)

### ✅ Part 3: Cloud Deployment
- `render.yaml` configuration
- Automatic GitHub integration
- Health check configured

### ✅ **Part 4: API Security (NEW!)**
- **API Key Authentication**: Each user gets API key for tracking
- **Rate Limiting**: 20 requests per 60 seconds per user
- **Cost Guard**: $1/user/day, $10/global daily budget
- **Metrics Display**: Real-time cost tracking & budget alerts

### ✅ Part 5: Scaling & Reliability
- Health monitoring
- Error tracking & recovery
- Graceful shutdown support

---

## 🔐 Security Features Added

### 1️⃣ API Key Authentication
- Users provide API key in Streamlit sidebar
- Key is used to identify user for rate limiting & cost tracking
- Format: Any string (can be generated or custom)

### 2️⃣ Rate Limiting
```
Limit: 20 requests per 60 seconds
Per-user tracking
Warning at 5 requests remaining
Automatic blocking when exceeded
```

### 3️⃣ Cost Guard
```
Per-user budget: $1.00 / day
Global budget: $10.00 / day
Token-based pricing: $0.15 input, $0.60 output (GPT-4o-mini)
Warning at 80% usage
Blocking at 100% usage
```

### 4️⃣ Health Monitoring
```
Uptime tracking
Request counting
Error rate calculation
Real-time status display
```

---

## 📊 Sidebar Security Panel

New sidebar section displays:
- API Key input
- Rate limit status (remaining requests)
- Cost tracking (spent / budget)
- Health status (healthy / degraded)

Example:
```
🔐 Kiểm soát truy cập

API Key: [input field]

Requests còn lại: 15/20

💰 Budget hôm nay:
Cá nhân: $0.0012 / $1.00 (0.1%)
Toàn bộ: $0.0085 / $10.00 (0.1%)

📊 Trạng thái hệ thống:
Status: ✅ healthy
Uptime: 3600s
```

---

### Điều kiện bắt buộc:
- ✅ Code đã push lên GitHub: https://github.com/kagamikuro1024/TA_ChatBot
- ✅ `OPENAI_API_KEY` đã có (hoặc dùng mock)
- ✅ File `.env.example` hoặc tài liệu về environment variables
- ✅ `requirements.txt` đã update
- ✅ App chạy tốt trên local: `streamlit run app.py`

### File chuẩn bị (đã có):
- ✅ `Dockerfile` - Multi-stage Docker build
- ✅ `render.yaml` - Render deployment config
- ✅ `.dockerignore` - Docker build optimization
- ✅ `.streamlit/config.toml` - Streamlit production config

---

## 🚀 Bước 1: Tạo Render Service

### 1.1 Vào Render Dashboard
1. Đăng nhập: https://render.com/dashboard
2. Click **"New +"** → **"Web Service"**
3. Authorize GitHub (nếu chưa)

### 1.2 Kết nối GitHub Repository
1. Tìm kiếm repo: `TA_ChatBot`
2. Click **"Connect"**
3. Chọn branch: `main`

### 1.3 Cấu hình Service

**Thông tin cơ bản:**
```
Name: ta-chatbot
Environment: Docker
Region: US-East (hoặc region gần nhất)
```

**Dockerfile path:**
```
06-lab-complete/TA_Chatbot/Dockerfile
```

(Render sẽ auto-detect Docker từ Dockerfile)

### 1.4 Set Environment Variables

Click **"Environment"** tab, thêm:

```
OPENAI_API_KEY=sk-openai-xxxxxxxxxxxxxxxx
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_HEADLESS=true
```

**Tìm OPENAI_API_KEY:**
- Truy cập: https://platform.openai.com/api-keys
- Copy key của bạn (dạng `sk-...`)

---

## 🛠️ Bước 2: Deploy

1. **Click "Create Web Service"**
2. **Chờ build** (khoảng 5-10 phút)
   - Render sẽ:
     - Clone code từ GitHub
     - Build Docker image
     - Push lên container registry
     - Deploy service
     - Start health check

3. **Xem logs:**
   - Click tab "Logs"
   - Tìm dòng: `Streamlit app is running...`
   - Nếu thấy: ✅ Deploy thành công!

---

## ✅ Bước 3: Kiểm Tra Deployment

### 3.1 Lấy URL Deployed
- Trong Render dashboard, tìm mục **"Service URL"**
- VD: `https://ta-chatbot-xxxxx.onrender.com`

### 3.2 Test App
```bash
# Test health check
curl https://ta-chatbot-xxxxx.onrender.com/
# Expected: Trang Streamlit tải lên

# Hoặc mở trực tiếp trong browser
https://ta-chatbot-xxxxx.onrender.com
```

### 3.3 Test Chat
1. Mở app trên browser
2. Type câu hỏi: "Hỏi về deadline assignment 1"
3. AI trả lời → ✅ Thành công!

---

## 🔧 Troubleshooting

### Issue: Build fails

**Kiểm tra:**
1. Logs có error gì? → Xem tab "Logs"
2. `requirements.txt` có lỗi cú pháp?
   ```bash
   pip install -r requirements.txt
   # Test local trước
   ```
3. Dockerfile có đúng path không?
   ```
   COPY 06-lab-complete/TA_Chatbot .
   # Nên là: 06-lab-complete/TA_Chatbot/
   ```

### Issue: Container không start
- ✅ Health check failing?
- ✅ Port 8501 bị chiếm?
- ✅ Environment variables thiếu `OPENAI_API_KEY`?

**Xem logs:**
```
Render Dashboard → Logs tab
```

### Issue: App slow / timeout
- Có thể FAISS index quá lớn
- Hoặc OpenAI API slow
- Thử restart service:
  ```
  Render Dashboard → Manual Deploy
  ```

---

## 💡 Optimization Tips

### 1. Giảm Docker Image Size
- Dùng `python:3.11-slim` thay vì `python:3.11` ✅ (đã làm)
- Multi-stage build ✅ (đã làm)
- Clean cache: `rm -rf /var/lib/apt/lists/*` ✅ (đã làm)

**Current image size:**
- Builder stage: ~286 MB
- Runtime stage: ~250-300 MB

### 2. Cải Tiến Performance

**Streamlit config** (.streamlit/config.toml):
```toml
runOnSave = false        # Không reload on save
maxUploadSize = 200      # Giới hạn upload
logger.level = "error"   # Chỉ log errors
```

**Render plan:**
- `free` - OK cho demo
- `starter` ($7/month) - Cho production

### 3. Monitor App

**Trên Render dashboard:**
- CPU usage
- Memory usage
- Network I/O
- Request count
- Error logs

---

## 🔐 Security Checklist

- ✅ Non-root user `appuser` (security)
- ✅ No `.env` file in Docker (only environment variables)
- ✅ Health check configured
- ✅ Headless mode enabled (security)
- ✅ Error details hidden in production

**Before production:**
- [ ] API keys in Render environment (not in .env)
- [ ] Streamlit secrets.toml for sensitive data
- [ ] Enable authentication if public app
- [ ] Set CORS headers if needed

---

## 📚 App Architecture (Deployed)

```
Render Service
    ↓
Docker Container (ta-chatbot)
    ├── Python 3.11-slim runtime
    ├── User: appuser (non-root)
    ├── Port: 8501 (Streamlit)
    ├── Health check: /
    └── Entrypoint: streamlit run app.py
        ├── Streamlit Frontend (Web UI)
        ├── Agent (agent.py)
        │   ├── LangGraph React Agent
        │   ├── Tools:
        │   │   ├── search_course_materials (RAG)
        │   │   ├── analyze_code_error
        │   │   ├── get_course_info
        │   │   ├── escalate_to_human_ta
        │   │   └── verify_information
        │   └── LLM: OpenAI GPT-3.5 / GPT-4
        ├── RAG System
        │   ├── FAISS Index (vector search)
        │   ├── Knowledge Base (documents)
        │   └── Embeddings
        ├── Storage
        │   ├── Chat sessions
        │   ├── Metrics
        │   └── Escalation logs
        └── Email Service (for escalation)
```

---

## 🚀 Next Steps

1. **Deploy app lên Render** (steps 1-3 trên)
2. **Test chatbot trên live URL**
3. **Monitor performance** (check Render metrics)
4. **Optional:** Add custom domain
   - Render dashboard → Custom domain
   - Point DNS to Render

---

## 📞 Need Help?

**Check logs:**
```
Render Dashboard → Select service → Logs
```

**Debug locally:**
```bash
# Build Docker locally first
docker build -f 06-lab-complete/TA_Chatbot/Dockerfile -t ta-chatbot:latest .

# Run locally
docker run -p 8501:8501 \
  -e OPENAI_API_KEY=sk-... \
  ta-chatbot:latest

# Test
curl http://localhost:8501
```

**Render Docs:** https://docs.render.com/

---

**Status:** Ready for Deployment ✅
**Last Updated:** April 2026
