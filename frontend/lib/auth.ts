import { SignJWT, jwtVerify, type JWTPayload } from "jose";

export type UserRole = "admin" | "client";

export interface SessionPayload extends JWTPayload {
  sub: string;
  email: string;
  role: UserRole;
}

const COOKIE_NAME = "taqim_session";
const secret = new TextEncoder().encode(process.env.AUTH_SECRET || "dev-secret-change-me");

export const authCookieName = COOKIE_NAME;

export async function createSession(payload: SessionPayload): Promise<string> {
  return new SignJWT(payload)
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime("12h")
    .sign(secret);
}

export async function verifySession(token: string): Promise<SessionPayload | null> {
  try {
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
