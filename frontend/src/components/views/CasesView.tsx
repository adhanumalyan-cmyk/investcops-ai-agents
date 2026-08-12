import React, { useState, useMemo } from 'react';
import {
  Briefcase, Search, SlidersHorizontal, Plus, Clock, ExternalLink,
  LayoutGrid, Rows3, MapPin, FolderSearch
} from 'lucide-react';
import { motion } from 'framer-motion';
import {
  PageHeader, GlassCard, Badge, Button, EmptyState, MOTION, AccentColor
} from '../ui';
import { CaseItem, RiskLevel } from '../../types/investigation';
import { cn } from '../../utils/cn';

const RISK_ACCENT: Record<RiskLevel, AccentColor> = {
  CRITICAL: 'red', HIGH: 'amber', MEDIUM: 'blue', LOW: 'emerald'
};

const FILTERS: (RiskLevel | 'ALL')[] = ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];

interface CasesViewProps {
  cases: CaseItem[];
  onSelectCase: (c: CaseItem) => void;
  onNewCase: () => void;
}

export const CasesView: React.FC<CasesViewProps> = ({ cases, onSelectCase, onNewCase }) => {
  const [query, setQuery] = useState('');
  const [risk, setRisk] = useState<RiskLevel | 'ALL'>('ALL');
  const [view, setView] = useState<'grid' | 'list'>('grid');

  const filtered = useMemo(() => cases.filter(c => {
    const matchRisk = risk === 'ALL' || c.risk === risk;
    const q = query.toLowerCase();
    const matchQuery = !q || [c.id, c.name, c.category, c.primaryVector].join(' ').toLowerCase().includes(q);
    return matchRisk && matchQuery;
  }), [cases, risk, query]);

  return (
    <div className="space-y-7">
      <PageHeader
        title="Cyber Crime Case Vault"
        subtitle="Centralized repository of active state-level cyber investigations synchronized with the Kerala Police Cyberdome central registry."
        icon={Briefcase}
        iconAccent="blue"
        badge={<Badge accent="blue">{cases.length} TOTAL FILES</Badge>}
        actions={<Button icon={Plus} size="lg" onClick={onNewCase}>Register New Incident</Button>}
      />

      {/* Filter toolbar */}
      <GlassCard accent="blue" padding="sm" {...MOTION.fadeUp(0.05)}>
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text" value={query} onChange={e => setQuery(e.target.value)}
              placeholder="Search by Case ID, syndicate, or vector…"
              aria-label="Search cases"
              className="w-full pl-10 pr-4 py-2 bg-black/30 border border-blue-500/20 rounded-xl text-xs font-mono text-white placeholder-slate-500 focus:outline-none focus:border-blue-500/60 focus:shadow-[0_0_0_3px_rgba(59,130,246,0.22)] transition-all"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <SlidersHorizontal className="w-4 h-4 text-slate-500 shrink-0" />
            <div className="flex items-center gap-1 p-1 rounded-xl bg-black/30 border border-white/[0.08]">
            {FILTERS.map(f => (
                <button key={f} onClick={() => setRisk(f)}
                  className={cn('px-2.5 py-1 rounded-lg text-[10.5px] font-mono font-bold transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/60',
                    risk === f ? 'bg-blue-600 text-white shadow-[0_0_12px_rgba(59,130,246,0.35)]' : 'text-slate-500 hover:text-white hover:bg-slate-800')}>
                  {f}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-1 p-1 rounded-xl bg-black/30 border border-white/[0.08]">
              {([['grid', LayoutGrid], ['list', Rows3]] as const).map(([mode, Icon]) => (
                <button key={mode} onClick={() => setView(mode)} aria-label={`${mode} view`}
                  className={cn('p-1.5 rounded-lg transition-all', view === mode ? 'bg-blue-500/20 text-blue-400' : 'text-slate-600 hover:text-slate-300')}>
                  <Icon className="w-4 h-4" />
                </button>
              ))}
            </div>
          </div>
        </div>
      </GlassCard>

      {filtered.length === 0 ? (
        <EmptyState
          icon={FolderSearch}
          title="No matching cases found"
          description="Adjust your search query or risk filter to view registered Cyberdome case files."
          action={<Button variant="secondary" onClick={() => { setQuery(''); setRisk('ALL'); }}>Reset Filters</Button>}
        />
      ) : view === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          {filtered.map((c, i) => (
            <motion.article
              key={c.id}
              {...MOTION.fadeUp(i * 0.05)}
              whileHover={{ y: -4 }}
              onClick={() => onSelectCase(c)}
              tabIndex={0}
              role="button"
              onKeyDown={e => { if (e.key === 'Enter') onSelectCase(c); }}
              className="liquid-glass border border-blue-500/20 hover:border-blue-500/55 rounded-2xl p-5 cursor-pointer transition-all duration-300 hover:shadow-[0_0_28px_rgba(59,130,246,0.22)] flex flex-col justify-between group focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/60"
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <span className="font-mono text-[11px] font-bold text-blue-400">{c.id}</span>
                  <Badge accent={RISK_ACCENT[c.risk]} size="xs" pulse={c.risk === 'CRITICAL'}>
                    {c.risk} · {c.riskScore}
                  </Badge>
                </div>
                <h3 className="font-poppins font-bold text-[15px] text-slate-100 group-hover:text-white leading-snug line-clamp-2 mb-1.5 transition-colors">
                  {c.name}
                </h3>
                <p className="text-[11.5px] text-slate-500 leading-relaxed line-clamp-2 mb-3">{c.summary}</p>
              </div>

              <div className="pt-3 border-t border-slate-800/80 space-y-2">
                <div className="flex items-center justify-between text-[10px] font-mono">
                  <span className="text-purple-400 truncate">{c.category}</span>
                  <span className="text-slate-600 flex items-center gap-1 shrink-0">
                    <Clock className="w-3 h-3" />{c.lastUpdated}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[10.5px] font-mono text-slate-500 flex items-center gap-1 truncate">
                    <MapPin className="w-3 h-3 text-slate-600 shrink-0" />{c.location}
                  </span>
                  <ExternalLink className="w-4 h-4 text-slate-600 group-hover:text-blue-400 group-hover:translate-x-0.5 transition-all shrink-0" />
                </div>
              </div>
            </motion.article>
          ))}
        </div>
      ) : (
        <GlassCard accent="blue" padding="none" className="overflow-hidden">
          <ul className="divide-y divide-slate-800/70">
            {filtered.map((c, i) => (
              <motion.li key={c.id} {...MOTION.slideLeft(i * 0.04)}>
                <button onClick={() => onSelectCase(c)}
                  className="w-full flex items-center gap-4 p-4 text-left hover:bg-slate-800/40 transition-colors group focus:outline-none focus-visible:bg-slate-800/60">
                  <span className="font-mono text-[11px] font-bold text-blue-400 w-32 shrink-0">{c.id}</span>
                  <div className="flex-1 min-w-0">
                    <h4 className="font-poppins font-semibold text-[13.5px] text-slate-100 group-hover:text-white truncate">{c.name}</h4>
                    <p className="text-[10.5px] font-mono text-slate-500 truncate">{c.category} · {c.primaryVector}</p>
                  </div>
                  <Badge accent={RISK_ACCENT[c.risk]} size="xs">{c.risk}</Badge>
                  <span className="text-[10.5px] font-mono text-slate-600 w-24 text-right shrink-0 hidden sm:block">{c.lastUpdated}</span>
                  <ExternalLink className="w-4 h-4 text-slate-600 group-hover:text-blue-400 shrink-0 transition-colors" />
                </button>
              </motion.li>
            ))}
          </ul>
        </GlassCard>
      )}
    </div>
  );
};
