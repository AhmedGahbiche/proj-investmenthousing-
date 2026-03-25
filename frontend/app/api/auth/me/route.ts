import { NextRequest, NextResponse } from "next/server";
import { authCookieName, verifySession } from "@/lib/auth";

export async function GET(req: NextRequest) {
  const token = req.cookies.get(authCookieName)?.value;
  if (!token) return NextResponse.json({ authenticated: false }, { status: 401 });

  const session = await verifySession(token);
  if (!session) return NextResponse.json({ authenticated: false }, { status: 401 });

  return NextResponse.json({ authenticated: true, user: session });
}
