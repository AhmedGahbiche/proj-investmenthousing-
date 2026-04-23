import { SignJWT, jwtVerify, type JWTPayload } from "jose";

export type UserRole = "admin" | "client";

export interface SessionPayload extends JWTPayload {
  sub: string;
  email: string;
  role: UserRole;
}

const COOKIE_NAME = "taqim_session";

function getAuthSecret(): Uint8Array {
  const rawSecret = process.env.AUTH_SECRET;
  if (!rawSecret || rawSecret.trim().length < 16) {
    throw new Error("AUTH_SECRET must be set and at least 16 characters long");
  }
  return new TextEncoder().encode(rawSecret);
}

export const authCookieName = COOKIE_NAME;

export async function createSession(payload: SessionPayload): Promise<string> {
  const secret = getAuthSecret();
  return new SignJWT(payload)
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime("12h")
    .sign(secret);
}

export async function verifySession(token: string): Promise<SessionPayload | null> {
  try {
    const secret = getAuthSecret();
    const { payload } = await jwtVerify(token, secret);
    return {
      sub: String(payload.sub || ""),
      email: String(payload.email || ""),
      role: payload.role as UserRole,
    };
  } catch {
    return null;
  }
}
