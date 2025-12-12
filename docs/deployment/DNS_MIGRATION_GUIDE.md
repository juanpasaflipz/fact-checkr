# 🌐 DNS & Hosting Migration Guide

This guide walks you through the manual steps required to separate your domains.

**Goal:**
- **Marketing Site**: `factcheck.mx` (Hosted on Vercel/Netlify via `perihelion` repo)
- **Web Application**: `app.factcheck.mx` (Hosted on Firebase/Vercel via `fact-checkr` repo)

---

## 📅 Step 1: Update Application Domain (fact-checkr)

Since your users are currently visiting `factcheck.mx` to see the app, we first need to move the app to its new home.

### If using Firebase Hosting:
1.  Go to the [Firebase Console](https://console.firebase.google.com/).
2.  Select your project (**fact-checkr** or similar).
3.  Navigate to **Hosting** in the left sidebar.
4.  Click **"Add custom domain"**.
5.  Enter `app.factcheck.mx`.
6.  Firebase will give you a **TXT record** to verify ownership (if needed) and **A records** or **CNAME records** for the subdomain.
7.  **Do not delete** `factcheck.mx` yet if you want to keep it live until the marketing site is ready, BUT be aware that once you change DNS in Step 3, the old connection will break.
perihelion-singularity
### If using Vercel (for frontend):
1.  Go to your Vercel Dashboard.
2.  Select the **fact-checkr** project.
3.  Go to **Settings** > **Domains**.
4.  Add `app.factcheck.mx`.
5.  (Optional) You can redirect `factcheck.mx` to `app.factcheck.mx` temporarily if you wish, or just prepare the new subdomain.

---

## 🚀 Step 2: Deploy Marketing Site (perihelion)

1.  Push your `` code to GitHub.
2.  Create a new project in **Vercel** (recommended for static sites) or Netlify.
3.  Import the `perihelion-singularity` repository.
4.  Deploy it.
5.  Go to **Settings** > **Domains** in this new project.
6.  Add `factcheck.mx` (root domain).

---

## 🔗 Step 3: Update DNS Records

**WARNING**: This step will briefly take your site offline/unstable while changes propagate (usually 15-60 mins).

Log in to your Domain Registrar (Namecheap, GoDaddy, Cloudflare, etc.) and update your records:

### 1. Point Root Domain (`@`) to Marketing Site
*   **Type**: A Record
*   **Host**: `@`
*   **Value**: `76.76.21.21` (If using Vercel) **OR** the IP addresses provided by your hosting provider for `perihelion`.
*   *(Remove any old A records pointing to the App's hosting if they conflict)*

### 2. Point Subdomain (`app`) to Web Application
*   **Type**: CNAME Record (or A Record depending on provider)
*   **Host**: `app`
*   **Value**: `hosting.firebaseapp.com` (If Firebase) **OR** `cname.vercel-dns.com` (If Vercel).
*   *Check your hosting provider's specific instructions from Step 1.*

---

## ✅ Step 4: Verification

1.  **Wait** for DNS propagation (can take up to 24h, usually faster).
2.  **Visit `factcheck.mx`**: You should see your **Landing Page**.
3.  **Visit `app.factcheck.mx`**: You should see your **Web Application**.
4.  **Test Links**: Click "Log In" or "Get Started" on the landing page -> Should take you to `app.factcheck.mx`.
