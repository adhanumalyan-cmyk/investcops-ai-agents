// frontend/src/lib/api.ts
// INVESTCOPS AI — Backend API Client
// Uses Vite proxy: /api -> http://localhost:8000

// ------------------------------------------------------------
// Types
// ------------------------------------------------------------

export interface ExtractRequest {
  case_id: string;
  investigator?: string;
  fetch_call_logs?: boolean;
  fetch_contacts?: boolean;
  fetch_sms?: boolean;
  fetch_media?: boolean;
  max_media_files?: number;
  adb_path?: string;
}

export interface ExtractResponse {
  status: string;
  case_id: string;
  case_folder: string;
  message: string;
  details: {
    call_logs?: number;
    contacts?: number;
    sms?: number;
    media?: number;
  };
}

export interface UploadResponse {
  success: boolean;
  case_id: string;
  evidence_id: string;
  file_name: string;
  hash: string;
  case_folder: string;
  results: {
    entities: Record<string, any[]>;
    contradictions: any[];
    risk_score: number;
    fir_draft: string;
    insights_summary: string;
  };
}

export interface AnalyzeResponse {
  status: string;
  case_id: string;
  results: {
    entities: Record<string, any[]>;
    relationships: any[];
    timeline: any[];
    contradictions: any[];
    risk_score: number;
    insights_summary: string;
    fir_draft: string;
    mentor_recommendations: string[];
  };
  message: string;
}

// ------------------------------------------------------------
// API Base URL (Proxy handles /api -> http://localhost:8000)
// ------------------------------------------------------------

const API_BASE = '/api';

// ============================================================
// 1. HEALTH CHECK
// ============================================================

export async function apiHealth(): Promise<{ status: string }> {
  try {
    const res = await fetch('http://localhost:8000/health');
    if (!res.ok) throw new Error('Health check failed');
    return await res.json();
  } catch {
    return { status: 'offline' };
  }
}

// ============================================================
// 2. EXTRACT PHONE DATA (USB / ADB)
// ============================================================

export async function extractPhoneData(
  payload: ExtractRequest
): Promise<ExtractResponse> {
  const response = await fetch(`${API_BASE}/cases/extract`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      case_id: payload.case_id,
      investigator: payload.investigator || 'investigator',
      fetch_call_logs: payload.fetch_call_logs ?? true,
      fetch_contacts: payload.fetch_contacts ?? true,
      fetch_sms: payload.fetch_sms ?? true,
      fetch_media: payload.fetch_media ?? false,
      max_media_files: payload.max_media_files ?? 50,
      adb_path: payload.adb_path || 'adb',
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Extract failed: ${response.status}`);
  }
  return await response.json();
}

// ============================================================
// 3. RUN AI ANALYSIS (AGENTS 1-11)
// ============================================================

export async function analyzeCase(case_id: string): Promise<AnalyzeResponse> {
  const response = await fetch(`${API_BASE}/ai/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ case_id }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Analysis failed: ${response.status}`);
  }
  return await response.json();
}

// ============================================================
// 4. FULL PIPELINE (EXTRACT + ANALYZE)
// ============================================================

export async function runFullPipeline(
  case_id: string,
  investigator?: string
): Promise<AnalyzeResponse> {
  console.log(`📱 Extracting data for case: ${case_id}`);
  await extractPhoneData({ case_id, investigator });
  
  console.log(`🧠 Running AI analysis for case: ${case_id}`);
  return await analyzeCase(case_id);
}

// ============================================================
// 5. UPLOAD EVIDENCE + ANALYZE (NEW — For UploadEvidenceView)
// ============================================================

export async function uploadEvidenceAndAnalyze(
  file: File,
  caseId: string = 'TEST001',
  investigator: string = 'investigator',
  category: string = 'unknown'
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('case_id', caseId);
  formData.append('investigator', investigator);
  formData.append('category', category);

  // Vite proxy will forward /api/upload/evidence -> http://localhost:8000/api/upload/evidence
  const response = await fetch(`${API_BASE}/upload/evidence`, {
    method: 'POST',
    body: formData,
    // DO NOT set Content-Type header manually! Browser sets it with correct boundary.
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(error.detail || `Upload failed: ${response.status}`);
  }

  return await response.json();
}

// ============================================================
// 6. DEPRECATED / LEGACY FUNCTIONS
// ============================================================

/**
 * @deprecated - Use uploadEvidenceAndAnalyze() or analyzeCase() instead
 */
export async function firConvertViaBackend(text: string): Promise<{
  fir: string;
  provider: string;
  mock: boolean;
}> {
  console.warn('⚠️ firConvertViaBackend is deprecated. Use uploadEvidenceAndAnalyze().');
  
  // Attempt to use the real analyze endpoint as fallback
  try {
    const response = await fetch(`${API_BASE}/ai/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ case_id: 'DEFAULT' }),
    });
    if (response.ok) {
      const data = await response.json();
      return {
        fir: data.results?.fir_draft || 'No FIR generated',
        provider: 'backend',
        mock: false,
      };
    }
  } catch {
    // Fallback to mock
  }

  return {
    fir: `[MOCK FIR] Investigation report generated for case.\n\nEvidence provided: ${text.slice(0, 200)}...\n\nThis is a placeholder FIR draft. Connect to backend for real analysis.`,
    provider: 'mock',
    mock: true,
  };
}

/**
 * @deprecated - Blockchain not implemented in backend yet
 */
export async function blockchainNotarizeViaBackend(payload: {
  fileName: string;
  fileSize: string;
  hash: string;
}) {
  console.warn('⚠️ Blockchain endpoint not implemented in backend. This is a stub.');
  return {
    success: false,
    message: 'Blockchain notarization is a future feature.',
    txHash: null,
  };
}

/**
 * @deprecated - Blockchain not implemented in backend yet
 */
export async function blockchainVerifyViaBackend(hash: string) {
  console.warn('⚠️ Blockchain endpoint not implemented in backend. This is a stub.');
  return {
    verified: false,
    message: 'Blockchain verification is a future feature.',
    record: null,
  };
}