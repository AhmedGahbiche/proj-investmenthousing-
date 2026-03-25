"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

export default function TopNav({ role }: { role?: "admin" | "client" }) {
  const router = useRouter();

  async function logout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/login");
    router.refresh();
  }

  return (
    <header style={{ borderBottom: "1px solid var(--line)", background: "#fff" }}>
      <div className="shell" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "14px 0" }}>
        <Link href="/" style={{ fontWeight: 800, letterSpacing: ".03em", color: "var(--brand)" }}>
          TAQIM
        </Link>
        <nav style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <Link className="btn btn-ghost" href="/">Home</Link>
          {role === "admin" && <Link className="btn btn-ghost" href="/admin">Admin</Link>}
          {role === "client" && <Link className="btn btn-ghost" href="/client">Client</Link>}
          {role && (
            <button className="btn btn-primary" onClick={logout}>Sign out</button>
          )}
          {!role && <Link className="btn btn-primary" href="/login">Sign in</Link>}
        </nav>
      </div>
    </header>
  );
}
