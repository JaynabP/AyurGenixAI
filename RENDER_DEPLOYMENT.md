# 🚀 AyurGenixAI - Render Deployment Guide

## ✅ **Pre-Deployment Checklist**

All files are properly configured for Render deployment:
- ✅ `main.py` - FastAPI app with proper port configuration
- ✅ `requirements.txt` - All dependencies listed
- ✅ `Procfile` - Render deployment command
- ✅ `runtime.txt` - Python version specified
- ✅ `.gitignore` - Sensitive files excluded
- ✅ Environment ready for GEMINI_API_KEY

## 🔧 **Step-by-Step Render Deployment**

### **Step 1: Prepare Repository**

```bash
# Commit all changes (if not already done)
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### **Step 2: Create Render Account & Service**

1. **Sign up/Login to Render**:
   - Go to https://render.com
   - Sign up with GitHub account
   - Connect your GitHub account

2. **Create New Web Service**:
   - Click "New +" → "Web Service"
   - Select "Build and deploy from a Git repository"
   - Choose your repository: `JaynabP/AyurGenixAI`
   - Click "Connect"

### **Step 3: Configure Service Settings**

**Basic Settings**:
- **Name**: `ayurgenixai` (or your preferred name)
- **Region**: Choose closest to your users
- **Branch**: `main`
- **Root Directory**: Leave empty (root of repo)

**Build Settings**:
- **Runtime**: `Python 3`
- **Build Command**: `pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

**Instance Type**:
- **Free Tier**: Select "Free" for testing  
- **Paid Tier**: Select "Starter" or higher for production (recommended)

### **Step 4: Set Environment Variables**

In the Render dashboard, go to "Environment" tab and add:

| Key | Value |
|-----|-------|
| `GEMINI_API_KEY` | `AIzaSyC6ZPzOTR_yDMctE8R1q2pOHYAXigvVWAo` |
| `PYTHON_VERSION` | `3.10.14` |

### **Step 5: Deploy**

1. Click "Create Web Service"
2. Render will automatically:
   - Clone your repository
   - Install dependencies from `requirements.txt`
   - Start the application using the Procfile command

### **Step 6: Monitor Deployment**

**Deployment Logs**: Check the logs tab for any errors
**Expected Log Output**:
```
==> Building application
==> Installing dependencies from requirements.txt
==> Starting application
INFO:main:Initializing AyurGenixAI system...
INFO:main:Initializing RAG processor...
INFO:simple_rag_processor:Successfully loaded 446 records
INFO:main:AyurGenixAI system initialized successfully!
INFO:uvicorn.server:Application startup complete.
```

## 🌐 **Access Your Deployed API**

After successful deployment:

- **API URL**: `https://your-service-name.onrender.com`
- **API Docs**: `https://your-service-name.onrender.com/docs`
- **Health Check**: `https://your-service-name.onrender.com/health`

## 🧪 **Test Deployment**

### **1. Health Check**
```bash
curl https://your-service-name.onrender.com/health
```

### **2. Test Prescription Generation**
```bash
curl -X POST "https://your-service-name.onrender.com/generate-medication" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Patient",
    "age": 30,
    "gender": "Female",
    "constitution_dosha": "Pitta",
    "symptoms": ["acidity", "heartburn"],
    "doctor_diagnosis": "Hyperacidity"
  }'
```

## ⚠️ **Common Issues & Solutions**

### **Issue 1: Build Fails**
**Solution**: Check dependencies in `requirements.txt`
```bash
# If you see version conflicts, use:
fastapi==0.104.1
uvicorn[standard]==0.24.0
# Remove version ranges that might conflict
```

### **Issue 2: App Doesn't Start**
**Solution**: Check environment variables
- Ensure `GEMINI_API_KEY` is set correctly
- Check logs for specific error messages

### **Issue 3: Timeout Errors**
**Solution**: 
- Free tier has limitations - upgrade to Starter plan
- Optimize model loading in startup

### **Issue 4: Memory Issues**
**Solution**:
- Upgrade to higher tier instance
- The model loads 446 records + AI model

## 🔒 **Security Configuration**

### **Production CORS Settings**
Update `main.py` for production:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],  # Specify your domain
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## 📊 **Performance Optimization**

### **For Production Use**:

1. **Upgrade Instance**: Use "Starter" plan or higher
2. **Set Persistent Storage**: If needed for caching
3. **Monitor Usage**: Check Render dashboard for metrics

## 🔄 **Continuous Deployment**

Render automatically redeploys when you push to `main` branch:

```bash
# Make changes locally
git add .
git commit -m "Update feature"
git push origin main
# Render will automatically redeploy
```

## 🎯 **Deployment Commands Summary**

```bash
# 1. Final preparation
git add .
git commit -m "Final deployment prep"
git push origin main

# 2. On Render Dashboard:
# - Create Web Service
# - Connect GitHub repo: JaynabP/AyurGenixAI
# - Set environment variable: GEMINI_API_KEY
# - Deploy

# 3. Test deployment
curl https://your-service-name.onrender.com/health
```

## ✅ **Final Checklist**

Before deployment, ensure:
- [ ] Repository pushed to GitHub
- [ ] Procfile created and committed
- [ ] requirements.txt updated
- [ ] GEMINI_API_KEY ready
- [ ] .env file NOT committed (in .gitignore)
- [ ] All endpoints tested locally

## 🎉 **Success!**

Your **AyurGenixAI** will be live at:
- **API**: `https://your-service-name.onrender.com`
- **Documentation**: `https://your-service-name.onrender.com/docs`

**Your intelligent Ayurvedic prescription system is now globally accessible!** 🌟

---

*Note: Render's free tier spins down after 15 minutes of inactivity. For production use, consider upgrading to a paid plan for consistent uptime.*