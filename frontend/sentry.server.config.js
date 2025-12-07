import * as Sentry from "@sentry/nextjs";

const dsn = process.env.SENTRY_DSN;

// Only initialize Sentry if DSN is configured
if (dsn) {
  Sentry.init({
    dsn: dsn,

  // Adjust this value in production, or use tracesSampler for greater control
  tracesSampleRate: 0.1,

    // Setting this option to true will print useful information to the console while you're setting up Sentry.
    debug: process.env.NODE_ENV === 'development',

    // Uncomment the line below to enable Spotlight (https://spotlightjs.com)
    // spotlight: process.env.NODE_ENV === 'development',
  });
}
