import { NextRequest, NextResponse } from "next/server";
import { timingSafeEqual } from "node:crypto";
import { authCookieName, createSession } from "@/lib/auth";

function safeEqual(left: string, right: string): boolean {
  const leftBuffer = Buffer.from(left);
  const rightBuffer = Buffer.from(right);
  if (leftBuffer.length !== rightBuffer.length) {
    return false;
  }
  return timingSafeEqual(leftBuffer, rightBuffer);
}

export async function POST(req: NextRequest) {
  const adminEmail = process.env.ADMIN_EMAIL;
  const adminPassword = process.env.ADMIN_PASSWORD;
  const clientEmail = process.env.CLIENT_EMAIL;
  const clientPassword = process.env.CLIENT_PASSWORD;

  if (!adminEmail || !adminPassword || !clientEmail || !clientPassword) {
    return NextResponse.json(
      { error: "Authentication is not configured on the server" },
      { status: 500 }
    );
  }

  const body = await req.json().catch(() => null);
  if (!body?.email || !body?.password) {
    return NextResponse.json({ error: "Email and password are required" }, { status: 400 });
  }

  const email = String(body.email).toLowerCase();
  const password = String(body.password);

  let role: "admin" | "client" | null = null;
  if (safeEqual(email, adminEmail.toLowerCase()) && safeEqual(password, adminPassword)) role = "admin";
  if (safeEqual(email, clientEmail.toLowerCase()) && safeEqual(password, clientPassword)) role = "client";

  if (!role) {
    return NextResponse.json({ error: "Invalid credentials" }, { status: 401 });
  }

  const token = await createSession({
    sub: role,
    email,
    role,
  });

  const res = NextResponse.json({ role, email });
  res.cookies.set(authCookieName, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 12,
  });
  return res;
}
