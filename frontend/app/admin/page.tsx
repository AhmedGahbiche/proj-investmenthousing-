"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import SharedNavbar from "@/components/SharedNavbar";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export default function AdminDashboard() {
  const [system, setSystem] = useState<any>(null);
  const [documents, setDocuments] = useState<any[]>([]);

  useEffect(() => {
    fetch(`${BACKEND}/system/status`).then((r) => r.json()).then(setSystem).catch(() => setSystem({ status: "unreachable" }));
    fetch(`${BACKEND}/documents?limit=20&offset=0`).then((r) => r.json()).then(setDocuments).catch(() => setDocuments([]));
  }, []);

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <SharedNavbar active="valuation" />

      <header className="md:ml-64 sticky top-0 z-30 h-16 px-6 border-b border-slate-200 bg-white/80 backdrop-blur flex items-center justify-between">
        <h1 className="text-xl font-black text-blue-950">Valuation Workspace</h1>
        <div className="flex items-center gap-3">
          <Button asLink href="/analysis">New Analysis</Button>
          <Button asLink href="/client" variant="outline">Dashboard</Button>
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
          <Card className="md:col-span-2">
            <CardContent className="p-6">
              <p className="text-xs uppercase tracking-widest text-slate-500 font-bold">System Status</p>
              <p className="mt-2 text-4xl font-black text-blue-950">{system?.status || "loading"}</p>
              <p className="mt-2 text-sm text-slate-500">DB: {system?.database || "-"} • Cache: {system?.cache || "-"}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <p className="text-xs uppercase tracking-widest text-slate-500 font-bold">Documents</p>
              <p className="mt-2 text-4xl font-black text-blue-950">{documents.length}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <p className="text-xs uppercase tracking-widest text-slate-500 font-bold">Mode</p>
              <p className="mt-2 text-4xl font-black text-blue-950">OpenAI</p>
            </CardContent>
          </Card>
        </div>

        <div className="mb-6 flex items-center justify-between">
          <h3 className="text-xl font-black text-blue-950">Recent Uploaded Documents</h3>
          <Button asLink variant="outline" href="/client">Go To Upload</Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {documents.slice(0, 8).map((doc) => (
            <Card key={doc.id}>
              <CardContent className="p-5">
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
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}
