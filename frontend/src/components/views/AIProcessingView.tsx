import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Bot, FolderOpen, ScanSearch, FileText, Users, Link2, CalendarClock,
  ShieldAlert, FileCheck, Zap, CheckCircle2, Loader2, Lock, MessageSquare,
  Image, Video, FileStack, UserSearch, Heart, Layers, Gauge, AlertTriangle,
  ArrowRight, X, Clock, Cpu, Activity, Sparkles, FastForward,
  RotateCcw, LucideIcon
} from 'lucide-react';
import { motion } from 'framer-motion';
import {
  PageHeader, GlassCard, CardHeader, CardOrb, Badge, Button, ActionBar,
  ProgressBar, FloatingParticles, MOTION, AccentColor, AnimatedCounter
} from '../ui';
import { cn } from '../../utils/cn';

type AgentState = 'waiting' | 'reading' | 'running' | 'completed';

interface Agent {
  id: number;
  title: string;
  description: string;
  icon: LucideIcon;
  eta: string;
  state: AgentState;
  progress: number;
}

const AGENT_BLUEPRINT: Omit<Agent, 'state' | 'progress'>[] = [
  { id: 0, title: 'Evidence Upload',             icon: FolderOpen,   eta: '~1s',  description: 'SHA-256 chain-of-custody hash registered. Validating file integrity and MIME signatures.' },
  { id: 1, title: 'Evidence Analysis Agent',     icon: ScanSearch,   eta: '~2s',  description: 'Deep binary inspection, header analysis, and malware sandbox detonation in isolated enclave.' },
  { id: 2, title: 'OCR & Text Extraction Agent', icon: FileText,     eta: '~2s',  description: 'Multi-language Tesseract OCR with Vision LLM for handwritten notes and screenshots.' },
  { id: 3, title: 'Entity Extraction Agent',     icon: Users,        eta: '~2s',  description: 'NER extraction for phone numbers, emails, crypto wallets, UPI IDs, and social handles.' },
  { id: 4, title: 'Source Correlation Agent',    icon: Link2,        eta: '~2s',  description: 'Cross-referencing entities with Cyberdome vault, NCRP database, and darkweb feeds.' },
  { id: 5, title: 'Timeline Reconstruction Agent', icon: CalendarClock, eta: '~1s', description: 'Building temporal event graph from timestamps, EXIF metadata, and blockchain ledgers.' },
  { id: 6, title: 'Risk Assessment Agent',       icon: ShieldAlert,  eta: '~1s',  description: 'CyberLLM multi-factor threat scoring via behavioural analysis and syndicate profiling.' },
  { id: 7, title: 'Report Generation Agent',     icon: FileCheck,    eta: '~1s',  description: 'Compiling ISO 27037 court-admissible dossier with Section 65B evidence certificate.' }
];

/* Optimized step durations for a crisp ~8 second total simulation */
const DURATIONS = [700, 1100, 1300, 1200, 1400, 1000, 900, 800];

const MONITOR: { label: string; target: number; icon: LucideIcon; accent: AccentColor; suffix?: string; isRisk?: boolean }[] = [
  { label: 'Evidence Files',     target: 8,    icon: FileStack,     accent: 'blue' },
  { label: 'Messages',           target: 3542, icon: MessageSquare, accent: 'purple' },
  { label: 'Images',             target: 52,   icon: Image,         accent: 'pink' },
  { label: 'Videos',             target: 14,   icon: Video,         accent: 'rose' },
  { label: 'Documents',          target: 31,   icon: FileText,      accent: 'amber' },
  { label: 'Potential Suspects', target: 2,    icon: UserSearch,    accent: 'red' },
  { label: 'Victims',            target: 1,    icon: Heart,         accent: 'emerald' },
  { label: 'Entities Found',     target: 86,   icon: Layers,        accent: 'blue' },
  { label: 'Confidence',         target: 96,   icon: Gauge,         accent: 'emerald', suffix: '%' },
  { label: 'Risk Level',         target: 0,    icon: AlertTriangle, accent: 'red', isRisk: true }
];

const STATE_BADGE: Record<AgentState, { label: string; accent: AccentColor }> = {
  waiting:   { label: 'WAITING',   accent: 'slate' },
  reading:   { label: 'READING',   accent: 'blue' },
  running:   { label: 'RUNNING',   accent: 'purple' },
  completed: { label: 'COMPLETED', accent: 'emerald' }
};

const wait = (ms: number) => new Promise(r => setTimeout(r, ms));

interface AIProcessingViewProps {
  onViewResults?: () => void;
  onCancel?: () => void;
}

export const AIProcessingView: React.FC<AIProcessingViewProps> = ({ onViewResults, onCancel }) => {
  const [agents, setAgents] = useState<Agent[]>(
    AGENT_BLUEPRINT.map(a => ({ ...a, state: 'waiting' as AgentState, progress: 0 }))
  );
  const [complete, setComplete] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [countersOn, setCountersOn] = useState(false);
  const cancelledRef = useRef(false);

  /* Elapsed timer */
  useEffect(() => {
    if (complete) return;
    const t = setInterval(() => setElapsed(e => e + 1), 1000);
    return () => clearInterval(t);
  }, [complete]);

  /* Fast-forward/Instant Complete handler */
  const handleFastForward = useCallback(() => {
    cancelledRef.current = true;
    setAgents(AGENT_BLUEPRINT.map(a => ({ ...a, state: 'completed' as AgentState, progress: 100 })));
    setCountersOn(true);
    setComplete(true);
  }, []);

  /* Reset/Restart simulation handler */
  const handleRestart = useCallback(() => {
    cancelledRef.current = true;
    setTimeout(() => {
      cancelledRef.current = false;
      setAgents(AGENT_BLUEPRINT.map(a => ({ ...a, state: 'waiting' as AgentState, progress: 0 })));
      setComplete(false);
      setElapsed(0);
      setCountersOn(false);
    }, 100);
  }, []);

  /* Main Agent Orchestration Loop */
  useEffect(() => {
    cancelledRef.current = false;

    (async () => {
      await wait(300);
      if (cancelledRef.current) return;
      setCountersOn(true);

      for (let i = 0; i < AGENT_BLUEPRINT.length; i++) {
        if (cancelledRef.current) return;

        // Transition agent to 'reading'
        setAgents(p => p.map((a, x) => x === i ? { ...a, state: 'reading', progress: 10 } : a));

        await wait(350);
        if (cancelledRef.current) return;

        // Transition agent to 'running'
        setAgents(p => p.map((a, x) => x === i ? { ...a, state: 'running', progress: 25 } : a));

        const ticks = 6;
        for (let t = 1; t <= ticks; t++) {
          await wait(DURATIONS[i] / ticks);
          if (cancelledRef.current) return;
          setAgents(p => p.map((a, x) => x === i ? { ...a, progress: 25 + Math.round((75 * t) / ticks) } : a));
        }

        if (cancelledRef.current) return;

        // Transition agent to 'completed'
        setAgents(p => p.map((a, x) => x === i ? { ...a, state: 'completed', progress: 100 } : a));
      }

      if (!cancelledRef.current) {
        await wait(300);
        setComplete(true);
      }
    })();

    return () => {
      cancelledRef.current = true;
    };
  }, []);

  /* Results navigation trigger — fast forwards if still running */
  const handleViewResults = () => {
    if (!complete) {
      handleFastForward();
    }
    onViewResults?.();
  };

  const doneCount = agents.filter(a => a.state === 'completed').length;
  const activeAgent = agents.find(a => a.state === 'reading' || a.state === 'running');
  const overall = Math.round((doneCount / agents.length) * 100);

  const fmt = (s: number) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;

  return (
    <div className="space-y-7 relative">
      <FloatingParticles count={22} />

      <PageHeader
        title="AI Investigation Processing"
        subtitle="Analyzing uploaded evidence using specialized AI agents. Each agent autonomously processes, correlates, and synthesizes intelligence from the evidence corpus."
        icon={Bot}
        iconAccent="purple"
        badge={
          complete
            ? <Badge accent="emerald" icon={CheckCircle2} glow>ANALYSIS COMPLETE</Badge>
            : <motion.span
                animate={{ boxShadow: ['0 0 12px rgba(59,130,246,0.2)', '0 0 26px rgba(139,92,246,0.45)', '0 0 12px rgba(59,130,246,0.2)'] }}
                transition={{ repeat: Infinity, duration: 2.2 }}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 text-[10px] font-mono font-bold bg-blue-500/12 text-blue-300 border border-blue-500/40 rounded-lg"
              >
                <Loader2 className="w-3 h-3 animate-spin" />ANALYSIS IN PROGRESS
              </motion.span>
        }
        actions={
          <div className="flex items-center gap-2.5 flex-wrap">
            {!complete && (
              <Button
                variant="secondary"
                size="sm"
                icon={FastForward}
                onClick={handleFastForward}
                title="Instantly complete simulation"
              >
                Fast-Forward
              </Button>
            )}
            {complete && (
              <Button
                variant="secondary"
                size="sm"
                icon={RotateCcw}
                onClick={handleRestart}
                title="Restart simulation"
              >
                Rerun Pipeline
              </Button>
            )}
            <div className="px-3 py-2 rounded-xl liquid-glass border border-blue-500/20 text-[11px] font-mono text-slate-300 flex items-center gap-2">
              <Clock className="w-3.5 h-3.5 text-blue-400" />
              <span className="tabular-nums">{fmt(elapsed)}</span>
            </div>
            <div className="px-3 py-2 rounded-xl liquid-glass border border-purple-500/20 text-[11px] font-mono text-slate-300 flex items-center gap-2">
              <Cpu className="w-3.5 h-3.5 text-purple-400" />
              <span className="text-purple-400 font-bold">{doneCount}/{agents.length}</span> agents
            </div>
          </div>
        }
      />

      <div className="grid grid-cols-1 xl:grid-cols-5 gap-5 lg:gap-6 relative z-10">

        {/* ══ LEFT: Agent Workflow ══ */}
        <div className="xl:col-span-3 min-w-0">
          <GlassCard accent="blue" padding="lg" className="overflow-hidden">
            <CardOrb accent="blue" position="-top-24 -left-24" size="w-64 h-64" />
            <CardOrb accent="purple" position="-bottom-24 -right-24" size="w-64 h-64" />

            <CardHeader
              title="Agentic AI Investigation Workflow"
              icon={Sparkles}
              accent="purple"
              right={
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono text-slate-500 hidden sm:block">Multi-Agent Orchestration</span>
                  {!complete && (
                    <button
                      onClick={handleFastForward}
                      className="text-[10px] font-mono text-purple-400 hover:text-purple-300 flex items-center gap-1 transition-colors bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/20"
                    >
                      <FastForward className="w-2.5 h-2.5" /> Skip to End
                    </button>
                  )}
                </div>
              }
            />

            <ol className="relative z-10">
              {agents.map((agent, i) => {
                const Icon = agent.icon;
                const active = agent.state === 'reading' || agent.state === 'running';
                const done = agent.state === 'completed';
                const last = i === agents.length - 1;
                const badge = STATE_BADGE[agent.state];

                return (
                  <li key={agent.id}>
                    <motion.div
                      {...MOTION.slideLeft(i * 0.06)}
                      className={cn(
                        'relative flex gap-4 p-4 rounded-2xl border transition-all duration-500',
                        active ? 'bg-blue-950/40 border-blue-500/50 shadow-[0_0_30px_rgba(59,130,246,0.18)] animate-border-glow'
                          : done ? 'bg-emerald-950/20 border-emerald-500/30'
                          : 'bg-white/[0.03] border-white/[0.07]'
                      )}
                    >
                      {/* Agent avatar */}
                      <div className={cn(
                        'relative w-12 h-12 rounded-2xl shrink-0 flex items-center justify-center border transition-all duration-500',
                        active ? 'bg-blue-500/20 border-blue-500 shadow-[0_0_20px_rgba(59,130,246,0.4)]'
                          : done ? 'bg-emerald-500/15 border-emerald-500/45'
                          : 'bg-slate-900 border-slate-800'
                      )}>
                        {done ? <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                          : active
                            ? <motion.span animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 3, ease: 'linear' }}>
                                <Icon className="w-6 h-6 text-blue-400" />
                              </motion.span>
                            : <Icon className="w-6 h-6 text-slate-600" />}

                        {active && (
                          <motion.span
                            className="absolute inset-0 rounded-2xl border-2 border-blue-400/35"
                            animate={{ scale: [1, 1.22, 1], opacity: [0.6, 0, 0.6] }}
                            transition={{ repeat: Infinity, duration: 2 }}
                          />
                        )}
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2 mb-1 flex-wrap">
                          <h3 className={cn('font-poppins font-bold text-[13.5px]',
                            active ? 'text-white' : done ? 'text-emerald-200' : 'text-slate-500')}>
                            {agent.title}
                          </h3>
                          <div className="flex items-center gap-2 shrink-0">
                            <span className="text-[9.5px] font-mono text-slate-600">{agent.eta}</span>
                            <Badge accent={badge.accent} size="xs" pulse={active}>
                              {active && <Loader2 className="w-2.5 h-2.5 animate-spin" />}
                              {badge.label}
                            </Badge>
                          </div>
                        </div>

                        <p className={cn('text-[11.5px] leading-relaxed',
                          active ? 'text-slate-300' : done ? 'text-slate-500' : 'text-slate-600')}>
                          {agent.description}
                        </p>

                        {(active || done) && (
                          <div className="mt-2.5">
                            <ProgressBar
                              value={agent.progress}
                              accent={done ? 'emerald' : 'blue'}
                              height="h-1.5"
                              showLabel
                              label="Progress"
                            />
                          </div>
                        )}
                      </div>
                    </motion.div>

                    {/* Glowing connector */}
                    {!last && (
                      <div className="flex justify-start pl-[38px] py-1">
                        <div className="flex flex-col items-center h-6">
                          <motion.span
                            className={cn('w-0.5 flex-1 rounded-full',
                              agents[i + 1].state !== 'waiting' ? 'bg-gradient-to-b from-emerald-500/60 to-blue-500/60'
                                : active || done ? 'bg-gradient-to-b from-blue-500/50 to-slate-800'
                                : 'bg-slate-800')}
                            animate={active ? { opacity: [0.45, 1, 0.45] } : {}}
                            transition={{ repeat: Infinity, duration: 1.5 }}
                          />
                          <motion.span
                            className={cn('w-2 h-2 rounded-full mt-0.5',
                              agents[i + 1].state !== 'waiting' ? 'bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.6)]'
                                : active ? 'bg-blue-500/50' : 'bg-slate-700')}
                            animate={active ? { scale: [1, 1.4, 1] } : {}}
                            transition={{ repeat: Infinity, duration: 1.2 }}
                          />
                        </div>
                      </div>
                    )}
                  </li>
                );
              })}
            </ol>

            <div className="mt-5 pt-4 border-t border-slate-800 relative z-10">
              <ProgressBar
                value={overall}
                accent={complete ? 'emerald' : 'blue'}
                height="h-2"
                showLabel
                label="Overall Pipeline Progress"
              />
            </div>
          </GlassCard>
        </div>

        {/* ══ RIGHT: Monitoring ══ */}
        <div className="xl:col-span-2 space-y-5 lg:space-y-6 min-w-0">

          <GlassCard accent="purple" className="overflow-hidden">
            <CardOrb accent="purple" />
            <CardHeader title="Live AI Monitoring" icon={Activity} accent="purple"
              right={<Badge accent="emerald" size="xs" dot>STREAMING</Badge>} />

            <div className="grid grid-cols-2 gap-3 relative z-10">
              {MONITOR.map((m, i) => {
                const Icon = m.icon;
                const accentText = {
                  blue: 'text-blue-400', purple: 'text-purple-400', pink: 'text-pink-400',
                  rose: 'text-rose-400', amber: 'text-amber-400', red: 'text-red-400',
                  emerald: 'text-emerald-400', cyan: 'text-cyan-400', orange: 'text-orange-400', slate: 'text-slate-400'
                }[m.accent];
                const accentBorder = {
                  blue: 'border-blue-500/30', purple: 'border-purple-500/30', pink: 'border-pink-500/30',
                  rose: 'border-rose-500/30', amber: 'border-amber-500/30', red: 'border-red-500/30',
                  emerald: 'border-emerald-500/30', cyan: 'border-cyan-500/30', orange: 'border-orange-500/30', slate: 'border-slate-700'
                }[m.accent];
                const accentBg = {
                  blue: 'bg-blue-500/10', purple: 'bg-purple-500/10', pink: 'bg-pink-500/10',
                  rose: 'bg-rose-500/10', amber: 'bg-amber-500/10', red: 'bg-red-500/10',
                  emerald: 'bg-emerald-500/10', cyan: 'bg-cyan-500/10', orange: 'bg-orange-500/10', slate: 'bg-slate-500/10'
                }[m.accent];

                return (
                  <motion.div key={m.label} {...MOTION.scaleIn(i * 0.05)}
                    className={cn('p-3 rounded-xl bg-white/[0.04] border', accentBorder)}>
                    <div className="flex items-center gap-2 mb-1.5">
                      <div className={cn('w-7 h-7 rounded-lg flex items-center justify-center shrink-0', accentBg)}>
                        <Icon className={cn('w-3.5 h-3.5', accentText)} />
                      </div>
                      <span className="text-[10px] font-mono text-slate-500 leading-tight">{m.label}</span>
                    </div>
                    {m.isRisk ? (
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="font-poppins font-extrabold text-lg text-red-400">
                          {countersOn ? 'HIGH' : '—'}
                        </span>
                        {countersOn && <Badge accent="red" size="xs" pulse>CRITICAL</Badge>}
                      </div>
                    ) : (
                      <h4 className={cn('font-poppins font-extrabold text-lg', accentText)}>
                        <AnimatedCounter target={m.target} suffix={m.suffix} run={countersOn} duration={1800 + i * 200} />
                      </h4>
                    )}
                  </motion.div>
                );
              })}
            </div>
          </GlassCard>

          {/* Active agent spotlight */}
          <GlassCard accent="blue">
            <CardHeader title="Active Agent" icon={Bot} accent="blue" />
            {complete ? (
              <div className="text-center py-4">
                <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto mb-2" />
                <p className="font-poppins font-bold text-emerald-300 text-[13px]">All Agents Finished</p>
                <p className="text-[10.5px] text-slate-500 font-mono mt-1">Investigation ready for review</p>
              </div>
            ) : activeAgent ? (
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <motion.div
                    animate={{ boxShadow: ['0 0 14px rgba(59,130,246,0.2)', '0 0 30px rgba(59,130,246,0.5)', '0 0 14px rgba(59,130,246,0.2)'] }}
                    transition={{ repeat: Infinity, duration: 2 }}
                    className="w-12 h-12 rounded-2xl bg-blue-500/20 border border-blue-500 flex items-center justify-center shrink-0"
                  >
                    <motion.span animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 4, ease: 'linear' }}>
                      <activeAgent.icon className="w-6 h-6 text-blue-400" />
                    </motion.span>
                  </motion.div>
                  <div className="min-w-0">
                    <h4 className="font-poppins font-bold text-[13px] text-white truncate">{activeAgent.title}</h4>
                    <span className="text-[10px] font-mono text-blue-400 uppercase">{activeAgent.state}…</span>
                  </div>
                </div>
                <ProgressBar value={activeAgent.progress} accent="blue" />
                <p className="text-[11px] text-slate-500 leading-relaxed">{activeAgent.description}</p>
              </div>
            ) : (
              <div className="text-center py-4">
                <Loader2 className="w-8 h-8 text-blue-400 mx-auto mb-2 animate-spin" />
                <p className="text-[11px] text-slate-500 font-mono">Initializing pipeline…</p>
              </div>
            )}
          </GlassCard>

          <GlassCard accent="emerald" padding="sm">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center shrink-0">
                <Lock className="w-5 h-5 text-emerald-400" />
              </div>
              <div className="min-w-0">
                <h4 className="text-[12.5px] font-semibold text-slate-100">Secure Enclave Active</h4>
                <p className="text-[10px] text-emerald-400 font-mono flex items-center gap-1 mt-0.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  AES-256 · TLS 1.3 · Authorized Only
                </p>
              </div>
            </div>
          </GlassCard>
        </div>
      </div>

      <ActionBar
        left={<><Lock className="w-4 h-4 text-emerald-400 shrink-0" /><span>Secure Analysis Enclave · Case KPC-2026-8941</span></>}
      >
        <Button variant="secondary" size="lg" icon={X} onClick={onCancel}>Cancel Analysis</Button>
        <Button
          size="lg"
          icon={FileCheck}
          iconRight={ArrowRight}
          onClick={handleViewResults}
        >
          View Investigation Results
        </Button>
      </ActionBar>
    </div>
  );
};
