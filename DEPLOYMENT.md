# 🚀 NBKR Chatbot Deployment Guide

## Quick Deploy Options (Easiest First)

### ⭐ Option 1: Render (Recommended - FREE & Easy)

**Steps:**
1. Go to [render.com](https://render.com) and sign up (use GitHub account)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository: `https://github.com/23kb1a3080-cloud/department_chatbot`
4. Configure:
   - **Name**: nbkr-chatbot
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt && python -m spacy download en_core_web_sm`
   - **Start Command**: `uvicorn rag_chatbot:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free
5. Click "Create Web Service"
6. Wait 5-10 minutes for deployment
7. Your chatbot will be live at: `https://nbkr-chatbot.onrender.com`

**Pros**: Free, auto-deploys on git push, easy setup
**Cons**: Sleeps after 15 min inactivity (takes 30s to wake up)

---

### Option 2: Railway (FREE with GitHub Student Pack)

**Steps:**
1. Go to [railway.app](https://railway.app)
2. Sign in with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway auto-detects Python and deploys
6. Live URL provided automatically

**Pros**: Fast, no sleep, great free tier
**Cons**: Requires credit card after trial

---

### Option 3: Fly.io (FREE Tier Available)

**Steps:**
1. Install flyctl: `powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"`
2. Sign up: `flyctl auth signup`
3. Navigate to project folder
4. Run: `flyctl launch`
5. Follow prompts (use defaults)
6. Deploy: `flyctl deploy`

**Pros**: Good free tier, fast
**Cons**: Requires CLI installation

---

### Option 4: Hugging Face Spaces (FREE)

**Steps:**
1. Go to [huggingface.co/spaces](https://huggingface.co/spaces)
2. Create new Space
3. Choose "Docker" as SDK
4. Upload your files or connect GitHub
5. Add Dockerfile (already created)
6. Space will auto-deploy

**Pros**: Free forever, ML-focused platform
**Cons**: Slower cold starts

---

### Option 5: Google Cloud Run (FREE Tier)

**Steps:**
1. Install Google Cloud SDK
2. Login: `gcloud auth login`
3. Build: `gcloud builds submit --tag gcr.io/PROJECT_ID/nbkr-chatbot`
4. Deploy: `gcloud run deploy --image gcr.io/PROJECT_ID/nbkr-chatbot --platform managed`

**Pros**: Scales to zero, pay per use
**Cons**: Requires Google Cloud account

---

### Option 6: Heroku (Paid - $5/month)

**Steps:**
1. Install Heroku CLI: `npm install -g heroku`
2. Login: `heroku login`
3. Create app: `heroku create nbkr-chatbot`
4. Push: `git push heroku master`
5. Scale: `heroku ps:scale web=1`

**Pros**: Reliable, well-documented
**Cons**: No longer free

---

### Option 7: Docker + Any VPS (DigitalOcean, AWS, Azure)

**Steps:**
1. Build image: `docker build -t nbkr-chatbot .`
2. Run locally: `docker run -p 8000:8000 nbkr-chatbot`
3. Push to Docker Hub: `docker push username/nbkr-chatbot`
4. Deploy to VPS: `docker pull username/nbkr-chatbot && docker run -d -p 80:8000 nbkr-chatbot`

**Pros**: Full control, no sleep
**Cons**: Requires server management

---

## 🎯 Recommended for Your Submission: **Render**

### Why Render?
- ✅ Completely FREE
- ✅ No credit card required
- ✅ Auto-deploys from GitHub
- ✅ HTTPS included
- ✅ Takes 5 minutes to set up
- ✅ Perfect for academic projects

### After Deployment:
Your chatbot will be accessible at:
```
https://nbkr-chatbot.onrender.com
```

Share this URL in your submission!

---

## 📝 Environment Variables (if needed)

If deployment asks for environment variables, leave them empty. The chatbot works without external dependencies.

---

## 🔧 Troubleshooting

**Issue**: Build fails with "spaCy model not found"
**Fix**: Ensure build command includes: `python -m spacy download en_core_web_sm`

**Issue**: Port binding error
**Fix**: Use `--port $PORT` in start command (Render/Heroku provide PORT variable)

**Issue**: Memory limit exceeded
**Fix**: Use smaller FAISS index or upgrade to paid tier

---

## 📊 What's Deployed?

- ✅ RAG chatbot with FAISS vector search
- ✅ ML intent classifier (TF-IDF + Naive Bayes)
- ✅ NLP processing (spaCy)
- ✅ 194 knowledge base documents
- ✅ Timetables (1st, 2nd, 3rd year)
- ✅ Faculty information
- ✅ Circulars & announcements
- ✅ WebSocket real-time chat
- ✅ Structured HTML responses

---

## 🎓 For Your Submission

Include this in your project report:

**Live Demo URL**: `https://nbkr-chatbot.onrender.com`

**Technology Stack**:
- Backend: FastAPI + Python 3.10
- RAG: FAISS + Sentence Transformers
- ML: scikit-learn (TF-IDF + Naive Bayes)
- NLP: spaCy
- Deployment: Render (Cloud Platform)

**Features**:
- Real-time chat with WebSocket
- Semantic search with 194 documents
- Intent classification (8 classes)
- Structured HTML responses
- Multi-year timetable support
- Faculty directory
- Circulars & announcements

---

## 🚨 Quick Deploy NOW (5 minutes)

1. Open [render.com](https://render.com)
2. Sign up with GitHub
3. New Web Service → Connect repo
4. Use these settings:
   - Build: `pip install -r requirements.txt && python -m spacy download en_core_web_sm`
   - Start: `uvicorn rag_chatbot:app --host 0.0.0.0 --port $PORT`
5. Click Deploy
6. Done! 🎉

Your chatbot will be live in 10 minutes.
