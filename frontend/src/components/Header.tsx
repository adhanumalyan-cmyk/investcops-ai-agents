import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  Search, Bell, ShieldCheck, ChevronDown, Sparkles, X, ExternalLink,
  UserCheck, CheckCheck, Cpu, Clock, Briefcase, Command
} from 'lucide-react';
import { mockNotifications, mockCases } from '../data/mockData';
import { CaseItem } from '../types/investigation';
import { cn } from '../utils/cn';
import { Badge } from './ui';

interface HeaderProps {
  onSelectCase: (c: CaseItem) => void;
  onOpenUpload: () => void;
  activeCaseId?: string;
}

/** Hook: closes a popover on outside click + Escape */
function useDismiss(ref: React.RefObject<HTMLDivElement | null>, onClose: () => void) {
  useEffect(() => {
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    };
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('mousedown', onDown);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDown);
      document.removeEventListener('keydown', onKey);
    };
  }, [ref, onClose]);
}

export const Header: React.FC<HeaderProps> = ({ onSelectCase, onOpenUpload, activeCaseId = 'KPC-2026-8941' }) => {
  const [query, setQuery] = useState('');
  const [searchOpen, setSearchOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [notifications, setNotifications] = useState(mockNotifications);
  const [now, setNow] = useState(new Date());

  const searchRef = useRef<HTMLDivElement>(null);
  const notifRef = useRef<HTMLDivElement>(null);
  const profileRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useDismiss(searchRef, useCallback(() => setSearchOpen(false), []));
  useDismiss(notifRef, useCallback(() => setNotifOpen(false), []));
  useDismiss(profileRef, useCallback(() => setProfileOpen(false), []));

  /* Live clock */
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  /* ⌘K / Ctrl+K focus shortcut */
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        inputRef.current?.focus();
        setSearchOpen(true);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const unread = notifications.filter(n => !n.read).length;

  const results = query.trim() === '' ? [] : mockCases.filter(c =>
    [c.id, c.name, c.category, c.primaryVector, ...c.iocs]
      .join(' ').toLowerCase().includes(query.toLowerCase())
  );

  const dateStr = now.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
  const timeStr = now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });

  return (
    <header className="h-16 lg:h-[4.5rem] liquid-glass border-b border-[rgba(51,65,85,0.4)] px-4 lg:px-6 xl:px-8 flex items-center gap-3 lg:gap-4 sticky top-0 z-30">

      {/* ── NoteNext Space Context ── */}
      <div className="hidden md:flex items-center gap-2.5 shrink-0">
        <div className="w-9 h-9 rounded-xl bg-violet-500/10 border border-violet-500/30 flex items-center justify-center shrink-0">
          <Briefcase className="w-4 h-4 text-violet-600" />
        </div>
        <div className="min-w-0">
          <span className="text-[9px] font-mono text-slate-500 uppercase tracking-wider block leading-none mb-0.5">NoteNext Space</span>
          <span className="text-xs font-mono font-bold text-violet-600 block leading-none">{activeCaseId}</span>
        </div>
      </div>

      <div className="hidden lg:block w-px h-8 bg-slate-800 shrink-0" />

      {/* ── Search ── */}
      <div className="flex-1 max-w-xl relative min-w-0" ref={searchRef}>
        <div className="relative flex items-center">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 pointer-events-none" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={e => { setQuery(e.target.value); setSearchOpen(true); }}
            onFocus={() => setSearchOpen(true)}
            placeholder="Search notes, cases, evidence…"
            aria-label="Search investigation database"
            className="w-full pl-10 pr-16 py-2 liquid-glass border border-[rgba(51,65,85,0.45)] rounded-xl text-xs font-mono text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500/60 focus:shadow-[0_0_0_3px_rgba(59,130,246,0.22)] transition-all"
          />
          {query ? (
            <button onClick={() => setQuery('')} aria-label="Clear search"
              className="absolute right-3 p-1 text-slate-500 hover:text-white rounded transition-colors">
              <X className="w-3.5 h-3.5" />
            </button>
          ) : (
            <kbd className="absolute right-3 hidden sm:flex items-center gap-0.5 px-1.5 py-0.5 text-[9px] font-mono text-slate-500 bg-slate-800/80 rounded border border-slate-700">
              <Command className="w-2.5 h-2.5" />K
            </kbd>
          )}
        </div>

        {searchOpen && query.trim() && (
          <div className="absolute top-full left-0 right-0 mt-2 liquid-glass border border-[rgba(51,65,85,0.5)] rounded-2xl shadow-2xl shadow-black/60 overflow-hidden z-50">
            <div className="px-3 py-2 bg-white/[0.03] border-b border-[rgba(51,65,85,0.4)] flex items-center justify-between text-[10px] font-mono text-slate-400">
              <span>{results.length} MATCHES</span>
              <span className="text-purple-400 flex items-center gap-1"><Sparkles className="w-3 h-3" /> CyberLLM Vector Search</span>
            </div>
            <div className="max-h-72 overflow-y-auto divide-y divide-[rgba(51,65,85,0.4)]">
              {results.length ? results.map(item => (
                <button key={item.id}
                  onClick={() => { onSelectCase(item); setSearchOpen(false); setQuery(''); }}
                  className="w-full p-3 text-left hover:bg-white/[0.04] transition-colors flex items-start justify-between gap-3 group">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 mb-0.5 flex-wrap">
                      <span className="font-mono text-[11px] font-bold text-violet-600">{item.id}</span>
                      <Badge accent={item.risk === 'CRITICAL' ? 'red' : item.risk === 'HIGH' ? 'amber' : 'blue'} size="xs">
                        {item.risk} {item.riskScore}
                      </Badge>
                    </div>
                    <p className="text-xs font-semibold text-slate-100 truncate">{item.name}</p>
                    <p className="text-[10px] text-slate-500 font-mono truncate">{item.primaryVector}</p>
                  </div>
                  <ExternalLink className="w-3.5 h-3.5 text-slate-600 group-hover:text-violet-600 shrink-0 mt-1 transition-colors" />
                </button>
              )) : (
                <div className="p-6 text-center text-[11px] text-slate-500 font-mono">
                  No match for "{query}" — press Enter for deep node scan.
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* ── Right controls ── */}
      <div className="flex items-center gap-2 lg:gap-2.5 ml-auto shrink-0">

        {/* AI Status */}
        <div className="hidden xl:flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-emerald-500/8 border border-emerald-500/25">
          <span className="relative flex h-2 w-2 shrink-0">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
          </span>
          <Cpu className="w-3.5 h-3.5 text-emerald-400" />
          <div className="leading-none">
            <span className="text-[8.5px] font-mono text-slate-500 uppercase block mb-0.5">AI Engine</span>
            <span className="text-[10px] font-mono font-bold text-emerald-400">NoteNext AI v4.0</span>
          </div>
        </div>

        {/* Date & Time */}
        <div className="hidden lg:flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-black/30 border border-white/[0.1]">
          <Clock className="w-3.5 h-3.5 text-violet-600 shrink-0" />
          <div className="leading-none">
            <span className="text-[8.5px] font-mono text-slate-500 uppercase block mb-0.5">{dateStr}</span>
            <span className="text-[10px] font-mono font-bold text-slate-200 tabular-nums">{timeStr} IST</span>
          </div>
        </div>

        {/* Quick upload */}
        <button onClick={onOpenUpload}
          className="hidden 2xl:inline-flex items-center gap-1.5 px-3 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white rounded-xl text-[11px] font-semibold shadow-[0_0_15px_rgba(59,130,246,0.3)] hover:shadow-[0_0_25px_rgba(139,92,246,0.45)] transition-all active:scale-95">
          <Sparkles className="w-3.5 h-3.5" /> Upload
        </button>

        {/* Notifications */}
        <div className="relative" ref={notifRef}>
          <button onClick={() => setNotifOpen(o => !o)} aria-label={`Notifications, ${unread} unread`}
            className="w-9 h-9 rounded-xl liquid-glass border border-[rgba(51,65,85,0.5)] hover:border-blue-500/50 flex items-center justify-center text-slate-300 hover:text-white transition-all relative focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/60">
            <Bell className="w-4 h-4" />
            {unread > 0 && (
              <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 bg-red-500 text-white font-bold text-[9px] rounded-full flex items-center justify-center border-2 border-[#111827]">
                {unread}
              </span>
            )}
          </button>

          {notifOpen && (
            <div className="absolute right-0 mt-2.5 w-[21rem] liquid-glass border border-[rgba(51,65,85,0.5)] rounded-2xl shadow-2xl shadow-black/60 overflow-hidden z-50">
              <div className="p-3.5 bg-white/[0.03] border-b border-[rgba(51,65,85,0.4)] flex items-center justify-between">
                <h3 className="font-poppins font-bold text-sm text-white flex items-center gap-2">
                  Live Threat Feed
                  {unread > 0 && <Badge accent="red" size="xs">{unread} NEW</Badge>}
                </h3>
                {unread > 0 && (
                  <button onClick={() => setNotifications(p => p.map(n => ({ ...n, read: true })))}
                    className="text-[10px] text-violet-600 hover:text-blue-300 flex items-center gap-1 font-mono transition-colors">
                    <CheckCheck className="w-3 h-3" /> Mark read
                  </button>
                )}
              </div>
              <div className="max-h-80 overflow-y-auto divide-y divide-[rgba(51,65,85,0.4)]">
                {notifications.map(n => (
                  <div key={n.id} className={cn('p-3 hover:bg-white/[0.04] transition-colors', !n.read && 'bg-blue-500/[0.06]')}>
                    <div className="flex items-start gap-2.5">
                      <span className={cn('w-2 h-2 rounded-full shrink-0 mt-1.5',
                        n.type === 'CRITICAL' ? 'bg-red-500 shadow-[0_0_6px_#EF4444]' :
                        n.type === 'WARNING' ? 'bg-amber-500 shadow-[0_0_6px_#F59E0B]' :
                        'bg-blue-400 shadow-[0_0_6px_#3B82F6]')} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2 mb-0.5">
                          <h4 className="text-[11.5px] font-semibold text-slate-100 truncate">{n.title}</h4>
                          <span className="text-[9px] text-slate-500 font-mono shrink-0">{n.time}</span>
                        </div>
                        <p className="text-[11px] text-slate-400 leading-relaxed">{n.message}</p>
                        {n.caseId && <span className="inline-block mt-1.5 text-[9px] font-mono font-bold text-violet-600 bg-violet-500/10 px-1.5 py-0.5 rounded border border-blue-500/20">{n.caseId}</span>}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <div className="p-2.5 bg-white/[0.03] border-t border-[rgba(51,65,85,0.4)] text-center">
                <span className="text-[9.5px] font-mono text-slate-500">Connected to NoteNext Cloud</span>
              </div>
            </div>
          )}
        </div>

        {/* Profile */}
        <div className="relative" ref={profileRef}>
          <button onClick={() => setProfileOpen(o => !o)} aria-label="Investigator profile"
            className="flex items-center gap-2 p-1 pl-2 rounded-xl liquid-glass border border-[rgba(51,65,85,0.5)] hover:border-blue-500/50 transition-all group focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/60">
            <div className="hidden md:flex flex-col items-end leading-none">
              <span className="text-[11px] font-bold text-slate-100 group-hover:text-violet-600 transition-colors">DySP Rajesh V.</span>
              <span className="text-[9px] text-slate-500 font-mono mt-0.5">KP-CYD-042</span>
            </div>
            <div className="relative shrink-0">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-purple-600 p-0.5">
                <div className="w-full h-full rounded-[6px] bg-[#0B1020]/90 flex items-center justify-center">
                  <UserCheck className="w-4 h-4 text-violet-600" />
                </div>
              </div>
              <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-emerald-400 rounded-full border-2 border-[#0B1020]" />
            </div>
            <ChevronDown className={cn('w-3.5 h-3.5 text-slate-500 transition-transform hidden sm:block', profileOpen && 'rotate-180')} />
          </button>

          {profileOpen && (
            <div className="absolute right-0 mt-2.5 w-64 liquid-glass border border-[rgba(51,65,85,0.5)] rounded-2xl shadow-2xl shadow-black/60 p-4 z-50">
              <div className="flex items-center gap-3 pb-3 border-b border-[rgba(51,65,85,0.4)]">
                <div className="w-10 h-10 rounded-xl bg-purple-500/15 border border-purple-500/35 flex items-center justify-center shrink-0">
                  <UserCheck className="w-5 h-5 text-purple-400" />
                </div>
                <div className="min-w-0">
                  <h4 className="text-[13px] font-bold text-slate-100 truncate">DySP Rajesh V. Kumar</h4>
                  <p className="text-[10px] text-violet-600 font-mono">NoteNext Intelligence Lead</p>
                </div>
              </div>
              <div className="mt-3 space-y-1.5 text-[11px] font-mono">
                {[
                  ['Badge ID', 'KP-CYD-042', 'text-white'],
                  ['Clearance', 'LEVEL 5', 'text-emerald-400'],
                  ['Station', 'NoteNext Lab', 'text-slate-200']
                ].map(([k, v, c]) => (
                  <div key={k} className="flex items-center justify-between p-2 rounded-lg bg-white/[0.04]">
                    <span className="text-slate-500">{k}</span>
                    <span className={cn('font-bold', c)}>{v}</span>
                  </div>
                ))}
              </div>
              <div className="mt-3 pt-3 border-t border-[rgba(51,65,85,0.4)] flex items-center justify-between text-[10px] font-mono">
                <span className="flex items-center gap-1 text-slate-400"><ShieldCheck className="w-3 h-3 text-emerald-400" /> MFA Verified</span>
                <span className="text-purple-400">v4.0</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
