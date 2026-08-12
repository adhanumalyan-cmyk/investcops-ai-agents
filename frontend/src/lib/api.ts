// NoteNext Unified API - connects Frontend to Backend (or fallback to direct Ollama/mock)
const API_BASE = (import.meta as any).env?.VITE_API_BASE || '/api';

export async function apiHealth(): Promise<{status:string}> {
  try {
    const r = await fetch(`${API_BASE}/health`);
    return await r.json();
  } catch { return {status:'offline'} as any; }
}

export async function firConvertViaBackend(text: string, opts?: {mock?:boolean, model?:string}): Promise<{fir:string, provider:string, mock:boolean}> {
  try {
    const r = await fetch(`${API_BASE}/fir/convert`, {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ text, mock: opts?.mock })
    });
    if (!r.ok) throw new Error('backend error');
    return await r.json();
  } catch (e) {
    // fallback to direct ollama/mock via old lib
    const { generateWithQwen, mockFIRFromText, FIR_SYSTEM_PROMPT, DEFAULT_OLLAMA } = await import('./ollama');
    try {
      const direct = await generateWithQwen(text, DEFAULT_OLLAMA, FIR_SYSTEM_PROMPT);
      if (direct) return { fir: direct, provider:'ollama-direct', mock:false };
    } catch {}
    return { fir: mockFIRFromText(text), provider:'mock', mock:true };
  }
}

export async function blockchainNotarizeViaBackend(payload: {fileName: string, fileSize: string, hash: string}) {
  try {
    const r = await fetch(`${API_BASE}/blockchain/notarize`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
    if (!r.ok) throw new Error('notarize fail');
    return await r.json();
  } catch { return null; }
}

export async function blockchainVerifyViaBackend(hash: string) {
  try {
    const r = await fetch(`${API_BASE}/blockchain/verify`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({hash})});
    if (!r.ok) throw new Error('verify fail');
    return await r.json();
  } catch { return null; }
}
