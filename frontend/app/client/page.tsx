"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import TopNav from "@/components/TopNav";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

type AnalysisData = {
  analysis_id: string;
  status: string;
  created_at: string;
  updated_at: string;
  outputs:
    | Array<{
        module_name: string;
        result_json: Record<string, any>;
        confidence?: number;
      }>
    | Record<string, Record<string, any>>
    | null;
};

type NormalizedOutput = {
  module_name: string;
  result_json: Record<string, any>;
  confidence?: number;
};

function normalizeOutputs(outputs: AnalysisData["outputs"]): NormalizedOutput[] {
  if (!outputs) return [];

  if (Array.isArray(outputs)) {
    return outputs;
  }

  return Object.entries(outputs).map(([module_name, result_json]) => ({
    module_name,
    result_json: result_json || {},
  })) as NormalizedOutput[];
}

export default function ClientDashboard() {
  const [files, setFiles] = useState<File[]>([]);
  const [uploadedDocuments, setUploadedDocuments] = useState<Array<{ document_id: number; filename: string }>>([]);
  const [documentId, setDocumentId] = useState<number | null>(null);
  const [analysisId, setAnalysisId] = useState<string>("");
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
  const [reportUrl, setReportUrl] = useState<string>("");
  const [reportText, setReportText] = useState<string>("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const normalizedOutputs = useMemo(() => normalizeOutputs(analysis?.outputs || null), [analysis]);

  const finalReport = useMemo(
    () => normalizedOutputs.find((o) => o.module_name === "final_recommendation"),
    [normalizedOutputs]
  );

  const llmSource = useMemo(() => {
    const rawOutputs = analysis?.outputs;
    if (rawOutputs && !Array.isArray(rawOutputs)) {
      return rawOutputs?.final_json?.llm_source || null;
    }

    const candidate = normalizedOutputs.find(
      (o) => o.module_name === "final_recommendation" || o.module_name === "final_json"
    );
    return candidate?.result_json?.llm_source || null;
  }, [analysis, normalizedOutputs]);

  async function uploadDocument(e: FormEvent) {
    e.preventDefault();
    if (files.length === 0) return;

    setBusy(true);
    setError("");

    try {
      const successes: Array<{ document_id: number; filename: string }> = [];
      const failures: string[] = [];

      for (const file of files) {
        const form = new FormData();
        form.append("file", file);

        const res = await fetch(`${BACKEND}/upload`, { method: "POST", body: form });
        const data = await res.json();

        if (!res.ok) {
          failures.push(`${file.name}: ${data.detail || "Upload failed"}`);
          continue;
        }

        successes.push({
          document_id: data.document_id,
          filename: data.filename || file.name,
        });
      }

      if (successes.length > 0) {
        setUploadedDocuments((prev) => [...prev, ...successes]);
        setDocumentId(successes[successes.length - 1].document_id);
      }

      if (failures.length > 0) {
        setError(failures.join(" | "));
      }
    } finally {
      setBusy(false);
    }
  }

  async function startAnalysis() {
    if (!documentId) return;

    setBusy(true);
    setError("");

    const res = await fetch(`${BACKEND}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ document_id: documentId }),
    });

    const data = await res.json();
    setBusy(false);

    if (!res.ok) {
      setError(data.detail || "Analysis start failed");
      return;
    }

    setAnalysisId(data.analysis_id);
    setReportUrl(data.report_url || "");
    setReportText("");
    setAnalysis(null);
  }

  async function startPropertyAnalysis() {
    if (uploadedDocuments.length === 0) return;

    setBusy(true);
    setError("");

    const res = await fetch(`${BACKEND}/analyze/property`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ document_ids: uploadedDocuments.map((d) => d.document_id) }),
    });

    const data = await res.json();
    setBusy(false);

    if (!res.ok) {
      setError(data.detail || "Property analysis failed");
      return;
    }

    setAnalysisId(data.analysis_id);
    setReportUrl(data.report_url || "");
    setReportText("");
    setAnalysis(null);
  }

  async function loadPlainTextReport(reportPath: string) {
    const txtPath = reportPath.replace(/\/html$/, "/txt");
    const res = await fetch(`${BACKEND}${txtPath}`);
    if (!res.ok) {
      setError("Report was generated but plain-text version could not be loaded");
      return;
    }
    const text = await res.text();
    setReportText(text);
  }

  useEffect(() => {
    if (!analysisId) return;

    let timer: NodeJS.Timeout;
    const poll = async () => {
      const res = await fetch(`${BACKEND}/analyze/${analysisId}`);
      const data = await res.json();

      if (!res.ok) {
        setError(data.detail || "Failed to fetch analysis status");
        return;
      }

      setAnalysis(data);
      const statusReportUrl = data?.outputs?.final_json?.report_url;
      if (typeof statusReportUrl === "string" && statusReportUrl.length > 0) {
        setReportUrl(statusReportUrl);
        loadPlainTextReport(statusReportUrl);
      }
      if (data.status === "completed" || data.status === "failed") return;
      timer = setTimeout(poll, 2200);
    };

    poll();
    return () => clearTimeout(timer);
  }, [analysisId]);

  return (
    <main className="page-enter">
      <TopNav role="client" />
      <section className="shell" style={{ padding: "24px 0 36px" }}>
        <div className="kicker">Client Workspace</div>
        <h1 style={{ marginTop: 8 }}>Deal Analysis Console</h1>

        <article className="card" style={{ marginTop: 14, padding: 16 }}>
          <h2 style={{ marginTop: 0 }}>1) Upload Property Files</h2>
          <form onSubmit={uploadDocument} style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <input
              type="file"
              multiple
              className="input"
              onChange={(e) => setFiles(Array.from(e.target.files || []))}
              style={{ maxWidth: 360 }}
            />
            <button disabled={busy || files.length === 0} className="btn btn-primary" type="submit">
              {busy ? "Uploading..." : `Upload ${files.length || ""} file${files.length === 1 ? "" : "s"}`.trim()}
            </button>
          </form>
          {uploadedDocuments.length > 0 && (
            <div style={{ marginTop: 10 }}>
              <p style={{ color: "var(--ok)", margin: 0 }}>
                Uploaded successfully: {uploadedDocuments.length} document(s)
              </p>
              <div style={{ marginTop: 8 }}>
                <label style={{ fontWeight: 600, fontSize: 14 }}>Choose document for analysis</label>
                <select
                  className="input"
                  style={{ marginTop: 6, maxWidth: 420 }}
                  value={documentId ?? ""}
                  onChange={(e) => setDocumentId(Number(e.target.value))}
                >
                  {uploadedDocuments.map((doc) => (
                    <option key={`${doc.document_id}-${doc.filename}`} value={doc.document_id}>
                      #{doc.document_id} - {doc.filename}
                    </option>
                  ))}
                </select>
              </div>
              <button
                disabled={busy || uploadedDocuments.length === 0}
                className="btn btn-ghost"
                style={{ marginTop: 10 }}
                onClick={startPropertyAnalysis}
              >
                {busy ? "Starting..." : `Analyze Entire Property (${uploadedDocuments.length} docs)`}
              </button>
            </div>
          )}
        </article>

        <article className="card" style={{ marginTop: 14, padding: 16 }}>
          <h2 style={{ marginTop: 0 }}>2) Launch AI Due Diligence</h2>
          <button disabled={busy || !documentId} className="btn btn-primary" onClick={startAnalysis}>
            {busy ? "Starting..." : "Start Analysis"}
          </button>
          {analysisId && <p style={{ marginTop: 10 }}>Analysis ID: {analysisId}</p>}
          {analysis && <p style={{ marginTop: 4, color: "var(--muted)" }}>Status: <strong>{analysis.status}</strong></p>}
        </article>

        <article className="card" style={{ marginTop: 14, padding: 16 }}>
          <h2 style={{ marginTop: 0 }}>3) Results</h2>
          {!analysis && <p style={{ color: "var(--muted)" }}>No analysis output yet.</p>}

          {(reportUrl || finalReport?.result_json?.report_url || finalReport?.result_json?.analysis_id) && (
            <div style={{ marginTop: 10 }}>
              <p style={{ margin: 0, color: "var(--ok)", fontWeight: 700 }}>
                Final report generated successfully.
              </p>
              {llmSource && (
                <p style={{ marginTop: 6, marginBottom: 0, color: "var(--muted)" }}>
                  Report generated by: <strong>{llmSource}</strong>
                </p>
              )}
              <a
                href={
                  reportUrl
                    ? `${BACKEND}${reportUrl}`
                    : finalReport?.result_json?.report_url
                    ? `${BACKEND}${finalReport.result_json.report_url}`
                    : `${BACKEND}/reports/${finalReport?.result_json?.analysis_id}/html`
                }
                target="_blank"
                className="btn btn-primary"
                style={{ marginTop: 10, display: "inline-block" }}
                rel="noreferrer"
              >
                Open Generated Property Report (HTML)
              </a>
              <a
                href={
                  reportUrl
                    ? `${BACKEND}${reportUrl.replace(/\/html$/, "/pdf")}`
                    : finalReport?.result_json?.report_url
                    ? `${BACKEND}${String(finalReport.result_json.report_url).replace(/\/html$/, "/pdf")}`
                    : `${BACKEND}/reports/${finalReport?.result_json?.analysis_id}/pdf`
                }
                target="_blank"
                className="btn btn-ghost"
                style={{ marginTop: 10, marginLeft: 10, display: "inline-block" }}
                rel="noreferrer"
              >
                Open PDF Report
              </a>
            </div>
          )}

          {reportText && (
            <div style={{ marginTop: 14 }}>
              <h3 style={{ marginTop: 0 }}>Plain Text Report</h3>
              <pre
                style={{
                  margin: 0,
                  whiteSpace: "pre-wrap",
                  background: "#f5f8fb",
                  border: "1px solid #e3ebf2",
                  borderRadius: 10,
                  padding: 12,
                  maxHeight: 420,
                  overflow: "auto",
                }}
              >
                {reportText}
              </pre>
            </div>
          )}

          {error && <p style={{ color: "var(--danger)", marginTop: 10 }}>{error}</p>}
        </article>
      </section>
    </main>
  );
}
