import React, { useState, useRef, useCallback, useEffect } from 'react';
import {
  UploadCloud, FileText, FileCheck, ShieldCheck, Hash, FileImage, FileVideo,
  FileAudio, Archive, Mail, MessageSquare, Camera, Send, Database, X,
  CheckCircle2, Clock, Trash2, Zap, Lock, Users, HardDrive, FolderSearch,
  Fingerprint, Network, Timer, ShieldAlert, FileSearch, ArrowRight,
  RotateCcw, Image as ImageIcon, AlertCircle, Loader2, LucideIcon
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  PageHeader, GlassCard, CardHeader, CardOrb, Badge, Button, ActionBar,
  EmptyState, ProgressBar, MOTION, AccentColor
} from '../ui';
import { cn } from '../../utils/cn';
import { sha256Hex, saveToLedger, generateTxHash } from '../../lib/blockchain';
import { BlockchainLedger } from '../BlockchainLedger';
// 👇 NEW IMPORT
import { uploadEvidenceAndAnalyze } from '../../lib/api';

/* ── Types ── */
type FileStatus = 'validating' | 'uploading' | 'complete' | 'rejected' | 'analyzing';

export interface UploadedFile {
  id: string;
  name: string;
  size: string;
  type: string;
  uploadedAt: string;
  category: string;
  status: FileStatus;
  progress: number;
  fileObj?: File; // 👈 Actual file object for upload
  error?: string;
  result?: any; // AI result
}

interface UploadEvidenceViewProps {
  onAnalyze?: (files: UploadedFile[], results: any) => void;
  onCancel?: () => void;
}

/* ── Config ── */
const ACCEPTED = ['pdf', 'txt', 'docx', 'jpg', 'jpeg', 'png', 'mp4', 'mp3', 'zip', 'raw', 'json', 'wav', 'apk'];

const SUPPORTED_TYPES: { label: string; icon: LucideIcon; color: string }[] = [
  { label: 'PDF',  icon: FileText,  color: 'text-red-400' },
  { label: 'TXT',  icon: FileText,  color: 'text-slate-400' },
  { label: 'DOCX', icon: FileText,  color: 'text-blue-400' },
  { label: 'JPG',  icon: FileImage, color: 'text-emerald-400' },
  { label: 'PNG',  icon: FileImage, color: 'text-purple-400' },
  { label: 'MP4',  icon: FileVideo, color: 'text-pink-400' },
  { label: 'MP3',  icon: FileAudio, color: 'text-amber-400' },
  { label: 'ZIP',  icon: Archive,   color: 'text-orange-400' }
];

const CATEGORIES: { id: string; label: string; icon: LucideIcon; accent: AccentColor; description: string }[] = [
  { id: 'whatsapp',  label: 'WhatsApp Chat',    icon: MessageSquare, accent: 'emerald', description: 'Exported .txt / .zip logs' },
  { id: 'instagram', label: 'Instagram Export', icon: Camera,        accent: 'pink',    description: 'DM dumps & story reports' },
  { id: 'telegram',  label: 'Telegram Chat',    icon: Send,          accent: 'blue',    description: 'JSON / SQLite dumps' },
  { id: 'email',     label: 'Email Evidence',   icon: Mail,          accent: 'amber',   description: 'EML / MBOX / PST' },
  { id: 'images',    label: 'Images',           icon: ImageIcon,     accent: 'purple',  description: 'Screenshots & photos' },
  { id: 'videos',    label: 'Videos',           icon: FileVideo,     accent: 'rose',    description: 'CCTV & mobile footage' },
  { id: 'audio',     label: 'Audio Files',      icon: FileAudio,     accent: 'orange',  description: 'Call & deepfake audio' },
  { id: 'documents', label: 'Documents',        icon: FileText,      accent: 'blue',    description: 'PDFs & transaction slips' },
  { id: 'backup',    label: 'Device Backup',    icon: Database,      accent: 'cyan',    description: 'Disk & Android dumps' }
];

const PIPELINE: { title: string; icon: LucideIcon; accent: AccentColor; description: string }[] = [
  { title: 'Evidence Upload',        icon: UploadCloud,  accent: 'blue',    description: 'SHA-256 custody registered' },
  { title: 'Evidence Analysis',      icon: Fingerprint,  accent: 'purple',  description: 'MIME & malware scanning' },
  { title: 'Entity Extraction',      icon: Users,        accent: 'pink',    description: 'NER for names, wallets, IPs' },
  { title: 'Source Correlation',     icon: Network,      accent: 'amber',   description: 'Cyberdome vault matching' },
  { title: 'Timeline Reconstruction',icon: Timer,        accent: 'emerald', description: 'Temporal event graph' },
  { title: 'Risk Assessment',        icon: ShieldAlert,  accent: 'red',     description: 'CyberLLM threat scoring' },
  { title: 'Investigation Report',   icon: FileCheck,    accent: 'blue',    description: 'ISO 27037 court dossier' }
];

const ACCENT_CARD: Record<string, string> = {
  emerald: 'bg-emerald-500/12 border-emerald-500/45 text-emerald-400 shadow-[0_0_18px_rgba(16,185,129,0.18)]',
  pink:    'bg-pink-500/12 border-pink-500/45 text-pink-400 shadow-[0_0_18px_rgba(236,72,153,0.18)]',
  blue:    'bg-blue-500/12 border-blue-500/45 text-blue-400 shadow-[0_0_18px_rgba(59,130,246,0.18)]',
  amber:   'bg-amber-500/12 border-amber-500/45 text-amber-400 shadow-[0_0_18px_rgba(245,158,11,0.18)]',
  purple:  'bg-purple-500/12 border-purple-500/45 text-purple-400 shadow-[0_0_18px_rgba(139,92,246,0.18)]',
  rose:    'bg-rose-500/12 border-rose-500/45 text-rose-400 shadow-[0_0_18px_rgba(244,63,94,0.18)]',
  orange:  'bg-orange-500/12 border-orange-500/45 text-orange-400 shadow-[0_0_18px_rgba(249,115,22,0.18)]',
  cyan:    'bg-cyan-500/12 border-cyan-500/45 text-cyan-400 shadow-[0_0_18px_rgba(6,182,212,0.18)]'
};

export const UploadEvidenceView: React.FC<UploadEvidenceViewProps> = ({ onAnalyze, onCancel }) => {
  const [dragActive, setDragActive] = useState(false);
  const [category, setCategory] = useState('whatsapp');
  const [caseId, setCaseId] = useState('KPC-2026-8941'); // 👈 NEW
  const [investigator, setInvestigator] = useState('DySP Rajesh'); // 👈 NEW
  const [files, setFiles] = useState<UploadedFile[]>([]); // 👈 Changed: empty instead of SEED_FILES
  const [analyzing, setAnalyzing] = useState(false);
  const [step, setStep] = useState(0);
  const [justAdded, setJustAdded] = useState(false);
  const [globalResult, setGlobalResult] = useState<any>(null);

  const browseRef = useRef<HTMLInputElement>(null);
  const deviceRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!justAdded) return;
    const t = setTimeout(() => setJustAdded(false), 2200);
    return () => clearTimeout(t);
  }, [justAdded]);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true);
    else if (e.type === 'dragleave') setDragActive(false);
  }, []);

  const addFiles = useCallback((list: FileList | null) => {
    if (!list?.length) return;

    const incoming: UploadedFile[] = Array.from(list).map((f, i) => {
      const ext = f.name.split('.').pop()?.toLowerCase() || '';
      const valid = ACCEPTED.includes(ext);
      const mb = f.size / (1024 * 1024);
      return {
        id: `f-${Date.now()}-${i}`,
        name: f.name,
        size: mb >= 1 ? `${mb.toFixed(1)} MB` : `${(f.size / 1024).toFixed(1)} KB`,
        type: `${ext.toUpperCase() || 'BIN'} File`,
        uploadedAt: 'Just now',
        category,
        status: valid ? 'validating' : 'rejected',
        progress: valid ? 0 : 100,
        fileObj: f, // 👈 Store actual file object
        error: valid ? undefined : `Unsupported .${ext} format`
      };
    });

    setFiles(prev => [...incoming, ...prev]);

    incoming.filter(f => f.status === 'validating').forEach((file, idx) => {
      setTimeout(() => {
        setFiles(prev => prev.map(f => f.id === file.id ? { ...f, status: 'uploading' } : f));
        let p = 0;
        const tick = setInterval(() => {
          p += Math.floor(Math.random() * 22) + 12;
          if (p >= 100) {
            clearInterval(tick);
            setFiles(prev => prev.map(f => f.id === file.id ? { ...f, progress: 100, status: 'complete' } : f));
            setJustAdded(true);
            // Blockchain notarize (mock) - only for demo, actual notarization happens in backend
            sha256Hex(`${file.name}-${file.size}-${Date.now()}`).then(hash=>{
              const tx = generateTxHash(hash);
              saveToLedger({
                hash, fileName: file.name, fileSize: file.size,
                timestamp: new Date().toLocaleString('en-IN', { day:'2-digit', month:'short', year:'numeric', hour:'2-digit', minute:'2-digit'}),
                isoTimestamp: new Date().toISOString(),
                officer: 'DySP Rajesh V. Kumar', badge: 'KP-CYD-042', caseId: 'KPC-2026-8941',
                txHash: tx, blockNumber: Math.floor(8000000 + Math.random()*500000), verified: true
              });
            });
          } else {
            setFiles(prev => prev.map(f => f.id === file.id ? { ...f, progress: p } : f));
          }
        }, 180);
      }, 350 + idx * 220);
    });
  }, [category]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation();
    setDragActive(false);
    addFiles(e.dataTransfer.files);
  }, [addFiles]);

  const removeFile = (id: string) => setFiles(prev => prev.filter(f => f.id !== id));

  const readyFiles = files.filter(f => f.status === 'complete' && f.fileObj);
  const rejectedCount = files.filter(f => f.status === 'rejected').length;
  const busy = files.some(f => f.status === 'uploading' || f.status === 'validating' || f.status === 'analyzing');

  // ============================================================
  // 👇 UPDATED: REAL ANALYSIS WITH BACKEND
  // ============================================================
  const startAnalysis = async () => {
    if (!readyFiles.length) return;
    setAnalyzing(true);
    setStep(0);
    setGlobalResult(null);

    // Take first ready file for demo
    const targetFile = readyFiles[0];
    if (!targetFile.fileObj) return;

    try {
      setFiles(prev => prev.map(f =>
        f.id === targetFile.id ? { ...f, status: 'analyzing' } : f
      ));
      setStep(1);

      // 🔥 ACTUAL API CALL
      const response = await uploadEvidenceAndAnalyze(
        targetFile.fileObj,
        caseId,
        investigator,
        category
      );

      setStep(2);
      await new Promise(r => setTimeout(r, 300));
      setStep(3);
      await new Promise(r => setTimeout(r, 300));
      setStep(4);
      await new Promise(r => setTimeout(r, 300));
      setStep(5);

      setFiles(prev => prev.map(f =>
        f.id === targetFile.id ? { ...f, status: 'complete', result: response.results } : f
      ));

      setGlobalResult(response);
      setAnalyzing(false);

      onAnalyze?.(readyFiles, response.results);

    } catch (error: any) {
      console.error('Analysis failed:', error);
      setFiles(prev => prev.map(f =>
        f.id === targetFile.id ? { ...f, status: 'rejected', error: error.message || 'Analysis failed' } : f
      ));
      setAnalyzing(false);
    }
  };

  return (
    <div className="space-y-7">
      <PageHeader
        title="Upload Digital Evidence"
        subtitle="Securely upload digital evidence for AI-powered investigation. All uploads are AES-256 encrypted, SHA-256 hash verified, and court-admissible under Section 65B of the Indian Evidence Act."
        icon={UploadCloud}
        iconAccent="blue"
        badge={<Badge accent="purple" icon={Zap} glow>AI-POWERED</Badge>}
        actions={
          <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-emerald-500/8 border border-emerald-500/25 text-[11px] font-mono text-emerald-400">
            <Lock className="w-4 h-4 shrink-0" /> ISO 27037 Secure Channel
          </div>
        }
      />

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5 lg:gap-6">

        {/* ══ LEFT: Upload + Categories + Files ══ */}
        <div className="xl:col-span-2 space-y-5 lg:space-y-6 min-w-0">

          {/* Case Details */}
          <GlassCard accent="blue">
            <div className="grid grid-cols-2 gap-4">
              <label className="space-y-1">
                <span className="text-[11px] font-mono text-slate-500">CASE ID</span>
                <input value={caseId} onChange={e => setCaseId(e.target.value)} className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-sm text-white focus:border-blue-500/50 focus:outline-none" />
              </label>
              <label className="space-y-1">
                <span className="text-[11px] font-mono text-slate-500">INVESTIGATOR</span>
                <input value={investigator} onChange={e => setInvestigator(e.target.value)} className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-sm text-white focus:border-blue-500/50 focus:outline-none" />
              </label>
            </div>
          </GlassCard>

          {/* Dropzone */}
          <motion.div
            {...MOTION.fadeUp(0.05)}
            onDragEnter={handleDrag} onDragOver={handleDrag}
            onDragLeave={handleDrag} onDrop={handleDrop}
            className={cn(
              'relative overflow-hidden rounded-2xl border-2 border-dashed p-8 lg:p-11 text-center liquid-glass transition-all duration-300',
              dragActive
                ? 'border-blue-400 bg-blue-950/30 shadow-[0_0_45px_rgba(59,130,246,0.28)] scale-[1.01]'
                : justAdded
                ? 'border-emerald-500/60 shadow-[0_0_35px_rgba(16,185,129,0.22)]'
                : 'border-blue-500/30 hover:border-blue-500/60'
            )}
          >
            <CardOrb accent="blue" position="-top-24 -right-24" size="w-64 h-64" />
            <CardOrb accent="purple" position="-bottom-24 -left-24" size="w-64 h-64" />

            <input ref={browseRef} type="file" multiple className="hidden" onChange={e => addFiles(e.target.files)} />
            <input ref={deviceRef} type="file" multiple className="hidden" onChange={e => addFiles(e.target.files)} />

            <div className="relative z-10 flex flex-col items-center">
              <motion.div
                animate={dragActive ? { y: -8, scale: 1.08 } : justAdded ? { scale: [1, 1.12, 1] } : { y: 0, scale: 1 }}
                transition={{ type: 'spring', stiffness: 300, damping: 18 }}
                className={cn(
                  'w-20 h-20 rounded-3xl border flex items-center justify-center mb-5 transition-colors',
                  justAdded
                    ? 'bg-emerald-500/20 border-emerald-500/50 shadow-[0_0_30px_rgba(16,185,129,0.3)]'
                    : 'bg-gradient-to-tr from-blue-600/25 to-purple-600/25 border-blue-500/40 shadow-[0_0_30px_rgba(59,130,246,0.22)]'
                )}
              >
                {justAdded
                  ? <CheckCircle2 className="w-10 h-10 text-emerald-400" />
                  : <UploadCloud className="w-10 h-10 text-blue-400" />}
              </motion.div>

              <h2 className="font-poppins font-bold text-xl text-white mb-1.5">
                {dragActive ? 'Drop Files to Begin Upload'
                  : justAdded ? 'Evidence Secured Successfully'
                  : 'Drop your files here or click to browse'}
              </h2>
              <p className="text-sm text-slate-400 mb-6 max-w-md leading-relaxed">
                Maximum single upload <span className="text-slate-200 font-semibold">10 GB</span>. Bulk uploads are chunked and hash-verified to preserve chain-of-custody.
              </p>

              <div className="flex flex-col sm:flex-row items-center gap-3">
                <Button size="lg" icon={UploadCloud} onClick={() => browseRef.current?.click()}>Choose Files</Button>
                <Button size="lg" variant="secondary" icon={HardDrive} onClick={() => deviceRef.current?.click()}>Upload from Device</Button>
              </div>

              {/* Supported types */}
              <div className="mt-8 pt-5 border-t border-slate-800/80 w-full max-w-2xl">
                <p className="text-[10px] uppercase tracking-[0.12em] text-slate-500 font-mono font-bold mb-3">Supported File Types</p>
                <div className="flex flex-wrap items-center justify-center gap-2">
                  {SUPPORTED_TYPES.map(t => {
                    const Icon = t.icon;
                    return (
                      <span key={t.label} className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 text-[11px] font-mono text-slate-300 hover:border-slate-700 transition-colors">
                        <Icon className={cn('w-3.5 h-3.5', t.color)} />{t.label}
                      </span>
                    );
                  })}
                </div>
              </div>
            </div>
          </motion.div>

          {/* Categories */}
          <GlassCard accent="purple" {...MOTION.fadeUp(0.12)}>
            <CardHeader
              title="Select Evidence Category"
              icon={FolderSearch}
              accent="purple"
              right={<Badge accent="purple" size="xs">{CATEGORIES.find(c => c.id === category)?.label}</Badge>}
            />
            <p className="text-[11.5px] text-slate-500 -mt-2 mb-3.5">
              Selecting a category optimizes the AI extraction pipeline for that data type.
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3" role="radiogroup" aria-label="Evidence category">
              {CATEGORIES.map(c => {
                const Icon = c.icon;
                const active = category === c.id;
                return (
                  <button
                    key={c.id}
                    role="radio"
                    aria-checked={active}
                    onClick={() => setCategory(c.id)}
                    className={cn(
                      'p-3.5 rounded-2xl border text-left transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/60',
                      active
                        ? ACCENT_CARD[c.accent]
                        : 'bg-slate-900/40 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200 hover:-translate-y-0.5'
                    )}
                  >
                    <Icon className="w-5 h-5 mb-2" />
                    <h4 className="font-poppins font-bold text-[12.5px] leading-tight">{c.label}</h4>
                    <p className="text-[10px] opacity-75 mt-0.5 leading-tight truncate">{c.description}</p>
                  </button>
                );
              })}
            </div>
          </GlassCard>

          {/* Uploaded Files */}
          <GlassCard accent="blue" {...MOTION.fadeUp(0.18)}>
            <CardHeader
              title="Uploaded Files"
              icon={FileSearch}
              accent="blue"
              right={
                <div className="flex items-center gap-2">
                  <Badge accent="blue" size="xs">{readyFiles.length} ready</Badge>
                  {rejectedCount > 0 && <Badge accent="red" size="xs">{rejectedCount} rejected</Badge>}
                  {files.length > 0 && (
                    <button onClick={() => setFiles([])}
                      className="text-[10px] font-mono text-slate-500 hover:text-red-400 flex items-center gap-1 transition-colors">
                      <RotateCcw className="w-3 h-3" /> Clear
                    </button>
                  )}
                </div>
              }
            />

            {files.length === 0 ? (
              <EmptyState
                compact
                icon={Archive}
                title="No evidence uploaded yet"
                description="Drop files above or click Choose Files to begin the forensic ingestion pipeline."
              />
            ) : (
              <ul className="space-y-2.5">
                <AnimatePresence mode="popLayout">
                  {files.map((file, i) => {
                    const cat = CATEGORIES.find(c => c.id === file.category);
                    const CatIcon = cat?.icon || FileText;
                    const rejected = file.status === 'rejected';
                    const uploading = file.status === 'uploading' || file.status === 'validating';
                    const analyzingStatus = file.status === 'analyzing';

                    return (
                      <motion.li
                        key={file.id}
                        layout
                        initial={{ opacity: 0, x: -12 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 14, height: 0 }}
                        transition={{ delay: i * 0.03 }}
                        className={cn(
                          'flex items-center gap-3.5 p-3.5 rounded-xl border transition-all group',
                          rejected
                            ? 'bg-red-950/20 border-red-500/30'
                            : analyzingStatus
                            ? 'bg-blue-950/20 border-blue-500/40'
                            : 'bg-white/[0.04] border-white/[0.08] hover:border-blue-500/40 hover:bg-blue-500/[0.06]'
                        )}
                      >
                        {/* Preview thumb */}
                        <div className={cn(
                          'w-11 h-11 rounded-xl border flex items-center justify-center shrink-0',
                          rejected ? 'bg-red-500/10 border-red-500/30' : 'bg-blue-500/10 border-blue-500/30'
                        )}>
                          {rejected
                            ? <AlertCircle className="w-5 h-5 text-red-400" />
                            : analyzingStatus
                            ? <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
                            : <CatIcon className="w-5 h-5 text-blue-400" />}
                        </div>

                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <h4 className={cn('text-[13px] font-semibold truncate max-w-[16rem]',
                              rejected ? 'text-red-300' : 'text-slate-100 group-hover:text-white')}>
                              {file.name}
                            </h4>
                            {!rejected && <Badge accent="purple" size="xs">{cat?.label.split(' ')[0]}</Badge>}
                          </div>

                          <div className="flex items-center gap-2.5 mt-1 text-[10.5px] font-mono text-slate-500 flex-wrap">
                            <span>{file.size}</span><span>·</span>
                            <span>{file.type}</span><span>·</span>
                            <span className="flex items-center gap-1"><Clock className="w-2.5 h-2.5" />{file.uploadedAt}</span>
                          </div>

                          {uploading && (
                            <div className="mt-2 max-w-xs">
                              <ProgressBar value={file.progress} accent="blue" height="h-1" />
                            </div>
                          )}
                          {analyzingStatus && (
                            <div className="mt-1 text-[10px] font-mono text-blue-400">
                              🔄 AI Analysis in progress...
                            </div>
                          )}
                          {rejected && file.error && (
                            <p className="text-[10.5px] font-mono text-red-400 mt-1">{file.error}</p>
                          )}
                        </div>

                        <div className="flex items-center gap-2.5 shrink-0">
                          {file.status === 'complete' && file.result && (
                            <Badge accent="emerald" size="xs" icon={CheckCircle2}>RISK {file.result.risk_score}/100</Badge>
                          )}
                          {file.status === 'complete' && !file.result && (
                            <Badge accent="emerald" size="xs" icon={CheckCircle2}>READY</Badge>
                          )}
                          {uploading && (
                            <Badge accent="blue" size="xs">
                              <Loader2 className="w-2.5 h-2.5 animate-spin" />{file.progress}%
                            </Badge>
                          )}
                          {analyzingStatus && (
                            <Badge accent="blue" size="xs">
                              <Loader2 className="w-2.5 h-2.5 animate-spin" /> ANALYZING
                            </Badge>
                          )}
                          {rejected && <Badge accent="red" size="xs">REJECTED</Badge>}

                          {!analyzingStatus && (
                            <button
                              onClick={() => removeFile(file.id)}
                              aria-label={`Remove ${file.name}`}
                              className="w-8 h-8 rounded-lg bg-slate-800/80 hover:bg-red-500/20 text-slate-500 hover:text-red-400 border border-slate-700 hover:border-red-500/40 flex items-center justify-center transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-red-500/60"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </div>
                      </motion.li>
                    );
                  })}
                </AnimatePresence>
              </ul>
            )}
          </GlassCard>
        </div>

        {/* ══ RIGHT: Pipeline + Security ══ */}
        <div className="space-y-5 lg:space-y-6 min-w-0">

          <GlassCard accent="purple" {...MOTION.fadeUp(0.1)} className="overflow-hidden">
            <CardOrb accent="purple" />
            <CardHeader title="AI Processing Pipeline" icon={Zap} accent="purple" />
            <p className="text-[11.5px] text-slate-500 -mt-2 mb-4 relative z-10">
              Evidence flows through the CyberLLM agent chain:
            </p>

            <ol className="relative z-10">
              {PIPELINE.map((s, i) => {
                const Icon = s.icon;
                const active = analyzing && i === step;
                const done = analyzing ? i < step : false;
                const hasResults = globalResult !== null;

                return (
                  <li key={s.title} className="flex gap-3 relative">
                    {i < PIPELINE.length - 1 && (
                      <span className={cn('absolute left-[19px] top-10 w-0.5 h-7 rounded-full transition-colors duration-500',
                        done || (hasResults && i < 6) ? 'bg-gradient-to-b from-emerald-500/60 to-emerald-500/15' : 'bg-slate-800')} />
                    )}

                    <div className={cn(
                      'w-10 h-10 rounded-xl shrink-0 flex items-center justify-center border transition-all duration-400',
                      active ? 'bg-blue-500/20 border-blue-500 shadow-[0_0_20px_rgba(59,130,246,0.4)]'
                        : done || (hasResults && i < 6) ? 'bg-emerald-500/15 border-emerald-500/45'
                        : 'bg-slate-900 border-slate-800'
                    )}>
                      {done || (hasResults && i < 6) ? <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                        : active ? <motion.span animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 2, ease: 'linear' }}>
                            <Icon className="w-5 h-5 text-blue-400" /></motion.span>
                        : <Icon className="w-5 h-5 text-slate-600" />}
                    </div>

                    <div className="pb-5 pt-1 flex-1 min-w-0">
                      <h4 className={cn('font-poppins font-semibold text-[12.5px] leading-tight',
                        active ? 'text-white' : done || (hasResults && i < 6) ? 'text-emerald-300' : 'text-slate-500')}>
                        {s.title}
                      </h4>
                      <p className="text-[10.5px] text-slate-600 leading-tight mt-0.5">{s.description}</p>
                    </div>
                  </li>
                );
              })}
            </ol>

            {globalResult && (
              <motion.div {...MOTION.scaleIn()} className="relative z-10 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-center">
                <CheckCircle2 className="w-6 h-6 text-emerald-400 mx-auto mb-1" />
                <p className="text-[11px] font-bold text-emerald-300 font-mono">ANALYSIS COMPLETE</p>
                <p className="text-[10px] text-emerald-400/70">Risk Score: {globalResult.results.risk_score}/100</p>
              </motion.div>
            )}
          </GlassCard>

          <GlassCard accent="emerald" {...MOTION.fadeUp(0.15)} className="overflow-hidden">
            <CardOrb accent="emerald" position="-bottom-16 -right-16" />
            <CardHeader title="Security Guarantees" icon={ShieldCheck} accent="emerald" />
            <div className="space-y-3 relative z-10">
              {[
                { icon: Lock,       accent: 'emerald' as const, title: 'End-to-End Encrypted',        text: 'TLS 1.3 in transit, AES-256 at rest. Keys held in Cyberdome HSM.' },
                { icon: HardDrive,  accent: 'blue'    as const, title: 'Secure Evidence Storage',      text: 'Immutable write-once storage with hash-chained ledger.' },
                { icon: Users,      accent: 'purple'  as const, title: 'Authorized Investigators Only',text: 'Role-based access with YubiKey MFA and full audit logging.' }
              ].map(item => {
                const Icon = item.icon;
                return (
                  <div key={item.title} className={cn(
                    'flex items-start gap-3 p-3 rounded-xl border transition-colors',
                    item.accent === 'emerald' && 'bg-emerald-950/20 border-emerald-500/20 hover:border-emerald-500/40',
                    item.accent === 'blue'    && 'bg-blue-950/20 border-blue-500/20 hover:border-blue-500/40',
                    item.accent === 'purple'  && 'bg-purple-950/20 border-purple-500/20 hover:border-purple-500/40'
                  )}>
                    <Icon className={cn('w-5 h-5 shrink-0 mt-0.5',
                      item.accent === 'emerald' && 'text-emerald-400',
                      item.accent === 'blue' && 'text-blue-400',
                      item.accent === 'purple' && 'text-purple-400')} />
                    <div className="min-w-0">
                      <h4 className="text-[12.5px] font-semibold text-slate-100">{item.title}</h4>
                      <p className="text-[10.5px] text-slate-500 mt-0.5 leading-relaxed">{item.text}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </GlassCard>
        </div>
      </div>

      {/* Blockchain Evidence Locker - Feature 3 */}
      <GlassCard accent="blue" {...MOTION.fadeUp(0.2)}>
        <CardHeader title="Blockchain Evidence Locker (65B)" icon={ShieldCheck} accent="blue" right={<Badge accent="emerald" size="xs" dot>BLOCKCHAIN NOTARIZED</Badge>}/>
        <p className="text-xs text-slate-500 -mt-2 mb-4">Every uploaded file is auto-hashed (SHA-256) and notarized on Polygon blockchain + IPFS. Tamper-proof, court-admissible under Section 65B Indian Evidence Act. Verify anytime.</p>
        <BlockchainLedger />
        <div className="mt-4 flex flex-wrap gap-2">
          <Button size="sm" variant="secondary" icon={Hash} onClick={async ()=>{
            const h = await sha256Hex(`demo-${Date.now()}`);
            const tx = generateTxHash(h);
            saveToLedger({ hash: h, fileName: `demo_evidence_${Date.now()}.bin`, fileSize: '1.2 MB', timestamp: new Date().toLocaleString('en-IN'), isoTimestamp:new Date().toISOString(), officer:'DySP Rajesh V. Kumar', badge:'KP-CYD-042', caseId:'KPC-2026-8941', txHash: tx, blockNumber: Math.floor(8000000+Math.random()*500000), verified:true});
            window.dispatchEvent(new Event('storage'));
            location.reload();
          }}>Demo: Notarize Dummy Hash</Button>
          <span className="text-[11px] font-mono text-slate-600 flex items-center">QR on report auto-generated from this ledger • Real deploy uses Pinata + Polygon Amoy</span>
        </div>
      </GlassCard>

      <ActionBar
        left={
          <>
            <FileSearch className="w-4 h-4 text-blue-400 shrink-0" />
            <span>
              <span className="text-slate-200 font-bold">{readyFiles.length}</span> files ready
              <span className="text-purple-400 ml-2">
                · {CATEGORIES.find(c => c.id === category)?.label}
              </span>
            </span>
          </>
        }
      >
        <Button variant="secondary" size="lg" icon={X} onClick={() => { setFiles([]); setAnalyzing(false); setStep(0); onCancel?.(); }}>
          Cancel
        </Button>
        <Button
          size="lg"
          icon={Zap}
          iconRight={analyzing ? undefined : ArrowRight}
          loading={analyzing}
          disabled={!readyFiles.length || busy}
          onClick={startAnalysis}
        >
          {analyzing ? `Analyzing… ${Math.min(step + 1, PIPELINE.length)}/${PIPELINE.length}` : 'Analyze Evidence'}
        </Button>
      </ActionBar>
    </div>
  );
};