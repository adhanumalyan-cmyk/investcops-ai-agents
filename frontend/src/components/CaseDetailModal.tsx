import React, { useState, useEffect, useCallback } from 'react';
import {
  X, ShieldAlert, Download, Lock, Sparkles, UserCheck, Network,
  FileText, Copy, Check, MapPin, Activity, Layers
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { CaseItem } from '../types/investigation';
import { Badge, Button, AccentColor } from './ui';
import { cn } from '../utils/cn';

type Tab = 'overview' | 'graph' | 'iocs';

const TABS: { id: Tab; label: string; icon: typeof FileText; accent: AccentColor }[] = [
  { id: 'overview', label: 'Intelligence Overview', icon: FileText,    accent: 'blue' },
  { id: 'graph',    label: 'Suspect Network',       icon: Network,     accent: 'purple' },
  { id: 'iocs',     label: 'Matched IOCs',          icon: ShieldAlert, accent: 'amber' }
];

interface Props {
  caseItem: CaseItem | null;
  onClose: () => void;
  onGenerateReport?: (c: CaseItem) => void;
}

export const CaseDetailModal: React.FC<Props> = ({ caseItem, onClose, onGenerateReport }) => {
  const [copied, setCopied] = useState(false);
  const [tab, setTab] = useState<Tab>('overview');

  /* Escape to close + lock body scroll */
  useEffect(() => {
    if (!caseItem) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', onKey);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = '';
    };
  }, [caseItem, onClose]);

  const copy = useCallback((text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, []);

  return (
    <AnimatePresence>
      {caseItem && (
        <motion.div
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
          onClick={onClose}
          role="dialog" aria-modal="true" aria-label={`Case ${caseItem.id}`}
          className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/80 backdrop-blur-md overflow-y-auto"
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: 18 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 18 }}
            transition={{ type: 'spring', stiffness: 300, damping: 28 }}
            onClick={e => e.stopPropagation()}
            className="liquid-glass border border-[rgba(59,130,246,0.3)] rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden shadow-[0_0_60px_rgba(59,130,246,0.22)] flex flex-col my-auto"
          >
            {/* Header */}
            <div className="p-5 sm:p-6 bg-white/[0.04] border-b border-[rgba(51,65,85,0.4)] flex items-start justify-between gap-4">
              <div className="min-w-0 space-y-1">
                <div className="flex items-center gap-2 flex-wrap text-[11px] font-mono">
                  <Badge accent="blue" size="xs">{caseItem.id}</Badge>
                  <span className="text-purple-400 font-semibold">{caseItem.category}</span>
                  <span className="text-slate-600">·</span>
                  <span className="text-slate-500 flex items-center gap-1">
                    <MapPin className="w-3 h-3 text-red-400" />{caseItem.location}
                  </span>
                </div>
                <h2 className="font-poppins font-bold text-lg sm:text-xl text-white leading-tight">{caseItem.name}</h2>
                <p className="text-[11px] text-slate-500 font-mono">
                  Assigned: <span className="text-slate-300 font-bold">{caseItem.assignedOfficer}</span>
                </p>
              </div>
              <button onClick={onClose} aria-label="Close dialog"
                className="p-2 rounded-xl bg-white/[0.06] hover:bg-white/[0.12] text-slate-400 hover:text-white transition-colors shrink-0 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/60">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Tabs */}
            <div className="px-5 sm:px-6 bg-white/[0.025] border-b border-[rgba(51,65,85,0.4)] flex items-center gap-4 overflow-x-auto" role="tablist">
              {TABS.map(t => {
                const Icon = t.icon;
                const active = tab === t.id;
                return (
                  <button key={t.id} role="tab" aria-selected={active} onClick={() => setTab(t.id)}
                    className={cn('py-3 border-b-2 text-[11.5px] font-mono font-bold flex items-center gap-1.5 whitespace-nowrap transition-all',
                      active
                        ? t.accent === 'blue' ? 'border-blue-500 text-blue-400'
                          : t.accent === 'purple' ? 'border-purple-500 text-purple-400'
                          : 'border-amber-500 text-amber-400'
                        : 'border-transparent text-slate-500 hover:text-slate-200')}>
                    <Icon className="w-3.5 h-3.5" />{t.label}
                    {t.id === 'iocs' && <span className="opacity-70">({caseItem.iocs.length})</span>}
                  </button>
                );
              })}
            </div>

            {/* Body */}
            <div className="p-5 sm:p-6 overflow-y-auto flex-1">
              {tab === 'overview' && (
                <div className="space-y-5">
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {[
                      { icon: null, label: 'AI Risk Rating', value: `${caseItem.risk} SEVERITY`, big: String(caseItem.riskScore), accent: 'red' as const },
                      { icon: Activity, label: 'Current Status', value: caseItem.status, accent: 'blue' as const },
                      { icon: Layers, label: 'Evidence Objects', value: `${caseItem.evidenceCount} Files Vaulted`, accent: 'purple' as const }
                    ].map(item => (
                      <div key={item.label} className={cn('p-4 rounded-xl bg-white/[0.04] border flex items-center gap-3',
                        item.accent === 'red' ? 'border-red-500/30' : item.accent === 'blue' ? 'border-blue-500/30' : 'border-purple-500/30')}>
                        <div className={cn('w-11 h-11 rounded-xl border flex items-center justify-center shrink-0 font-mono font-bold',
                          item.accent === 'red' ? 'bg-red-500/15 border-red-500/40 text-red-400'
                            : item.accent === 'blue' ? 'bg-blue-500/15 border-blue-500/40 text-blue-400'
                            : 'bg-purple-500/15 border-purple-500/40 text-purple-400')}>
                          {item.big ? item.big : item.icon ? <item.icon className="w-5 h-5" /> : null}
                        </div>
                        <div className="min-w-0">
                          <span className="text-[9.5px] text-slate-500 uppercase font-mono block">{item.label}</span>
                          <h4 className={cn('text-[12.5px] font-bold font-poppins truncate',
                            item.accent === 'red' ? 'text-red-400' : item.accent === 'blue' ? 'text-blue-300' : 'text-purple-300')}>
                            {item.value}
                          </h4>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="p-4 rounded-2xl bg-white/[0.04] border border-white/[0.08] space-y-2">
                    <div className="flex items-center justify-between gap-2">
                      <h3 className="font-poppins font-bold text-[13px] text-slate-200 flex items-center gap-2">
                        <Sparkles className="w-4 h-4 text-purple-400" /> AI Executive Threat Summary
                      </h3>
                      <span className="text-[9.5px] font-mono text-emerald-400 shrink-0">CyberLLM v4.2</span>
                    </div>
                    <p className="text-[12.5px] text-slate-400 leading-relaxed">{caseItem.summary}</p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div className="p-4 rounded-2xl bg-white/[0.04] border border-white/[0.08] space-y-1.5">
                      <span className="text-[9.5px] text-slate-500 uppercase font-mono font-bold">Primary Attack Vector</span>
                      <p className="text-[13px] text-slate-200 font-semibold">{caseItem.primaryVector}</p>
                    </div>
                    <div className="p-4 rounded-2xl bg-white/[0.04] border border-white/[0.08] space-y-2">
                      <span className="text-[9.5px] text-slate-500 uppercase font-mono font-bold flex items-center gap-1">
                        <UserCheck className="w-3 h-3 text-amber-400" /> Linked Suspect Entities
                      </span>
                      <div className="space-y-1">
                        {caseItem.suspects.map(s => (
                          <div key={s} className="text-[11px] font-mono text-amber-300 font-bold bg-amber-950/30 px-2.5 py-1 rounded border border-amber-500/20">{s}</div>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="p-4 rounded-2xl bg-white/[0.04] border border-white/[0.08] space-y-2">
                    <div className="flex items-center justify-between text-[9.5px] font-mono">
                      <span className="text-slate-500 uppercase font-bold flex items-center gap-1">
                        <Lock className="w-3 h-3 text-emerald-400" /> Chain of Custody Hash (SHA-256)
                      </span>
                      <span className="text-emerald-400">ISO 27037 VALIDATED</span>
                    </div>
                    <div className="flex items-center justify-between gap-2 p-2.5 bg-black/30 rounded-xl border border-white/[0.1]">
                      <span className="text-[11px] font-mono text-blue-300 font-bold truncate">{caseItem.hashChain}</span>
                      <button onClick={() => copy(caseItem.hashChain)} aria-label="Copy hash"
                        className="p-1.5 rounded-lg bg-white/[0.06] hover:bg-white/[0.12] text-slate-400 shrink-0 transition-colors">
                        {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {tab === 'graph' && (
                <div className="p-5 rounded-2xl bg-white/[0.04] border border-purple-500/30 space-y-5">
                  <div className="flex items-center justify-between text-[11px] font-mono text-slate-500 border-b border-slate-800 pb-3">
                    <span>Interactive Node Neural Topology</span>
                    <span className="text-purple-400 flex items-center gap-1"><Network className="w-3.5 h-3.5" /> i2 Compatible</span>
                  </div>
                  <div className="relative h-64 bg-black/40 rounded-2xl border border-white/[0.08] overflow-hidden cyber-grid">
                    <svg className="absolute inset-0 w-full h-full stroke-blue-500/25" strokeWidth={2} aria-hidden="true">
                      <line x1="50%" y1="50%" x2="25%" y2="25%" strokeDasharray="4" />
                      <line x1="50%" y1="50%" x2="75%" y2="25%" />
                      <line x1="50%" y1="50%" x2="30%" y2="75%" />
                      <line x1="50%" y1="50%" x2="70%" y2="75%" strokeDasharray="4" />
                    </svg>
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 p-3 rounded-2xl bg-red-500/20 border-2 border-red-500 shadow-[0_0_25px_rgba(239,68,68,0.4)] flex flex-col items-center gap-1">
                      <ShieldAlert className="w-5 h-5 text-red-400 animate-pulse" />
                      <span className="text-[9.5px] font-mono font-bold text-red-300">{caseItem.id}</span>
                    </div>
                    {[
                      { pos: 'top-[22%] left-[18%]', label: 'C2 IP Node', accent: 'purple' },
                      { pos: 'top-[22%] right-[18%]', label: 'Crypto Wallet', accent: 'amber' },
                      { pos: 'bottom-[22%] left-[24%]', label: 'Bot Handler', accent: 'blue' },
                      { pos: 'bottom-[22%] right-[24%]', label: 'Mule Account', accent: 'emerald' }
                    ].map(n => (
                      <div key={n.label} className={cn('absolute p-2 rounded-xl border text-[9.5px] font-mono font-bold', n.pos,
                        n.accent === 'purple' ? 'bg-purple-500/20 border-purple-500/50 text-purple-300'
                          : n.accent === 'amber' ? 'bg-amber-500/20 border-amber-500/50 text-amber-300'
                          : n.accent === 'blue' ? 'bg-blue-500/20 border-blue-500/50 text-blue-300'
                          : 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300')}>
                        {n.label}
                      </div>
                    ))}
                  </div>
                  <p className="text-[11px] text-slate-500 font-mono text-center">
                    Autonomous graph clustering identified 4 linked incidents across state borders.
                  </p>
                </div>
              )}

              {tab === 'iocs' && (
                <div className="p-4 rounded-2xl bg-white/[0.04] border border-white/[0.08] space-y-3">
                  <h4 className="font-poppins font-bold text-[13px] text-slate-200">Indicators of Compromise Catalog</h4>
                  <ul className="space-y-2">
                    {caseItem.iocs.map(ioc => (
                       <li key={ioc} className="p-3 bg-white/[0.04] rounded-xl border border-white/[0.1] flex items-center justify-between gap-3">
                        <span className="text-[11.5px] font-mono text-blue-400 font-bold truncate">{ioc}</span>
                        <Badge accent="red" size="xs">BLACKLISTED</Badge>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-4 sm:p-5 bg-white/[0.03] border-t border-white/[0.08] flex flex-wrap items-center justify-between gap-3">
              <span className="text-[10.5px] font-mono text-slate-500 flex items-center gap-2">
                <Lock className="w-3.5 h-3.5 text-emerald-400" /> Enclave access logged
              </span>
              <Button size="lg" icon={Download}
                onClick={() => { onGenerateReport?.(caseItem); onClose(); }}>
                Export Court Dossier
              </Button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
