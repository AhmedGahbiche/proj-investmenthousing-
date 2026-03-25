"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function SignupPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 300));
    setLoading(false);
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
            <Link href="/login" className="hover:text-blue-800 transition-colors">Sign In</Link>
          </div>
        </div>
      </nav>

      <main className="relative pt-28 pb-16 px-4 min-h-screen flex items-center justify-center">
        <section className="relative z-10 w-full max-w-md">
          <div className="bg-white border border-slate-200 shadow-[0px_28px_56px_rgba(15,45,94,0.12)] rounded-2xl p-8 md:p-10">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-100 border border-blue-200 mb-5">
              <span className="text-[11px] font-bold uppercase tracking-widest text-blue-900">Create Account</span>
            </div>

            <h1 className="text-3xl font-extrabold text-blue-950 tracking-tight">Sign Up</h1>
            <p className="mt-2 text-sm text-slate-600">Create your account to access the client dashboard.</p>

            <form onSubmit={onSubmit} className="mt-8 space-y-5">
              <label className="block">
                <span className="block mb-2 text-xs font-bold uppercase tracking-wider text-slate-600">Full Name</span>
                <input
                  className="w-full bg-slate-100/80 border border-slate-200 rounded-lg px-4 py-3 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-900/20"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  autoComplete="name"
                  required
                />
              </label>

              <label className="block">
                <span className="block mb-2 text-xs font-bold uppercase tracking-wider text-slate-600">Email</span>
                <input
                  type="email"
                  className="w-full bg-slate-100/80 border border-slate-200 rounded-lg px-4 py-3 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-900/20"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                  required
                />
              </label>

              <label className="block">
                <span className="block mb-2 text-xs font-bold uppercase tracking-wider text-slate-600">Password</span>
                <input
                  type="password"
                  className="w-full bg-slate-100/80 border border-slate-200 rounded-lg px-4 py-3 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-900/20"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="new-password"
                  required
                />
              </label>

              <button
                disabled={loading}
                className="w-full bg-gradient-to-br from-blue-950 to-blue-700 text-white py-3.5 rounded-lg font-bold text-sm tracking-widest uppercase shadow-lg shadow-blue-900/10 disabled:opacity-50"
              >
                {loading ? "Creating Account..." : "Sign Up"}
              </button>
            </form>

            <p className="mt-6 text-xs text-slate-500">
              Already have an account? <Link href="/login" className="font-bold text-blue-900">Sign in</Link>
            </p>
          </div>
        </section>
      </main>
    </div>
  );
}
