import React, { useState, useEffect } from 'react';
import { Smartphone, Cable, ShieldCheck, Download, Hash, HardDrive, FileText, Image as ImageIcon, MessageSquare, Phone, Clock, CheckCircle2, AlertTriangle, Loader2, Zap, Search, HardDrive as Drive, Cpu, Usb, Play, RefreshCw, Copy, Check } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { PageHeader, GlassCard, CardHeader, CardOrb, Badge, Button, ProgressBar, MOTION } from '../ui';
import { cn } from '../../utils/cn';

interface DeviceInfo {
  connected: boolean;
  mock: boolean;
  reason?: string;
  device_id?: string;
  model?: string;
  android?: string;
  adb_available?: boolean;
}
interface ExtractFile { path: string; size: number; sha256: string; desc?: string; }
interface ExtractResult { success: boolean; mock: boolean; out_dir: string; files: ExtractFile[]; log: string[]; manifest?: any; device?: DeviceInfo; }

export const USBFieldExtractorView: React.FC = () => {
  const [device, setDevice] = useState<DeviceInfo | null>(null);
  const [checking, setChecking] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [log, setLog] = useState<string[]>([]);
  const [result, setResult] = useState<ExtractResult | null>(null);
  const [caseId, setCaseId] = useState('KPC-2026-8941');
  const [copied, setCopied] = useState('');
  const [history, setHistory] = useState<any[]>([]);

  const apiBase = '/api';

  const checkDevice = async () => {
    setChecking(true);
    try {
      const r = await fetch(`${apiBase}/field/status`);
      const j = await r.json();
      setDevice(j);
    } catch {
      setDevice({ connected: false, mock: true, reason: 'Backend not reachable — will use MOCK demo', adb_available: false });
    } finally { setChecking(false); }
    // history
    try {
      const h = await fetch(`${apiBase}/field/list`);
      const hj = await h.json();
      setHistory(hj.backups || []);
    } catch {}
  };

  useEffect(() => { checkDevice(); }, []);

  const startExtract = async () => {
    setExtracting(true); setProgress(0); setLog([]); setResult(null);
    let p = 0;
    const timer = setInterval(() => { p = Math.min(95, p + Math.random()*12+4); setProgress(Math.floor(p)); }, 300);
    try {
      const r = await fetch(`${apiBase}/field/extract`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({caseId})});
      const j = await r.json();
      clearInterval(timer); setProgress(100);
      setResult(j);
      setLog(j.log || []);
      checkDevice();
    } catch (e: any) {
      clearInterval(timer);
      setLog([`Error: ${e.message}`, 'Using MOCK fallback...']);
      // mock fallback locally
      setResult({ success: true, mock: true, out_dir: 'field_backups/' + caseId + '_' + Date.now(), files: [
        {path:'WhatsApp/chat_export.txt', size: 45200, sha256: 'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2'}, 
        {path:'DCIM/Camera/photo_001.jpg', size: 3240000, sha256: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08'},
        {path:'Contacts/contacts.vcf', size: 8800, sha256: '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8'},
      ], log: ['MOCK extraction: 3 files'] });
    } finally { setExtracting(false); }
  };

  const copy = async (t:string, id:string) => { await navigator.clipboard.writeText(t); setCopied(id); setTimeout(()=>setCopied(''),1500); };

  return (
    <div className="space-y-7">
      <PageHeader
        title="USB Field Extractor — On-Spot Phone Forensics"
        subtitle="Connect suspect / missing person phone via USB cable to officer laptop → One-click logical extraction (WhatsApp, Photos, Contacts, Browser, Call Logs, SMS) → Auto SHA256 + Blockchain notarized. No root, no data sharing — all on police instance. Cable = Evidence."
        icon={Smartphone}
        iconAccent="purple"
        badge={<Badge accent="purple" icon={Cable} glow>FIELD READY</Badge>}
        actions={
          <div className="flex gap-2">
            <div className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-[11px] font-mono ${device?.connected ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-600' : 'bg-amber-500/10 border-amber-500/30 text-amber-700'}`}>
              <Usb className="w-3.5 h-3.5"/> {checking ? 'Checking...' : device?.connected ? `${device.model} • Android ${device.android}` : device?.adb_available === false ? 'ADB Not Installed (Mock Demo)' : 'No Device (Mock Demo)'}
            </div>
            <Button variant="secondary" icon={RefreshCw} onClick={checkDevice}>Check Device</Button>
          </div>
        }
      />

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* LEFT: Extract */}
        <div className="xl:col-span-2 space-y-5">
          <GlassCard accent="purple" {...MOTION.fadeUp(0.05)}>
            <CardHeader title="On-Spot Extraction" icon={Cable} accent="purple" right={<Badge accent={device?.connected ? 'emerald' : 'amber'} size="xs">{device?.connected ? 'DEVICE READY' : 'MOCK READY'}</Badge>} />
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <label className="space-y-1">
                  <span className="text-[11px] font-mono text-slate-500">CASE ID</span>
                  <input value={caseId} onChange={e=>setCaseId(e.target.value)} className="w-full px-3 py-2.5 rounded-xl bg-white/80 border border-slate-200 text-sm font-mono text-slate-800 focus:border-violet-500/50 focus:outline-none" placeholder="KPC-2026-8941"/>
                </label>
                <div className="flex items-end">
                  <div className="p-3 rounded-xl bg-violet-500/5 border border-violet-500/20 text-xs text-slate-600 leading-relaxed flex-1">
                    <strong className="text-violet-700">How:</strong> Enable USB Debugging → Connect cable → Tap Authorize → Click Extract. All files stay on police laptop, hashed & blockchain-stamped.
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-white/60 border border-slate-200">
                <div className="text-xs font-bold text-slate-800 mb-2 flex items-center gap-1.5"><ShieldCheck className="w-4 h-4 text-violet-600"/> What Gets Extracted (Logical, No Root):</div>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-[11px]">
                  {[
                    {k:'WhatsApp Chats', icon: MessageSquare, d:'msgstore.db + export'},
                    {k:'Photos / DCIM', icon: ImageIcon, d:'Camera, Screenshots'},
                    {k:'Contacts', icon: Phone, d:'contacts.vcf'},
                    {k:'Call Logs', icon: Phone, d:'54 calls'},
                    {k:'SMS', icon: MessageSquare, d:'210 SMS'},
                    {k:'Browser History', icon: Search, d:'Chrome history'},
                  ].map(i=>{
                    const Icon = i.icon;
                    return (
                    <div key={i.k} className="p-2.5 rounded-xl bg-violet-500/5 border border-violet-500/10 flex gap-2 items-center">
                      <Icon className="w-4 h-4 text-violet-600 shrink-0" />
                      <div><div className="font-semibold text-slate-700">{i.k}</div><div className="text-slate-500 text-[10px]">{i.d}</div></div>
                    </div>
                  )})}
                </div>
                <div className="mt-3 text-[11px] font-mono text-amber-700 bg-amber-500/10 border border-amber-500/20 p-2.5 rounded-xl">
                  ⚠️ Need: USB Debugging ON (Settings → Developer Options). iPhone: Tap Trust. No root, no APK install, 15 sec extact. Deleted data needs lab (Cellebrite).
                </div>
              </div>

              <Button size="lg" icon={extracting ? Loader2 : Play} loading={extracting} onClick={startExtract} className="w-full justify-center">
                {extracting ? `Extracting... ${progress}%` : device?.connected ? `🔌 Extract Phone Now (${device.model})` : `▶️ Demo Extract (Mock Phone)`}
              </Button>
              {extracting && <ProgressBar value={progress} accent="purple" showLabel label="Logical extraction via ADB" />}
              {log.length>0 && (
                <div className="p-3 rounded-xl bg-[#0B1020] border border-slate-800 font-mono text-[11px] text-emerald-300 max-h-40 overflow-auto">
                  {log.map((l,i)=><div key={i}>{l}</div>)}
                </div>
              )}
            </div>
          </GlassCard>

          {/* Results */}
          <AnimatePresence>
            {result && (
              <motion.div {...MOTION.scaleIn()} >
                <GlassCard accent={result.mock ? 'amber' : 'emerald'}>
                  <CardHeader title={result.mock ? 'Mock Extraction Result (Demo)' : 'Real Extraction Result'} icon={CheckCircle2} accent={result.mock?'amber':'emerald'} right={<Badge accent={result.mock?'amber':'emerald'} size="xs">{result.files.length} files • {result.mock?'MOCK':'REAL'}</Badge>} />
                  <div className="space-y-3">
                    <div className="p-3 rounded-xl bg-white/60 border border-slate-200 flex flex-wrap gap-2 items-center justify-between">
                      <span className="text-xs font-mono text-slate-600">Output: <span className="text-violet-700 font-bold">{result.out_dir}</span></span>
                      <Badge accent="blue" size="xs" dot>Auto Blockchain Notarized</Badge>
                    </div>
                    <div className="space-y-2 max-h-72 overflow-auto">
                      {result.files.map(f=>(
                        <div key={f.path} className="p-2.5 rounded-xl bg-white/70 border border-slate-200 flex items-center gap-3">
                          <div className="w-9 h-9 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center shrink-0">
                            <HardDrive className="w-4 h-4 text-violet-600"/>
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="text-xs font-bold text-slate-800 truncate">{f.path}</div>
                            <div className="text-[10px] font-mono text-slate-500 truncate">{f.sha256} • {f.size} bytes</div>
                          </div>
                          <button onClick={()=>copy(f.sha256, f.sha256)} className="w-7 h-7 rounded-lg bg-slate-800 hover:bg-slate-700 text-white flex items-center justify-center">{copied===f.sha256 ? <Check className="w-3 h-3"/> : <Copy className="w-3 h-3"/>}</button>
                        </div>
                      ))}
                    </div>
                    <div className="flex gap-2">
                      <Button icon={ShieldCheck} variant="secondary">View in Case {caseId}</Button>
                      <Button icon={Hash} variant="ghost">Ledger Verified</Button>
                    </div>
                  </div>
                </GlassCard>
              </motion.div>
            )}
          </AnimatePresence>

          <GlassCard accent="blue" {...MOTION.fadeUp(0.1)}>
            <CardHeader title="Another Mobile-La Enna Aagum?" icon={Smartphone} accent="blue"/>
            <div className="text-xs text-slate-600 leading-relaxed space-y-2">
              <p><strong>Web Link Only:</strong> Phone-la link open panni nee select panna files mattum thaan extract aagum — auto illa, safe!</p>
              <p><strong>USB Cable + Extract Button:</strong> Appo thaan full logical data (WhatsApp, Photos, Contacts...) auto extract aagum — 1 click-la, laptop-la save aagum, blockchain hash udane.</p>
              <p className="p-2.5 rounded-xl bg-emerald-500/5 border border-emerald-500/20 text-emerald-700">Demo la MOCK data, real device connect panna REAL files varum. ADB install pannina pothum: <code className="bg-white px-1 rounded">adb --version</code></p>
            </div>
          </GlassCard>
        </div>

        {/* RIGHT */}
        <div className="space-y-5">
          <GlassCard accent="purple" {...MOTION.fadeUp(0.08)}>
            <CardHeader title="Device Status" icon={Cpu} accent="purple"/>
            {device ? (
              <div className="space-y-3">
                <div className={`p-3 rounded-xl border flex items-center gap-3 ${device.connected ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-amber-500/5 border-amber-500/20'}`}>
                  {device.connected ? <CheckCircle2 className="w-5 h-5 text-emerald-600"/> : <AlertTriangle className="w-5 h-5 text-amber-600"/>}
                  <div>
                    <div className={`text-sm font-bold ${device.connected?'text-emerald-700':'text-amber-700'}`}>{device.connected ? 'Ready to Extract' : 'No Device — Mock Demo Ready'}</div>
                    <div className="text-[11px] font-mono text-slate-500">{device.reason || `${device.model} • ${device.device_id}`}</div>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="p-2.5 rounded-xl bg-white/60 border border-slate-200"><div className="text-[10px] font-mono text-slate-500">ADB</div><div className={`font-bold ${device.adb_available ? 'text-emerald-700' : 'text-amber-700'}`}>{device.adb_available ? 'Installed' : 'Not Found'}</div></div>
                  <div className="p-2.5 rounded-xl bg-white/60 border border-slate-200"><div className="text-[10px] font-mono text-slate-500">MODE</div><div className="font-bold text-violet-700">{device.mock ? 'MOCK' : device.connected ? 'REAL' : 'MOCK'}</div></div>
                </div>
                {!device.adb_available && (
                  <div className="p-2.5 rounded-xl bg-slate-900 text-slate-200 text-xs font-mono leading-relaxed">
                    Install ADB:<br/>
                    <code className="text-emerald-300">winget install Google.PlatformTools</code> (Windows)<br/>
                    <code className="text-emerald-300">brew install android-platform-tools</code> (Mac)<br/>
                    Then restart backend: <code className="text-cyan-300">python backend/main.py</code>
                  </div>
                )}
              </div>
            ) : <div className="text-xs text-slate-500">Checking...</div>}
          </GlassCard>

          <GlassCard accent="blue" {...MOTION.fadeUp(0.12)}>
            <CardHeader title="Recent Extractions" icon={Clock} accent="blue"/>
            {history.length===0 ? <div className="text-xs text-slate-500 py-6 text-center border border-dashed border-slate-200 rounded-xl">No extractions yet. Do first extract above.</div> : (
              <div className="space-y-2 max-h-64 overflow-auto">
                {history.map((h:any)=>(
                  <div key={h.folder} className="p-2.5 rounded-xl bg-white/60 border border-slate-200">
                    <div className="text-xs font-bold text-slate-800">{h.case_id}</div>
                    <div className="text-[11px] font-mono text-slate-500">{h.folder} • {h.files} files • {h.mock ? 'MOCK' : 'REAL'}</div>
                  </div>
                ))}
              </div>
            )}
          </GlassCard>

          <GlassCard accent="emerald" {...MOTION.fadeUp(0.14)}>
            <CardHeader title="CMD to Run Server Again" icon={HardDrive} accent="emerald"/>
            <div className="space-y-2 font-mono text-xs">
              <div className="p-2.5 rounded-xl bg-slate-900 text-emerald-300">
                <div className="text-slate-400"># Terminal 1 — Frontend</div>
                cd project<br/>npm run dev -- --host 0.0.0.0 --port 5173
              </div>
              <div className="p-2.5 rounded-xl bg-slate-900 text-cyan-300">
                <div className="text-slate-400"># Terminal 2 — Backend (new window)</div>
                cd project<br/>python backend/main.py<br/># or python3 backend/main.py
              </div>
              <div className="p-2.5 rounded-xl bg-slate-900 text-amber-300">
                <div className="text-slate-400"># Standalone USB (no dashboard)</div>
                python backend/field_extractor.py --info<br/>python backend/field_extractor.py --extract --case KPC-2026-8941
              </div>
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  );
};
