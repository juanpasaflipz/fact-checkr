# Figma Prompt: Stripe Checkout Screenshots

## Pre-Payment Screen: Pricing Tiers Selection

Create a Stripe checkout page showing FactCheckr MX subscription tiers with the following specifications:

### Layout
- **Header**: "Choose Your Plan" or "Upgrade to Pro"
- **Three-column pricing card layout** (Free | Pro | Team)
- **Pro tier highlighted** with "Most Popular" badge
- **Annual/Monthly toggle** at top
- **Mobile-responsive design** (show mobile version as well)

### Free Tier Card ($0/month)
**Left column, basic styling:**
- Title: "Free"
- Price: "$0" /month
- Subtitle: "Perfect for casual users"
- Features list:
  - ✅ 10 manual verifications/month
  - ✅ 100 API requests/day
  - ✅ 50 search queries/day
  - ✅ Last 7 days of data only
  - ✅ Basic analytics
  - ❌ No exports
  - ❌ No API access
  - ❌ No alerts
- Button: "Current Plan" (disabled/grayed out if user is on Free)

### Pro Tier Card ($19/month or $190/year) - HIGHLIGHTED
**Center column, prominent styling with border/glow:**
- **"Most Popular" badge** at top
- Title: "Pro"
- Price: 
  - Monthly: "$19" /month
  - Annual: "$190" /year (with "Save $38/year (17% discount)" text)
- Subtitle: "Perfect for journalists, researchers, content creators"
- Features list (everything in Free, plus):
  - ✅ **Unlimited** manual verifications
  - ✅ **10,000** API requests/day
  - ✅ **Unlimited** search queries
  - ✅ **Full historical** data access (all-time)
  - ✅ **Advanced analytics** (365 days)
  - ✅ **Unlimited exports** (CSV, JSON, Excel, PDF)
  - ✅ **Custom alerts** (5 active alerts)
  - ✅ **Priority processing** (2x faster)
  - ✅ **API access** (RESTful API)
  - ✅ **Save collections** (up to 10)
  - ✅ **Bulk verification**
  - ✅ **24-hour email support**
- Button: "Start 7-Day Free Trial" or "Subscribe to Pro" (primary CTA, blue/green)
- **Annual savings callout**: "💰 Pay $190/year instead of $228/year = Save $38/year"

### Team Tier Card ($79/month or $790/year)
**Right column:**
- Title: "Team"
- Price:
  - Monthly: "$79" /month
  - Annual: "$790" /year (with "Save $158/year (17% discount)" text)
- Subtitle: "Perfect for small newsrooms, NGOs (2-10 users)"
- Features list (everything in Pro, plus):
  - ✅ **Up to 10 team members**
  - ✅ **Shared collections** and dashboards
  - ✅ **Team activity logs**
  - ✅ **Role-based permissions**
  - ✅ **50,000 API requests/day**
  - ✅ **20 active alerts**
  - ✅ **Priority email support** (12-hour response)
  - ✅ **Custom branding options**
- Button: "Subscribe to Team" (secondary style)
- **Annual savings callout**: "💰 Pay $790/year instead of $948/year = Save $158/year"

### Design Elements
- **Color scheme**: Professional blue/green primary, clean white cards
- **Typography**: Clear hierarchy, easy-to-read feature lists
- **Icons**: Checkmarks (✅) for included features, X (❌) for excluded
- **Spacing**: Generous padding, clear separation between tiers
- **Trust indicators**: "30-day money-back guarantee" at bottom
- **Security badge**: "Secure payment powered by Stripe"

---

## Post-Payment Screen: Success/Confirmation

Create a Stripe payment success page with the following specifications:

### Layout
- **Centered card/container** on clean background
- **Success icon** (checkmark in circle, green)
- **Confirmation message**
- **Subscription details**
- **Next steps/CTA buttons**

### Header Section
- **Large green checkmark icon** (✓ in circle)
- **Title**: "Payment Successful!" or "Welcome to Pro!"
- **Subtitle**: "Your subscription is now active"

### Subscription Details Card
**White card with border/shadow containing:**
- **Plan**: "Pro Plan" or "Team Plan"
- **Billing**: "Monthly" or "Annual"
- **Amount**: "$19.00/month" or "$190.00/year"
- **Next billing date**: "Next charge: [Date]"
- **Payment method**: "Card ending in •••• 4242" with card icon
- **Invoice**: Link to "Download receipt"

### What's Next Section
**Bulleted list or cards showing:**
- ✅ "Unlimited verifications are now active"
- ✅ "Full historical data access enabled"
- ✅ "Export functionality unlocked"
- ✅ "API access credentials sent to your email"
- ✅ "Check your inbox for welcome email"

### Action Buttons
- **Primary CTA**: "Go to Dashboard" or "Start Verifying" (large, prominent)
- **Secondary**: "View Subscription Settings" (outlined button)
- **Tertiary**: "Download Invoice" (text link)

### Additional Elements
- **Support contact**: "Questions? Contact support@factcheckr.mx"
- **Trust message**: "Your subscription is managed securely by Stripe"
- **Cancel anytime**: "You can cancel anytime from your account settings"

### Design Elements
- **Color scheme**: Success green (#10B981 or similar), clean white
- **Typography**: Clear, celebratory but professional
- **Spacing**: Generous whitespace, clear hierarchy
- **Icons**: Success checkmark, subscription details icons
- **Visual**: Subtle celebration (confetti optional, keep professional)

---

## Mobile Versions

Create mobile-optimized versions of both screens:
- **Stacked cards** instead of side-by-side
- **Full-width buttons**
- **Simplified feature lists** (can use accordions)
- **Touch-friendly** sizing (44px minimum for buttons)
- **Swipeable** pricing cards (optional)

---

## Technical Specifications

### Dimensions
- **Desktop**: 1920x1080 or 1440x900
- **Mobile**: 375x812 (iPhone) or 390x844
- **Tablet**: 768x1024

### Colors (Suggested)
- **Primary**: #2563EB (blue) or #059669 (green)
- **Success**: #10B981 (green)
- **Text**: #1F2937 (dark gray)
- **Background**: #F9FAFB (light gray) or white
- **Card background**: White (#FFFFFF)
- **Border**: #E5E7EB (light gray)

### Typography
- **Headings**: Bold, 24-32px
- **Body**: Regular, 16px
- **Features**: Regular, 14-16px
- **Prices**: Bold, 36-48px

---

## Usage Instructions for Figma

1. **Create two separate frames**: "Pre-Payment" and "Post-Payment"
2. **Use auto-layout** for responsive cards
3. **Create component variants** for monthly/annual toggle
4. **Add hover states** for interactive elements
5. **Include dark mode variant** (optional)
6. **Export as PNG/JPG** at 2x resolution for screenshots
7. **Include both English and Spanish versions** if needed

---

## Key Messaging

### Pre-Payment
- Focus on **value** ("Unlimited verifications", "Full history")
- Highlight **savings** (annual discount prominently displayed)
- Show **clear differentiation** between tiers
- Make **Pro tier** the obvious choice (most popular badge)

### Post-Payment
- **Celebrate** the upgrade (success messaging)
- **Reassure** (payment confirmed, subscription active)
- **Guide** next steps (what they can do now)
- **Build confidence** (easy cancellation, secure payment)

---

## Additional Screenshots to Consider

1. **Payment Form** (Stripe Elements): Card input, billing details
2. **Processing State**: Loading spinner during payment
3. **Error State**: Payment failed, retry option
4. **Upgrade Flow**: From Free to Pro (showing current usage)
5. **Billing Management**: Subscription settings page

