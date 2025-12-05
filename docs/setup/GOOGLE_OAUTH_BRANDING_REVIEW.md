# Google OAuth Branding Setup Review

## ✅ What's Correct

1. **Authorized Domains:**
   - ✅ `backend-production-72ea.up.railway.app` - Correct (your backend domain)
   - ✅ `factcheck.mx` - Correct (your frontend domain)

2. **Developer Contact:**
   - ✅ `juan@injupe.com` - Valid email

## ⚠️ What's Missing (Required for Production)

1. **Application home page:** 
   - Currently: EMPTY
   - Should be: `https://www.factcheck.mx` or `https://factcheck.mx`
   - This is required for production apps

2. **Application privacy policy link:**
   - Currently: EMPTY
   - Should be: A public URL to your privacy policy
   - Example: `https://www.factcheck.mx/privacy` or `https://factcheck.mx/privacy-policy`
   - **Required for production apps**

3. **Application terms of service link:**
   - Currently: EMPTY
   - Should be: A public URL to your terms of service
   - Example: `https://www.factcheck.mx/terms` or `https://factcheck.mx/terms-of-service`
   - **Required for production apps**

## 📝 Action Items

### 1. Fill Required URL Fields

You need to add these URLs in the Google Cloud Console:

**Application home page:**
```
https://www.factcheck.mx
```

**Application privacy policy link:**
```
https://www.factcheck.mx/privacy
```
*(Create this page if it doesn't exist yet)*

**Application terms of service link:**
```
https://www.factcheck.mx/terms
```
*(Create this page if it doesn't exist yet)*

### 2. Verify OAuth Client Configuration

Make sure in the "Clients" section of Google Cloud Console, you have these redirect URIs:

**For Local Development:**
```
http://localhost:8000/api/auth/google/callback
```

**For Production:**
```
https://backend-production-72ea.up.railway.app/api/auth/google/callback
```

### 3. App Logo (Optional but Recommended)

- Upload a square logo (120px × 120px)
- Formats: JPG, PNG, or BMP
- Max size: 1MB

## 🔍 Verification Checklist

- [ ] Application home page filled: `https://www.factcheck.mx`
- [ ] Privacy policy link added (create page if needed)
- [ ] Terms of service link added (create page if needed)
- [ ] Production redirect URI added in OAuth client: `https://backend-production-72ea.up.railway.app/api/auth/google/callback`
- [ ] Local redirect URI added in OAuth client: `http://localhost:8000/api/auth/google/callback`
- [ ] App logo uploaded (optional)

## 📌 Important Notes

1. **Privacy Policy & Terms Pages:**
   - These pages must be publicly accessible (no login required)
   - They should be actual pages on your website, not placeholder links
   - Google will verify these URLs during app verification

2. **Authorized Domains:**
   - Your current domains are correct
   - Only the domain names are needed here (e.g., `factcheck.mx`)
   - Don't include paths or protocols

3. **Testing vs Production:**
   - If your app is in "Testing" mode, you can use test users
   - For production/public access, you'll need to complete verification
   - The required URL fields are necessary for verification

