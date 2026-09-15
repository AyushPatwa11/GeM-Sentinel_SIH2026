# GeM Sentinel - Complete Deployment Guide

## 📋 Deployment Architecture

```
┌─────────────────┐         ┌──────────────────┐
│  Vercel (CDN)   │◄────────►  Railway Backend │
│  React Frontend │         │  FastAPI + DB    │
└─────────────────┘         └──────────────────┘
   (5173 Local)            (8000 Local)
```

---

## 🚀 Part 1: Frontend Deployment on Vercel

### Step 1: Prepare Frontend for Vercel

✅ Already done! Your `vercel.json` is configured.

### Step 2: Connect to Vercel

1. **Go to Vercel**: https://vercel.com
2. **Sign up/Login** with GitHub account
3. **Click "Add New..."** → **Project**
4. **Import Repository**: Select `AyushPatwa11/GeM-Sentinel_SIH2026`
5. **Configure Project**:
   - **Framework Preset**: React
   - **Build Command**: `cd frontend && npm run build`
   - **Output Directory**: `frontend/dist`
   - **Install Command**: `cd frontend && npm install`

### Step 3: Environment Variables on Vercel

In Vercel Dashboard → Project Settings → Environment Variables:

```
VITE_API_URL=https://your-railway-backend-url/api
```

(Leave this blank for now, update after backend is deployed)

### Step 4: Deploy

Click **Deploy** - Vercel will automatically build and deploy your frontend!

**Your Frontend URL**: `https://your-project.vercel.app`

---

## 🚀 Part 2: Backend Deployment on Railway

### Option A: Railway (Recommended - Easiest)

#### Step 1: Prepare Backend

1. **Check Python version** in `backend/requirements.txt`:
   ```bash
   # Should be compatible with Python 3.10+
   ```

2. **Create `runtime.txt`** in backend folder:
   ```
   python-3.10.12
   ```

#### Step 2: Connect to Railway

1. **Go to Railway**: https://railway.app
2. **Sign up/Login** with GitHub
3. **New Project** → **Deploy from GitHub repo**
4. **Select**: `AyushPatwa11/GeM-Sentinel_SIH2026`
5. **Configure**:
   - **Root Directory**: `backend`
   - **Framework**: Python

#### Step 3: Environment Variables on Railway

Railway Dashboard → Project → Variables:

```
DATABASE_URL=postgresql://[user]:[password]@[host]:[port]/[database]
SECRET_KEY=your-secret-key-here
ENVIRONMENT=production
CORS_ORIGINS=https://your-project.vercel.app
```

**Get DATABASE_URL**:
- Railway Auto-generates PostgreSQL addon
- Copy the `DATABASE_URL` from PostgreSQL plugin

#### Step 4: Set Start Command

Railway → Settings → Start Command:
```
cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

#### Step 5: Deploy

Railway automatically deploys on push to GitHub!

**Your Backend URL**: `https://your-railway-project.railway.app`

---

### Option B: Render (Alternative)

If you prefer Render instead of Railway:

1. **Go to**: https://render.com
2. **New → Web Service**
3. **Connect GitHub repo**
4. **Configure**:
   - **Name**: `gem-sentinel-backend`
   - **Environment**: Python 3.10
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`

5. **Add PostgreSQL**:
   - Click "Create Database"
   - Copy connection string to `DATABASE_URL` variable

---

## 🔄 Step 3: Connect Frontend to Backend

After backend is deployed:

1. **Get Backend URL** from Railway/Render dashboard
2. **Update Vercel Environment Variables**:
   - Go to Vercel Dashboard
   - Project Settings → Environment Variables
   - Set `VITE_API_URL=https://your-backend-url/api`
3. **Redeploy Frontend** (Vercel auto-redeploys on variable change)

---

## 🗄️ Database Setup

### PostgreSQL on Railway (Auto-created)

Railway automatically creates PostgreSQL when you select Python framework.

**To verify database**:
1. Railway Dashboard → PostgreSQL plugin
2. Copy `DATABASE_URL`
3. Connection details appear there

### Run Migrations

```bash
# Local (for testing)
cd backend
alembic upgrade head

# On Railway (via SSH/CLI)
railway run alembic upgrade head
```

---

## 🔐 Environment Variables Summary

### Frontend (Vercel)
```
VITE_API_URL=https://your-backend-url/api
```

### Backend (Railway)
```
DATABASE_URL=postgresql://user:password@host:port/gem_sentinel
SECRET_KEY=your-secret-key-min-32-chars
ENVIRONMENT=production
CORS_ORIGINS=https://your-frontend-vercel-url
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

---

## ✅ Deployment Checklist

### Frontend (Vercel)
- [ ] GitHub repo connected
- [ ] `vercel.json` configured
- [ ] Environment variables set
- [ ] Build succeeds locally (`npm run build`)
- [ ] Frontend URL working

### Backend (Railway)
- [ ] GitHub repo connected
- [ ] `Procfile` configured
- [ ] `requirements.txt` updated
- [ ] Database URL set
- [ ] Secret keys generated
- [ ] CORS origins configured
- [ ] Migrations run successfully
- [ ] API endpoints responding

### Integration
- [ ] Frontend `VITE_API_URL` points to backend
- [ ] Backend `CORS_ORIGINS` includes frontend URL
- [ ] Login works end-to-end
- [ ] API calls from frontend succeed

---

## 🧪 Test Deployment

### Frontend Test
```bash
# After Vercel deployment
curl https://your-project.vercel.app
# Should return HTML (check browser)
```

### Backend Test
```bash
# After Railway deployment
curl https://your-backend-url/health
# Should return: {"status": "healthy"}

# Test login
curl -X POST https://your-backend-url/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"officer@gem.gov.in","password":"demo"}'
# Should return JWT token
```

### End-to-End Test
1. Open frontend URL in browser
2. Login with credentials
3. Create a tender
4. Submit a bid
5. Check audit logs

---

## 🐛 Troubleshooting

### Frontend: 404 on Vercel
- Check `vercel.json` output directory
- Verify build logs in Vercel dashboard

### Backend: 502 Bad Gateway
- Check Railway logs: Dashboard → Deployments
- Verify environment variables
- Run migrations: `railway run python backend/app/db/seed.py`

### CORS Errors
- Verify `CORS_ORIGINS` includes frontend URL
- Add `*` temporarily for testing (remove in production)

### Database Connection Failed
- Check `DATABASE_URL` format
- Test locally: `psql $DATABASE_URL`
- Ensure migrations ran

### API 401 Unauthorized
- Check JWT token expiration
- Verify `SECRET_KEY` is set on backend
- Check token in browser localStorage

---

## 📊 Cost Estimates (Monthly)

| Service | Free Tier | Paid Tier |
|---------|-----------|-----------|
| Vercel Frontend | $0 | $20+ |
| Railway Backend | $5 credit | $5-50+ |
| PostgreSQL | Included | Included |
| **Total** | **$5/month** | **$25+/month** |

---

## 🚀 Production Checklist

Before going live:
- [ ] Enable HTTPS (auto with Vercel/Railway)
- [ ] Set up monitoring (Railway has built-in)
- [ ] Configure backups (Railway PostgreSQL has auto-backups)
- [ ] Set up error tracking (optional: Sentry)
- [ ] Enable logging
- [ ] Test disaster recovery
- [ ] Document API endpoints
- [ ] Set up CI/CD (auto via GitHub integration)

---

## 📞 Support Links

- **Vercel Docs**: https://vercel.com/docs
- **Railway Docs**: https://docs.railway.app
- **Railway CLI**: `npm i -g @railway/cli`
- **FastAPI Production**: https://fastapi.tiangolo.com/deployment/

---

## Quick Deploy Commands

### Deploy to Railway (via CLI)
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link project
railway link

# Deploy
railway up
```

### View Logs
```bash
# Frontend (Vercel)
vercel logs --follow

# Backend (Railway)
railway logs --follow
```

---

**Deployment Guide v1.0**  
**Last Updated**: September 15, 2026  
**Status**: ✅ Ready to Deploy

