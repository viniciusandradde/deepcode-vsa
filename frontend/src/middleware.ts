import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
    const path = request.nextUrl.pathname;

    // Define paths that are public (no auth required)
    const isPublicPath = path === '/login' || path === '/register' || path.startsWith('/api/') || path.startsWith('/_next/') || path.includes('favicon.ico');

    const isAuthenticated = request.cookies.has('vsa_auth');

    // Redirect to login if accessing a protected route without auth cookie
    // Note: We don't protect API routes here to allow the frontend to handle 401s gracefully
    if (!isPublicPath && !isAuthenticated) {
        return NextResponse.redirect(new URL('/login', request.url));
    }

    // Redirect to home if accessing login/register while authenticated
    if ((path === '/login' || path === '/register') && isAuthenticated) {
        return NextResponse.redirect(new URL('/', request.url));
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
         * - favicon.ico (favicon file)
         */
        '/((?!api|_next/static|_next/image|favicon.ico).*)',
    ],
};
