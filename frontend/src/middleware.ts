import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { SESSION_COOKIE_NAME, normalizeSessionToken } from '@/lib/session-cookie';

export function middleware(request: NextRequest) {
  // Allow public access to auth routes and API routes
  if (
    request.nextUrl.pathname.startsWith('/auth') ||
    request.nextUrl.pathname.startsWith('/api') ||
    request.nextUrl.pathname.startsWith('/_next') ||
    request.nextUrl.pathname === '/favicon.ico'
  ) {
    return NextResponse.next();
  }

  const token = normalizeSessionToken(request.cookies.get(SESSION_COOKIE_NAME)?.value);
  if (!token) {
    // Redirect to login if not authenticated
    return NextResponse.redirect(new URL('/auth/oidc/login', request.url));
    // NOTE: /auth/oidc/login might be a POST route, but we can't do much from middleware.
    // If it's a POST route, maybe we can redirect to a public splash page?
    // Let's redirect to /auth/callback? No.
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico, sitemap.xml, robots.txt (metadata files)
     */
    '/((?!api|_next/static|_next/image|favicon.ico|sitemap.xml|robots.txt).*)',
  ],
};
