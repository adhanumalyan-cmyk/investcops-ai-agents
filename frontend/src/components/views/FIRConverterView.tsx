import React, { useState } from 'react';
import { FileText, Sparkles, Copy, Check, Cpu, Wifi, WifiOff, Settings2, Languages, Scale, AlertTriangle, Download, Trash2, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { PageHeader, GlassCard, CardHeader, CardOrb, Badge, Button, MOTION } from '../ui';
import { generateWithQwen, mockFIRFromText, FIR_SYSTEM_PROMPT, DEFAULT_OLLAMA, OllamaConfig } from '../../lib/ollama';
import { firConvertViaBackend, apiHealth } from '../../lib/api';

const SAMPLE_TEXTS = [
  { label: 'UPI Fraud (English)', text: "Sir, I got a call from +91 98470 12345 saying my PhonePe is blocked. They sent a link, I clicked and lost Rs. 45000 via UPI. Transaction ID 123456789012. Please help." },
  { label: 'Manglish', text: "Sir ente accountil ninnu 25000 poyi. Oru loan appil ninnu call vannu, link click cheyyan paranj. Telegramil @quickloan_official ennu paranj fraud aanu. Please FIR eduth tharum." },
  { label: 'Malayalam', text: "സർ, എനിക്ക് വാട്സാപ്പിൽ ഒരു APK ഫയൽ വന്നു KSEB ബിൽ പേയ്മെന്റ് എന്ന് പറഞ്ഞ്. ഇൻസ്റ്റാൾ ചെയ്തപ്പോൾ എന്റെ ഫോണിൽ നിന്ന് 38000 രൂപ നഷ്ടപ്പെട്ടു." },
  { label: 'Job Scam', text: "I was contacted on Telegram for part-time job liking YouTube videos. They asked me to pay Rs. 2000 for registration then Rs. 50000 for tasks. Now they blocked me. Username @task_earner_pro" },
];

export const FIRConverterView: React.FC = () => {
  const [input, setInput] = useState('');
  const [output, setOutput] = useState('');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [useMock, setUseMock] = useState(false);
  const [ollamaStatus, setOllamaStatus] = useState<'idle'|'online'|'offline'>('idle');
  const [config, setConfig] = useState<OllamaConfig>(DEFAULT_OLLAMA);
  const [showSettings, setShowSettings] = useState(false);
  const [error, setError] = useState('');

  const testOllama = async () => {
    setOllamaStatus('idle');
    try {
      // Try backend first (properly connected), then direct Ollama
      const health = await apiHealth();
      if ((health as any).status === 'ok') {
        setOllamaStatus('online');
        return;
      }
      const res = await fetch(`${config.baseUrl.replace(/\/$/,'')}/api/tags`, { method: 'GET' });
      setOllamaStatus(res.ok ? 'online' : 'offline');
    } catch {
      setOllamaStatus('offline');
    }
  };

  const handleConvert = async () => {
    if (!input.trim()) return;
    setLoading(true); setError(''); setOutput('');
    
    // Try connected backend first (vite proxy /api -> backend:8000)
    if (!useMock) {
      try {
        const backend = await firConvertViaBackend(input, { mock: false });
        if (backend?.fir) {
          setOutput(backend.fir);
          setOllamaStatus(backend.mock ? 'offline' : 'online');
          if (backend.mock) setError(`Backend used mock (Ollama not running at ${config.baseUrl}). Start Ollama to use real Qwen3.`);
          setLoading(false);
          return;
        }
      } catch {}
    }

    // Fallback to direct Ollama / mock as before
    let online = false;
    try {
      await fetch(`${config.baseUrl.replace(/\/$/,'')}/api/tags`, { method:'GET', signal: AbortSignal.timeout(1500) }).then(r => { online = r.ok });
    } catch { online = false; }
    
    if (!online || useMock) {
      await new Promise(r => setTimeout(r, 900));
      setOutput(mockFIRFromText(input));
      if (!online) setError(`Ollama not reachable at ${config.baseUrl} — using offline high-quality mock (Qwen3 template). Backend will auto-fallback too.`);
      setLoading(false);
      return;
    }
    try {
      const result = await generateWithQwen(input, config, FIR_SYSTEM_PROMPT);
      if (!result) throw new Error('Empty response');
      setOutput(result);
      setOllamaStatus('online');
    } catch (e: any) {
      setError(`Ollama error: ${e.message}. Used mock fallback. Check that 'ollama serve' and 'ollama pull ${config.model}' are done.`);
      setOutput(mockFIRFromText(input));
      setOllamaStatus('offline');
    } finally {
      setLoading(false);
    }
  };

  const copy = async () => {
    await navigator.clipboard.writeText(output);
    setCopied(true); setTimeout(()=>setCopied(false), 2000);
  };

  const download = () => {
    const blob = new Blob([output], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = `FIR-Draft-${Date.now()}.txt`; a.click(); URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-7">
      <PageHeader
        title="Text-to-FIR Converter"
        subtitle="Convert victim's informal complaint (English, Malayalam, Manglish) into a formal Section 173 BNSS FIR draft using Qwen3 via Ollama — court-ready, with correct BNS & IT Act sections."
        icon={FileText}
        iconAccent="purple"
        badge={<Badge accent="purple" icon={Sparkles} glow>QWEN3 • OLLAMA</Badge>}
        actions={
          <>
            <div className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-[11px] font-mono ${ollamaStatus==='online' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : ollamaStatus==='offline' ? 'bg-red-500/10 border-red-500/30 text-red-400' : 'bg-slate-900 border-slate-800 text-slate-400'}`}>
              {ollamaStatus==='online' ? <Wifi className="w-3.5 h-3.5"/> : ollamaStatus==='offline' ? <WifiOff className="w-3.5 h-3.5"/> : <Cpu className="w-3.5 h-3.5"/>}
              {ollamaStatus==='online' ? 'OLLAMA ONLINE' : ollamaStatus==='offline' ? 'OFFLINE (MOCK)' : 'NOT TESTED'}
            </div>
            <Button variant="secondary" icon={Settings2} onClick={()=>setShowSettings(!showSettings)}>Ollama Settings</Button>
          </>
        }
      />

      <AnimatePresence>
        {showSettings && (
          <motion.div {...MOTION.fadeUp()} className="liquid-glass border border-slate-800 rounded-2xl p-5 space-y-4">
            <div className="flex items-center gap-2 text-sm font-bold text-white"><Settings2 className="w-4 h-4 text-purple-400"/> Ollama Configuration</div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <label className="space-y-1">
                <span className="text-[11px] font-mono text-slate-500">OLLAMA BASE URL</span>
                <input value={config.baseUrl} onChange={e=>setConfig({...config, baseUrl:e.target.value})} placeholder="http://localhost:11434" className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-sm text-white focus:border-purple-500/50 focus:outline-none"/>
              </label>
              <label className="space-y-1">
                <span className="text-[11px] font-mono text-slate-500">MODEL</span>
                <select value={config.model} onChange={e=>setConfig({...config, model:e.target.value})} className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-sm text-white focus:border-purple-500/50 focus:outline-none">
                  <option value="qwen3:0.6b">qwen3:0.6b (600M - fastest)</option>
                  <option value="qwen3:1.7b">qwen3:1.7b</option>
                  <option value="qwen3:4b">qwen3:4b</option>
                  <option value="qwen3:8b">qwen3:8b</option>
                  <option value="qwen2.5:3b">qwen2.5:3b (fallback)</option>
                </select>
              </label>
              <div className="flex items-end gap-2">
                <Button variant="secondary" onClick={testOllama} className="w-full">Test Connection</Button>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={useMock} onChange={e=>setUseMock(e.target.checked)} className="rounded"/>
                <span className="text-xs text-slate-400">Force mock mode (offline demo)</span>
              </label>
              <span className="text-[11px] font-mono text-slate-600">Setup: <code className="bg-slate-900 px-1.5 py-0.5 rounded">ollama serve</code> + <code className="bg-slate-900 px-1.5 py-0.5 rounded">ollama pull {config.model}</code></span>
            </div>
            <div className="p-3 rounded-xl bg-blue-500/5 border border-blue-500/20 text-xs text-slate-400 leading-relaxed">
              <strong className="text-blue-300">How Qwen3 is used:</strong> Prompt = <code className="text-purple-300">{FIR_SYSTEM_PROMPT.slice(0,110)}...</code> + victim text → Ollama <code>/api/generate</code> (temperature 0.3) → FIR draft. If offline, we use a deterministic high-quality mock so demo never fails.
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input */}
        <GlassCard accent="purple" {...MOTION.fadeUp(0.05)} className="flex flex-col">
          <CardHeader title="Victim's Informal Statement" icon={Languages} accent="purple" right={<Badge accent="blue" size="xs">MALAYALAM + ENGLISH + MANGLISH</Badge>} />
          <div className="space-y-3 flex-1 flex flex-col">
            <div className="flex flex-wrap gap-1.5">
              {SAMPLE_TEXTS.map(s=> (
                <button key={s.label} onClick={()=>setInput(s.text)} className="px-2.5 py-1 rounded-lg bg-white/[0.04] border border-white/[0.08] hover:border-purple-500/40 text-[11px] text-slate-400 hover:text-purple-300 transition-colors">{s.label}</button>
              ))}
            </div>
            <textarea
              value={input}
              onChange={e=>setInput(e.target.value)}
              placeholder="Paste victim's message here... Example: 'Sir ente phoneil loan app fraud nadannu, Rs 40000 poyi...' or English/Malayalam mixed. The AI will understand and create a formal FIR."
              className="flex-1 min-h-[280px] w-full p-4 rounded-xl bg-[#0B1020] border border-slate-800 text-sm text-slate-200 placeholder:text-slate-600 focus:border-purple-500/40 focus:outline-none resize-none leading-relaxed"
            />
            <div className="flex items-center justify-between gap-3">
              <span className="text-[11px] font-mono text-slate-500">{input.length} chars • Supports Malayalam script & Manglish</span>
              <div className="flex gap-2">
                <Button variant="ghost" icon={Trash2} onClick={()=>{setInput(''); setOutput('');}}>Clear</Button>
                <Button icon={Sparkles} loading={loading} disabled={!input.trim()} onClick={handleConvert}>Convert to FIR</Button>
              </div>
            </div>
            {error && <div className="flex gap-2 p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs text-amber-300 leading-relaxed"><AlertTriangle className="w-4 h-4 shrink-0"/> {error}</div>}
          </div>
        </GlassCard>

        {/* Output */}
        <GlassCard accent="emerald" {...MOTION.fadeUp(0.1)} className="flex flex-col">
          <CardHeader title="Formal FIR Draft (BNSS 173)" icon={Scale} accent="emerald" right={output && <div className="flex gap-1.5"><Button size="sm" variant="secondary" icon={copied?Check:Copy} onClick={copy}>{copied?'Copied':'Copy'}</Button><Button size="sm" variant="secondary" icon={Download} onClick={download}>TXT</Button></div>} />
          {!output ? (
            <div className="flex-1 flex flex-col items-center justify-center py-16 text-center border border-dashed border-slate-800 rounded-xl bg-slate-900/30">
              <div className="w-14 h-14 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center mb-3"><Scale className="w-7 h-7 text-slate-600"/></div>
              <p className="text-sm font-bold text-slate-400">FIR will appear here</p>
              <p className="text-xs text-slate-600 mt-1 max-w-xs">Qwen3 will auto-add BNS Sections, IT Act, timeline, and officer assignment. Ready to print & sign.</p>
              {loading && <Loader2 className="w-6 h-6 animate-spin text-purple-400 mt-4"/>}
            </div>
          ) : (
            <div className="relative">
              <CardOrb accent="emerald" position="-top-16 -right-16" size="w-48 h-48"/>
              <pre className="whitespace-pre-wrap break-words p-4 rounded-xl bg-[#0B1020] border border-slate-800 text-[12.5px] leading-6 text-slate-200 font-mono max-h-[520px] overflow-auto custom-scrollbar relative z-10">{output}</pre>
              <div className="mt-3 flex items-center gap-2 text-[11px] font-mono text-emerald-400"><Check className="w-3.5 h-3.5"/> AI Draft • Verify with SHO before filing • Blockchain hash will be added on saving</div>
            </div>
          )}
        </GlassCard>
      </div>

      <GlassCard accent="blue" {...MOTION.fadeUp(0.15)}>
        <div className="flex items-center gap-2 mb-2"><Cpu className="w-4 h-4 text-blue-400"/><span className="text-sm font-bold text-white">How to run with real Qwen3 locally</span><Badge accent="blue" size="xs">OLLAMA</Badge></div>
        <ol className="list-decimal list-inside space-y-1 text-xs text-slate-400 leading-relaxed">
          <li>Install Ollama from <a href="https://ollama.com" target="_blank" className="text-blue-400 underline">ollama.com</a> and run <code className="bg-slate-900 px-1 py-0.5 rounded text-purple-300">ollama serve</code></li>
          <li>Pull model: <code className="bg-slate-900 px-1 py-0.5 rounded text-purple-300">ollama pull qwen3:0.6b</code> (only 400MB, works on even 8GB RAM) or <code className="bg-slate-900 px-1 py-0.5 rounded text-purple-300">ollama pull qwen3:4b</code></li>
          <li>Keep Ollama running, click <em>Test Connection</em> above - it should show ONLINE</li>
          <li>Now conversions will use real Qwen3 inference at <code className="bg-slate-900 px-1 py-0.5 rounded">http://localhost:11434</code>. Demo fallback ensures hackathon never fails even without Ollama.</li>
        </ol>
      </GlassCard>
    </div>
  );
};
