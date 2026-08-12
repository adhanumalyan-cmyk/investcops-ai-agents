import React, { useMemo, useCallback } from 'react';
import {
  Download, Printer, Share2, CheckCircle2, Briefcase, UserCheck, Shield,
  FileStack, Calendar, AlertTriangle, MessageSquare, Image, Video,
  FileText, FileAudio, MapPin, Users, Phone, Mail, AtSign, Monitor, Globe2,
  CalendarClock, Zap, ShieldAlert, Lock, QrCode, PenTool,
  Link2, CircleDot, ShieldCheck, Hash, Award, LucideIcon
} from 'lucide-react';
import { motion } from 'framer-motion';
import {
  PageHeader, GlassCard, SectionHeader, CardOrb, Badge, Button,
  StatTile, EntityTag, TimelineItem, GraphNode,
  MOTION, AccentColor, ACCENTS
} from '../ui';
import { cn } from '../../utils/cn';

/* ── QR placeholder (deterministic pattern) ── */
const QRCode: React.FC<{ size?: number }> = ({ size = 100 }) => {
  const grid = useMemo(() => {
    const n = 21;
    const g: boolean[][] = Array.from({ length: n }, (_, r) =>
      Array.from({ length: n }, (_, c) => ((r * 7 + c * 13 + (r ^ c)) % 5) < 2)
    );
    const finder = (r0: number, c0: number) => {
      for (let dr = 0; dr < 7; dr++) for (let dc = 0; dc < 7; dc++) {
        const border = dr === 0 || dr === 6 || dc === 0 || dc === 6;
        const inner = dr >= 2 && dr <= 4 && dc >= 2 && dc <= 4;
        g[r0 + dr][c0 + dc] = border || inner;
      }
    };
    finder(0, 0); finder(0, n - 7); finder(n - 7, 0);
    return g;
  }, []);

  const cs = size / 21;
  return (
    <svg width={size} height={size} className="rounded-lg bg-white p-1" role="img" aria-label="Report verification QR code">
      {grid.map((row, r) => row.map((on, c) =>
        on ? <rect key={`${r}-${c}`} x={c * cs} y={r * cs} width={cs} height={cs} fill="#0B1020" /> : null
      ))}
    </svg>
  );
};

/* ── Data ── */
const CASE_INFO: { label: string; value: string; icon: LucideIcon; accent: AccentColor; mono?: boolean }[] = [
  { label: 'Case ID',            value: 'INV-2026-001',                  icon: Briefcase,    accent: 'blue', mono: true },
  { label: 'Investigator',       value: 'Inspector Arjun Nair',          icon: UserCheck,    accent: 'purple' },
  { label: 'Case Type',          value: 'Child Protection Investigation',icon: Shield,       accent: 'pink' },
  { label: 'Evidence Uploaded',  value: '8 Files',                       icon: FileStack,    accent: 'amber' },
  { label: 'Investigation Date', value: '05 August 2026',                icon: Calendar,     accent: 'blue' },
  { label: 'Status',             value: 'Completed',                     icon: CheckCircle2, accent: 'emerald' },
  { label: 'Priority',           value: 'High',                          icon: AlertTriangle,accent: 'red' }
];

const EVIDENCE: { label: string; value: number; icon: LucideIcon; accent: AccentColor }[] = [
  { label: 'Messages',    value: 3542, icon: MessageSquare, accent: 'blue' },
  { label: 'Images',      value: 52,   icon: Image,         accent: 'pink' },
  { label: 'Videos',      value: 14,   icon: Video,         accent: 'rose' },
  { label: 'Documents',   value: 31,   icon: FileText,      accent: 'amber' },
  { label: 'Audio Files', value: 8,    icon: FileAudio,     accent: 'orange' },
  { label: 'Locations',   value: 5,    icon: MapPin,        accent: 'emerald' }
];

const ENTITIES: { category: string; icon: LucideIcon; accent: AccentColor; items: string[] }[] = [
  { category: 'Names',           icon: Users,         accent: 'blue',    items: ['Rahul Krishnan', 'Sneha M. Nair', 'Arjun V. Menon'] },
  { category: 'Phone Numbers',   icon: Phone,         accent: 'purple',  items: ['+91 98470 XXXXX', '+91 94002 XXXXX'] },
  { category: 'Email Addresses', icon: Mail,          accent: 'pink',    items: ['rahul.k@protonmail.com', 'sneha.nair2024@gmail.com'] },
  { category: 'Usernames',       icon: AtSign,        accent: 'amber',   items: ['@darkphoenix_04', '@sneha_nair_kl'] },
  { category: 'IP Addresses',    icon: Globe2,        accent: 'red',     items: ['185.220.101.45', '103.253.144.12'] },
  { category: 'Devices',         icon: Monitor,       accent: 'emerald', items: ['Samsung S24 Ultra', 'iPhone 15 Pro'] },
  { category: 'Locations',       icon: MapPin,        accent: 'cyan',    items: ['Kochi, Ernakulam', 'Kozhikode Beach Rd'] },
  { category: 'Dates',           icon: CalendarClock, accent: 'blue',    items: ['2026-06-10', '2026-06-16'] }
];

const TIMELINE: { date: string; title: string; description: string; severity: 'info' | 'warn' | 'critical'; icon: LucideIcon }[] = [
  { date: '10 Jun 2026', title: 'Instagram Follow',              severity: 'info',     icon: CircleDot,     description: 'Suspect account @darkphoenix_04 followed victim at 21:14 IST.' },
  { date: '11 Jun 2026', title: 'WhatsApp Conversation Started', severity: 'info',     icon: CircleDot,     description: 'First direct message at 23:14 IST with disappearing messages enabled.' },
  { date: '12 Jun 2026', title: 'Images Shared',                 severity: 'warn',     icon: Zap,           description: '12 images shared over 4 hours. 4 contained EXIF geolocation metadata.' },
  { date: '13 Jun 2026', title: 'Location Matched',              severity: 'warn',     icon: Zap,           description: 'EXIF GPS matched suspect residence within 200m radius.' },
  { date: '15 Jun 2026', title: 'Threat Message Detected',       severity: 'critical', icon: AlertTriangle, description: 'CyberLLM flagged explicit threat. Hostile intent score 94/100.' },
  { date: '16 Jun 2026', title: 'High Risk Behaviour Identified',severity: 'critical', icon: AlertTriangle, description: 'Behavioural escalation confirmed. Case elevated to HIGH RISK.' }
];

const GRAPH: { label: string; sublabel: string; accent: AccentColor }[] = [
  { label: 'Victim',       sublabel: 'Sneha M. Nair (Minor)',  accent: 'emerald' },
  { label: 'Instagram',    sublabel: '@sneha_nair_kl',         accent: 'pink' },
  { label: 'Suspect',      sublabel: 'Rahul Krishnan',         accent: 'red' },
  { label: 'Phone Number', sublabel: '+91 98470 XXXXX',        accent: 'purple' },
  { label: 'Email',        sublabel: 'rahul.k@protonmail.com', accent: 'blue' },
  { label: 'Telegram',     sublabel: '@darkphoenix_04',        accent: 'cyan' },
  { label: 'Location',     sublabel: 'Kochi, Ernakulam',       accent: 'amber' }
];

export const ReportsView: React.FC = () => {
  const handlePrint = useCallback(() => window.print(), []);

  return (
    <div className="space-y-7">

      <div data-print-hide>
        <PageHeader
          title="Investigation Report"
          subtitle="AI-Generated Investigation Summary — compiled by NoteNext CyberLLM v4.2 with ISO 27037 chain-of-custody validation and Section 65B digital evidence certification."
          icon={FileText}
          iconAccent="blue"
          badge={<Badge accent="emerald" icon={CheckCircle2} glow>REPORT GENERATED SUCCESSFULLY</Badge>}
          actions={
            <>
              <Button variant="secondary" icon={Download}>Download PDF</Button>
              <Button variant="secondary" icon={Printer} onClick={handlePrint}>Print Report</Button>
              <Button icon={Share2}>Share Report</Button>
            </>
          }
        />
      </div>

      {/* ── Official letterhead ── */}
      <motion.div {...MOTION.fadeUp()} className="print-block liquid-glass border border-blue-500/30 rounded-2xl p-5 relative overflow-hidden">
        <div className="absolute top-2 right-4 opacity-[0.06] pointer-events-none" aria-hidden="true">
          <Award className="w-40 h-40 text-blue-400" />
        </div>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 relative z-10">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-blue-600 to-purple-600 p-0.5 shadow-[0_0_20px_rgba(59,130,246,0.4)] shrink-0">
              <div className="w-full h-full bg-[#0B1020]/90 rounded-[14px] flex items-center justify-center">
                <ShieldCheck className="w-6 h-6 text-blue-400" />
              </div>
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-poppins font-bold text-base nn-text-gradient tracking-wide uppercase">NoteNext Intelligence Lab</span>
                <Badge accent="blue" size="xs">OFFICIAL FORENSIC DOSSIER</Badge>
              </div>
              <p className="text-[10px] text-slate-500 font-mono mt-0.5 uppercase tracking-wider">
                Section 65B Digital Evidence Certificate · ISO 27037 Validated · Connected Backend
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4 text-[10.5px] font-mono shrink-0">
            <div className="text-right">
              <span className="block text-slate-500">Report Reference</span>
              <span className="text-blue-400 font-bold">RPT-2026-INV-001</span>
            </div>
            <div className="w-px h-8 bg-slate-800" />
            <div className="text-right">
              <span className="block text-slate-500">Classification</span>
              <span className="text-red-400 font-bold flex items-center gap-1 justify-end">
                <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />RESTRICTED / L5
              </span>
            </div>
          </div>
        </div>
      </motion.div>

      {/* 01 — Case Information */}
      <section className="print-block">
        <SectionHeader title="Case Information" number="01" accent="blue" divider />
        <GlassCard accent="blue" className="overflow-hidden">
          <CardOrb accent="blue" />
          <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-7 gap-3 relative z-10">
            {CASE_INFO.map((info, i) => {
              const Icon = info.icon;
              const a = ACCENTS[info.accent];
              return (
                <motion.div key={info.label} {...MOTION.fadeUp(i * 0.04)}
                  className={cn('p-3 rounded-xl bg-white/[0.04] border space-y-1.5', a.border)}>
                  <div className="flex items-center gap-1.5">
                    <Icon className={cn('w-3.5 h-3.5 shrink-0', a.text)} />
                    <span className="text-[9.5px] font-mono text-slate-500 uppercase tracking-wider truncate">{info.label}</span>
                  </div>
                  <p className={cn('text-[12.5px] font-bold leading-tight',
                    info.mono ? 'font-mono text-blue-300' : 'font-poppins text-white')}>
                    {info.value}
                  </p>
                </motion.div>
              );
            })}
          </div>
        </GlassCard>
      </section>

      {/* 02 — Evidence Summary */}
      <section className="print-block">
        <SectionHeader title="Evidence Summary" number="02" accent="purple" divider />
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
          {EVIDENCE.map((e, i) => (
            <StatTile key={e.label} label={e.label} value={e.value} icon={e.icon} accent={e.accent} delay={i * 0.05} />
          ))}
        </div>
      </section>

      {/* 03 — Extracted Entities */}
      <section className="print-block">
        <SectionHeader
          title="Extracted Entities" number="03" accent="pink" divider
          badge={<Badge accent="purple" size="xs">{ENTITIES.reduce((s, g) => s + g.items.length, 0)} across {ENTITIES.length} categories</Badge>}
        />
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          {ENTITIES.map((g, i) => {
            const Icon = g.icon;
            const a = ACCENTS[g.accent];
            return (
              <GlassCard key={g.category} accent={g.accent} padding="sm" {...MOTION.scaleIn(i * 0.05)}>
                <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-3">
                  <div className="flex items-center gap-2 min-w-0">
                    <div className={cn('w-7 h-7 rounded-lg border flex items-center justify-center shrink-0', a.bg, a.border)}>
                      <Icon className={cn('w-3.5 h-3.5', a.text)} />
                    </div>
                    <h4 className="font-poppins font-bold text-[13px] text-white truncate">{g.category}</h4>
                  </div>
                  <Badge accent={g.accent} size="xs">{g.items.length}</Badge>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {g.items.map(item => <EntityTag key={item} accent={g.accent}>{item}</EntityTag>)}
                </div>
              </GlassCard>
            );
          })}
        </div>
      </section>

      {/* 04 + 05 — Timeline & Graph */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 lg:gap-6">
        <section className="print-block">
          <SectionHeader title="Timeline Reconstruction" number="04" accent="blue" />
          <GlassCard accent="blue" className="overflow-hidden h-full">
            <CardOrb accent="blue" position="-top-24 -left-24" size="w-64 h-64" />
            <CardOrb accent="purple" position="-bottom-24 -right-24" size="w-64 h-64" />
            <div className="relative z-10">
              {TIMELINE.map((e, i) => (
                <TimelineItem key={i} {...e} index={i} isLast={i === TIMELINE.length - 1} />
              ))}
            </div>
          </GlassCard>
        </section>

        <section className="print-block">
          <SectionHeader
            title="Relationship Graph" number="05" accent="purple"
            right={<span className="text-[10px] font-mono text-purple-400 flex items-center gap-1"><Link2 className="w-3 h-3" /> Interactive Topology</span>}
          />
          <GlassCard accent="purple" className="overflow-hidden h-full">
            <CardOrb accent="purple" />
            <div className="relative z-10 py-1">
              <svg className="absolute inset-0 w-full h-full pointer-events-none" aria-hidden="true">
                {GRAPH.slice(0, -1).map((_, i) => (
                  <motion.line key={i}
                    x1="50%" y1={30 + i * 62} x2="50%" y2={64 + i * 62}
                    stroke="rgba(139,92,246,0.35)" strokeWidth="2" strokeDasharray="4 4"
                    initial={{ pathLength: 0, opacity: 0 }} animate={{ pathLength: 1, opacity: 1 }}
                    transition={{ delay: 0.3 + i * 0.1, duration: 0.5 }}
                  />
                ))}
              </svg>
              <div className="space-y-3 relative z-10">
                {GRAPH.map((n, i) => (
                  <div key={n.label} className="mx-5">
                    <GraphNode {...n} index={i} tag={`N·${String(i + 1).padStart(2, '0')}`} />
                  </div>
                ))}
              </div>
            </div>
          </GlassCard>
        </section>
      </div>

      {/* ── Footer: signature + QR ── */}
      <motion.section {...MOTION.fadeUp(0.3)}
        className="print-block liquid-glass border border-blue-500/25 rounded-2xl p-6 relative overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-96 h-40 bg-gradient-to-b from-blue-600/10 to-transparent blur-3xl pointer-events-none" aria-hidden="true" />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative z-10 items-center">
          {/* Branding */}
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-blue-600 to-purple-600 p-0.5 shadow-[0_0_20px_rgba(59,130,246,0.4)] shrink-0">
                <div className="w-full h-full bg-[#0B1020] rounded-[14px] flex items-center justify-center">
                  <ShieldAlert className="w-6 h-6 text-blue-400" />
                </div>
              </div>
              <div>
                <p className="text-[9.5px] font-mono text-slate-500 uppercase">Generated by</p>
                <h3 className="font-poppins font-extrabold text-lg text-white leading-tight">
                  NoteNext<span className="text-blue-500">.AI</span>
                </h3>
              </div>
            </div>
            <p className="text-[11.5px] text-slate-400 leading-relaxed">Agentic Child Protection Investigation Assistant</p>
            <p className="text-[12px] font-poppins italic text-purple-300 font-semibold">"From Evidence to Intelligence"</p>
          </div>

          {/* Digital signature */}
          <div className="bg-[#0B1020]/80 border border-slate-800 rounded-xl p-4 space-y-2">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
              <PenTool className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-[9.5px] font-mono font-bold text-slate-400 uppercase tracking-wider">Digital Signature</span>
            </div>
            <div className="text-center py-1">
              <p className="text-xl text-blue-300 italic" style={{ fontFamily: '"Brush Script MT", "Segoe Script", cursive' }}>Arjun Nair</p>
              <div className="w-full h-px bg-slate-700 my-1.5" />
              <p className="text-[10px] font-mono text-slate-400">Inspector Arjun Nair</p>
              <p className="text-[9px] font-mono text-slate-600">NoteNext Lab · Badge NN-042</p>
            </div>
            <div className="flex items-center gap-1.5 pt-1 border-t border-slate-800">
              <Hash className="w-3 h-3 text-emerald-400 shrink-0" />
              <span className="text-[9px] font-mono text-emerald-400 truncate">SHA-256: e3b0c44298fc1c14…b7852b855</span>
            </div>
          </div>

          {/* QR verification */}
          <div className="flex items-center gap-4 md:justify-end">
            <div className="text-right min-w-0">
              <div className="flex items-center md:justify-end gap-1.5 mb-1">
                <QrCode className="w-3.5 h-3.5 text-blue-400" />
                <span className="text-[9.5px] font-mono font-bold text-slate-400 uppercase tracking-wider">Scan to Verify</span>
              </div>
              <p className="text-[10px] font-mono text-slate-500">Report ID: <span className="text-blue-400 font-bold">RPT-2026-INV-001</span></p>
              <p className="text-[9.5px] font-mono text-slate-600 mt-0.5">cyberdome.kerala.gov.in/verify</p>
              <div className="flex items-center md:justify-end gap-1 mt-2">
                <Lock className="w-3 h-3 text-emerald-400 shrink-0" />
                <span className="text-[9px] font-mono text-emerald-400">Blockchain notarized</span>
              </div>
            </div>
            <div className="shrink-0 p-2 rounded-xl bg-[#0B1020] border border-blue-500/30 shadow-[0_0_20px_rgba(59,130,246,0.18)]">
              <QRCode size={96} />
            </div>
          </div>
        </div>

        <div className="mt-6 pt-4 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-2 text-[9.5px] font-mono text-slate-500">
          <span className="flex items-center gap-2">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            ISO 27037 Compliant · Section 65B Certified · Court-Admissible
          </span>
          <span className="flex items-center gap-3">
            <span>Report v1.0 · 05 Aug 2026 14:32 IST</span>
            <span className="hidden sm:inline">·</span>
            <span className="text-red-400">RESTRICTED / L5 CLEARANCE</span>
          </span>
        </div>
      </motion.section>
    </div>
  );
};
