import { NextRequest, NextResponse } from "next/server";
import { authCookieName, createSession } from "@/lib/auth";

const users = {
  admin: {
    email: process.env.ADMIN_EMAIL || "admin@taqim.tn",
    password: process.env.ADMIN_PASSWORD || "Admin#2026",
  },
  client: {
    email: process.env.CLIENT_EMAIL || "client@taqim.tn",
    password: process.env.CLIENT_PASSWORD || "Client#2026",
  },
};

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => null);
  if (!body?.email || !body?.password) {
    return NextResponse.json({ error: "Email and password are required" }, { status: 400 });
  }

  const email = String(body.email).toLowerCase();
  const password = String(body.password);

  let role: "admin" | "client" | null = null;
  if (email === users.admin.email.toLowerCase() && password === users.admin.password) role = "admin";
  if (email === users.client.email.toLowerCase() && password === users.client.password) role = "client";

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
