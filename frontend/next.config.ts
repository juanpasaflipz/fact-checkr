import { withSentryConfig } from "@sentry/nextjs";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Performance optimizations
  reactStrictMode: true,
  poweredByHeader: false, // Security: Remove X-Powered-By header
  
  // Image optimization
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
    formats: ['image/avif', 'image/webp'],
  },

  // Security headers
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin'
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()'
          }
        ]
      }
    ];
  },

  // Environment variables validation
  env: {
    NEXT_PUBLIC_APP_VERSION: process.env.npm_package_version || '1.0.0',
  },

  // Development Proxy to bypass CORS
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*', // Proxy to Backend
      },
      {
        source: '/claims/:path*',
        destination: 'http://localhost:8000/claims/:path*', // Proxy to Backend
      },
      {
        source: '/stats',
        destination: 'http://localhost:8000/stats', // Proxy to Backend
      },
      {
        source: '/health',
        destination: 'http://localhost:8000/health', // Proxy to Backend
      },
      {
        source: '/topics/:path*',
        destination: 'http://localhost:8000/topics/:path*', // Proxy to Backend
      },
      {
        source: '/entities',
        destination: 'http://localhost:8000/entities', // Proxy to Backend
      },
      {
        source: '/trends/:path*',
        destination: 'http://localhost:8000/trends/:path*', // Proxy to Backend
      }
    ];
  },

  // Build output configuration for various platforms
  output: 'standalone', // Optimized for Docker/containerized deployments
};

// Make sure adding Sentry options is the last code to run before exporting
// Only wrap with Sentry if DSN is configured
const sentryOrg = process.env.SENTRY_ORG;
const sentryProject = process.env.SENTRY_PROJECT;
const sentryDsn = process.env.SENTRY_DSN || process.env.NEXT_PUBLIC_SENTRY_DSN;

let finalConfig: NextConfig;

if (sentryDsn && sentryOrg && sentryProject) {
  finalConfig = withSentryConfig(nextConfig, {
    // For all available options, see:
    // https://docs.sentry.io/platforms/javascript/guides/nextjs/manual-setup/

    org: sentryOrg,
    project: sentryProject,

    // Only print logs for uploading source maps in CI
    silent: !process.env.CI,

    // For all available options, see:
    // https://docs.sentry.io/platforms/javascript/guides/nextjs/manual-setup/

    // Upload a larger set of source maps for prettier stack traces (increases build time)
    widenClientFileUpload: true,

    // Automatically annotate React components to show their full name in breadcrumbs and session replay
    reactComponentAnnotation: {
      enabled: true,
    },

    // Uncomment to route browser requests to Sentry through a Next.js rewrite to circumvent ad-blockers.
    // This can increase your server load as well as your hosting bill.
    // Note: Check that the configured route will not match with your Next.js middleware, otherwise reporting of client-
    // side errors will fail.
    // tunnelRoute: "/monitoring",

    // Hides source maps from generated client bundles
    sourcemaps: {
      disable: true,
    },

    // Automatically tree-shake Sentry logger statements to reduce bundle size
    disableLogger: true,

    // Enables automatic instrumentation of Vercel Cron Monitors. (Does not yet work with App Router route handlers.)
    // See the following for more information:
    // https://docs.sentry.io/product/cron/jobs/

    // Note: Comments in this file will be stripped. TODO comments are fine, but regular comments will be
    // removed from the source maps when uploaded to Sentry. This prevents you from seeing them when debugging.
    automaticVercelMonitors: true,
  });
} else {
  // Sentry not configured, use config without Sentry wrapper
  finalConfig = nextConfig;
}

export default finalConfig;
