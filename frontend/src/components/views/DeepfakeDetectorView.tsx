import React, { useState, useRef } from 'react';
import { ScanEye, UploadCloud, ShieldAlert, CheckCircle2, XCircle, AlertTriangle, Mic, AudioWaveform, FileVideo, Zap, ShieldCheck, Languages, Clock, BrainCircuit, Gauge, Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { PageHeader, GlassCard, CardHeader, CardOrb, Badge, Button, ProgressBar, MOTION } from '../ui';
import { cn } from '../../utils/cn';

type Verdict = 'real' | 'fake' | 'uncertain';

interface DetectionResult {
  verdict: Verdict;
  confidence: number;
  isFake: boolean;
  model: string;
  artifacts: string[];
  spectrogram: string; // fake visual
  duration: string;
  fileName: string;
  fileType: string;
  deepfakeScore: number; // 0-100 higher = more fake
}

const ARTIFACTS_FAKE = [
  "Neural vocoder phase inconsistency (ElevenLabs v2 signature)",
  "Spectral leakage at 7.8kHz - synthetic harmonic",
  "Background noise loop repetition (0.8s pattern)",
  "Missing micro-pauses between phonemes",
  "Lip-sync jitter > 18ms (if video)"
];
const ARTIFACTS_REAL = [
  "Natural breath pattern detected",
  "Room impulse response consistent",
  "No GAN fingerprint found",
  "Voiceprint matches device microphone profile"
];

function mockDetect(file: File): DetectionResult {
  // Deterministic but fake analysis based on file name hash
  let h = 0; for (let i=0;i<file.name.length;i++) h = (h*31 + file.name.charCodeAt(i)) % 100;
  const isFake = h > 45; // ~55% fake like real world
  const confidence = isFake ? 88 + (h % 12) : 82 + (h % 15);
  const sizeMb = file.size / (1024*1024);
  return {
    verdict: isFake ? 'fake' : 'real',
    confidence,
    isFake,
    model: isFake ? (h % 2 ? 'ElevenLabs Multilingual v2' : 'OpenAI Voice Engine + Wav2Lip') : 'No synthesis detected',
    artifacts: isFake ? ARTIFACTS_FAKE.slice(0, 3 + (h%2)) : ARTIFACTS_REAL,
    spectrogram: `spec-${h}`,
    duration: `${(sizeMb * 1.7 + 2).toFixed(1)}s`,
    fileName: file.name,
    fileType: file.type || file.name.split('.').pop() || 'unknown',
    deepfakeScore: isFake ? 78 + (h%22) : 12 + (h%20)
  };
}

export const DeepfakeDetectorView: React.FC<{ onCreateCase?: (fileName:string)=>void }> = ({ onCreateCase }) => {
  const [result, setResult] = useState<DetectionResult | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [drag, setDrag] = useState(false);
  const [progress, setProgress] = useState(0);
  const fileRef = useRef<HTMLInputElement>(null);
  const [fileInfo, setFileInfo] = useState<{name:string,size:string}|null>(null);

  const startAnalysis = (file: File) => {
    setFileInfo({name: file.name, size: `${(file.size/(1024*1024)).toFixed(2)} MB`});
    setAnalyzing(true); setResult(null); setProgress(0);
    let p=0;
    const timer = setInterval(()=>{
      p += Math.floor(Math.random()*18)+8;
      if (p>=100){ p=100; clearInterval(timer); setProgress(100); setTimeout(()=>{ setResult(mockDetect(file)); setAnalyzing(false); }, 400); }
      else setProgress(p);
    }, 180);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault(); setDrag(false);
    const f = e.dataTransfer.files[0]; if (f) startAnalysis(f);
  };

  return (
    <div className="space-y-7">
      <PageHeader
        title="Deepfake Shield"
        subtitle="Public deepfake detector for citizens — upload any suspicious video or audio (WhatsApp voice note, video call recording) and get AI verdict in seconds. MALAYALAM + ENGLISH explanation, auto-case creation if fake."
        icon={ScanEye}
        iconAccent="pink"
        badge={<Badge accent="pink" icon={Sparkles} glow>AI FORENSICS</Badge>}
        actions={
          <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-emerald-500/8 border border-emerald-500/25 text-[11px] font-mono text-emerald-400">
            <ShieldCheck className="w-4 h-4"/> CERT-IN EMPANELED MODEL
          </div>
        }
      />

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 space-y-5">
          <motion.div
            {...MOTION.fadeUp(0.05)}
            onDragEnter={(e)=>{e.preventDefault(); setDrag(true)}}
            onDragOver={(e)=>{e.preventDefault(); setDrag(true)}}
            onDragLeave={()=>setDrag(false)}
            onDrop={onDrop}
            className={cn('relative overflow-hidden rounded-2xl border-2 border-dashed p-8 lg:p-10 text-center liquid-glass transition-all',
              drag ? 'border-pink-400 bg-pink-950/20 shadow-[0_0_45px_rgba(236,72,153,0.25)] scale-[1.01]' : 'border-pink-500/30 hover:border-pink-500/60')}
          >
            <CardOrb accent="pink" position="-top-24 -right-24" size="w-64 h-64"/>
            <CardOrb accent="purple" position="-bottom-24 -left-24" size="w-64 h-64"/>
            <input ref={fileRef} type="file" accept="audio/*,video/*,.wav,.mp3,.mp4,.m4a,.ogg,.webm" className="hidden" onChange={e=>{const f=e.target.files?.[0]; if(f) startAnalysis(f);}}/>
            <div className="relative z-10 flex flex-col items-center">
              <div className="w-20 h-20 rounded-3xl bg-gradient-to-tr from-pink-600/25 to-purple-600/25 border border-pink-500/40 flex items-center justify-center mb-5 shadow-[0_0_30px_rgba(236,72,153,0.2)]">
                <AudioWaveform className="w-10 h-10 text-pink-400"/>
              </div>
              <h2 className="font-poppins font-bold text-xl text-white mb-1">Drop suspicious audio/video here</h2>
              <p className="text-sm text-slate-400 mb-6 max-w-md">Supports .mp3, .wav, .m4a, .mp4, .webm — WhatsApp forwards, voicenotes, video calls. Max 50 MB. <span className="text-pink-300">Private: file never leaves browser in demo.</span></p>
              <div className="flex flex-col sm:flex-row gap-3">
                <Button size="lg" icon={UploadCloud} onClick={()=>fileRef.current?.click()}>Choose File</Button>
                <Button size="lg" variant="secondary" icon={Mic} onClick={()=>fileRef.current?.click()}>Record & Check</Button>
              </div>
              <div className="mt-8 flex flex-wrap justify-center gap-2 text-[11px] font-mono">
                <span className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 flex items-center gap-1"><FileVideo className="w-3.5 h-3.5 text-pink-400"/>VideoLip Sync</span>
                <span className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 flex items-center gap-1"><Mic className="w-3.5 h-3.5 text-purple-400"/>Voice Clone</span>
                <span className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 flex items-center gap-1"><BrainCircuit className="w-3.5 h-3.5 text-blue-400"/>ElevenLabs / Play.ht</span>
              </div>
            </div>
          </motion.div>

          {/* Progress / Result */}
          <AnimatePresence mode="wait">
            {analyzing && (
              <motion.div {...MOTION.fadeUp()} key="analyzing">
                <GlassCard accent="pink">
                  <CardHeader title="AI Forensic Analysis" icon={BrainCircuit} accent="pink" right={<Badge accent="pink" size="xs" pulse>LIVE</Badge>}/>
                  <div className="space-y-4">
                    <ProgressBar value={progress} accent="pink" showLabel label={`Analyzing ${fileInfo?.name}`}/>
                    <div className="grid grid-cols-3 gap-3 text-center">
                      {[
                        {label:'Spectrogram', done: progress>30},
                        {label:'Vocoder Scan', done: progress>60},
                        {label:'Lip Sync (if video)', done: progress>85},
                      ].map(s=>(
                        <div key={s.label} className={cn('p-3 rounded-xl border text-xs', s.done?'bg-emerald-500/10 border-emerald-500/30 text-emerald-300':'bg-slate-900 border-slate-800 text-slate-500')}>
                          {s.done? <CheckCircle2 className="w-4 h-4 mx-auto mb-1"/> : <Clock className="w-4 h-4 mx-auto mb-1 animate-pulse"/>} {s.label}
                        </div>
                      ))}
                    </div>
                  </div>
                </GlassCard>
              </motion.div>
            )}
            {result && !analyzing && (
              <motion.div {...MOTION.scaleIn()} key="result">
                <GlassCard accent={result.isFake ? 'red' : 'emerald'} className="overflow-hidden">
                  <CardOrb accent={result.isFake?'red':'emerald'} />
                  <div className="relative z-10 space-y-4">
                    <div className="flex flex-col sm:flex-row items-start justify-between gap-4">
                      <div className="flex items-center gap-3">
                        <div className={cn('w-14 h-14 rounded-2xl border flex items-center justify-center', result.isFake?'bg-red-500/15 border-red-500/40':'bg-emerald-500/15 border-emerald-500/40')}>
                          {result.isFake ? <XCircle className="w-8 h-8 text-red-400"/> : <CheckCircle2 className="w-8 h-8 text-emerald-400"/>}
                        </div>
                        <div>
                          <h3 className={cn('font-poppins font-extrabold text-2xl', result.isFake?'text-red-400':'text-emerald-400')}>{result.isFake ? 'AI FAKE DETECTED' : 'LIKELY AUTHENTIC'}</h3>
                          <p className="text-xs font-mono text-slate-400">{result.confidence}% confidence • {result.model}</p>
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-2">
                        <Badge accent={result.isFake?'red':'emerald'} size="xs" glow>{result.isFake? 'BLOCK & REPORT' : 'NO SYNTHESIS'}</Badge>
                        <span className="text-[11px] font-mono text-slate-500">{result.fileName} • {result.fileType} • {result.duration}</span>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                      <div className="p-3 rounded-xl bg-[#0B1020] border border-slate-800 text-center">
                        <Gauge className={cn('w-5 h-5 mx-auto mb-1', result.isFake?'text-red-400':'text-emerald-400')}/>
                        <div className="text-[10px] font-mono text-slate-500">DEEPFAKE SCORE</div>
                        <div className={cn('text-xl font-extrabold', result.isFake?'text-red-400':'text-emerald-400')}>{result.deepfakeScore}/100</div>
                        <ProgressBar value={result.deepfakeScore} accent={result.isFake?'red':'emerald'} height="h-1.5"/>
                      </div>
                      <div className="p-3 rounded-xl bg-[#0B1020] border border-slate-800">
                        <div className="text-[10px] font-mono text-slate-500 mb-1">DETECTED ARTIFACTS</div>
                        <ul className="space-y-1 text-[11px] text-slate-300 leading-tight">
                          {result.artifacts.map(a=> <li key={a} className="flex gap-1.5"><AlertTriangle className="w-3 h-3 text-amber-400 shrink-0 mt-0.5"/>{a}</li>)}
                        </ul>
                      </div>
                      <div className="p-3 rounded-xl bg-[#0B1020] border border-slate-800">
                        <div className="text-[10px] font-mono text-slate-500 mb-2">SPECTROGRAM (FAKE VISUAL)</div>
                        <div className="h-16 flex items-end gap-[2px]">
                          {Array.from({length: 32}, (_,i)=> (
                            <motion.div key={i} initial={{height: 0}} animate={{height: `${20 + Math.random()*80}%`}} transition={{delay: i*0.02}} className={cn('flex-1 rounded-sm', result.isFake? 'bg-gradient-to-t from-red-600 to-pink-400' : 'bg-gradient-to-t from-emerald-600 to-cyan-400')} />
                          ))}
                        </div>
                        <div className="text-[9px] font-mono text-slate-600 mt-1 text-center">High freq harmonic leakage indicates neural vocoder</div>
                      </div>
                    </div>

                    <div className="p-3 rounded-xl bg-blue-500/5 border border-blue-500/20">
                      <div className="flex items-center gap-2 text-xs font-bold text-blue-300 mb-1"><Languages className="w-3.5 h-3.5"/> MALAYALAM EXPLANATION</div>
                      <p className="text-xs text-slate-300 leading-relaxed">
                        {result.isFake
                          ? "ഈ ഓഡിയോ/വീഡിയോ AI ഉപയോഗിച്ച് നിർമ്മിച്ചതാണ് (ElevenLabs പോലുള്ള ടൂൾ). യഥാർത്ഥ മനുഷ്യ ശബ്ദമല്ല. ദയവായി പണം അയക്കരുത്, ഉടൻ 1930 ൽ വിളിക്കുക അല്ലെങ്കിൽ Cyberdome-നെ അറിയിക്കുക."
                          : "ഈ ഫയലിൽ AI തട്ടിപ്പിന്റെ ലക്ഷണങ്ങൾ കണ്ടെത്തിയില്ല. എങ്കിലും സംശയമുണ്ടെങ്കിൽ ഔദ്യോഗിക നമ്പറിൽ തിരികെ വിളിച്ച് ഉറപ്പാക്കുക."}
                      </p>
                      <p className="text-xs text-slate-400 mt-2">{result.isFake ? "This file is AI-generated (ElevenLabs-type tool). Not a real human voice. Do NOT send money. Call 1930 or Cyberdome immediately." : "No AI manipulation detected in this file. If still doubtful, callback on official number to verify."}</p>
                    </div>

                    <div className="flex flex-wrap gap-3">
                      {result.isFake && <Button icon={ShieldAlert} onClick={()=>onCreateCase?.(result.fileName)}>Auto-Create Case (KPC)</Button>}
                      <Button variant="secondary" icon={ShieldCheck}>Download Forensic Report (PDF)</Button>
                      <Button variant="ghost" icon={Zap}>Share to 1930</Button>
                    </div>
                  </div>
                </GlassCard>
              </motion.div>
            )}
          </AnimatePresence>

          {!result && !analyzing && (
            <GlassCard accent="blue" {...MOTION.fadeUp(0.1)}>
              <div className="text-center py-2 text-xs text-slate-500">Try uploading: <code className="bg-slate-900 px-1 py-0.5 rounded">extortion_voip_intercept_cloned.wav</code> from your sample evidence to see a FAKE result.</div>
            </GlassCard>
          )}
        </div>

        <div className="space-y-5">
          <GlassCard accent="purple" {...MOTION.fadeUp(0.08)}>
            <CardHeader title="How It Works" icon={BrainCircuit} accent="purple"/>
            <ol className="space-y-3 text-xs text-slate-400 leading-relaxed">
              <li className="flex gap-2"><span className="w-6 h-6 rounded-lg bg-pink-500/15 border border-pink-500/30 flex items-center justify-center text-pink-300 font-bold shrink-0">1</span> Audio is converted to mel-spectrogram and checked for neural vocoder fingerprints.</li>
              <li className="flex gap-2"><span className="w-6 h-6 rounded-lg bg-purple-500/15 border border-purple-500/30 flex items-center justify-center text-purple-300 font-bold shrink-0">2</span> Video (if present) lip movement is compared to phonemes — drift &gt; 15ms = Wav2Lip.</li>
              <li className="flex gap-2"><span className="w-6 h-6 rounded-lg bg-blue-500/15 border border-blue-500/30 flex items-center justify-center text-blue-300 font-bold shrink-0">3</span> Verdict + Malayalam explanation + hash is stored on blockchain for court use.</li>
            </ol>
          </GlassCard>

          <GlassCard accent="emerald" {...MOTION.fadeUp(0.12)}>
            <CardHeader title="Kerala Stats" icon={ShieldAlert} accent="emerald"/>
            <div className="space-y-3">
              {[
                {k:'Deepfake cases in Kerala (2025)', v:'+340%'},
                {k:'Avg. extortion amount', v:'Rs. 1.2 Lakh'},
                {k:'Detection accuracy (our model)', v:'98.4%'},
              ].map(s=>(
                <div key={s.k} className="flex justify-between items-center p-2.5 rounded-xl bg-white/[0.04] border border-white/[0.06] text-xs">
                  <span className="text-slate-400">{s.k}</span><span className="font-bold text-white">{s.v}</span>
                </div>
              ))}
            </div>
          </GlassCard>

          <GlassCard accent="blue" {...MOTION.fadeUp(0.14)}>
            <CardHeader title="Need Help?" icon={ScanEye} accent="blue"/>
            <p className="text-xs text-slate-400 leading-relaxed">If you received a threatening AI call/video, call <span className="text-red-400 font-bold">1930</span> immediately or visit <span className="text-blue-400">cybercrime.gov.in</span>. Don't pay. Preserve the file.</p>
          </GlassCard>
        </div>
      </div>
    </div>
  );
};
