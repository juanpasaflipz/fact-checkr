import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Performance monitoring middleware
export function middleware(request: NextRequest) {
  const start = Date.now();

  // Add custom headers for security and performance
  const response = NextResponse.next();

  // Security headers
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('X-Frame-Options', 'SAMEORIGIN');
  response.headers.set('X-XSS-Protection', '1; mode=block');

  // Performance monitoring (log slow requests in development)
  if (process.env.NODE_ENV === 'development') {
    const end = Date.now();
    const duration = end - start;

    if (duration > 1000) { // Log requests taking more than 1 second
      console.warn(`Slow request: ${request.method} ${request.url} took ${duration}ms`);
    }
  }

  return response;
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!api|_next/static|_next/image|favicon.ico|public/).*)',
  ],
};
