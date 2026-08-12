/**
 * ═══════════════════════════════════════════════════════════
 * NoteNext — Shared Enterprise UI Kit
 * ───────────────────────────────────────────────────────────
 * Single source of truth for every card, button, badge,
 * heading, and animation primitive used across the platform.
 * Guarantees identical radius, shadow, glow, spacing & motion.
 * ═══════════════════════════════════════════════════════════
 */
import React, { useState, useEffect, useRef, useMemo } from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';
import { LucideIcon, Loader2 } from 'lucide-react';
import { cn } from '../../utils/cn';

/* ═══════════════════════════════════════════════════════════
   DESIGN TOKENS
   ═══════════════════════════════════════════════════════════ */
export type AccentColor =
  | 'blue' | 'purple' | 'emerald' | 'amber' | 'red'
  | 'pink' | 'rose' | 'cyan' | 'orange' | 'slate';

interface AccentTheme {
  text: string;
  bg: string;
  border: string;
  borderHover: string;
  glow: string;
  glowHover: string;
  dot: string;
  raw: string;
}

export const ACCENTS: Record<AccentColor, AccentTheme> = {
  blue:    { text: 'text-blue-400',    bg: 'bg-blue-500/10',    border: 'border-blue-500/30',    borderHover: 'hover:border-blue-500/60',    glow: 'shadow-[0_0_15px_rgba(59,130,246,0.15)]',  glowHover: 'hover:shadow-[0_0_25px_rgba(59,130,246,0.25)]',  dot: 'bg-blue-400',    raw: '#3B82F6' },
  purple:  { text: 'text-purple-400',  bg: 'bg-purple-500/10',  border: 'border-purple-500/30',  borderHover: 'hover:border-purple-500/60',  glow: 'shadow-[0_0_15px_rgba(139,92,246,0.15)]',  glowHover: 'hover:shadow-[0_0_25px_rgba(139,92,246,0.25)]',  dot: 'bg-purple-400',  raw: '#8B5CF6' },
  emerald: { text: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', borderHover: 'hover:border-emerald-500/60', glow: 'shadow-[0_0_15px_rgba(16,185,129,0.15)]',  glowHover: 'hover:shadow-[0_0_25px_rgba(16,185,129,0.25)]',  dot: 'bg-emerald-400', raw: '#22C55E' },
  amber:   { text: 'text-amber-400',   bg: 'bg-amber-500/10',   border: 'border-amber-500/30',   borderHover: 'hover:border-amber-500/60',   glow: 'shadow-[0_0_15px_rgba(245,158,11,0.15)]',  glowHover: 'hover:shadow-[0_0_25px_rgba(245,158,11,0.25)]',  dot: 'bg-amber-400',   raw: '#F59E0B' },
  red:     { text: 'text-red-400',     bg: 'bg-red-500/10',     border: 'border-red-500/30',     borderHover: 'hover:border-red-500/60',     glow: 'shadow-[0_0_15px_rgba(239,68,68,0.18)]',   glowHover: 'hover:shadow-[0_0_25px_rgba(239,68,68,0.3)]',    dot: 'bg-red-400',     raw: '#EF4444' },
  pink:    { text: 'text-pink-400',    bg: 'bg-pink-500/10',    border: 'border-pink-500/30',    borderHover: 'hover:border-pink-500/60',    glow: 'shadow-[0_0_15px_rgba(236,72,153,0.15)]',  glowHover: 'hover:shadow-[0_0_25px_rgba(236,72,153,0.25)]',  dot: 'bg-pink-400',    raw: '#EC4899' },
  rose:    { text: 'text-rose-400',    bg: 'bg-rose-500/10',    border: 'border-rose-500/30',    borderHover: 'hover:border-rose-500/60',    glow: 'shadow-[0_0_15px_rgba(244,63,94,0.15)]',   glowHover: 'hover:shadow-[0_0_25px_rgba(244,63,94,0.25)]',   dot: 'bg-rose-400',    raw: '#F43F5E' },
  cyan:    { text: 'text-cyan-400',    bg: 'bg-cyan-500/10',    border: 'border-cyan-500/30',    borderHover: 'hover:border-cyan-500/60',    glow: 'shadow-[0_0_15px_rgba(6,182,212,0.15)]',   glowHover: 'hover:shadow-[0_0_25px_rgba(6,182,212,0.25)]',   dot: 'bg-cyan-400',    raw: '#06B6D4' },
  orange:  { text: 'text-orange-400',  bg: 'bg-orange-500/10',  border: 'border-orange-500/30',  borderHover: 'hover:border-orange-500/60',  glow: 'shadow-[0_0_15px_rgba(249,115,22,0.15)]',  glowHover: 'hover:shadow-[0_0_25px_rgba(249,115,22,0.25)]',  dot: 'bg-orange-400',  raw: '#F97316' },
  slate:   { text: 'text-slate-400',   bg: 'bg-slate-500/10',   border: 'border-slate-700',      borderHover: 'hover:border-slate-600',      glow: '',                                          glowHover: '',                                               dot: 'bg-slate-400',   raw: '#94A3B8' }
};

/* Shared motion presets — keeps timing identical everywhere */
export const MOTION = {
  page:      { initial: { opacity: 0, y: 14 }, animate: { opacity: 1, y: 0 }, exit: { opacity: 0, y: -10 }, transition: { duration: 0.32, ease: [0.22, 1, 0.36, 1] as const } },
  fadeUp:    (d = 0) => ({ initial: { opacity: 0, y: 12 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.4, delay: d, ease: [0.22, 1, 0.36, 1] as const } }),
  fadeIn:    (d = 0) => ({ initial: { opacity: 0 }, animate: { opacity: 1 }, transition: { duration: 0.4, delay: d } }),
  slideLeft: (d = 0) => ({ initial: { opacity: 0, x: -10 }, animate: { opacity: 1, x: 0 }, transition: { duration: 0.35, delay: d } }),
  scaleIn:   (d = 0) => ({ initial: { opacity: 0, scale: 0.94 }, animate: { opacity: 1, scale: 1 }, transition: { duration: 0.35, delay: d, type: 'spring' as const, stiffness: 220, damping: 22 } })
};

/* ═══════════════════════════════════════════════════════════
   GLASS CARD — the universal surface
   ═══════════════════════════════════════════════════════════ */
interface GlassCardProps extends Omit<HTMLMotionProps<'div'>, 'ref'> {
  accent?: AccentColor;
  hoverable?: boolean;
  glow?: boolean;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  children: React.ReactNode;
  className?: string;
}

export const GlassCard = React.forwardRef<HTMLDivElement, GlassCardProps>(({
  accent = 'blue',
  hoverable = false,
  glow = false,
  padding = 'md',
  className,
  children,
  ...rest
}, ref) => {
  const a = ACCENTS[accent];
  const pad = { none: '', sm: 'p-4', md: 'p-5', lg: 'p-6' }[padding];

  return (
    <motion.div
      ref={ref}
      className={cn(
        /* Liquid-glass surface */
        'liquid-glass rounded-2xl border transition-all duration-300 relative',
        a.border,
        glow && a.glow,
        hoverable && cn(a.borderHover, a.glowHover, 'hover:-translate-y-[3px] hover:shadow-[0_14px_48px_rgba(0,0,0,0.42)] cursor-pointer'),
        pad,
        className
      )}
      {...rest}
    >
      {children}
    </motion.div>
  );
});
GlassCard.displayName = 'GlassCard';

/* Decorative ambient orb for card backgrounds */
export const CardOrb: React.FC<{ accent?: AccentColor; position?: string; size?: string }> = ({
  accent = 'blue',
  position = '-top-16 -right-16',
  size = 'w-48 h-48'
}) => {
  const bgMap: Record<AccentColor, string> = {
    blue: 'bg-white/[0.04]', purple: 'bg-white/[0.04]', emerald: 'bg-white/[0.04]',
    amber: 'bg-white/[0.04]', red: 'bg-white/[0.04]', pink: 'bg-white/[0.04]',
    rose: 'bg-white/[0.04]', cyan: 'bg-white/[0.04]', orange: 'bg-white/[0.04]', slate: 'bg-white/[0.04]'
  };
  return <div className={cn('absolute rounded-full blur-3xl pointer-events-none', position, size, bgMap[accent])} aria-hidden="true" />;
};

/* ═══════════════════════════════════════════════════════════
   BUTTON — 4 unified variants
   ═══════════════════════════════════════════════════════════ */
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  icon?: LucideIcon;
  iconRight?: LucideIcon;
  loading?: boolean;
  children?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  icon: Icon,
  iconRight: IconRight,
  loading = false,
  disabled,
  className,
  children,
  ...rest
}) => {
  const sizes = {
    sm: 'px-3 py-1.5 text-xs gap-1.5',
    md: 'px-4 py-2 text-xs gap-2',
    lg: 'px-6 py-2.5 text-sm gap-2'
  }[size];

  const variants = {
    /* Primary — gradient with ripple glow */
    primary: 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white border border-transparent shadow-[0_0_22px_rgba(59,130,246,0.32)] hover:shadow-[0_0_32px_rgba(139,92,246,0.48)] ripple',
    /* Secondary — liquid-glass surface */
    secondary: 'liquid-glass text-slate-200 hover:text-white border border-[rgba(51,65,85,0.45)] hover:border-blue-500/50 hover:shadow-[0_8px_32px_rgba(0,0,0,0.35)]',
    /* Ghost — minimal transparent */
    ghost: 'bg-transparent hover:bg-white/5 text-slate-400 hover:text-white border border-transparent hover:border-[rgba(51,65,85,0.5)]',
    /* Danger */
    danger: 'bg-red-500/12 hover:bg-red-500/22 text-red-300 hover:text-red-200 border border-red-500/30 hover:border-red-500/55 hover:shadow-[0_0_22px_rgba(239,68,68,0.28)]'
  }[variant];

  const iconSize = size === 'lg' ? 'w-4 h-4' : 'w-3.5 h-3.5';

  return (
    <button
      disabled={disabled || loading}
      className={cn(
        'inline-flex items-center justify-center font-semibold rounded-xl transition-all duration-200 active:scale-[0.97]',
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/60 focus-visible:ring-offset-2 focus-visible:ring-offset-white',
        'disabled:opacity-45 disabled:cursor-not-allowed disabled:shadow-none disabled:active:scale-100',
        sizes, variants, className
      )}
      {...rest}
    >
      {loading ? <Loader2 className={cn(iconSize, 'animate-spin')} /> : Icon && <Icon className={iconSize} />}
      {children}
      {IconRight && !loading && <IconRight className={iconSize} />}
    </button>
  );
};

/* ═══════════════════════════════════════════════════════════
   BADGE
   ═══════════════════════════════════════════════════════════ */
interface BadgeProps {
  accent?: AccentColor;
  icon?: LucideIcon;
  pulse?: boolean;
  dot?: boolean;
  glow?: boolean;
  size?: 'xs' | 'sm';
  children: React.ReactNode;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  accent = 'blue', icon: Icon, pulse, dot, glow, size = 'sm', children, className
}) => {
  const a = ACCENTS[accent];
  const sizing = size === 'xs' ? 'px-1.5 py-0.5 text-[9px] gap-1' : 'px-2.5 py-1 text-[10px] gap-1.5';

  return (
    <span className={cn(
      'inline-flex items-center font-mono font-bold rounded-lg border whitespace-nowrap',
      a.bg, a.text, a.border, glow && a.glow, pulse && 'animate-pulse', sizing, className
    )}>
      {dot && <span className={cn('w-1.5 h-1.5 rounded-full shrink-0', a.dot)} />}
      {Icon && <Icon className={size === 'xs' ? 'w-2.5 h-2.5' : 'w-3 h-3'} />}
      {children}
    </span>
  );
};

/* ═══════════════════════════════════════════════════════════
   PAGE HEADER — identical across all 8 pages
   ═══════════════════════════════════════════════════════════ */
interface PageHeaderProps {
  title: string;
  subtitle: string;
  icon: LucideIcon;
  iconAccent?: AccentColor;
  badge?: React.ReactNode;
  actions?: React.ReactNode;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title, subtitle, icon: Icon, iconAccent = 'blue', badge, actions
}) => (
  <motion.header
    {...MOTION.fadeUp()}
    className="flex flex-col lg:flex-row lg:items-start justify-between gap-4 border-b border-slate-800/80 pb-5"
  >
    <div className="min-w-0">
      <div className="flex items-center gap-2.5 flex-wrap">
        <h1 className="font-poppins font-bold text-2xl lg:text-[1.75rem] text-white tracking-tight flex items-center gap-2.5 leading-tight">
          <Icon className={cn('w-7 h-7 lg:w-8 lg:h-8 shrink-0', ACCENTS[iconAccent].text)} />
          {title}
        </h1>
        {badge}
      </div>
      <p className="text-sm text-slate-400 mt-1.5 max-w-3xl font-sans leading-relaxed">{subtitle}</p>
    </div>
    {actions && <div className="flex items-center gap-2.5 shrink-0 flex-wrap">{actions}</div>}
  </motion.header>
);

/* ═══════════════════════════════════════════════════════════
   SECTION HEADER — numbered / iconed section dividers
   ═══════════════════════════════════════════════════════════ */
interface SectionHeaderProps {
  title: string;
  icon?: LucideIcon;
  number?: string;
  accent?: AccentColor;
  badge?: React.ReactNode;
  right?: React.ReactNode;
  divider?: boolean;
}

export const SectionHeader: React.FC<SectionHeaderProps> = ({
  title, icon: Icon, number, accent = 'blue', badge, right, divider
}) => {
  const a = ACCENTS[accent];
  return (
    <div className="flex items-center gap-2 mb-3 flex-wrap">
      {number && (
        <div className={cn('w-6 h-6 rounded-lg border flex items-center justify-center shrink-0', a.bg, a.border)}>
          <span className={cn('text-[10px] font-mono font-bold', a.text)}>{number}</span>
        </div>
      )}
      {Icon && !number && <Icon className={cn('w-4 h-4 shrink-0', a.text)} />}
      <h2 className="font-poppins font-bold text-lg text-white leading-tight">{title}</h2>
      {badge}
      {divider && <div className="flex-1 h-px bg-slate-800/70 ml-2 min-w-[2rem]" />}
      {right && <div className="ml-auto flex items-center gap-2">{right}</div>}
    </div>
  );
};

/* Compact card header used inside panels */
export const CardHeader: React.FC<{
  title: string; icon?: LucideIcon; accent?: AccentColor; right?: React.ReactNode;
}> = ({ title, icon: Icon, accent = 'blue', right }) => (
  <div className="flex items-center gap-2 border-b border-slate-800 pb-3 mb-4 relative z-10">
    {Icon && <Icon className={cn('w-4 h-4 shrink-0', ACCENTS[accent].text)} />}
    <h3 className="font-poppins font-bold text-sm text-white">{title}</h3>
    {right && <div className="ml-auto flex items-center gap-2">{right}</div>}
  </div>
);

/* ═══════════════════════════════════════════════════════════
   ANIMATED COUNTER
   ═══════════════════════════════════════════════════════════ */
export const AnimatedCounter: React.FC<{
  target: number; duration?: number; suffix?: string; prefix?: string; run?: boolean;
}> = ({ target, duration = 1600, suffix = '', prefix = '', run = true }) => {
  const [val, setVal] = useState(0);
  const raf = useRef<number>(0);

  useEffect(() => {
    if (!run) return;
    const start = performance.now();
    const tick = (now: number) => {
      const p = Math.min((now - start) / duration, 1);
      setVal(Math.round((1 - Math.pow(1 - p, 3)) * target));
      if (p < 1) raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf.current);
  }, [target, duration, run]);

  return <span>{prefix}{val.toLocaleString()}{suffix}</span>;
};

/* ═══════════════════════════════════════════════════════════
   STAT TILE — unified metric card
   ═══════════════════════════════════════════════════════════ */
interface StatTileProps {
  label: string;
  value: number | string;
  icon: LucideIcon;
  accent?: AccentColor;
  caption?: string;
  suffix?: string;
  animate?: boolean;
  delay?: number;
  onClick?: () => void;
  badge?: React.ReactNode;
}

export const StatTile: React.FC<StatTileProps> = ({
  label, value, icon: Icon, accent = 'blue', caption, suffix = '', animate = true, delay = 0, onClick, badge
}) => {
  const a = ACCENTS[accent];
  const numeric = typeof value === 'number';

  return (
    <motion.div
      {...MOTION.fadeUp(delay)}
      whileHover={{ y: -3 }}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick(); } } : undefined}
      className={cn(
        'liquid-glass rounded-2xl border p-4 transition-all duration-300 relative overflow-hidden group',
        a.border, a.borderHover, a.glowHover,
        onClick && 'cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/60'
      )}
    >
      <div className={cn('absolute -top-10 -right-10 w-24 h-24 rounded-full blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500', a.bg)} aria-hidden="true" />

      <div className="flex items-start justify-between mb-2 relative z-10 gap-2">
        <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider leading-tight">{label}</span>
        <div className={cn('w-9 h-9 rounded-xl border flex items-center justify-center shrink-0', a.bg, a.border)}>
          <Icon className={cn('w-4 h-4', a.text)} />
        </div>
      </div>

      <div className="relative z-10 flex items-baseline gap-2 flex-wrap">
        <h3 className={cn('font-poppins font-extrabold text-2xl tracking-tight', a.text)}>
          {numeric && animate
            ? <AnimatedCounter target={value as number} suffix={suffix} duration={1500 + delay * 800} />
            : <>{value}{suffix}</>}
        </h3>
        {badge}
      </div>

      {caption && <p className="text-[11px] text-slate-500 font-mono mt-1 relative z-10 leading-tight">{caption}</p>}
    </motion.div>
  );
};

/* ═══════════════════════════════════════════════════════════
   CIRCULAR PROGRESS
   ═══════════════════════════════════════════════════════════ */
export const CircularProgress: React.FC<{
  value: number; size?: number; strokeWidth?: number; accent?: AccentColor; label?: string; sublabel?: string;
}> = ({ value, size = 110, strokeWidth = 8, accent = 'blue', label, sublabel }) => {
  const r = (size - strokeWidth) / 2;
  const c = 2 * Math.PI * r;
  const stroke = ACCENTS[accent].raw;
  const uid = useMemo(() => `cp-${Math.random().toString(36).slice(2, 9)}`, []);

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90" role="img" aria-label={`${label}: ${value}%`}>
          <defs>
            <linearGradient id={uid} x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor={stroke} stopOpacity={1} />
              <stop offset="100%" stopColor={stroke} stopOpacity={0.55} />
            </linearGradient>
          </defs>
          <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,0.14)" strokeWidth={strokeWidth} />
          <motion.circle
            cx={size / 2} cy={size / 2} r={r} fill="none"
            stroke={`url(#${uid})`} strokeWidth={strokeWidth} strokeLinecap="round"
            strokeDasharray={c}
            initial={{ strokeDashoffset: c }}
            animate={{ strokeDashoffset: c * (1 - value / 100) }}
            transition={{ duration: 1.5, ease: 'easeOut', delay: 0.25 }}
            style={{ filter: `drop-shadow(0 0 6px ${stroke}70)` }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-poppins font-extrabold text-2xl text-white leading-none">{value}%</span>
          {sublabel && <span className="text-[9px] font-mono text-slate-500 uppercase mt-0.5">{sublabel}</span>}
        </div>
      </div>
      {label && <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider font-bold">{label}</span>}
    </div>
  );
};

/* ═══════════════════════════════════════════════════════════
   PROGRESS BAR
   ═══════════════════════════════════════════════════════════ */
export const ProgressBar: React.FC<{
  value: number; accent?: AccentColor; height?: string; gradient?: boolean; showLabel?: boolean; label?: string;
}> = ({ value, accent = 'blue', height = 'h-1.5', gradient = true, showLabel, label }) => (
  <div className="w-full">
    {showLabel && (
      <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 mb-1">
        <span>{label || 'Progress'}</span>
        <span className={ACCENTS[accent].text}>{value}%</span>
      </div>
    )}
    <div
      className={cn('w-full bg-slate-800 rounded-full overflow-hidden border border-slate-800', height)}
      role="progressbar" aria-valuenow={value} aria-valuemin={0} aria-valuemax={100}
    >
      <motion.div
        className={cn('h-full rounded-full',
          gradient
            ? accent === 'emerald' ? 'bg-gradient-to-r from-emerald-500 to-emerald-400'
            : accent === 'red' ? 'bg-gradient-to-r from-red-500 to-orange-400'
            : 'bg-gradient-to-r from-blue-500 via-purple-500 to-blue-400'
            : ACCENTS[accent].dot
        )}
        initial={{ width: 0 }}
        animate={{ width: `${value}%` }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
      />
    </div>
  </div>
);

/* ═══════════════════════════════════════════════════════════
   EMPTY STATE
   ═══════════════════════════════════════════════════════════ */
export const EmptyState: React.FC<{
  icon: LucideIcon; title: string; description?: string; action?: React.ReactNode; compact?: boolean;
}> = ({ icon: Icon, title, description, action, compact }) => (
  <motion.div
    {...MOTION.fadeIn()}
    className={cn(
      'flex flex-col items-center justify-center text-center rounded-2xl border border-dashed border-slate-800',
      compact ? 'py-8 px-4' : 'py-14 px-6'
    )}
  >
    <div className="w-14 h-14 rounded-2xl bg-slate-900/80 border border-slate-800 flex items-center justify-center mb-3">
      <Icon className="w-7 h-7 text-slate-600" />
    </div>
    <h4 className="font-poppins font-bold text-sm text-slate-300">{title}</h4>
    {description && <p className="text-xs text-slate-500 mt-1 max-w-sm font-sans leading-relaxed">{description}</p>}
    {action && <div className="mt-4">{action}</div>}
  </motion.div>
);

/* ═══════════════════════════════════════════════════════════
   SKELETON LOADER
   ═══════════════════════════════════════════════════════════ */
export const Skeleton: React.FC<{ className?: string }> = ({ className }) => (
  <div className={cn('animate-pulse rounded-xl bg-slate-800/60', className)} aria-hidden="true" />
);

/* ═══════════════════════════════════════════════════════════
   STICKY ACTION BAR — identical footer on action pages
   ═══════════════════════════════════════════════════════════ */
export const ActionBar: React.FC<{ left?: React.ReactNode; children: React.ReactNode }> = ({ left, children }) => (
  <div className="sticky bottom-0 -mx-6 lg:-mx-8 px-6 lg:px-8 py-4 liquid-glass border-t border-[rgba(51,65,85,0.4)] flex flex-col sm:flex-row items-center justify-between gap-3 z-30">
    <div className="text-xs font-mono text-slate-400 flex items-center gap-2 text-center sm:text-left">{left}</div>
    <div className="flex items-center gap-3 flex-wrap justify-center">{children}</div>
  </div>
);

/* ═══════════════════════════════════════════════════════════
   FLOATING PARTICLES — ambient background
   ═══════════════════════════════════════════════════════════ */
export const FloatingParticles: React.FC<{ count?: number }> = ({ count = 24 }) => {
  const particles = useMemo(() =>
    Array.from({ length: count }, (_, i) => ({
      id: i,
      left: `${Math.random() * 100}%`,
      size: `${2 + Math.random() * 3}px`,
      bg: Math.random() > 0.5 ? 'rgba(59,130,246,0.35)' : 'rgba(139,92,246,0.35)',
      dur: `${8 + Math.random() * 12}s`,
      delay: `${Math.random() * 10}s`
    })), [count]);

  return (
    <div className="particles-container" aria-hidden="true">
      {particles.map(p => (
        <div key={p.id} className="particle" style={{
          left: p.left, width: p.size, height: p.size, background: p.bg,
          animationDuration: p.dur, animationDelay: p.delay
        }} />
      ))}
    </div>
  );
};

/* ═══════════════════════════════════════════════════════════
   ENTITY TAG
   ═══════════════════════════════════════════════════════════ */
export const EntityTag: React.FC<{ accent?: AccentColor; children: React.ReactNode }> = ({ accent = 'blue', children }) => {
  const a = ACCENTS[accent];
  return (
    <span className={cn('px-2 py-1 rounded-lg text-[11px] font-mono font-semibold border transition-all hover:scale-[1.03] cursor-default', a.bg, a.text, a.border)}>
      {children}
    </span>
  );
};

/* ═══════════════════════════════════════════════════════════
   TIMELINE ITEM — shared by Results + Report
   ═══════════════════════════════════════════════════════════ */
export const TimelineItem: React.FC<{
  date: string; title: string; description: string;
  severity?: 'info' | 'warn' | 'critical';
  icon: LucideIcon; isLast?: boolean; index?: number;
}> = ({ date, title, description, severity = 'info', icon: Icon, isLast, index = 0 }) => {
  const isCritical = severity === 'critical';
  const isWarn = severity === 'warn';

  const nodeStyle = isCritical
    ? 'bg-red-500/20 border-red-500 shadow-[0_0_20px_rgba(239,68,68,0.3)]'
    : isWarn
    ? 'bg-amber-500/15 border-amber-500/40 shadow-[0_0_12px_rgba(245,158,11,0.2)]'
    : 'bg-blue-500/15 border-blue-500/40 shadow-[0_0_12px_rgba(59,130,246,0.2)]';

  const iconColor = isCritical ? 'text-red-400' : isWarn ? 'text-amber-400' : 'text-blue-400';
  const titleColor = isCritical ? 'text-red-300' : isWarn ? 'text-amber-200' : 'text-white';

  return (
    <div className="flex gap-4">
      <div className="flex flex-col items-center shrink-0">
        <motion.div
          initial={{ scale: 0 }} animate={{ scale: 1 }}
          transition={{ delay: 0.15 + index * 0.11, type: 'spring', stiffness: 260, damping: 18 }}
          className={cn('relative w-10 h-10 rounded-2xl flex items-center justify-center border', nodeStyle)}
        >
          <Icon className={cn('w-5 h-5', iconColor)} />
          {isCritical && (
            <motion.span
              className="absolute inset-0 rounded-2xl border-2 border-red-500/40"
              animate={{ scale: [1, 1.28, 1], opacity: [0.65, 0, 0.65] }}
              transition={{ repeat: Infinity, duration: 2 }}
            />
          )}
        </motion.div>
        {!isLast && (
          <motion.div
            initial={{ scaleY: 0 }} animate={{ scaleY: 1 }}
            transition={{ delay: 0.25 + index * 0.11, duration: 0.32 }}
            style={{ transformOrigin: 'top' }}
            className="w-0.5 flex-1 min-h-[24px] rounded-full bg-gradient-to-b from-blue-500/40 to-slate-800"
          />
        )}
      </div>

      <motion.div {...MOTION.slideLeft(0.2 + index * 0.11)} className="pb-5 flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1 flex-wrap">
          <span className="font-mono text-[11px] font-bold text-slate-500">{date}</span>
          <span className={cn('font-poppins font-bold text-sm', titleColor)}>{title}</span>
          {isCritical && <Badge accent="red" size="xs" pulse>CRITICAL</Badge>}
        </div>
        <p className="text-xs text-slate-400 leading-relaxed font-sans">{description}</p>
      </motion.div>
    </div>
  );
};

/* ═══════════════════════════════════════════════════════════
   GRAPH NODE — shared relationship graph node
   ═══════════════════════════════════════════════════════════ */
export const GraphNode: React.FC<{
  label: string; sublabel: string; accent: AccentColor; index: number; tag?: string;
}> = ({ label, sublabel, accent, index, tag }) => {
  const a = ACCENTS[accent];
  return (
    <motion.div
      {...MOTION.scaleIn(0.15 + index * 0.1)}
      whileHover={{ scale: 1.02, x: 2 }}
      className={cn('flex items-center gap-3 p-3 rounded-xl border transition-all', a.bg, a.border, a.glow)}
    >
      <motion.span
        className={cn('w-3 h-3 rounded-full shrink-0', a.dot)}
        style={{ boxShadow: `0 0 8px ${a.raw}` }}
        animate={{ scale: [1, 1.35, 1], opacity: [0.75, 1, 0.75] }}
        transition={{ repeat: Infinity, duration: 2 + index * 0.25 }}
      />
      <div className="min-w-0 flex-1">
        <span className={cn('font-poppins font-bold text-xs block leading-tight', a.text)}>{label}</span>
        <span className="text-[10px] text-slate-400 font-mono truncate block">{sublabel}</span>
      </div>
      {tag && <Badge accent={accent} size="xs">{tag}</Badge>}
    </motion.div>
  );
};

/* ═══════════════════════════════════════════════════════════
   INFO ROW — label/value pair
   ═══════════════════════════════════════════════════════════ */
export const InfoRow: React.FC<{
  label: string; value: React.ReactNode; icon?: LucideIcon; accent?: AccentColor;
}> = ({ label, value, icon: Icon, accent = 'slate' }) => (
  <div className="flex items-center justify-between p-3 rounded-xl bg-white/[0.04] border border-[rgba(51,65,85,0.45)] hover:border-[rgba(51,65,85,0.7)] transition-colors text-xs gap-3">
    <span className="text-slate-400 font-mono flex items-center gap-2 min-w-0">
      {Icon && <Icon className={cn('w-3.5 h-3.5 shrink-0', ACCENTS[accent].text)} />}
      <span className="truncate">{label}</span>
    </span>
    <span className="font-bold text-slate-100 shrink-0">{value}</span>
  </div>
);
