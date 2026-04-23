"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");

    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    const data = await res.json();
    setLoading(false);

    if (!res.ok) {
      setError(data.error || "Authentication failed");
      return;
    }

    router.push("/client");
    router.refresh();
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 antialiased overflow-x-hidden">
      <nav className="fixed top-0 w-full flex justify-between items-center px-6 h-16 bg-white/80 backdrop-blur-md shadow-sm z-50">
        <div className="flex items-center gap-8">
          <span className="text-xl font-bold text-blue-950 tracking-tight">Taqim</span>
          <div className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-500">
            <Link href="/" className="hover:text-blue-800 transition-colors">Home</Link>
            <Link href="/client" className="hover:text-blue-800 transition-colors">Documents</Link>
            <Link href="/admin" className="hover:text-blue-800 transition-colors">Dashboard</Link>
          </div>
        </div>
        <Link
          href="/client"
          className="bg-gradient-to-br from-blue-950 to-blue-800 text-white px-5 py-2 rounded-lg text-sm font-semibold shadow-sm"
        >
          New Audit
        </Link>
      </nav>

      <main className="relative pt-28 pb-16 px-4 min-h-screen flex items-center justify-center">
        <div className="absolute top-0 right-0 -translate-y-1/2 translate-x-1/4 w-[700px] h-[700px] bg-blue-200/20 rounded-full blur-[110px]" />
        <div className="absolute bottom-0 left-0 translate-y-1/2 -translate-x-1/4 w-[500px] h-[500px] bg-amber-200/20 rounded-full blur-[90px]" />

        <section className="relative z-10 w-full max-w-md">
          <div className="bg-white border border-slate-200 shadow-[0px_28px_56px_rgba(15,45,94,0.12)] rounded-2xl p-8 md:p-10">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-100 border border-amber-200 mb-5">
              <span className="text-[11px] font-bold uppercase tracking-widest text-amber-900">Secure Sign-In</span>
            </div>

            <h1 className="text-3xl font-extrabold text-blue-950 tracking-tight">Platform Access</h1>
            <p className="mt-2 text-sm text-slate-600">
              Sign in to continue your due diligence workflows and reports.
            </p>

            <form onSubmit={onSubmit} className="mt-8 space-y-5">
              <label className="block">
                <span className="block mb-2 text-xs font-bold uppercase tracking-wider text-slate-600">Email</span>
                <input
                  className="w-full bg-slate-100/80 border border-slate-200 rounded-lg px-4 py-3 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-900/20"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                  placeholder="you@company.com"
                />
              </label>

              <label className="block">
                <span className="block mb-2 text-xs font-bold uppercase tracking-wider text-slate-600">Password</span>
                <input
                  type="password"
                  className="w-full bg-slate-100/80 border border-slate-200 rounded-lg px-4 py-3 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-900/20"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  placeholder="Enter your password"
                />
              </label>

              {error && <p className="text-sm font-semibold text-red-700">{error}</p>}

              <button
                disabled={loading}
                className="w-full bg-gradient-to-br from-blue-950 to-blue-700 text-white py-3.5 rounded-lg font-bold text-sm tracking-widest uppercase shadow-lg shadow-blue-900/10 disabled:opacity-50"
              >
                {loading ? "Authenticating..." : "Sign In"}
              </button>
            </form>

            <div className="mt-6 pt-5 border-t border-slate-200 text-xs text-slate-500 space-y-1.5">
              <p>Credentials are provided via secured environment variables.</p>
              <p>
                Need an account? <Link className="font-bold text-blue-900" href="/signup">Sign up</Link>
              </p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
