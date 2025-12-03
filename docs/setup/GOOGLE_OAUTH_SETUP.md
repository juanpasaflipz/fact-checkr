# Google OAuth Setup Guide

This guide explains how to set up Google OAuth authentication for FactCheckr MX.

## What is a Redirect URI?

The **redirect URI** is the URL that Google will redirect users to after they complete authentication. It must:
1. Be registered in Google Cloud Console as an authorized redirect URI
2. Match exactly what you configure in your backend environment variable
3. Point to your backend's OAuth callback endpoint

## Step-by-Step Setup

### Step 1: Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select or create a project
3. Navigate to **APIs & Services > Credentials**
4. Click **Create Credentials > OAuth client ID**
5. If prompted, configure the OAuth consent screen first:
   - Choose **External** (unless you have a Google Workspace)
   - Fill in app name: "FactCheckr MX"
   - Add your email as support contact
   - Add your email as developer contact
   - Save and continue through the scopes (you can skip)
   - Add test users if in testing mode
6. Back to creating OAuth client ID:
   - **Application type**: Web application
   - **Name**: FactCheckr MX (or any name)
   - **Authorized redirect URIs**: Add the redirect URI (see below)

### Step 2: Determine Your Redirect URI

The redirect URI format is:
```
{your-backend-url}/api/auth/google/callback
```

#### For Local Development:
```
http://localhost:8000/api/auth/google/callback
```

#### For Production (Railway/other hosting):
```
https://your-backend-domain.com/api/auth/google/callback
```

**Example:** If your backend is at `https://backend-production-72ea.up.railway.app`, then:
```
https://backend-production-72ea.up.railway.app/api/auth/google/callback
```

### Step 3: Add Redirect URI in Google Cloud Console

In the OAuth client creation form, add your redirect URI(s):

**For Development:**
```
http://localhost:8000/api/auth/google/callback
```

**For Production:**
```
https://your-backend-domain.com/api/auth/google/callback
```

**Important:** You can add multiple redirect URIs (one for dev, one for production). Just click "Add URI" for each.

### Step 4: Get Your Credentials

After creating the OAuth client:

1. **Client ID**: Copy this (looks like: `123456789-abc123def456.apps.googleusercontent.com`)
2. **Client Secret**: Copy this (looks like: `GOCSPX-abc123def456xyz789`)

### Step 5: Configure Backend Environment

Add these to your `backend/.env` file:

#### For Local Development:
```bash
GOOGLE_CLIENT_ID=123456789-abc123def456.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abc123def456xyz789
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
```

#### For Production:
```bash
GOOGLE_CLIENT_ID=123456789-abc123def456.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abc123def456xyz789
GOOGLE_REDIRECT_URI=https://your-backend-domain.com/api/auth/google/callback
```

**Important Notes:**
- The redirect URI must match **exactly** what you entered in Google Cloud Console
- No trailing slashes
- Use `http://` for localhost, `https://` for production
- The path `/api/auth/google/callback` is fixed (don't change it)

### Step 6: Restart Backend

After adding the environment variables:

```bash
cd backend
# Stop the server (Ctrl+C if running)
# Then restart
uvicorn main:app --reload
# Or use your startup script
```

## Testing

### Test the OAuth Flow

1. Start your backend: `cd backend && uvicorn main:app --reload`
2. Start your frontend: `cd frontend && npm run dev`
3. Navigate to `http://localhost:3000/signin`
4. Click "Continuar con Google"
5. You should be redirected to Google's login page
6. After logging in, you should be redirected back to your app

### Common Issues

#### Error: "redirect_uri_mismatch"

**Problem:** The redirect URI in your `.env` doesn't match what's in Google Cloud Console.

**Solution:**
1. Check `GOOGLE_REDIRECT_URI` in `backend/.env`
2. Verify it matches exactly in Google Cloud Console (APIs & Services > Credentials > Your OAuth Client)
3. Make sure there are no trailing slashes or extra spaces
4. Restart your backend after making changes

#### Error: "invalid_client"

**Problem:** Client ID or Client Secret is incorrect.

**Solution:**
1. Double-check `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `backend/.env`
2. Make sure you copied the full values (no truncation)
3. Verify they're from the correct OAuth client in Google Cloud Console

#### Error: "access_denied"

**Problem:** User cancelled the OAuth flow or app is in testing mode without test users.

**Solution:**
1. If in testing mode, add your email as a test user in OAuth consent screen
2. Or publish your app (for production use)

## Production Deployment

### Railway/Cloud Hosting

1. **Add environment variables** in your hosting platform:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `GOOGLE_REDIRECT_URI` (use your production backend URL)

2. **Update Google Cloud Console**:
   - Add your production redirect URI to the OAuth client
   - Example: `https://backend-production-72ea.up.railway.app/api/auth/google/callback`

3. **Verify the redirect URI matches exactly** between:
   - Google Cloud Console
   - Your backend environment variable

### Multiple Environments

You can use the same OAuth client for both development and production by adding multiple redirect URIs in Google Cloud Console:

1. Development: `http://localhost:8000/api/auth/google/callback`
2. Production: `https://your-backend-domain.com/api/auth/google/callback`

Just make sure your backend `.env` uses the correct one for each environment.

## Security Notes

- **Never commit** your `.env` file with real credentials
- Use different OAuth clients for development and production if possible
- Keep your Client Secret secure
- Regularly rotate credentials if compromised

## Quick Reference

**Redirect URI Format:**
```
{backend-url}/api/auth/google/callback
```

**Local Development:**
```
http://localhost:8000/api/auth/google/callback
```

**Production:**
```
https://your-backend-domain.com/api/auth/google/callback
```

**Backend Environment Variables:**
```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
```

