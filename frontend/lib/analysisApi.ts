export type UploadedDocument = {
  document_id: number;
  filename: string;
};

export type UploadDocumentsResult = {
  successes: UploadedDocument[];
  failures: string[];
};

export type PropertyAnalysisPayload = {
  document_ids: number[];
  property_name?: string;
};

export type PropertyAnalysisResult =
  | { ok: true; data: { analysis_id: string; report_url?: string } }
  | { ok: false; error: string };

function normalizeAnalysisId(value: unknown): string | null {
  if (typeof value === "string" && value.trim()) {
    return value;
  }
  if (typeof value === "number" && Number.isFinite(value)) {
    return String(value);
  }
  return null;
}

function parseErrorDetail(data: unknown, fallback: string): string {
  if (typeof data === "object" && data !== null) {
    const detail = (data as { detail?: unknown }).detail;
    if (typeof detail === "string" && detail.trim()) {
      return detail;
    }
    const error = (data as { error?: unknown }).error;
    if (typeof error === "string" && error.trim()) {
      return error;
    }
  }
  return fallback;
}

async function readJsonSafely(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

export async function uploadDocuments(
  backend: string,
  files: File[]
): Promise<UploadDocumentsResult> {
  const successes: UploadedDocument[] = [];
  const failures: string[] = [];
  const maxConcurrent = 3;

  async function uploadSingle(file: File): Promise<void> {
    const form = new FormData();
    form.append("file", file);

    const response = await fetch(`${backend}/upload`, {
      method: "POST",
      body: form,
      credentials: "include",
    });
    const data = await readJsonSafely(response);

    if (!response.ok) {
      failures.push(`${file.name}: ${parseErrorDetail(data, "Upload failed")}`);
      return;
    }

    const payload = data as { document_id?: unknown; filename?: unknown } | null;
    const documentId = Number(payload?.document_id);
    if (!Number.isFinite(documentId)) {
      failures.push(`${file.name}: Invalid upload response`);
      return;
    }

    successes.push({
      document_id: documentId,
      filename: typeof payload?.filename === "string" && payload.filename ? payload.filename : file.name,
    });
  }

  for (let i = 0; i < files.length; i += maxConcurrent) {
    const batch = files.slice(i, i + maxConcurrent);
    await Promise.all(batch.map((file) => uploadSingle(file)));
  }

  return { successes, failures };
}

export async function startPropertyAnalysisRequest(
  backend: string,
  payload: PropertyAnalysisPayload
): Promise<PropertyAnalysisResult> {
  const response = await fetch(`${backend}/analyze/property`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    credentials: "include",
  });

  const data = await readJsonSafely(response);

  if (!response.ok) {
    return { ok: false, error: parseErrorDetail(data, "Property analysis failed") };
  }

  const body = data as { analysis_id?: unknown; report_url?: unknown } | null;
  const analysisId = normalizeAnalysisId(body?.analysis_id);
  if (!analysisId) {
    return { ok: false, error: "Invalid analysis response" };
  }

  return {
    ok: true,
    data: {
      analysis_id: analysisId,
      report_url: typeof body?.report_url === "string" ? body.report_url : undefined,
    },
  };
}
