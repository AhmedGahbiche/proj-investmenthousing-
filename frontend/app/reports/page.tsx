"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import SharedNavbar from "@/components/SharedNavbar";
import { fetchBackendJson } from "@/lib/backendApi";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export default function ReportsPage() {
  const [documents, setDocuments] = useState<any[]>([]);

  useEffect(() => {
    fetchBackendJson<any[]>(`${BACKEND}/documents?limit=50&offset=0`)
      .then((data) => setDocuments(Array.isArray(data) ? data : []))
      .catch(() => setDocuments([]));
  }, []);

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <SharedNavbar active="my-reports" />

      <section className="md:ml-64 max-w-7xl mx-auto px-6 py-10">
        <div className="flex flex-col md:flex-row justify-between md:items-end gap-6 mb-10">
          <div>
            <h1 className="text-3xl font-black text-blue-950 tracking-tight">My Reports</h1>
            <p className="text-slate-600 mt-2">All generated and source-backed report records for your workspace.</p>
          </div>
          <Link href="/analysis" className="px-5 py-3 rounded-xl bg-blue-900 text-white text-sm font-bold">New Analysis</Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
          <article className="rounded-2xl bg-white border border-slate-200 p-6 shadow-sm">
            <p className="text-xs uppercase tracking-widest text-slate-500 font-bold">Total Entries</p>
            <p className="mt-2 text-4xl font-black text-blue-950">{documents.length}</p>
          </article>
          <article className="rounded-2xl bg-white border border-slate-200 p-6 shadow-sm">
            <p className="text-xs uppercase tracking-widest text-slate-500 font-bold">Report Source</p>
            <p className="mt-2 text-2xl font-black text-blue-950">Mock Backend</p>
          </article>
          <article className="rounded-2xl bg-white border border-slate-200 p-6 shadow-sm">
            <p className="text-xs uppercase tracking-widest text-slate-500 font-bold">Engine</p>
            <p className="mt-2 text-2xl font-black text-blue-950">OpenAI</p>
          </article>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {documents.map((doc) => (
            <article key={doc.id} className="rounded-2xl bg-white border border-slate-200 p-5 shadow-sm">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-lg font-black text-blue-950 leading-tight">{doc.filename}</h2>
                  <p className="text-xs text-slate-500 mt-1">Document #{doc.id}</p>
                </div>
                <span className="px-3 py-1 rounded-full text-[11px] font-bold bg-emerald-100 text-emerald-700 uppercase">
                  {doc.file_format}
                </span>
              </div>

              <div className="mt-4 pt-4 border-t border-slate-100 flex justify-between text-xs text-slate-500">
                <span>{new Date(doc.upload_timestamp).toLocaleString()}</span>
                <Link href="/analysis" className="font-bold text-blue-900">Analyze</Link>
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
