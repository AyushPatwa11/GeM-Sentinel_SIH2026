# Railway Backend Deployment Step-by-Step

## ✅ Your Backend is Ready!

Your FastAPI + PostgreSQL backend is optimized and ready for Railway deployment.

---

## 📋 Pre-Deployment Checklist

- [x] FastAPI setup
- [x] PostgreSQL configured
- [x] Environment variables prepared
- [x] `Procfile` configured
- [x] `requirements.txt` finalized
- [ ] GitHub repository connected
- [ ] Railway project created

---

## 🚀 Step 1: Prepare for Railway

### Check Backend Files

✅ **Procfile** (already created):
```
web: cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

✅ **runtime.txt** (Python version):
```
python-3.10.12
```

✅ **requirements.txt** (dependencies):
- Should be in `backend/requirements.txt`

---

## 🚀 Step 2: Railway Backend Deployment

### Option A: Railway Dashboard (Easiest)

#### Step 2.1: Create Railway Account
1. Go to https://railway.app
2. Click "Start Free"
3. Sign in with GitHub
4. Authorize Railway

#### Step 2.2: Create New Project
1. Dashboard → "New Project"
2. Select "Deploy from GitHub repo"
3. Choose `AyushPatwa11/GeM-Sentinel_SIH2026`

#### Step 2.3: Configure Build Settings
Railway auto-detects Python. Set:
- **Root Directory**: `backend` (if not auto-detected)
- **Framework**: Python

#### Step 2.4: Add PostgreSQL Database
1. Project page → "Add New" → "Database"
2. Select "PostgreSQL"
3. Railway creates database auto

#### Step 2.5: Configure Environment Variables
Project → Variables → Add:

```
DATABASE_URL=<auto-filled from PostgreSQL>
SECRET_KEY=your-secret-key-here-min-32-chars
ENVIRONMENT=production
LOG_LEVEL=INFO
CORS_ORIGINS=https://your-vercel-frontend.vercel.app
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440
```

**Generate SECRET_KEY**:
```bash
# On your local machine
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### Step 2.6: Deploy
1. Click "Deploy"
2. Railway builds and deploys your backend
3. Takes 3-5 minutes

#### Step 2.7: Get Backend URL
1. Railway Dashboard → Project
2. Click on your Web service
3. Copy the URL from "Domain" section
4. Example: `https://gem-sentinel-backend-prod.railway.app`

---

### Option B: Railway CLI (Advanced)

#### Step 2.1: Install Railway CLI
```bash
npm install -g @railway/cli
```

#### Step 2.2: Login to Railway
```bash
railway login
```

#### Step 2.3: Initialize Project
```bash
cd c:\Users\abhy4\GeM-Sentinel_SIH2026
railway init
```

**Answer prompts**:
```
? Project name: gem-sentinel-backend
? Environment: production
```

#### Step 2.4: Link Repository
```bash
railway link
```

#### Step 2.5: Add PostgreSQL
```bash
railway add
# Select: PostgreSQL
```

#### Step 2.6: Set Environment Variables
```bash
railway variables set DATABASE_URL=$DATABASE_URL  # Auto from PostgreSQL
railway variables set SECRET_KEY=your-secret-key
railway variables set ENVIRONMENT=production
railway variables set CORS_ORIGINS=https://your-vercel-url.vercel.app
```

#### Step 2.7: Deploy
```bash
railway up
```

---

## 🗄️ Step 3: Database Setup

### Railway PostgreSQL Auto Setup
PostgreSQL is automatically created when you select Python framework.

### Run Migrations

#### Via Railway Dashboard:
1. Project → PostgreSQL
2. Copy `DATABASE_URL`
3. Run locally:
```bash
cd backend
DATABASE_URL=<paste-url> alembic upgrade head
```

Or deploy first, then migrations auto-run on startup.

---

## ✅ Test Your Backend

### Test 1: Health Check
```bash
curl https://your-railway-backend.railway.app/health
# Should return: {"status":"healthy"}
```

### Test 2: Login Endpoint
```bash
curl -X POST https://your-railway-backend.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"officer@gem.gov.in","password":"demo"}'
# Should return JWT token
```

### Test 3: API Docs
Open in browser:
```
https://your-railway-backend.railway.app/docs
```

Should see Swagger UI with all endpoints.

---

## 🔧 Environment Variables Reference

### Required
```
DATABASE_URL=postgresql://user:pass@host:port/db
SECRET_KEY=your-32-char-secret-key
ENVIRONMENT=production
CORS_ORIGINS=https://your-vercel-frontend.vercel.app
```

### Optional
```
LOG_LEVEL=INFO
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440
DEBUG=False
```

---

## 📊 Railway Dashboard Features

### Deployments Tab
- View deployment history
- Rollback to previous version
- View deployment logs in real-time

### Logs Tab
- Real-time application logs
- Filter by log level
- Search logs

### Metrics Tab
- CPU usage
- Memory usage
- Network I/O
- Response times

---

## 🐛 Troubleshooting

### Build Failed
**Check logs**:
1. Railway Dashboard → Project
2. Click on Web Service
3. View Deployment Logs

**Common issues**:
- Missing dependencies → Add to `requirements.txt`
- Python version mismatch → Update `runtime.txt`
- Environment variables missing → Add all required vars

### Runtime Error
**Check Application Logs**:
1. Railway → Logs tab
2. Look for error messages
3. Check DATABASE_URL is correct

### Database Connection Failed
**Verify DATABASE_URL**:
1. Railway → PostgreSQL
2. Copy connection string
3. Test locally:
```bash
psql <database-url>
```

### CORS Errors
**Update CORS_ORIGINS**:
1. Railway Variables
2. Set `CORS_ORIGINS=https://your-vercel-url`
3. Redeploy

### 502 Bad Gateway
**Common causes**:
- App crashed → Check logs
- Out of memory → Upgrade plan
- Database not running → Restart PostgreSQL

---

## 🔐 Security Best Practices

### Environment Variables
- ✅ Never commit `.env` to GitHub
- ✅ Use strong `SECRET_KEY`
- ✅ Rotate `SECRET_KEY` quarterly
- ✅ Set `ENVIRONMENT=production`

### Database
- ✅ Use strong PostgreSQL password (Railway auto-generates)
- ✅ Enable SSL connections (Railway does this auto)
- ✅ Regular backups (Railway auto-backs up daily)

### CORS
- ✅ Whitelist only your Vercel frontend URL
- ✅ Don't use `*` in production

---

## 📈 Monitoring

### Set Up Alerts
Railway → Settings → Alerts:
- CPU > 80%
- Memory > 80%
- Deploy failures

### View Metrics
1. Railway Dashboard → Metrics
2. Monitor response times
3. Monitor error rates

---

## 🔄 Deployment Updates

### After Code Changes
1. Push to GitHub: `git push origin main`
2. Railway auto-detects and redeploys
3. Takes 2-5 minutes

### Rollback to Previous Deployment
1. Railway → Deployments
2. Click on previous deployment
3. Click "Rollback"

---

## 📞 Support

- **Railway Docs**: https://docs.railway.app
- **Railway Status**: https://railway-status.railway.app/
- **Support**: support@railway.app

---

## After Deployment Checklist

- [ ] Backend deployed on Railway
- [ ] PostgreSQL database running
- [ ] Environment variables configured
- [ ] `/health` endpoint responding
- [ ] API docs accessible at `/docs`
- [ ] Database migrations completed
- [ ] CORS configured for frontend URL
- [ ] Frontend URL updated in Vercel

---

## Next Steps

1. ✅ Backend deployed on Railway
2. ✅ Get backend URL: `https://your-railway-backend.railway.app`
3. ✅ Update frontend `VITE_API_URL` with this URL
4. ✅ Redeploy frontend on Vercel
5. ✅ Test end-to-end workflow

---

**Railway Deployment Guide v1.0**  
**Updated**: September 15, 2026  
**Status**: ✅ Ready

