import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Performance monitoring middleware
export function middleware(request: NextRequest) {
  const start = Date.now();

  // --- Auth Logic ---
  const { pathname } = request.nextUrl;
  
  // Public routes that don't require authentication
  const publicRoutes = [
    '/',
    '/signin',
    '/signup',
    '/temas',
    '/fuentes',
    '/tendencias',
    '/estadisticas',
  ];
  
  // Check if route is public
  const isPublicRoute = publicRoutes.some(route => 
    pathname === route || pathname.startsWith(`${route}/`)
  );
  
  // Check for auth token in cookies or headers
  const authToken = request.cookies.get('auth_token')?.value || 
                    request.headers.get('authorization')?.replace('Bearer ', '');
  
  // If no token and trying to access protected route, redirect to signin
  if (!isPublicRoute && !authToken) {
    const signInUrl = new URL('/signin', request.url);
    signInUrl.searchParams.set('redirect', pathname);
    return NextResponse.redirect(signInUrl);
  }
  
  // --- Security & Performance ---
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
     * - public files (public folder)
     */
    '/((?!api|_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
};
