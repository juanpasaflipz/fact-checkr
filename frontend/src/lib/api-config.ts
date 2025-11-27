/**
 * API Configuration Utility
 * Centralized configuration for backend API URLs
 */

/**
 * Get the base API URL
 * Priority:
 * 1. NEXT_PUBLIC_API_URL environment variable
 * 2. Automatic detection for Railway/Vercel deployments
 * 3. Default to localhost for local development
 */
export function getApiBaseUrl(): string {
  // Check for explicit environment variable (highest priority)
  if (typeof window !== 'undefined' && (window as any).__NEXT_DATA__?.env?.NEXT_PUBLIC_API_URL) {
    return (window as any).__NEXT_DATA__.env.NEXT_PUBLIC_API_URL;
  }
  
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }

  // For production deployments, try to detect Railway backend
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    
    // If we're on Railway/Vercel (not localhost), try to construct API URL
    if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
      // Check if there's a Railway backend URL in session storage (set by deployment)
      const savedApiUrl = sessionStorage.getItem('API_URL');
      if (savedApiUrl) {
        return savedApiUrl;
      }
    }
  }

  // Default to localhost for local development
  return 'http://localhost:8000';
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
      `1. Verify Railway backend is deployed and running`,
      `2. Check NEXT_PUBLIC_API_URL in Vercel/Railway environment variables`,
      `3. Test backend health: curl ${baseUrl}/health`,
      `4. Ensure CORS is configured in backend to allow requests from ${typeof window !== 'undefined' ? window.location.origin : 'your domain'}`,
      `5. Check Railway backend logs for startup errors`
    ];
  }
}

