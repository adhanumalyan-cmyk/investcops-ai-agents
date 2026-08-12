import React from 'react';
import {
  CheckCircle2, Download, FileJson2, Share2, FileStack, UserSearch, Heart,
  Link2, AlertTriangle, Target, MessageSquare, Image, Video, FileText,
  FileAudio, MapPin, Users, Phone, Mail, AtSign, Monitor, Globe2,
  CalendarClock, Fingerprint, Zap, Lock, ArrowRight,
  Briefcase, BarChart4, UploadCloud, CircleDot, LucideIcon
} from 'lucide-react';
import { motion } from 'framer-motion';
import {
  PageHeader, GlassCard, CardHeader, CardOrb, Badge, Button, ActionBar,
  StatTile, EntityTag, TimelineItem, GraphNode, InfoRow,
  MOTION, AccentColor
} from '../ui';

/* ── Data ── */
const SUMMARY: { label: string; value: number; icon: LucideIcon; accent: AccentColor; suffix?: string; isRisk?: boolean; caption: string }[] = [
  { label: 'Evidence Files',      value: 8,  icon: FileStack,     accent: 'blue',    caption: 'All hash-verified' },
  { label: 'Suspects Identified', value: 2,  icon: UserSearch,    accent: 'amber',   caption: 'Cross-platform match' },
  { label: 'Victims Identified',  value: 1,  icon: Heart,         accent: 'emerald', caption: 'Minor — POCSO scope' },
  { label: 'Relationships Found', value: 14, icon: Link2,         accent: 'purple',  caption: '7 primary nodes' },
  { label: 'Risk Level',          value: 0,  icon: AlertTriangle, accent: 'red',     caption: 'Escalation confirmed', isRisk: true },
  { label: 'AI Confidence',       value: 96, icon: Target,        accent: 'emerald', suffix: '%', caption: 'CyberLLM v4.2' }
];

const EVIDENCE: { label: string; value: number; icon: LucideIcon; accent: AccentColor }[] = [
  { label: 'Total Messages', value: 3542, icon: MessageSquare, accent: 'blue' },
  { label: 'Images',         value: 52,   icon: Image,         accent: 'pink' },
  { label: 'Videos',         value: 14,   icon: Video,         accent: 'rose' },
  { label: 'Documents',      value: 31,   icon: FileText,      accent: 'amber' },
  { label: 'Audio Files',    value: 8,    icon: FileAudio,     accent: 'orange' },
  { label: 'Locations',      value: 5,    icon: MapPin,        accent: 'emerald' }
];

const ENTITIES: { category: string; icon: LucideIcon; accent: AccentColor; items: string[] }[] = [
  { category: 'Names',           icon: Users,         accent: 'blue',    items: ['Rahul Krishnan', 'Sneha M. Nair', 'Arjun V. Menon'] },
  { category: 'Phone Numbers',   icon: Phone,         accent: 'purple',  items: ['+91 98470 XXXXX', '+91 94002 XXXXX'] },
  { category: 'Email Addresses', icon: Mail,          accent: 'pink',    items: ['rahul.k@protonmail.com', 'sneha.nair2024@gmail.com'] },
  { category: 'Usernames',       icon: AtSign,        accent: 'amber',   items: ['@darkphoenix_04', '@sneha_nair_kl'] },
  { category: 'Devices',         icon: Monitor,       accent: 'emerald', items: ['Samsung S24 Ultra', 'iPhone 15 Pro'] },
  { category: 'IP Addresses',    icon: Globe2,        accent: 'red',     items: ['185.220.101.45', '103.253.144.12'] },
  { category: 'Locations',       icon: MapPin,        accent: 'cyan',    items: ['Kochi, Ernakulam', 'Kozhikode Beach Rd'] },
  { category: 'Dates',           icon: CalendarClock, accent: 'blue',    items: ['2026-06-10', '2026-06-16'] }
];

const TIMELINE: { date: string; title: string; description: string; severity: 'info' | 'warn' | 'critical'; icon: LucideIcon }[] = [
  { date: '10 June', title: 'Instagram Follow',              severity: 'info',     icon: CircleDot,     description: 'Suspect followed victim on Instagram from handle @darkphoenix_04 at 21:14 IST.' },
  { date: '11 June', title: 'WhatsApp Conversation Started', severity: 'info',     icon: CircleDot,     description: 'First message sent at 23:14 IST with disappearing-messages enabled.' },
  { date: '12 June', title: 'Images Shared',                 severity: 'warn',     icon: Zap,           description: '12 images shared — 4 contained EXIF location metadata (Kochi, Ernakulam).' },
  { date: '13 June', title: 'Location Matched',              severity: 'warn',     icon: Zap,           description: 'GPS coordinates from EXIF match suspect residence within 200m radius.' },
  { date: '15 June', title: 'Threat Message Detected',       severity: 'critical', icon: AlertTriangle, description: 'CyberLLM flagged explicit threat. Hostile intent score: 94/100.' },
  { date: '16 June', title: 'High Risk Behaviour Flagged',   severity: 'critical', icon: AlertTriangle, description: 'Escalation confirmed: stalking → threat → coercion. Risk upgraded to HIGH.' }
];

const GRAPH: { label: string; sublabel: string; accent: AccentColor }[] = [
  { label: 'Victim',       sublabel: 'Sneha M. Nair',          accent: 'emerald' },
  { label: 'Instagram',    sublabel: '@sneha_nair_kl',         accent: 'pink' },
  { label: 'Suspect',      sublabel: 'Rahul Krishnan',         accent: 'red' },
  { label: 'Phone Number', sublabel: '+91 98470 XXXXX',        accent: 'purple' },
  { label: 'Email',        sublabel: 'rahul.k@protonmail.com', accent: 'blue' },
  { label: 'Location',     sublabel: 'Kochi, Ernakulam',       accent: 'amber' },
  { label: 'Telegram',     sublabel: '@darkphoenix_04',        accent: 'cyan' }
];

interface Props {
  onGenerateReport?: () => void;
  onAnalyzeNew?: () => void;
}

export const InvestigationResultsView: React.FC<Props> = ({ onGenerateReport, onAnalyzeNew }) => (
  <div className="space-y-7">

    <PageHeader
      title="Investigation Results"
      subtitle="AI has successfully analyzed the uploaded digital evidence. All entities, timelines, and risk factors have been processed by NoteNext CyberLLM v4.2."
      icon={BarChart4}
      iconAccent="emerald"
      badge={<Badge accent="emerald" icon={CheckCircle2} glow>ANALYSIS COMPLETED</Badge>}
      actions={
        <>
          <Button variant="secondary" icon={Download}>Export PDF</Button>
          <Button variant="secondary" icon={FileJson2}>Download JSON</Button>
          <Button icon={Share2}>Share Report</Button>
        </>
      }
    />

    {/* ── Summary tiles ── */}
    <section aria-label="Investigation summary" className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
      {SUMMARY.map((c, i) => (
        c.isRisk ? (
          <motion.div key={c.label} {...MOTION.fadeUp(i * 0.06)} whileHover={{ y: -3 }}
            className="liquid-glass rounded-2xl border border-red-500/30 hover:border-red-500/60 p-4 transition-all duration-300 hover:shadow-[0_0_25px_rgba(239,68,68,0.22)] relative overflow-hidden">
            <div className="flex items-start justify-between mb-2 gap-2">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">{c.label}</span>
              <div className="w-9 h-9 rounded-xl bg-red-500/10 border border-red-500/30 flex items-center justify-center shrink-0">
                <AlertTriangle className="w-4 h-4 text-red-400" />
              </div>
            </div>
            <div className="flex items-baseline gap-2 flex-wrap">
              <h3 className="font-poppins font-extrabold text-2xl text-red-400">HIGH</h3>
              <Badge accent="red" size="xs" pulse>CRITICAL</Badge>
            </div>
            <p className="text-[11px] text-slate-500 font-mono mt-1">{c.caption}</p>
          </motion.div>
        ) : (
          <StatTile key={c.label} label={c.label} value={c.value} icon={c.icon}
            accent={c.accent} suffix={c.suffix} caption={c.caption} delay={i * 0.06} />
        )
      ))}
    </section>

    {/* ── Three-column workspace ── */}
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 lg:gap-6">

      {/* LEFT */}
      <div className="lg:col-span-3 space-y-5 lg:space-y-6 min-w-0">
        <GlassCard accent="blue" {...MOTION.fadeUp(0.1)}>
          <CardHeader title="Evidence Summary" icon={FileStack} accent="blue" />
          <div className="space-y-2">
            {EVIDENCE.map((e, i) => (
              <motion.div key={e.label} {...MOTION.slideLeft(0.15 + i * 0.05)}>
                <InfoRow
                  label={e.label}
                  icon={e.icon}
                  accent={e.accent}
                  value={<span className="font-mono tabular-nums">{e.value.toLocaleString()}</span>}
                />
              </motion.div>
            ))}
          </div>
        </GlassCard>

        <GlassCard accent="purple" {...MOTION.fadeUp(0.15)}>
          <CardHeader
            title="Extracted Entities" icon={Fingerprint} accent="purple"
            right={<Badge accent="purple" size="xs">{ENTITIES.reduce((s, g) => s + g.items.length, 0)}</Badge>}
          />
          <div className="space-y-3.5 max-h-[26rem] overflow-y-auto pr-1">
            {ENTITIES.map((g, i) => {
              const Icon = g.icon;
              return (
                <motion.div key={g.category} {...MOTION.fadeUp(0.2 + i * 0.05)} className="space-y-1.5">
                  <div className="flex items-center gap-1.5">
                    <Icon className={`w-3.5 h-3.5 ${{
                      blue: 'text-blue-400', purple: 'text-purple-400', pink: 'text-pink-400',
                      amber: 'text-amber-400', emerald: 'text-emerald-400', red: 'text-red-400',
                      cyan: 'text-cyan-400', rose: 'text-rose-400', orange: 'text-orange-400', slate: 'text-slate-400'
                    }[g.accent]}`} />
                    <span className="text-[10px] font-mono font-bold text-slate-500 uppercase tracking-wider">{g.category}</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {g.items.map(item => <EntityTag key={item} accent={g.accent}>{item}</EntityTag>)}
                  </div>
                </motion.div>
              );
            })}
          </div>
        </GlassCard>
      </div>

      {/* CENTER — Timeline */}
      <div className="lg:col-span-5 min-w-0">
        <GlassCard accent="blue" {...MOTION.fadeUp(0.12)} className="overflow-hidden h-full">
          <CardOrb accent="blue" position="-top-24 -left-24" size="w-64 h-64" />
          <CardOrb accent="purple" position="-bottom-24 -right-24" size="w-64 h-64" />
          <CardHeader
            title="Timeline Reconstruction" icon={CalendarClock} accent="blue"
            right={<span className="text-[10px] font-mono text-slate-500">{TIMELINE.length} events</span>}
          />
          <div className="relative z-10">
            {TIMELINE.map((e, i) => (
              <TimelineItem key={i} {...e} index={i} isLast={i === TIMELINE.length - 1} />
            ))}
          </div>
        </GlassCard>
      </div>

      {/* RIGHT */}
      <div className="lg:col-span-4 space-y-5 lg:space-y-6 min-w-0">
        <GlassCard accent="purple" {...MOTION.fadeUp(0.16)} className="overflow-hidden">
          <CardOrb accent="purple" />
          <CardHeader
            title="Relationship Graph" icon={Link2} accent="purple"
            right={<span className="text-[10px] font-mono text-purple-400 hidden sm:block">i2 Compatible</span>}
          />
          <div className="relative z-10 py-1">
            <svg className="absolute inset-0 w-full h-full pointer-events-none" aria-hidden="true">
              {GRAPH.slice(0, -1).map((_, i) => (
                <motion.line key={i}
                  x1="50%" y1={30 + i * 62} x2="50%" y2={64 + i * 62}
                  stroke="rgba(139,92,246,0.32)" strokeWidth="2" strokeDasharray="4 4"
                  initial={{ pathLength: 0, opacity: 0 }} animate={{ pathLength: 1, opacity: 1 }}
                  transition={{ delay: 0.3 + i * 0.1, duration: 0.5 }}
                />
              ))}
            </svg>
            <div className="space-y-3 relative z-10">
              {GRAPH.map((n, i) => (
                <div key={n.label} className="mx-6">
                  <GraphNode {...n} index={i} tag={`N${String(i + 1).padStart(2, '0')}`} />
                </div>
              ))}
            </div>
          </div>
        </GlassCard>
      </div>
    </div>

    <ActionBar
      left={<><Lock className="w-4 h-4 text-emerald-400 shrink-0" />
        <span>Case KPC-2026-8941 · <span className="text-red-400 font-bold">HIGH RISK</span> · Analysis Complete</span></>}
    >
      <Button variant="secondary" size="lg" icon={UploadCloud} onClick={onAnalyzeNew}>Analyze New Evidence</Button>
      <Button size="lg" icon={Briefcase} iconRight={ArrowRight} onClick={onGenerateReport}>Generate Investigation Report</Button>
    </ActionBar>
  </div>
);
