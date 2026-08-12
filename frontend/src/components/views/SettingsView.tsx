import React, { useState } from 'react';
import { ShieldCheck, Cpu, Key, Save, CheckCircle2, Settings as SettingsIcon, Bell, Eye, EyeOff } from 'lucide-react';
import { PageHeader, GlassCard, CardHeader, CardOrb, Badge, Button, MOTION } from '../ui';
import { cn } from '../../utils/cn';

const Toggle: React.FC<{ on: boolean; onChange: () => void; label: string }> = ({ on, onChange, label }) => (
  <button
    role="switch" aria-checked={on} aria-label={label} onClick={onChange}
    className={cn(
      'w-11 h-6 rounded-full transition-colors relative p-0.5 shrink-0 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/60',
      on ? 'bg-emerald-500 shadow-[0_0_12px_rgba(16,185,129,0.4)]' : 'bg-slate-700'
    )}
  >
    <span className={cn('block w-5 h-5 rounded-full bg-white transition-transform duration-200', on ? 'translate-x-5' : 'translate-x-0')} />
  </button>
);

const SettingRow: React.FC<{ title: string; description: string; children: React.ReactNode }> = ({ title, description, children }) => (
  <div className="flex items-center justify-between gap-4 p-3.5 rounded-xl bg-white/[0.05] border border-white/[0.08] hover:border-white/[0.14] transition-colors">
    <div className="min-w-0">
      <span className="block text-[13px] font-semibold text-slate-100">{title}</span>
      <span className="block text-[10.5px] font-mono text-slate-500 mt-0.5 leading-relaxed">{description}</span>
    </div>
    {children}
  </div>
);

export const SettingsView: React.FC = () => {
  const [model, setModel] = useState('cyberllm-4.2');
  const [confidence, setConfidence] = useState(85);
  const [mfa, setMfa] = useState(true);
  const [alerts, setAlerts] = useState(true);
  const [autoEscalate, setAutoEscalate] = useState(false);
  const [showKey, setShowKey] = useState(false);
  const [saved, setSaved] = useState(false);

  const save = () => { setSaved(true); setTimeout(() => setSaved(false), 2400); };

  return (
    <div className="space-y-7 max-w-5xl">
      <PageHeader
        title="Platform Configuration"
        subtitle="Configure Cyberdome AI models, API credentials, clearance thresholds, and secure enclave parameters for this investigator workstation."
        icon={SettingsIcon}
        iconAccent="blue"
        badge={<Badge accent="purple">ADMIN ACCESS</Badge>}
        actions={
          <Button size="lg" icon={saved ? CheckCircle2 : Save} onClick={save}
            className={saved ? 'from-emerald-600 to-emerald-500' : ''}>
            {saved ? 'Configuration Saved' : 'Save System Settings'}
          </Button>
        }
      />

      <GlassCard accent="purple" padding="lg" {...MOTION.fadeUp(0.05)} className="overflow-hidden">
        <CardOrb accent="purple" />
        <CardHeader title="AI Neural Engine" icon={Cpu} accent="purple"
          right={<Badge accent="emerald" size="xs" dot>ONLINE</Badge>} />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 relative z-10">
          <div>
            <label htmlFor="model" className="block text-[11px] font-mono text-slate-400 mb-1.5">Primary Neural Model</label>
            <select id="model" value={model} onChange={e => setModel(e.target.value)}
              className="w-full bg-black/40 border border-blue-500/25 rounded-xl p-2.5 text-[12px] text-white font-mono focus:outline-none focus:border-blue-500 transition-colors">
              <option value="cyberllm-4.2">NoteNext CyberLLM v4.2 (14B fine-tuned)</option>
              <option value="palantir">Palantir Gotham Compatible Matrix v2</option>
              <option value="ibm-i2">IBM i2 Threat Classifier Engine</option>
            </select>
          </div>
          <div>
            <label htmlFor="conf" className="block text-[11px] font-mono text-slate-400 mb-1.5">
              Threat Confidence Threshold — <span className="text-blue-400 font-bold">{confidence}%</span>
            </label>
            <input id="conf" type="range" min={50} max={99} value={confidence}
              onChange={e => setConfidence(Number(e.target.value))}
              className="w-full mt-3 accent-blue-500 cursor-pointer" />
            <div className="flex justify-between text-[9.5px] font-mono text-slate-600 mt-1">
              <span>50% permissive</span><span>99% strict</span>
            </div>
          </div>
        </div>
      </GlassCard>

      <GlassCard accent="blue" padding="lg" {...MOTION.fadeUp(0.1)} className="overflow-hidden">
        <CardOrb accent="blue" />
        <CardHeader title="API Credentials" icon={Key} accent="blue" />
        <div className="space-y-3 relative z-10">
          <div>
            <label htmlFor="ncrp" className="block text-[11px] font-mono text-slate-400 mb-1.5">NCRP National Portal API Token</label>
            <div className="relative">
              <input id="ncrp" type={showKey ? 'text' : 'password'} readOnly
                value="ncrp_live_token_kp_cyberdome_904128"
                className="w-full bg-black/40 border border-white/[0.1] rounded-xl p-2.5 pr-11 text-[12px] font-mono text-blue-400" />
              <button onClick={() => setShowKey(s => !s)} aria-label={showKey ? 'Hide token' : 'Show token'}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-200 transition-colors">
                {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>
          <div>
            <label htmlFor="rpc" className="block text-[11px] font-mono text-slate-400 mb-1.5">Blockchain Trace RPC Endpoint</label>
            <input id="rpc" type="text" readOnly
              value="https://grpc.cyberdome.kerala.gov.in/v2/blockchain-ledger"
              className="w-full bg-black/40 border border-white/[0.1] rounded-xl p-2.5 text-[12px] font-mono text-purple-300" />
          </div>
        </div>
      </GlassCard>

      <GlassCard accent="emerald" padding="lg" {...MOTION.fadeUp(0.15)} className="overflow-hidden">
        <CardOrb accent="emerald" position="-bottom-16 -right-16" />
        <CardHeader title="Security & Enclave Controls" icon={ShieldCheck} accent="emerald" />
        <div className="space-y-3 relative z-10">
          <SettingRow title="Enforce Level 5 Hardware Token MFA"
            description="Requires YubiKey or officer security token for court dossier export.">
            <Toggle on={mfa} onChange={() => setMfa(m => !m)} label="Hardware MFA" />
          </SettingRow>
          <SettingRow title="Real-time Threat Alerts"
            description="Push critical IOC matches to the live notification feed instantly.">
            <Toggle on={alerts} onChange={() => setAlerts(a => !a)} label="Threat alerts" />
          </SettingRow>
          <SettingRow title="Auto-escalate Critical Cases"
            description="Automatically route risk scores above 90 to the duty supervisor queue.">
            <Toggle on={autoEscalate} onChange={() => setAutoEscalate(a => !a)} label="Auto escalate" />
          </SettingRow>
        </div>
      </GlassCard>

      <GlassCard accent="amber" padding="lg" {...MOTION.fadeUp(0.2)}>
        <CardHeader title="Notification Preferences" icon={Bell} accent="amber" />
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {['Critical Incidents', 'Report Completion', 'Weekly Digest'].map((label, i) => (
            <div key={label} className="p-3 rounded-xl bg-white/[0.04] border border-white/[0.08] text-center">
              <span className="block text-[12px] font-semibold text-slate-200 mb-2">{label}</span>
              <Badge accent={i === 0 ? 'red' : i === 1 ? 'emerald' : 'blue'} size="xs">
                {i === 2 ? 'EMAIL' : 'IN-APP + EMAIL'}
              </Badge>
            </div>
          ))}
        </div>
      </GlassCard>
    </div>
  );
};
