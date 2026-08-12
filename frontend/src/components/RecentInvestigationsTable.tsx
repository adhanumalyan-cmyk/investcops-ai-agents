import React, { useState, useMemo } from 'react';
import {
  Briefcase, Clock, ChevronRight, Sparkles, SlidersHorizontal, Search,
  Activity, UserCheck, CheckCircle2, FolderSearch
} from 'lucide-react';
import { motion } from 'framer-motion';
import { CaseItem, RiskLevel } from '../types/investigation';
import { GlassCard, Badge, EmptyState, MOTION, AccentColor } from './ui';
import { cn } from '../utils/cn';

const RISK_ACCENT: Record<RiskLevel, AccentColor> = {
  CRITICAL: 'red', HIGH: 'amber', MEDIUM: 'blue', LOW: 'emerald'
};

const STATUS_META: Record<string, { accent: AccentColor; icon: typeof Activity; label: string }> = {
  'Active Analysis':              { accent: 'blue',    icon: Activity,    label: 'Active Analysis' },
  'Evidence Pending':             { accent: 'purple',  icon: Clock,       label: 'Evidence Pending' },
  'Suspect Identified':           { accent: 'amber',   icon: UserCheck,   label: 'Suspect Identified' },
  'Closed - Court Dossier Ready': { accent: 'emerald', icon: CheckCircle2,label: 'Dossier Ready' },
  'Under Legal Review':           { accent: 'cyan',    icon: Clock,       label: 'Legal Review' }
};

const FILTERS: (RiskLevel | 'ALL')[] = ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];

interface Props {
  cases: CaseItem[];
  onSelectCase: (c: CaseItem) => void;
}

export const RecentInvestigationsTable: React.FC<Props> = ({ cases, onSelectCase }) => {
  const [risk, setRisk] = useState<RiskLevel | 'ALL'>('ALL');
  const [query, setQuery] = useState('');

  const filtered = useMemo(() => cases.filter(c => {
    const matchRisk = risk === 'ALL' || c.risk === risk;
    const q = query.toLowerCase();
    const matchQuery = !q || [c.id, c.name, c.category, c.primaryVector].join(' ').toLowerCase().includes(q);
    return matchRisk && matchQuery;
  }), [cases, risk, query]);

  return (
    <GlassCard accent="blue" padding="lg" {...MOTION.fadeUp(0.5)}>
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-800 mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-500/12 border border-blue-500/30 flex items-center justify-center shrink-0">
            <Briefcase className="w-5 h-5 text-blue-400" />
          </div>
          <div className="min-w-0">
            <h2 className="font-poppins font-bold text-lg text-white flex items-center gap-2 flex-wrap leading-tight">
              Recent Investigations
              <Badge accent="slate" size="xs">{filtered.length} records</Badge>
            </h2>
            <p className="text-[11.5px] text-slate-500 mt-0.5">
              Live case vault synchronized with Cyberdome Central Registry
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text" value={query} onChange={e => setQuery(e.target.value)}
              placeholder="Filter cases…" aria-label="Filter investigations"
              className="pl-8 pr-3 py-1.5 w-44 bg-black/30 border border-blue-500/20 rounded-xl text-[11px] font-mono text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500/60 transition-all"
            />
          </div>

          <div className="flex items-center gap-1 p-1 rounded-xl bg-black/30 border border-white/[0.08]">
            <SlidersHorizontal className="w-3.5 h-3.5 text-slate-600 ml-1.5 mr-0.5 shrink-0" />
            {FILTERS.map(f => (
              <button key={f} onClick={() => setRisk(f)}
                className={cn('px-2 py-1 rounded-lg text-[10px] font-mono font-bold transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/60',
                  risk === f ? 'bg-blue-600 text-white shadow-[0_0_10px_rgba(59,130,246,0.35)]' : 'text-slate-500 hover:text-white hover:bg-slate-800')}>
                {f}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Table */}
      {filtered.length === 0 ? (
        <EmptyState compact icon={FolderSearch} title="No matching investigations"
          description="Adjust the search query or risk filter to view case records." />
      ) : (
        <div className="overflow-x-auto -mx-2 px-2">
          <table className="w-full text-left border-collapse min-w-[52rem]">
            <thead>
              <tr className="border-b border-slate-800 text-[10px] font-poppins font-bold text-slate-500 uppercase tracking-wider">
                <th scope="col" className="pb-3 px-3">Case ID</th>
                <th scope="col" className="pb-3 px-3">Case Name &amp; Vector</th>
                <th scope="col" className="pb-3 px-3">Risk</th>
                <th scope="col" className="pb-3 px-3">Last Updated</th>
                <th scope="col" className="pb-3 px-3">Status</th>
                <th scope="col" className="pb-3 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filtered.map((c, i) => {
                const status = STATUS_META[c.status] || STATUS_META['Active Analysis'];
                const StatusIcon = status.icon;
                return (
                  <motion.tr
                    key={c.id}
                    {...MOTION.fadeUp(i * 0.04)}
                    onClick={() => onSelectCase(c)}
                    tabIndex={0}
                    onKeyDown={e => { if (e.key === 'Enter') onSelectCase(c); }}
                    className="group cursor-pointer hover:bg-slate-800/40 transition-colors focus:outline-none focus-visible:bg-slate-800/60"
                  >
                    <td className="py-3.5 px-3">
                      <span className="font-mono text-[11px] font-bold text-blue-400 group-hover:text-blue-300 flex items-center gap-2 transition-colors">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                        {c.id}
                      </span>
                    </td>
                    <td className="py-3.5 px-3 max-w-sm">
                      <span className="font-poppins font-semibold text-[13px] text-slate-100 group-hover:text-white block truncate transition-colors">
                        {c.name}
                      </span>
                      <span className="text-[10.5px] font-mono text-slate-500 truncate block mt-0.5">
                        <span className="text-purple-400 font-semibold">{c.category}</span> · {c.primaryVector}
                      </span>
                    </td>
                    <td className="py-3.5 px-3">
                      <Badge accent={RISK_ACCENT[c.risk]} size="xs" dot pulse={c.risk === 'CRITICAL'}>{c.risk}</Badge>
                    </td>
                    <td className="py-3.5 px-3">
                      <span className="text-[10.5px] font-mono text-slate-500 flex items-center gap-1.5 whitespace-nowrap">
                        <Clock className="w-3 h-3 text-slate-600" />{c.lastUpdated}
                      </span>
                    </td>
                    <td className="py-3.5 px-3">
                      <Badge accent={status.accent} size="xs" icon={StatusIcon}>{status.label}</Badge>
                    </td>
                    <td className="py-3.5 px-3 text-right">
                      <span className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-xl bg-slate-800/80 group-hover:bg-blue-600 text-slate-400 group-hover:text-white border border-slate-700/60 group-hover:border-blue-500 text-[10.5px] font-semibold transition-all whitespace-nowrap">
                        Analyze <ChevronRight className="w-3 h-3" />
                      </span>
                    </td>
                  </motion.tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <div className="flex flex-col sm:flex-row items-center justify-between gap-2 pt-4 mt-4 border-t border-slate-800 text-[10.5px] font-mono text-slate-500">
        <span className="flex items-center gap-2">
          <Sparkles className="w-3.5 h-3.5 text-purple-400" />
          Real-time graph neural network linking active nodes
        </span>
        <span>Showing {filtered.length} of {cases.length} registered case files</span>
      </div>
    </GlassCard>
  );
};
