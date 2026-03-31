import { NextRequest, NextResponse } from "next/server";
import { authCookieName, verifySession } from "./lib/auth";

function needsAuth(pathname: string): boolean {
  return pathname.startsWith("/admin") || pathname.startsWith("/client");
}

export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  if (!needsAuth(pathname)) {
    return NextResponse.next();
  }

  const token = req.cookies.get(authCookieName)?.value;
  if (!token) {
    return NextResponse.redirect(new URL("/login", req.url));
  }

  const session = await verifySession(token);
  if (!session) {
    return NextResponse.redirect(new URL("/login", req.url));
  }

  if (pathname.startsWith("/admin") && session.role !== "admin") {
    return NextResponse.redirect(new URL("/client", req.url));
  }

  if (pathname.startsWith("/client") && session.role !== "client") {
    return NextResponse.redirect(new URL("/admin", req.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/admin/:path*", "/client/:path*"],
};
