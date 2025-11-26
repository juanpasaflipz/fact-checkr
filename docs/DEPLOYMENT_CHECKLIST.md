# Deployment Checklist

Complete guide to deploy FactCheckr to production.

## ✅ Phase 1: Database Setup (Completed)

- [x] Neon PostgreSQL database created
- [x] Database connection string obtained
- [x] Database schema migrated

## ✅ Phase 2: Backend Deployment (Completed)

- [x] Railway account set up
- [x] Backend service deployed
- [x] Health check endpoint verified

## 🔄 Phase 3: Redis & Workers (In Progress)

### 3.1 Redis Setup
1. In Railway dashboard, click **+ New**
2. Select **Database** → **Redis**
3. Name: `factcheckr-redis`
4. Copy `REDIS_URL` from Redis service

### 3.2 Update Backend Environment
Add to backend service:
```
REDIS_URL=<from Redis service>
```

### 3.3 Deploy Celery Worker
1. Click **+ New** → **GitHub Repo** → `fact-checkr`
2. Name: `factcheckr-worker`
3. Railway Config Path: `backend/railway-worker.json`
4. Add environment variables (same as backend):
   - `DATABASE_URL`
   - `REDIS_URL`
   - `OPENAI_API_KEY`
   - `ANTHROPIC_API_KEY`
   - `PERPLEXITY_API_KEY`
5. Deploy and verify logs show: `✅ Worker module imported successfully`

### 3.4 Deploy Celery Beat
1. Click **+ New** → **GitHub Repo** → `fact-checkr`
2. Name: `factcheckr-beat`
3. Railway Config Path: `backend/railway-beat.json`
4. Add same environment variables as worker
5. Deploy and verify logs show: `✅ beat: Starting...`

## 📋 Phase 4: Frontend Deployment

### 4.1 Deploy to Vercel
1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **Add New** → **Project**
3. Import `fact-checkr` repository
4. Configure:
   - Framework: Next.js
   - Root Directory: `frontend`
5. Add environment variable:
   ```
   NEXT_PUBLIC_API_URL=<Railway backend URL>
   ```
6. Deploy

### 4.2 Update Backend CORS
Add to Railway backend service:
```
CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000
```

## 🔧 Phase 5: Configuration

### 5.1 Environment Variables Summary

**Backend (Railway)**:
```bash
DATABASE_URL=<Neon PostgreSQL>
REDIS_URL=<Railway Redis>
OPENAI_API_KEY=<your key>
ANTHROPIC_API_KEY=<your key>
PERPLEXITY_API_KEY=<your key>
CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000
```

**Worker & Beat (Railway)** - Same as backend

**Frontend (Vercel)**:
```bash
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

### 5.2 Verify All Services

- [ ] Backend API: `https://your-backend.railway.app/health`
- [ ] Worker: Check Railway logs for task processing
- [ ] Beat: Check Railway logs for scheduled tasks
- [ ] Frontend: Visit Vercel URL and verify pages load
- [ ] CORS: Test API calls from frontend

## 🧪 Phase 6: Testing

### 6.1 Backend Tests
```bash
# Health check
curl https://your-backend.railway.app/health

# API endpoints
curl https://your-backend.railway.app/api/v1/claims/recent

# Scraping status
curl https://your-backend.railway.app/api/v1/scraping/status
```

### 6.2 Frontend Tests
- [ ] Homepage loads
- [ ] Claims display correctly
- [ ] Topics page works
- [ ] Sources page works
- [ ] Statistics page works
- [ ] Trending page works

### 6.3 Worker Tests
- [ ] Check Railway logs for worker activity
- [ ] Verify scheduled scraping runs every hour
- [ ] Test manual task trigger (if applicable)

## 📊 Phase 7: Monitoring

### 7.1 Set Up Monitoring
- [ ] Railway: Monitor service health and logs
- [ ] Vercel: Enable Analytics
- [ ] Neon: Monitor database performance
- [ ] Set up alerts for service failures

### 7.2 Log Aggregation
- [ ] Backend logs in Railway
- [ ] Worker logs in Railway
- [ ] Frontend logs in Vercel
- [ ] Database logs in Neon

## 🚀 Phase 8: Post-Deployment

### 8.1 Documentation
- [ ] Update README with production URLs
- [ ] Document deployment process
- [ ] Create runbook for common issues

### 8.2 Security
- [ ] Verify all secrets are in environment variables
- [ ] Check CORS configuration
- [ ] Review security headers
- [ ] Enable HTTPS (automatic on Railway/Vercel)

### 8.3 Performance
- [ ] Test API response times
- [ ] Check frontend load times
- [ ] Monitor database query performance
- [ ] Verify CDN caching works

## 🔄 Ongoing Maintenance

### Daily
- Check service health
- Review error logs
- Monitor API usage

### Weekly
- Review database performance
- Check worker task success rate
- Analyze frontend analytics

### Monthly
- Review and optimize costs
- Update dependencies
- Review security advisories
- Backup database

## 📞 Support Resources

- **Railway**: https://railway.app/help
- **Vercel**: https://vercel.com/support
- **Neon**: https://neon.tech/docs
- **Next.js**: https://nextjs.org/docs
- **FastAPI**: https://fastapi.tiangolo.com

## 🆘 Troubleshooting

### Backend won't start
1. Check `DATABASE_URL` is correct
2. Verify Neon database is accessible
3. Review Railway logs for errors

### Worker not processing tasks
1. Verify `REDIS_URL` is set
2. Check Redis service is running
3. Review worker logs

### Frontend can't reach API
1. Verify `NEXT_PUBLIC_API_URL` is correct
2. Check backend CORS includes Vercel domain
3. Test backend health endpoint directly

### Database connection issues
1. Check Neon database status
2. Verify connection string format
3. Check IP allowlist (Neon allows all by default)

