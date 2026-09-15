# Vercel Frontend Deployment Step-by-Step

## ✅ Your Frontend is Ready!

Your React + Vite frontend is optimized and ready for Vercel deployment.

---

## 📋 Pre-Deployment Checklist

- [x] React + Vite setup
- [x] Environment variables configured
- [x] Build command verified
- [x] `vercel.json` configured
- [x] GitHub repository connected
- [ ] Backend deployed (do this first!)

---

## 🚀 Step 1: Deploy Backend First (Important!)

**Before deploying frontend, deploy backend to get the API URL**

See `DEPLOYMENT_GUIDE.md` for Railway backend deployment.

**You'll need this URL**: `https://your-railway-backend.railway.app`

---

## 🚀 Step 2: Vercel Frontend Deployment

### Option A: Via Vercel Dashboard (Easiest)

#### Step 2.1: Create Vercel Account
1. Go to https://vercel.com
2. Click "Sign Up"
3. Choose "Continue with GitHub"
4. Authorize Vercel to access your GitHub account

#### Step 2.2: Import Repository
1. Click "Add New" → "Project"
2. Search for `GeM-Sentinel_SIH2026`
3. Click "Import"

#### Step 2.3: Configure Project
Vercel should auto-detect:
- **Framework**: React ✓
- **Build Command**: `cd frontend && npm run build` ✓
- **Output Directory**: `frontend/dist` ✓
- **Install Command**: `cd frontend && npm install` ✓

If not, manually set them above.

#### Step 2.4: Environment Variables
1. Scroll to "Environment Variables"
2. Add:
   ```
   VITE_API_URL=https://your-railway-backend.railway.app/api
   ```
3. Click "Deploy"

#### Step 2.5: Wait for Deployment
- Vercel builds your frontend
- You'll see a progress bar
- Takes 2-5 minutes typically

#### Step 2.6: Get Your URL
After deployment completes:
- Your frontend URL: `https://your-project.vercel.app`

---

### Option B: Via Vercel CLI (Advanced)

#### Step 2.1: Install Vercel CLI
```bash
npm i -g vercel
```

#### Step 2.2: Login to Vercel
```bash
vercel login
```

#### Step 2.3: Deploy
```bash
cd c:\Users\abhy4\GeM-Sentinel_SIH2026
vercel --prod
```

#### Step 2.4: Answer Prompts
```
? Set up and deploy "C:\Users\abhy4\GeM-Sentinel_SIH2026"? [Y/n] Y
? Which scope do you want to deploy to? [your-username]
? Link to existing project? [y/N] N
? What's your project's name? gem-sentinel-frontend
? In which directory is your code? [./] ./frontend
? Want to modify these settings? [y/N] N
```

#### Step 2.5: Add Environment Variables
```bash
vercel env add VITE_API_URL
# Paste: https://your-railway-backend.railway.app/api
```

#### Step 2.6: Redeploy with Variables
```bash
vercel --prod
```

---

## ✅ Test Your Frontend

1. **Open in Browser**
   ```
   https://your-project.vercel.app
   ```

2. **Should See**:
   - GeM Sentinel landing page
   - Hero video playing
   - Sign In button
   - Officer/Bidder portals

3. **Test Login**:
   - Click "Sign In"
   - Email: `officer@gem.gov.in`
   - Password: `demo`
   - Should redirect to dashboard

4. **Test API Connection**:
   - Open browser DevTools (F12)
   - Go to Network tab
   - Click "Create Tender"
   - Check API requests are going to your backend URL

---

## 🔧 Environment Variables

### Frontend Only (Vercel)
```
VITE_API_URL=https://your-backend-url.railway.app/api
```

### Local Development
```bash
# Create frontend/.env.local
VITE_API_URL=http://localhost:8000/api
```

---

## 📊 Vercel Dashboard Features

### Deployments Tab
- View all deployments
- Rollback to previous version
- View deployment logs

### Settings Tab
- Domains (add custom domain)
- Environment variables
- Build & development settings
- Git integration

### Analytics Tab
- Performance metrics
- Web vitals
- Usage statistics

---

## 🎯 After Deployment

### Update Backend URL in Backend Code
If you change backend URL later:

1. Go to Vercel Dashboard
2. Settings → Environment Variables
3. Update `VITE_API_URL`
4. Redeploy (auto-triggers)

---

## 🐛 Troubleshooting

### Build Failed
**Check logs**:
1. Vercel Dashboard → Deployments
2. Click on failed deployment
3. Scroll to build logs
4. Look for error messages

**Common issues**:
- Missing npm dependencies → Add to `package.json`
- Build script error → Check `vercel.json`
- Wrong output directory → Update in `vercel.json`

### Frontend works but API calls fail
**Check API URL**:
1. Open browser DevTools (F12)
2. Go to Console
3. Type: `console.log(import.meta.env.VITE_API_URL)`
4. Should show your backend URL

**If wrong**:
- Update `VITE_API_URL` in Vercel env vars
- Redeploy

### 404 on subpaths
**React Router issue**:
1. Vercel → Settings → Build & Development
2. Framework: React
3. (Should auto-fix 404s)

If not, create `vercel.json`:
```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

---

## 📈 Performance Optimization

Vercel gives you free:
- ✅ Global CDN
- ✅ Automatic compression
- ✅ Image optimization
- ✅ Edge functions (Pro)

Your frontend will be **super fast!** 🚀

---

## 🔐 Security

Vercel provides:
- ✅ HTTPS auto (free)
- ✅ DDoS protection
- ✅ WAF (Web Application Firewall)
- ✅ Secure environment variables

---

## 📞 Support

- **Vercel Docs**: https://vercel.com/docs
- **Vercel Support**: https://vercel.com/support
- **Status Page**: https://www.vercelstatus.com/

---

## Next Steps After Frontend Deployment

1. ✅ Frontend deployed on Vercel
2. ✅ Backend deployed on Railway
3. ✅ Environment variables configured
4. ✅ Test end-to-end workflow:
   - Login → Create Tender → Submit Bid → View Decision
5. ✅ Set up custom domain (optional)
6. ✅ Monitor performance

---

**Vercel Deployment Guide v1.0**  
**Updated**: September 15, 2026  
**Status**: ✅ Ready

