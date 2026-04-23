"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import SharedNavbar from "@/components/SharedNavbar";
import {
  startPropertyAnalysisRequest,
  uploadDocuments,
  type UploadedDocument,
} from "@/lib/analysisApi";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export default function NewAnalysisPage() {
  const router = useRouter();
  const [files, setFiles] = useState<File[]>([]);
  const [uploadedDocuments, setUploadedDocuments] = useState<UploadedDocument[]>([]);
  const [propertyAddress, setPropertyAddress] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function uploadDocument(e: FormEvent) {
    e.preventDefault();
    if (files.length === 0) return;

    setBusy(true);
    setError("");
    setSuccess("");

    try {
      const { successes, failures } = await uploadDocuments(BACKEND, files);

      if (successes.length > 0) {
        setUploadedDocuments((prev) => [...prev, ...successes]);
        setSuccess(`${successes.length} file(s) uploaded successfully.`);
      }

      if (failures.length > 0) {
        setError(failures.join(" | "));
      }
    } finally {
      setBusy(false);
    }
  }

  async function startPropertyAnalysis(e: FormEvent) {
    e.preventDefault();
    if (uploadedDocuments.length === 0) return;

    setBusy(true);
    setError("");
    setSuccess("");

    try {
      const result = await startPropertyAnalysisRequest(BACKEND, {
        document_ids: uploadedDocuments.map((d) => d.document_id),
        property_name: propertyAddress || "Property Portfolio",
      });

      if (!result.ok) {
        setError(result.error);
        return;
      }

      router.push(`/report/${result.data.analysis_id}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="bg-slate-50 text-slate-900 antialiased">
      <SharedNavbar active="new-analysis" />

      <main className="md:ml-64 pt-10 pb-20 flex justify-center px-4">
        <div className="max-w-3xl w-full flex flex-col gap-8">
          <div className="flex items-center justify-between px-12 relative">
            <div className="absolute top-5 left-[15%] right-[15%] h-0.5 bg-slate-200 z-0"></div>
            <div className="flex flex-col items-center gap-2 z-10">
              <div className="w-10 h-10 rounded-full bg-blue-900 flex items-center justify-center shadow-sm text-white">
                <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>upload_file</span>
              </div>
              <span className="text-xs font-semibold uppercase tracking-wider text-blue-900">Upload</span>
            </div>
            <div className="flex flex-col items-center gap-2 z-10">
              <div className="w-10 h-10 rounded-full bg-white border-2 border-slate-200 flex items-center justify-center text-slate-500">
                <span className="material-symbols-outlined">analytics</span>
              </div>
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Analysis</span>
            </div>
            <div className="flex flex-col items-center gap-2 z-10">
              <div className="w-10 h-10 rounded-full bg-white border-2 border-slate-200 flex items-center justify-center text-slate-500">
                <span className="material-symbols-outlined">description</span>
              </div>
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Report</span>
            </div>
          </div>

          <div className="bg-white rounded-xl p-8 md:p-12 shadow-sm border-0">
            <div className="flex flex-col gap-10">
              <div className="text-center">
                <h1 className="text-2xl font-bold text-slate-900 tracking-tight mb-2">Initiate Property Audit</h1>
                <p className="text-slate-500 text-sm max-w-md mx-auto">Upload your title deed, permits, or property documents (PDF) to begin the premium due diligence process.</p>
              </div>

              <div className="relative group cursor-pointer">
                <div className="border-2 border-dashed border-slate-300 rounded-xl bg-slate-100/30 p-12 flex flex-col items-center gap-4 transition-all hover:border-blue-900/40 hover:bg-slate-100/60">
                  <div className="w-16 h-16 rounded-full bg-blue-900/10 flex items-center justify-center text-blue-900">
                    <span className="material-symbols-outlined text-4xl">cloud_upload</span>
                  </div>
                  <div className="text-center w-full">
                    <span className="block font-semibold text-blue-900">Click to upload or drag and drop</span>
                    <span className="block text-xs text-slate-500 mt-1">Maximum file size 25MB</span>
                    <input
                      type="file"
                      multiple
                      className="mt-4 block w-full rounded-lg border border-slate-200 bg-white p-3 text-sm"
                      onChange={(e) => setFiles(Array.from(e.target.files || []))}
                    />
                    <button
                      type="button"
                      disabled={busy || files.length === 0}
                      onClick={uploadDocument}
                      className="mt-3 px-4 py-2 rounded-lg bg-slate-900 text-white text-sm font-bold disabled:opacity-50"
                    >
                      {busy ? "Uploading..." : `Upload ${files.length || ""} file${files.length === 1 ? "" : "s"}`.trim()}
                    </button>
                  </div>
                </div>
              </div>

              {uploadedDocuments.length > 0 && (
                <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4">
                  <p className="text-sm font-semibold text-emerald-700">Uploaded documents ({uploadedDocuments.length})</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {uploadedDocuments.map((doc) => (
                      <span key={`${doc.document_id}-${doc.filename}`} className="text-xs px-2 py-1 rounded-full bg-white border border-emerald-200 text-emerald-800">
                        #{doc.document_id} {doc.filename}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <form className="flex flex-col gap-4" onSubmit={startPropertyAnalysis}>
                <label className="text-sm font-semibold text-slate-600 tracking-wide flex items-center gap-2" htmlFor="property-address">
                  <span className="material-symbols-outlined text-lg">location_on</span>
                  PROPERTY ADDRESS
                </label>
                <div className="relative">
                  <input
                    id="property-address"
                    value={propertyAddress}
                    onChange={(e) => setPropertyAddress(e.target.value)}
                    className="w-full bg-slate-200/50 border border-slate-200 rounded-lg px-4 py-4 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-900/20 focus:border-blue-900 focus:bg-white transition-all"
                    placeholder="Enter full property address for geographic analysis"
                    type="text"
                  />
                </div>

                <div className="pt-4">
                  <button
                    disabled={busy || uploadedDocuments.length === 0}
                    className="w-full bg-gradient-to-br from-blue-950 to-blue-800 text-white py-4 rounded-lg font-bold text-sm tracking-widest uppercase shadow-lg shadow-blue-900/10 hover:opacity-95 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
                  >
                    Start Analysis
                    <span className="material-symbols-outlined text-lg">arrow_forward</span>
                  </button>
                </div>
              </form>

              {success && <p className="text-sm font-semibold text-emerald-700">{success}</p>}
              {error && <p className="text-sm font-semibold text-red-700">{error}</p>}
            </div>
          </div>

          <div className="flex items-center justify-center gap-3 text-slate-500/70 text-xs px-8">
            <span className="material-symbols-outlined text-sm">security</span>
            <span>All documents are encrypted and handled with legal confidentiality standards.</span>
          </div>
        </div>
      </main>

      <footer className="w-full flex flex-col md:flex-row justify-between items-center px-12 py-12 gap-6 bg-slate-100 text-xs tracking-wider uppercase">
        <div className="font-bold text-blue-900">Taqim</div>
        <div className="text-slate-400 text-center md:text-left">© 2024 Taqim Real Estate Solutions. All rights reserved.</div>
        <div className="flex gap-6">
          <a className="text-slate-400 hover:text-blue-700 transition-opacity" href="#">Privacy Policy</a>
          <a className="text-slate-400 hover:text-blue-700 transition-opacity" href="#">Terms of Service</a>
          <a className="text-slate-400 hover:text-blue-700 transition-opacity" href="#">Legal Notice</a>
          <a className="text-slate-400 hover:text-blue-700 transition-opacity" href="#">Contact</a>
        </div>
      </footer>
    </div>
  );
}
