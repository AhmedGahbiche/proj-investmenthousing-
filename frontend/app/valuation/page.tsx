"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import SharedNavbar from "@/components/SharedNavbar";
import { fetchBackendJson } from "@/lib/backendApi";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export default function ValuationPage() {
  const [documents, setDocuments] = useState<any[]>([]);

  useEffect(() => {
    fetchBackendJson<any[]>(`${BACKEND}/documents?limit=20&offset=0`)
      .then((data) => setDocuments(Array.isArray(data) ? data : []))
      .catch(() => setDocuments([]));
  }, []);

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <SharedNavbar active="valuation" />

      <section className="md:ml-64 max-w-7xl mx-auto px-6 py-10">
        <div className="flex flex-col md:flex-row justify-between md:items-end gap-6 mb-10">
          <div>
            <h1 className="text-3xl font-black text-blue-950 tracking-tight">Valuation</h1>
            <p className="text-slate-600 mt-2">Market benchmarks, valuation indicators, and pricing context.</p>
          </div>
          <Link href="/analysis" className="px-5 py-3 rounded-xl bg-blue-900 text-white text-sm font-bold">Run New Valuation</Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-5 mb-10">
          <article className="md:col-span-2 rounded-2xl bg-white border border-slate-200 p-6 shadow-sm">
            <p className="text-xs uppercase tracking-widest text-slate-500 font-bold">Estimated Range</p>
            <p className="mt-2 text-4xl font-black text-blue-950">4.2M - 4.8M TND</p>
            <p className="mt-2 text-sm text-slate-500">Indicative synthetic benchmark for dashboard testing.</p>
          </article>
          <article className="rounded-2xl bg-white border border-slate-200 p-6 shadow-sm">
            <p className="text-xs uppercase tracking-widest text-slate-500 font-bold">Comparables</p>
            <p className="mt-2 text-4xl font-black text-blue-950">{Math.max(3, documents.length)}</p>
          </article>
          <article className="rounded-2xl bg-white border border-slate-200 p-6 shadow-sm">
            <p className="text-xs uppercase tracking-widest text-slate-500 font-bold">Yield</p>
            <p className="mt-2 text-4xl font-black text-blue-950">8.4%</p>
          </article>
        </div>

        <div className="rounded-2xl bg-white border border-slate-200 p-6 shadow-sm">
          <h2 className="text-xl font-black text-blue-950">Recent Inputs Used For Valuation</h2>
          <div className="mt-5 grid grid-cols-1 lg:grid-cols-2 gap-4">
            {documents.slice(0, 8).map((doc) => (
              <div key={doc.id} className="rounded-xl border border-slate-200 p-4">
                <p className="font-bold text-blue-950">{doc.filename}</p>
                <p className="text-xs text-slate-500 mt-1">#{doc.id} • {doc.file_format}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
