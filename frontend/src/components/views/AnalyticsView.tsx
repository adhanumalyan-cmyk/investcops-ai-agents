import React from 'react';
import { BarChart3, Zap, Activity, LineChart, ShieldAlert, Bitcoin, Smartphone } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, CartesianGrid } from 'recharts';
import { PageHeader, GlassCard, CardHeader, CardOrb, Badge, StatTile, MOTION } from '../ui';

const TREND = [
  { month: 'Jan', cases: 120, critical: 18 },
  { month: 'Feb', cases: 145, critical: 24 },
  { month: 'Mar', cases: 190, critical: 31 },
  { month: 'Apr', cases: 220, critical: 28 },
  { month: 'May', cases: 280, critical: 37 },
  { month: 'Jun', cases: 310, critical: 42 }
];

const CATEGORIES = [
  { name: 'Crypto Fraud',        value: 38, color: '#3B82F6' },
  { name: 'Ransomware',          value: 24, color: '#8B5CF6' },
  { name: 'Deepfake Audio/Video',value: 18, color: '#EC4899' },
  { name: 'APK Banking Trojans', value: 12, color: '#F59E0B' },
  { name: 'Data Leaks',          value: 8,  color: '#10B981' }
];

const TOOLTIP_STYLE = {
  backgroundColor: '#0B1020',
  border: '1px solid rgba(59,130,246,0.4)',
  borderRadius: 12,
  fontSize: 11,
  fontFamily: 'JetBrains Mono, monospace',
  boxShadow: '0 8px 24px rgba(0,0,0,0.5)'
};

export const AnalyticsView: React.FC = () => (
  <div className="space-y-7">
    <PageHeader
      title="Threat Intelligence Analytics"
      subtitle="Real-time attack vector telemetry, crypto laundering volume metrics, and darkweb correlation across all Kerala Cyberdome nodes."
      icon={LineChart}
      iconAccent="blue"
      badge={<Badge accent="blue" icon={Activity} glow>LIVE FEED ACTIVE</Badge>}
      actions={
        <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-emerald-500/8 border border-emerald-500/25 text-[11px] font-mono text-emerald-400">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse shrink-0" />
          Syncing State Nodes
        </div>
      }
    />

    <section className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 lg:gap-5">
      <StatTile label="Avg Detection Time" value="4.2s" icon={Zap} accent="blue" animate={false}
        caption="84% faster with CyberLLM" delay={0} />
      <StatTile label="Crypto Intercepted" value="$1.42M" icon={Bitcoin} accent="purple" animate={false}
        caption="Tron TRC-20 mixer hotspot" delay={0.06} />
      <StatTile label="Blocked APK Installs" value={1840} icon={Smartphone} accent="amber"
        caption="Kerala cyber cell network" delay={0.12} />
      <StatTile label="Active Syndicates" value={12} icon={ShieldAlert} accent="red"
        caption="High priority surveillance" delay={0.18} />
    </section>

    <section className="grid grid-cols-1 lg:grid-cols-3 gap-5 lg:gap-6">
      <GlassCard accent="blue" padding="lg" {...MOTION.fadeUp(0.24)} className="lg:col-span-2 overflow-hidden">
        <CardOrb accent="blue" />
        <CardHeader title="Incident Rate Trend (2026)" icon={BarChart3} accent="blue"
          right={<span className="text-[10px] font-mono text-slate-500">Monthly volume</span>} />
        <div className="h-72 w-full relative z-10">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={TREND} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
              <defs>
                <linearGradient id="gCases" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.42} />
                  <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gCritical" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#EF4444" stopOpacity={0.42} />
                  <stop offset="95%" stopColor="#EF4444" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.08)" vertical={false} />
              <XAxis dataKey="month" stroke="#64748B" fontSize={11} tickLine={false} axisLine={false} />
              <YAxis stroke="#64748B" fontSize={11} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ stroke: 'rgba(59,130,246,0.3)' }} />
              <Area type="monotone" dataKey="cases" stroke="#3B82F6" fill="url(#gCases)" strokeWidth={2.5} />
              <Area type="monotone" dataKey="critical" stroke="#EF4444" fill="url(#gCritical)" strokeWidth={2.5} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </GlassCard>

      <GlassCard accent="purple" padding="lg" {...MOTION.fadeUp(0.3)} className="overflow-hidden">
        <CardOrb accent="purple" />
        <CardHeader title="Vector Distribution" icon={Zap} accent="purple" />
        <div className="h-48 w-full relative z-10">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={CATEGORIES} dataKey="value" nameKey="name" cx="50%" cy="50%"
                innerRadius={48} outerRadius={70} paddingAngle={4} stroke="none">
                {CATEGORIES.map(c => <Cell key={c.name} fill={c.color} />)}
              </Pie>
              <Tooltip contentStyle={TOOLTIP_STYLE} />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <ul className="space-y-1.5 relative z-10 mt-3">
          {CATEGORIES.map(c => (
            <li key={c.name} className="flex items-center justify-between text-[11px] font-mono">
              <span className="flex items-center gap-2 text-slate-400 min-w-0">
                <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: c.color }} />
                <span className="truncate">{c.name}</span>
              </span>
              <span className="font-bold text-slate-200 shrink-0 ml-2">{c.value}%</span>
            </li>
          ))}
        </ul>
      </GlassCard>
    </section>
  </div>
);
