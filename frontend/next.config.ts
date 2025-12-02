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

export default nextConfig;
