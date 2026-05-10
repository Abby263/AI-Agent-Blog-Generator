import { NextRequest, NextResponse } from "next/server";

const DEFAULT_CANONICAL_URL = "https://ai-agent-blog-generator-app.vercel.app";

function canonicalUrl(): URL {
  const value = process.env.NEXT_PUBLIC_CANONICAL_URL ?? DEFAULT_CANONICAL_URL;
  return new URL(value);
}

function isLocalHost(host: string): boolean {
  return (
    host.startsWith("localhost") ||
    host.startsWith("127.0.0.1") ||
    host.startsWith("[::1]")
  );
}

export function proxy(request: NextRequest) {
  const canonical = canonicalUrl();
  const requestHost = request.headers.get("host")?.toLowerCase();
  const canonicalHost = canonical.host.toLowerCase();

  if (
    process.env.VERCEL_ENV !== "production" ||
    !requestHost ||
    requestHost === canonicalHost ||
    isLocalHost(requestHost)
  ) {
    return NextResponse.next();
  }

  const redirectUrl = new URL(
    `${request.nextUrl.pathname}${request.nextUrl.search}`,
    canonical.origin,
  );
  return NextResponse.redirect(redirectUrl, 308);
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
