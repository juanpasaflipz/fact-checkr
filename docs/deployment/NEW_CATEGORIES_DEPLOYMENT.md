# Deployment Guide: New Market Categories

This guide covers deploying the new market categories feature (sports, financial-markets, weather, social-incidents) to production.

## ✅ Pre-Deployment Checklist

### Code Changes Summary
- ✅ Frontend: Added 4 new categories to markets page, proposal form, and onboarding
- ✅ Backend: Updated category validation in auth router
- ✅ Backend: Enhanced market intelligence agent for category-specific analysis
- ✅ Database: No migration needed (categories are strings, already supported)

### Testing Status
- ✅ Tests passed locally
- ✅ Test markets created successfully
- ✅ Filtering verified
- ✅ Intelligence agent tested
- ✅ User preferences validated

## 🚀 Deployment Steps

### Step 1: Commit and Push Changes

```bash
# Review changes
git status
git diff

# Stage all changes
git add .

# Commit with descriptive message
git commit -m "feat: Add new market categories (sports, financial-markets, weather, social-incidents)

- Add 4 new categories to frontend markets page
- Update category validation in backend
- Enhance market intelligence agent for category-specific analysis
- Add comprehensive test suite
- Update user preferences to support new categories"

# Push to main branch
git push origin main
```

### Step 2: Backend Deployment (Railway)

The backend will auto-deploy when you push to main (if Railway is connected to your repo).

#### Manual Verification:

1. **Check Railway Dashboard**
   - Go to Railway dashboard
   - Verify backend service is deploying
   - Wait for deployment to complete

2. **Verify Health Check**
   ```bash
   curl https://fact-checkr-production.up.railway.app/health
   ```
   Should return: `{"status":"healthy"}`

3. **Test New Categories Endpoint**
   ```bash
   # Test that new categories are accepted
   curl -X POST "https://fact-checkr-production.up.railway.app/api/markets/propose" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "Test sports market",
       "category": "sports",
       "description": "Test"
     }'
   ```
   Should return 200 (or 401 if not authenticated, which is expected)

4. **Check Logs**
   - Railway Dashboard → Backend Service → Logs
   - Look for any errors related to category validation
   - Verify no import errors

#### No Database Migration Needed
- Categories are stored as strings in the `markets.category` column
- No schema changes required
- Existing markets continue to work

### Step 3: Frontend Deployment (Vercel)

1. **Verify Environment Variables**
   - Go to Vercel Dashboard → Your Project → Settings → Environment Variables
   - Ensure `NEXT_PUBLIC_API_URL` points to your Railway backend
   - Should be: `https://fact-checkr-production.up.railway.app`

2. **Trigger Deployment**
   - Vercel auto-deploys on push to main
   - Or manually: Vercel Dashboard → Deployments → Redeploy

3. **Verify Build**
   - Check Vercel build logs
   - Should complete without errors
   - Look for any TypeScript/build errors

4. **Test Frontend**
   ```bash
   # Visit your Vercel deployment URL
   # Navigate to /markets page
   # Verify new category tabs appear:
   # - Deportes (sports)
   # - Mercados Financieros (financial-markets)
   # - Clima (weather)
   # - Incidentes Sociales (social-incidents)
   ```

### Step 4: Post-Deployment Verification

#### Frontend Tests

1. **Markets Page**
   - [ ] Navigate to `/markets`
   - [ ] Verify all 4 new category tabs appear
   - [ ] Click each tab and verify filtering works
   - [ ] Verify "Todos" shows all markets including new categories

2. **Market Proposal Form**
   - [ ] Navigate to `/markets/propose`
   - [ ] Verify new categories appear in dropdown
   - [ ] Try creating a proposal with each new category
   - [ ] Verify proposal submits successfully

3. **Onboarding**
   - [ ] Create a new test account
   - [ ] Verify new categories appear in onboarding
   - [ ] Select new categories and verify they save
   - [ ] Verify "Para ti" feed filters correctly

#### Backend Tests

1. **API Endpoints**
   ```bash
   # Test category filtering
   curl "https://fact-checkr-production.up.railway.app/api/markets?category=sports&limit=5"
   
   # Test category validation
   curl -X PUT "https://fact-checkr-production.up.railway.app/api/auth/me/preferences" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"preferred_categories": ["sports", "financial-markets"]}'
   ```

2. **Market Intelligence Agent**
   - Create a test market in a new category
   - Verify agent assessment runs (check Celery logs)
   - Verify assessment includes category-specific context

#### Database Verification

```sql
-- Check that new categories can be used
SELECT category, COUNT(*) 
FROM markets 
WHERE category IN ('sports', 'financial-markets', 'weather', 'social-incidents')
GROUP BY category;

-- Verify user preferences can include new categories
SELECT preferred_categories 
FROM users 
WHERE preferred_categories IS NOT NULL;
```

## 🔄 Rollback Plan

If issues occur, you can rollback:

### Frontend Rollback
1. Go to Vercel Dashboard → Deployments
2. Find previous working deployment
3. Click "..." → "Promote to Production"

### Backend Rollback
1. Go to Railway Dashboard → Backend Service
2. Go to Deployments tab
3. Find previous working deployment
4. Click "Redeploy"

### Database Rollback
- No database changes were made
- Existing markets are unaffected
- No rollback needed

## 📊 Monitoring

After deployment, monitor:

1. **Error Rates**
   - Check Railway logs for category-related errors
   - Check Vercel logs for frontend errors
   - Monitor API error rates

2. **User Adoption**
   - Track markets created in new categories
   - Monitor category filter usage
   - Check user preferences selections

3. **Performance**
   - Verify market intelligence agent performance
   - Check API response times
   - Monitor database query performance

## 🐛 Troubleshooting

### Issue: New categories don't appear in frontend
- **Check**: Vercel build completed successfully
- **Check**: Browser cache (hard refresh: Cmd+Shift+R)
- **Check**: `NEXT_PUBLIC_API_URL` is correct
- **Fix**: Clear browser cache or redeploy frontend

### Issue: Category validation fails
- **Check**: Backend deployed latest code
- **Check**: Railway logs for errors
- **Check**: Auth router has updated `valid_categories` list
- **Fix**: Redeploy backend

### Issue: Markets don't filter by new categories
- **Check**: Markets exist with new categories in database
- **Check**: API endpoint returns filtered results
- **Check**: Frontend category filter state
- **Fix**: Verify database has markets with new categories

### Issue: Market intelligence agent errors
- **Check**: Celery worker logs
- **Check**: Agent has category-specific logic
- **Check**: API keys are set correctly
- **Fix**: Review agent code, check logs

## ✅ Success Criteria

Deployment is successful when:

- [ ] All 4 new category tabs appear on `/markets` page
- [ ] Markets can be filtered by new categories
- [ ] Market proposals can use new categories
- [ ] User preferences can include new categories
- [ ] Market intelligence agent processes new categories
- [ ] No errors in Railway/Vercel logs
- [ ] API endpoints accept new categories
- [ ] Existing functionality still works

## 📝 Post-Deployment Tasks

1. **Create Seed Markets** (Optional)
   ```bash
   # Run on production database (carefully!)
   cd backend
   python ../scripts/test_new_categories.py
   ```
   This creates example markets in each new category.

2. **Update Documentation**
   - Update user-facing docs if needed
   - Document new categories in help/FAQ

3. **Announce Feature**
   - Notify users about new categories
   - Create example markets to showcase feature

## 🎯 Next Steps After Deployment

1. Monitor usage and gather feedback
2. Create example markets in each category
3. Consider adding more categories if needed
4. Optimize market intelligence agent based on real usage
5. Add category-specific analytics

