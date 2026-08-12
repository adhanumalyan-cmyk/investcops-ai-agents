// Blockchain Evidence Locker - simulates Polygon/IPFS notarization
// Uses Web Crypto SHA256 + localStorage ledger + QR verification

export interface BlockchainRecord {
  hash: string;
  fileName: string;
  fileSize: string;
  timestamp: string;
  isoTimestamp: string;
  officer: string;
  badge: string;
  caseId: string;
  txHash: string; // simulated
  blockNumber: number;
  verified: boolean;
}

const LEDGER_KEY = 'investcops_blockchain_ledger_v1';

export async function sha256Hex(input: string | ArrayBuffer): Promise<string> {
  const buf = typeof input === 'string' ? new TextEncoder().encode(input) : input;
  const hash = await crypto.subtle.digest('SHA-256', buf as ArrayBuffer);
  return Array.from(new Uint8Array(hash)).map(b => b.toString(16).padStart(2, '0')).join('');
}

export async function sha256File(file: File): Promise<string> {
  const buf = await file.arrayBuffer();
  return sha256Hex(buf);
}

export function generateTxHash(hash: string): string {
  // Simulate Polygon TX hash 0x + 64 hex chars
  return '0x' + hash.slice(0, 64);
}

export function saveToLedger(record: BlockchainRecord) {
  const ledger = getLedger();
  ledger.unshift(record);
  localStorage.setItem(LEDGER_KEY, JSON.stringify(ledger.slice(0, 100)));
  return record;
}

export function getLedger(): BlockchainRecord[] {
  try {
    const raw = localStorage.getItem(LEDGER_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch { return []; }
}

export function verifyHash(hash: string): BlockchainRecord | null {
  const ledger = getLedger();
  return ledger.find(r => r.hash === hash) || null;
}

export function getIPFSUrl(hash: string): string {
  return `ipfs://Qm${hash.slice(0, 44)}`;
}

export function getPolygonScanUrl(txHash: string): string {
  return `https://amoy.polygonscan.com/tx/${txHash}`;
}
