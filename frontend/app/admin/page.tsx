"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import SharedNavbar from "@/components/SharedNavbar";
import { fetchBackendJson } from "@/lib/backendApi";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export default function AdminDashboard() {
  const [system, setSystem] = useState<any>(null);
  const [documents, setDocuments] = useState<any[]>([]);

  useEffect(() => {
    fetchBackendJson<any>(`${BACKEND}/system/status`).then(setSystem).catch(() => setSystem({ status: "unreachable" }));
    fetchBackendJson<any[]>(`${BACKEND}/documents?limit=20&offset=0`).then(setDocuments).catch(() => setDocuments([]));
  }, []);

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <SharedNavbar active="valuation" />

      <header className="md:ml-64 sticky top-0 z-30 h-16 px-6 border-b border-slate-200 bg-white/80 backdrop-blur flex items-center justify-between">
        <h1 className="text-xl font-black text-blue-950">Valuation Workspace</h1>
        <div className="flex items-center gap-3">
          <Link href="/analysis" className="px-4 py-2 rounded-lg bg-blue-900 text-white text-sm font-bold">New Analysis</Link>
          <Link href="/client" className="text-sm font-semibold text-slate-600">Dashboard</Link>
        </div>
      </header>

      <section className="md:ml-64 max-w-7xl mx-auto px-6 py-10">
        <div className="flex flex-col md:flex-row justify-between md:items-end gap-6 mb-10">
          <div>
            <h2 className="text-3xl font-black text-blue-950 tracking-tight">Operations Dashboard</h2>
            <p className="text-slate-600 mt-2">Monitor ingestion pipeline and recent reports.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-5 mb-10">
          <article className="md:col-span-2 rounded-2xl bg-white border border-slate-200 p-6 shadow-sm">
            <p className="text-xs uppercase tracking-widest text-slate-500 font-bold">System Status</p>
            <p className="mt-2 text-4xl font-black text-blue-950">{system?.status || "loading"}</p>
            <p className="mt-2 text-sm text-slate-500">DB: {system?.database || "-"} • Cache: {system?.cache || "-"}</p>
          </article>
          <article className="rounded-2xl bg-white border border-slate-200 p-6 shadow-sm">
            <p className="text-xs uppercase tracking-widest text-slate-500 font-bold">Documents</p>
            <p className="mt-2 text-4xl font-black text-blue-950">{documents.length}</p>
          </article>
          <article className="rounded-2xl bg-white border border-slate-200 p-6 shadow-sm">
            <p className="text-xs uppercase tracking-widest text-slate-500 font-bold">Mode</p>
            <p className="mt-2 text-4xl font-black text-blue-950">OpenAI</p>
          </article>
        </div>

        <div className="mb-6 flex items-center justify-between">
          <h3 className="text-xl font-black text-blue-950">Recent Uploaded Documents</h3>
          <Link href="/client" className="text-sm font-bold text-blue-900">Go To Upload</Link>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {documents.slice(0, 8).map((doc) => (
            <article key={doc.id} className="rounded-2xl bg-white border border-slate-200 p-5 shadow-sm">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h4 className="text-lg font-black text-blue-950 leading-tight">{doc.filename}</h4>
                  <p className="text-xs text-slate-500 mt-1">Document #{doc.id}</p>
                </div>
                <span className="px-3 py-1 rounded-full text-[11px] font-bold bg-emerald-100 text-emerald-700 uppercase">
                  {doc.file_format}
                </span>
              </div>
              <div className="mt-4 pt-4 border-t border-slate-100 flex justify-between text-xs text-slate-500">
                <span>Size: {doc.file_size} bytes</span>
                <span>{new Date(doc.upload_timestamp).toLocaleString()}</span>
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
