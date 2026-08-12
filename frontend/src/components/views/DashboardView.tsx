import React from 'react';
import {
  LayoutDashboard, ShieldCheck, UploadCloud, Bot, FileText, LineChart,
  Activity, Cpu, Zap, TrendingUp, Clock, ArrowRight, CircleDot,
  AlertTriangle, CheckCircle2, Database, LucideIcon
} from 'lucide-react';
import { motion } from 'framer-motion';
import {
  PageHeader, GlassCard, CardHeader, CardOrb, Badge,
  StatTile, ProgressBar, MOTION, AccentColor, AnimatedCounter
} from '../ui';
import { RecentInvestigationsTable } from '../RecentInvestigationsTable';
import { CaseItem } from '../../types/investigation';
import { cn } from '../../utils/cn';

interface DashboardStat {
  label: string; value: number; icon: LucideIcon; accent: AccentColor;
  caption: string; trend: string; route: string;
}

interface DashboardViewProps {
  stats: DashboardStat[];
  cases: CaseItem[];
  onNavigate: (route: string) => void;
  onSelectCase: (c: CaseItem) => void;
}

const QUICK_ACTIONS: { label: string; description: string; icon: LucideIcon; accent: AccentColor; route: string }[] = [
  { label: 'Upload Evidence',   description: 'Ingest new digital artifacts', icon: UploadCloud, accent: 'blue',    route: 'upload' },
  { label: 'Run AI Analysis',   description: 'Launch agent pipeline',        icon: Bot,         accent: 'purple',  route: 'ai-processing' },
  { label: 'View Results',      description: 'Entities & timelines',         icon: FileText,    accent: 'emerald', route: 'results' },
  { label: 'Generate Report',   description: 'Court-ready dossier',          icon: FileText,    accent: 'amber',   route: 'reports' }
];

const RECENT_ACTIVITY: { text: string; time: string; accent: AccentColor; icon: LucideIcon }[] = [
  { text: 'Report generated for KPC-2026-8890',        time: '4 min ago',  accent: 'emerald', icon: CheckCircle2 },
  { text: 'Risk score recalculated — 96/100 CRITICAL', time: '12 min ago', accent: 'red',     icon: AlertTriangle },
  { text: 'Timeline reconstructed — 847 events',       time: '28 min ago', accent: 'blue',    icon: Clock },
  { text: 'Entity extraction completed — 86 entities', time: '41 min ago', accent: 'purple',  icon: Database },
  { text: 'Evidence uploaded — 8 files verified',      time: '1 hr ago',   accent: 'blue',    icon: UploadCloud }
];

const AI_AGENTS: { name: string; load: number; accent: AccentColor }[] = [
  { name: 'Evidence Analysis',  load: 94, accent: 'emerald' },
  { name: 'Entity Extraction',  load: 87, accent: 'blue' },
  { name: 'Risk Assessment',    load: 78, accent: 'purple' },
  { name: 'Report Generation',  load: 62, accent: 'amber' }
];

const CASE_BREAKDOWN: { label: string; value: number; accent: AccentColor }[] = [
  { label: 'Crypto Fraud',    value: 38, accent: 'blue' },
  { label: 'Ransomware',      value: 24, accent: 'purple' },
  { label: 'Deepfake / AI',   value: 18, accent: 'purple' },
  { label: 'Banking Trojans', value: 12, accent: 'amber' },
  { label: 'Data Leaks',      value: 8,  accent: 'emerald' }
];

const accentTextMap: Record<AccentColor, string> = {
  blue: 'text-blue-400', purple: 'text-purple-400', emerald: 'text-emerald-400',
  amber: 'text-amber-400', red: 'text-red-400', pink: 'text-pink-400',
  rose: 'text-rose-400', cyan: 'text-cyan-400', orange: 'text-orange-400', slate: 'text-slate-400'
};

const accentBorderMap: Record<AccentColor, string> = {
  blue: 'border-blue-500/20 hover:border-blue-500/55', purple: 'border-purple-500/20 hover:border-purple-500/55',
  emerald: 'border-emerald-500/20 hover:border-emerald-500/55', amber: 'border-amber-500/20 hover:border-amber-500/55',
  red: 'border-red-500/20', pink: 'border-pink-500/20', rose: 'border-rose-500/20',
  cyan: 'border-cyan-500/20', orange: 'border-orange-500/20', slate: 'border-slate-700'
};

const accentGlowMap: Record<AccentColor, string> = {
  blue: 'hover:shadow-[0_0_28px_rgba(59,130,246,0.22)]', purple: 'hover:shadow-[0_0_28px_rgba(139,92,246,0.22)]',
  emerald: 'hover:shadow-[0_0_28px_rgba(16,185,129,0.22)]', amber: 'hover:shadow-[0_0_28px_rgba(245,158,11,0.22)]',
  red: '', pink: '', rose: '', cyan: '', orange: '', slate: ''
};

const accentIconMap: Record<AccentColor, string> = {
  blue: 'bg-blue-500/15 border-blue-500/30', purple: 'bg-purple-500/15 border-purple-500/30',
  emerald: 'bg-emerald-500/15 border-emerald-500/30', amber: 'bg-amber-500/15 border-amber-500/30',
  red: 'bg-red-500/15 border-red-500/30', pink: 'bg-pink-500/15 border-pink-500/30',
  rose: 'bg-rose-500/15 border-rose-500/30', cyan: 'bg-cyan-500/15 border-cyan-500/30',
  orange: 'bg-orange-500/15 border-orange-500/30', slate: 'bg-slate-500/10 border-slate-700'
};

export const DashboardView: React.FC<DashboardViewProps> = ({ stats, cases, onNavigate, onSelectCase }) => (
  <div className="space-y-7">
    <PageHeader
      title="Investigation Overview"
      subtitle="Real-time cyber threat posture across all active Kerala Police Cyberdome investigations. National Cyber Crime Portal feed synchronized."
      icon={LayoutDashboard} iconAccent="blue"
      badge={<Badge accent="blue" icon={Zap} glow>CYBERLLM v4.2 ONLINE</Badge>}
      actions={
        <div className="flex items-center gap-2.5 px-3.5 py-2 rounded-xl liquid-glass border border-blue-500/20 text-[11px] font-mono text-slate-300">
          <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>Cyberdome Node <span className="text-blue-400 font-bold">#042</span></span>
        </div>
      }
    />

    {/* KPI Tiles */}
    <section aria-label="Key metrics">
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 lg:gap-5">
        {stats.map((s, i) => (
          <StatTile key={s.label} label={s.label} value={s.value} icon={s.icon}
            accent={s.accent} caption={s.caption} delay={i * 0.06}
            onClick={() => onNavigate(s.route)}
            badge={
              <span className="inline-flex items-center gap-1 text-[9.5px] font-mono font-bold text-slate-400">
                <TrendingUp className="w-2.5 h-2.5 text-emerald-400" />{s.trend}
              </span>
            }
          />
        ))}
      </div>
    </section>

    {/* Quick Actions */}
    <section aria-label="Quick actions">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {QUICK_ACTIONS.map((a, i) => {
          const Icon = a.icon;
          return (
            <motion.button
              key={a.label} {...MOTION.fadeUp(0.25 + i * 0.05)} whileHover={{ y: -3 }}
              onClick={() => onNavigate(a.route)}
              className={cn(
                'group text-left p-4 rounded-2xl liquid-glass border transition-all duration-300',
                'focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/60',
                accentBorderMap[a.accent], accentGlowMap[a.accent]
              )}
            >
              <div className="flex items-start justify-between mb-3">
                <div className={cn('w-10 h-10 rounded-xl border flex items-center justify-center transition-transform group-hover:scale-110', accentIconMap[a.accent])}>
                  <Icon className={cn('w-5 h-5', accentTextMap[a.accent])} />
                </div>
                <ArrowRight className="w-4 h-4 text-slate-600 group-hover:text-slate-300 group-hover:translate-x-0.5 transition-all" />
              </div>
              <h3 className="font-poppins font-bold text-[13px] text-white leading-tight">{a.label}</h3>
              <p className="text-[10.5px] text-slate-500 font-mono mt-0.5 leading-tight">{a.description}</p>
            </motion.button>
          );
        })}
      </div>
    </section>

    {/* Operational Panels */}
    <section className="grid grid-cols-1 lg:grid-cols-3 gap-5" aria-label="Operational panels">

      {/* Recent Activity */}
      <GlassCard accent="blue" {...MOTION.fadeUp(0.35)} className="overflow-hidden">
        <CardOrb accent="blue" />
        <CardHeader title="Recent Activity" icon={Activity} accent="blue"
          right={<Badge accent="emerald" size="xs" dot>LIVE</Badge>} />
        <ul className="space-y-2 relative z-10">
          {RECENT_ACTIVITY.map((a, i) => {
            const Icon = a.icon;
            return (
              <motion.li key={i} {...MOTION.slideLeft(0.4 + i * 0.06)}
                className="flex items-start gap-2.5 p-2.5 rounded-xl bg-white/[0.04] border border-white/[0.06] hover:border-white/[0.1] transition-colors">
                <Icon className={cn('w-3.5 h-3.5 shrink-0 mt-0.5', accentTextMap[a.accent])} />
                <div className="min-w-0 flex-1">
                  <p className="text-[11.5px] text-slate-300 leading-snug">{a.text}</p>
                  <span className="text-[9.5px] font-mono text-slate-600">{a.time}</span>
                </div>
              </motion.li>
            );
          })}
        </ul>
      </GlassCard>

      {/* AI Status */}
      <GlassCard accent="purple" {...MOTION.fadeUp(0.4)} className="overflow-hidden">
        <CardOrb accent="purple" />
        <CardHeader title="AI Engine Status" icon={Cpu} accent="purple"
          right={<Badge accent="emerald" size="xs" dot pulse>OPERATIONAL</Badge>} />
        <div className="space-y-3 relative z-10">
          <div className="flex items-center gap-3 p-3 rounded-xl bg-purple-500/[0.08] border border-purple-500/20">
            <motion.div
              animate={{ boxShadow: ['0 0 12px rgba(139,92,246,0.18)','0 0 26px rgba(139,92,246,0.42)','0 0 12px rgba(139,92,246,0.18)'] }}
              transition={{ repeat: Infinity, duration: 2.4 }}
              className="w-10 h-10 rounded-xl bg-purple-500/15 border border-purple-500/40 flex items-center justify-center shrink-0"
            >
              <Bot className="w-5 h-5 text-purple-400" />
            </motion.div>
            <div className="min-w-0">
              <h4 className="font-poppins font-bold text-[13px] text-white leading-tight">CyberLLM v4.2</h4>
              <p className="text-[10px] font-mono text-slate-500">14B params · 8 agents online</p>
            </div>
            <span className="ml-auto font-poppins font-extrabold text-xl text-emerald-400">
              <AnimatedCounter target={99} suffix="%" />
            </span>
          </div>

          {AI_AGENTS.map((agent, i) => (
            <motion.div key={agent.name} {...MOTION.fadeIn(0.5 + i * 0.06)} className="space-y-1">
              <div className="flex items-center justify-between text-[10.5px] font-mono">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <CircleDot className="w-2.5 h-2.5 text-slate-600" />{agent.name}
                </span>
                <span className="text-slate-300 font-bold">{agent.load}%</span>
              </div>
              <ProgressBar value={agent.load} accent={agent.accent} height="h-1" />
            </motion.div>
          ))}
        </div>
      </GlassCard>

      {/* Case Statistics */}
      <GlassCard accent="emerald" {...MOTION.fadeUp(0.45)} className="overflow-hidden">
        <CardOrb accent="emerald" />
        <CardHeader title="Case Statistics" icon={LineChart} accent="emerald"
          right={
            <button onClick={() => onNavigate('analytics')}
              className="text-[10px] font-mono text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors">
              Details <ArrowRight className="w-3 h-3" />
            </button>
          }
        />
        <div className="space-y-3 relative z-10">
          <div className="grid grid-cols-2 gap-2.5">
            <div className="p-3 rounded-xl bg-emerald-500/[0.08] border border-emerald-500/20 text-center">
              <span className="block font-poppins font-extrabold text-xl text-emerald-400">
                <AnimatedCounter target={82} suffix="%" />
              </span>
              <span className="text-[9.5px] font-mono text-slate-500 uppercase">Resolution Rate</span>
            </div>
            <div className="p-3 rounded-xl bg-blue-500/[0.08] border border-blue-500/20 text-center">
              <span className="block font-poppins font-extrabold text-xl text-blue-400">
                <AnimatedCounter target={42} suffix="s" />
              </span>
              <span className="text-[9.5px] font-mono text-slate-500 uppercase">Avg Triage</span>
            </div>
          </div>

          <div className="space-y-2 pt-1">
            <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">Attack Vector Distribution</span>
            {CASE_BREAKDOWN.map((c, i) => (
              <motion.div key={c.label} {...MOTION.fadeIn(0.55 + i * 0.05)} className="space-y-1">
                <div className="flex items-center justify-between text-[10.5px] font-mono">
                  <span className="text-slate-400">{c.label}</span>
                  <span className="text-slate-300 font-bold">{c.value}%</span>
                </div>
                <ProgressBar value={c.value} accent={c.accent} height="h-1" gradient={false} />
              </motion.div>
            ))}
          </div>
        </div>
      </GlassCard>
    </section>

    {/* Recent Cases Table */}
    <section aria-label="Recent investigations">
      <RecentInvestigationsTable cases={cases} onSelectCase={onSelectCase} />
    </section>
  </div>
);
