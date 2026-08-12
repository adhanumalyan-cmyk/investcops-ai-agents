import React from 'react';
import {
  ShieldAlert, UploadCloud, Bot,
  BarChart4, FileText, LineChart, Settings, ChevronRight, ShieldCheck, Lock, ScanEye, Smartphone, FileText as FileTextIcon, Cable
} from 'lucide-react';
import { motion } from 'framer-motion';
import { cn } from '../utils/cn';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

interface NavItem {
  id: string;
  label: string;
  icon: typeof UploadCloud;
  badge?: string;
  badgeAccent?: 'blue' | 'emerald' | 'amber' | 'purple';
  dot?: string;
}

const NAV_GROUPS: { heading: string; items: NavItem[] }[] = [
  {
    heading: 'Investigation Workflow',
    items: [
      { id: 'upload', label: 'Upload Evidence', icon: UploadCloud, dot: 'bg-purple-400' },
      { id: 'field-extractor', label: 'USB Field Extractor', icon: Cable, badge: 'NEW', badgeAccent: 'emerald' },
      { id: 'fir-converter', label: 'FIR Generator', icon: FileTextIcon, badge: 'QWEN', badgeAccent: 'amber' },
      { id: 'ai-processing', label: 'AI Processing', icon: Bot, badge: 'LIVE', badgeAccent: 'emerald' },
      { id: 'results', label: 'Investigation Results', icon: BarChart4 },
      { id: 'reports', label: 'Investigation Report', icon: FileText }
    ]
  },
  {
    heading: 'AI Forensics Lab',
    items: [
      { id: 'deepfake', label: 'Deepfake Shield', icon: ScanEye, badge: 'AI', badgeAccent: 'purple' },
      { id: 'apk-scanner', label: 'APK Scanner', icon: Smartphone, badge: 'AI', badgeAccent: 'emerald' }
    ]
  },
  {
    heading: 'System',
    items: [
      { id: 'analytics', label: 'Analytics', icon: LineChart },
      { id: 'settings', label: 'Settings', icon: Settings }
    ]
  }
];

const BADGE_STYLES = {
  blue: 'bg-blue-500/15 text-blue-300 border-blue-500/30',
  emerald: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  amber: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  purple: 'bg-purple-500/15 text-purple-300 border-purple-500/30'
};

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab }) => (
  <aside
    className="w-64 xl:w-[17rem] liquid-glass border-r border-[rgba(51,65,85,0.4)] flex flex-col justify-between p-4 xl:p-5 min-h-screen sticky top-0 max-h-screen overflow-y-auto z-40 shrink-0"
    aria-label="Main navigation"
  >
    <div>
      {/* ── Brand — NoteNext ── */}
      <div className="flex items-center gap-3 pb-5 border-b border-slate-800/80 mb-5">
        <div className="relative shrink-0">
          <div className="w-11 h-11 rounded-2xl nn-gradient p-0.5 shadow-[0_0_22px_rgba(124,58,237,0.35)]">
            <div className="w-full h-full bg-white/90 rounded-[14px] flex items-center justify-center backdrop-blur">
              <ShieldAlert className="w-6 h-6 text-violet-600" />
            </div>
          </div>
          <span className="absolute -top-0.5 -right-0.5 flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500 border-2 border-white" />
          </span>
        </div>
        <div className="min-w-0">
          <span className="font-poppins font-bold text-[1.05rem] tracking-tight block leading-tight nn-text-gradient">
            NoteNext
          </span>
          <span className="flex items-center gap-1 text-[9.5px] font-medium tracking-wider text-violet-600 uppercase">
            <ShieldCheck className="w-2.5 h-2.5 shrink-0" />
            <span className="truncate">Intelligence Dashboard</span>
          </span>
        </div>
      </div>

      {/* ── Navigation Groups ── */}
      <nav className="space-y-5">
        {NAV_GROUPS.map(group => (
          <div key={group.heading}>
            <p className="px-3 text-[10px] font-semibold tracking-[0.12em] text-slate-500 uppercase mb-2">
              {group.heading}
            </p>
            <ul className="space-y-1">
              {group.items.map(item => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;

                return (
                  <li key={item.id}>
                    <button
                      onClick={() => setActiveTab(item.id)}
                      aria-current={isActive ? 'page' : undefined}
                      className={cn(
                        'w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-[13px] font-medium group relative',
                        'transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/60',
                        isActive
                          ? 'text-white'
                          : 'text-slate-400 hover:text-white hover:bg-white/[0.05] hover:translate-x-0.5'
                      )}
                    >
                      {/* Active pill background */}
                      {isActive && (
                        <motion.span
                          layoutId="sidebarActive"
                          transition={{ type: 'spring', stiffness: 380, damping: 32 }}
                          className="absolute inset-0 rounded-xl bg-gradient-to-r from-blue-600/25 to-purple-600/20 border border-blue-500/40 shadow-[0_0_18px_rgba(59,130,246,0.18)]"
                        />
                      )}
                      {/* Active left rail */}
                      {isActive && (
                        <motion.span
                          layoutId="sidebarRail"
                          transition={{ type: 'spring', stiffness: 380, damping: 32 }}
                          className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-6 rounded-r-full bg-gradient-to-b from-blue-400 to-purple-500 shadow-[0_0_8px_#3B82F6]"
                        />
                      )}

                      <span className="flex items-center gap-2.5 relative z-10 min-w-0">
                        <Icon className={cn(
                          'w-[18px] h-[18px] shrink-0 transition-colors duration-200',
                          isActive ? 'text-blue-400' : 'text-slate-500 group-hover:text-slate-200'
                        )} />
                        <span className="truncate">{item.label}</span>
                      </span>

                      <span className="flex items-center gap-1.5 relative z-10 shrink-0">
                        {item.badge && (
                          <span className={cn(
                            'px-1.5 py-0.5 text-[9px] font-mono font-bold rounded-md border',
                            BADGE_STYLES[item.badgeAccent || 'blue']
                          )}>
                            {item.badge}
                          </span>
                        )}
                        {item.dot && <span className={cn('w-1.5 h-1.5 rounded-full', item.dot)} />}
                        <ChevronRight className={cn(
                          'w-3.5 h-3.5 transition-all duration-200',
                          isActive
                            ? 'opacity-100 text-blue-400'
                            : 'opacity-0 -translate-x-1 text-slate-500 group-hover:opacity-100 group-hover:translate-x-0'
                        )} />
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>
    </div>

    {/* ── NoteNext Secure Footer ── */}
    <div className="pt-4 mt-5 border-t border-[rgba(51,65,85,0.5)] space-y-2.5">
      <div className="p-3 rounded-xl liquid-glass border border-violet-500/20 flex items-center gap-2.5">
        <div className="w-8 h-8 rounded-lg bg-violet-500/10 border border-violet-500/25 flex items-center justify-center shrink-0">
          <Lock className="w-4 h-4 text-violet-600" />
        </div>
        <div className="min-w-0">
          <span className="text-[11px] font-semibold text-slate-800 block leading-tight">NoteNext Secure</span>
          <span className="text-[9.5px] text-emerald-600 font-mono flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shrink-0" />
            BACKEND CONNECTED
          </span>
        </div>
      </div>
      <p className="text-[9px] font-mono text-slate-500 text-center tracking-wide">
        NoteNext v4.0 • LIQUID GLASS • 2026
      </p>
    </div>
  </aside>
);
