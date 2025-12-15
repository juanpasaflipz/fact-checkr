/**
 * API Configuration Utility
 * Centralized configuration for backend API URLs
 * 
 * Backend URL: https://factcheckr-backend-rdgcp6i5ta-uc.a.run.app
 */

/**
 * Get the base API URL
 * Priority:
 * 1. NEXT_PUBLIC_API_URL environment variable
 * 2. Automatic detection for Railway/Vercel deployments
 * 3. Default to localhost for local development
 */
export function getApiBaseUrl(): string {
  // Server/SSR: require an absolute URL
  if (typeof window === 'undefined') {
    return (
      process.env.NEXT_PUBLIC_API_URL ||
      process.env.API_URL ||
      'http://localhost:8000'
    );
  }

  // Check for explicit environment variable (highest priority)
  if (typeof window !== 'undefined' && (window as any).__NEXT_DATA__?.env?.NEXT_PUBLIC_API_URL) {
    return (window as any).__NEXT_DATA__.env.NEXT_PUBLIC_API_URL;
  }

  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }

  // For production deployments, use Railway backend URL
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;

    const isLocal = hostname === 'localhost' ||
      hostname === '127.0.0.1' ||
      hostname.startsWith('192.168.') ||
      hostname.startsWith('10.') ||
      hostname.endsWith('.local');

    if (!isLocal) {
      // Default production backend (override via NEXT_PUBLIC_API_URL when set)
      // Switched to Cloud Run (2025-12-15)
      return 'https://factcheckr-backend-rdgcp6i5ta-uc.a.run.app';
    }
  }

  // Default to relative path for local development to use Next.js proxy (avoids CORS)
  return '';
}

/**
 * Get full API URL for a given endpoint
 * @param endpoint - API endpoint (e.g., '/health', '/claims')
 * @returns Full URL string
 */
export function getApiUrl(endpoint: string): string {
  const baseUrl = getApiBaseUrl();
  // Remove leading slash from endpoint if present to avoid double slashes
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
  return `${baseUrl}/${cleanEndpoint}`;
}

/**
 * Check if we're in development mode
 */
export function isDevelopment(): boolean {
  if (typeof window !== 'undefined') {
    return window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  }
  return process.env.NODE_ENV === 'development';
}

/**
 * Get helpful error message for API connection issues
 */
export function getConnectionErrorHelp(): string[] {
  const baseUrl = getApiBaseUrl();
  const isLocal = baseUrl.includes('localhost') || baseUrl.includes('127.0.0.1');

  if (isLocal) {
    return [
      '1. Make sure backend is running locally: cd backend && python -m uvicorn main:app --reload',
      '2. Verify API URL in frontend/.env.local: NEXT_PUBLIC_API_URL=http://localhost:8000',
      '3. Test backend health: curl http://localhost:8000/health',
      '4. Check backend logs for errors'
    ];
  } else {
    return [
      `1. Verify Backend is deployed and running (Cloud Run)`,
      `2. Check NEXT_PUBLIC_API_URL in environment variables (should be https://factcheckr-backend-rdgcp6i5ta-uc.a.run.app)`,
      `3. Test backend health: curl ${baseUrl}/health`,
      `4. Ensure CORS is configured in backend to allow requests from ${typeof window !== 'undefined' ? window.location.origin : 'your domain'}`,
      `5. Check Cloud Run logs for startup errors`
    ];
  }

}

