import React, { useState, useEffect } from 'react';
import { ShieldCheck, Hash, Link2, Search, Clock, Database, Copy, Check } from 'lucide-react';
import { motion } from 'framer-motion';
import { GlassCard, CardHeader, Badge, Button, MOTION } from './ui';
import { BlockchainRecord, getLedger, verifyHash, sha256Hex } from '../lib/blockchain';
import { cn } from '../utils/cn';

export const BlockchainLedger: React.FC<{ compact?: boolean }> = ({ compact }) => {
  const [ledger, setLedger] = useState<BlockchainRecord[]>([]);
  const [query, setQuery] = useState('');
  const [verifyInput, setVerifyInput] = useState('');
  const [verifyResult, setVerifyResult] = useState<BlockchainRecord | null | 'notfound'>(null);
  const [copied, setCopied] = useState('');

  useEffect(()=>{ setLedger(getLedger()); }, []);
  const refresh = () => setLedger(getLedger());

  const handleVerify = async () => {
    if(!verifyInput.trim()) return;
    let h = verifyInput.trim();
    // If input is file content-like, hash it? For demo, if length <64 we hash it
    if(h.length < 64) h = await sha256Hex(h);
    const res = verifyHash(h);
    setVerifyResult(res || 'notfound');
  };

  const filtered = ledger.filter(r => !query || r.hash.includes(query) || r.fileName.includes(query) || r.txHash.includes(query));

  const copy = async (t: string, id: string) => { await navigator.clipboard.writeText(t); setCopied(id); setTimeout(()=>setCopied(''),1500); };

  if (compact && ledger.length===0) return null;

  return (
    <div className="space-y-4">
      <GlassCard accent="blue" padding="sm">
        <div className="flex flex-col sm:flex-row gap-3 items-start justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-blue-500/15 border border-blue-500/30 flex items-center justify-center"><Hash className="w-4 h-4 text-blue-400"/></div>
            <div>
              <div className="text-sm font-bold text-white">Blockchain Evidence Ledger</div>
              <div className="text-[11px] font-mono text-slate-500">Polygon Amoy Testnet • IPFS • SHA-256</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge accent="emerald" size="xs" dot>{ledger.length} NOTARIZED</Badge>
            <Button size="sm" variant="secondary" onClick={refresh}>Refresh</Button>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"/>
            <input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search by hash / file / tx..." className="w-full pl-9 pr-3 py-2 rounded-xl bg-[#0B1020] border border-slate-800 text-xs text-white placeholder:text-slate-600 focus:border-blue-500/40 focus:outline-none font-mono"/>
          </div>
          <div className="flex gap-2">
            <input value={verifyInput} onChange={e=>setVerifyInput(e.target.value)} placeholder="Paste SHA256 to verify..." className="flex-1 px-3 py-2 rounded-xl bg-[#0B1020] border border-slate-800 text-xs text-white placeholder:text-slate-600 focus:border-emerald-500/40 focus:outline-none font-mono"/>
            <Button size="sm" icon={ShieldCheck} onClick={handleVerify}>Verify</Button>
          </div>
        </div>

        {verifyResult && (
          <motion.div {...MOTION.fadeUp()} className={cn('mt-3 p-3 rounded-xl border text-xs', verifyResult==='notfound' ? 'bg-red-500/10 border-red-500/30 text-red-300' : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300')}>
            {verifyResult==='notfound' ? '❌ Hash NOT FOUND on blockchain - file may be tampered or not notarized.' :
              `✅ VERIFIED: ${verifyResult.fileName} notarized on ${verifyResult.timestamp} by ${verifyResult.officer} | Tx: ${verifyResult.txHash}`
            }
          </motion.div>
        )}
      </GlassCard>

      <div className="space-y-2 max-h-[420px] overflow-auto pr-1">
        {filtered.length===0 ? (
          <div className="py-8 text-center border border-dashed border-slate-800 rounded-xl text-xs text-slate-600">No notarized evidence yet. Upload a file in Upload Evidence to auto-notarize.</div>
        ) : filtered.map((r, i)=>(
          <motion.div key={r.hash} {...MOTION.fadeUp(i*0.03)} className="p-3 rounded-xl bg-white/[0.04] border border-white/[0.06] hover:border-blue-500/30 transition-colors">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="text-xs font-bold text-white truncate">{r.fileName}</div>
                <div className="text-[10px] font-mono text-slate-500 truncate">{r.hash}</div>
                <div className="flex flex-wrap gap-1.5 mt-1.5">
                  <Badge accent="blue" size="xs">Tx: {r.txHash.slice(0,10)}...</Badge>
                  <Badge accent="purple" size="xs">Block #{r.blockNumber}</Badge>
                  <span className="text-[10px] font-mono text-slate-600 flex items-center gap-1"><Clock className="w-3 h-3"/>{r.timestamp}</span>
                </div>
              </div>
              <div className="flex gap-1 shrink-0">
                <button onClick={()=>copy(r.hash, r.hash)} className="w-7 h-7 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 flex items-center justify-center text-slate-400 hover:text-white transition-colors">{copied===r.hash ? <Check className="w-3 h-3 text-emerald-400"/> : <Copy className="w-3 h-3"/>}</button>
                <button onClick={()=>copy(r.txHash, r.txHash)} className="w-7 h-7 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 flex items-center justify-center text-slate-400 hover:text-white transition-colors"><Link2 className="w-3 h-3"/></button>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="flex items-center justify-center gap-2 text-[10px] font-mono text-slate-600">
        <Database className="w-3 h-3"/> Ledger stored in localStorage + IPFS (mock Polygon). Real deploy: call <code className="bg-slate-900 px-1 rounded">Pinata + Polygon SDK</code>
      </div>
    </div>
  );
};
