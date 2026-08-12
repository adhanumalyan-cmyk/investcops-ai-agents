import React, { useState, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Briefcase, Clock, ShieldAlert, FileCheck2 } from 'lucide-react';

import GradientWaves from './components/GradientWaves';
import { Sidebar } from './components/Sidebar';
import { CaseDetailModal } from './components/CaseDetailModal';
import { DashboardView } from './components/views/DashboardView';
import { CasesView } from './components/views/CasesView';
import { UploadEvidenceView } from './components/views/UploadEvidenceView';
import { AIProcessingView } from './components/views/AIProcessingView';
import { InvestigationResultsView } from './components/views/InvestigationResultsView';
import { ReportsView } from './components/views/ReportsView';
import { AnalyticsView } from './components/views/AnalyticsView';
import { SettingsView } from './components/views/SettingsView';
import { DeepfakeDetectorView } from './components/views/DeepfakeDetectorView';
import { APKScannerView } from './components/views/APKScannerView';
import { FIRConverterView } from './components/views/FIRConverterView';
import { USBFieldExtractorView } from './components/views/USBFieldExtractorView';
import { MOTION } from './components/ui';

import { mockCases } from './data/mockData';
import { CaseItem } from './types/investigation';

export type RouteId =
  | 'dashboard' | 'cases' | 'upload' | 'ai-processing'
  | 'results' | 'reports' | 'analytics' | 'settings'
  | 'deepfake' | 'apk-scanner' | 'fir-converter' | 'field-extractor';

export const App: React.FC = () => {
  const [route, setRoute] = useState<RouteId>('dashboard');
  const [cases, setCases] = useState<CaseItem[]>(mockCases);
  const [selectedCase, setSelectedCase] = useState<CaseItem | null>(null);

  /* Navigate + scroll to top for a clean page change */
  const navigate = useCallback((next: string) => {
    setRoute(next as RouteId);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  const openCase = useCallback((c: CaseItem) => setSelectedCase(c), []);

  const createCase = useCallback(() => {
    const newCase: CaseItem = {
      id: `KPC-2026-${Math.floor(8000 + Math.random() * 1000)}`,
      name: 'Op PhantomGate — Deepfake Extortion Syndicate',
      category: 'AI Identity Extortion',
      risk: 'CRITICAL',
      riskScore: 91,
      lastUpdated: 'Just now',
      status: 'Active Analysis',
      primaryVector: 'Deepfake Generative AI & WhatsApp API Intercept',
      assignedOfficer: 'DySP Rajesh V. Kumar',
      evidenceCount: 1,
      location: 'Thiruvananthapuram Cyber Cell',
      summary: 'Newly registered high-priority incident involving automated AI deepfake video generation used for targeted blackmail.',
      suspects: ['Handle: @PhantomGate_Op'],
      iocs: ['185.220.101.99'],
      hashChain: 'd41d8cd98f00b204e9800998ecf8427e'
    };
    setCases(prev => [newCase, ...prev]);
    setSelectedCase(newCase);
  }, []);

  /* Dashboard KPI tiles — defined here so they stay in sync with routes */
  const dashboardStats = useMemo(() => [
    { label: 'Total Cases',       value: 1428, icon: Briefcase,  accent: 'blue'    as const, caption: '1,180 closed · 82.6% resolution', trend: '+12% MoM',        route: 'cases'   as const },
    { label: 'Pending Cases',     value: 184,  icon: Clock,      accent: 'amber'   as const, caption: 'SLA triage compliance 96%',       trend: 'Needs triage',    route: 'cases'   as const },
    { label: 'High Risk Cases',   value: 37,   icon: ShieldAlert, accent: 'red'     as const, caption: '8 ransomware · 14 crypto',        trend: '+3 critical',     route: 'cases'   as const },
    { label: 'Reports Generated', value: 962,  icon: FileCheck2, accent: 'purple'  as const, caption: 'ISO 27037 · Section 65B',         trend: '+28 this week',   route: 'reports' as const }
  ], []);

  const renderRoute = () => {
    switch (route) {
      case 'dashboard':
        return <DashboardView stats={dashboardStats} cases={cases} onNavigate={navigate} onSelectCase={openCase} />;
      case 'cases':
        return <CasesView cases={cases} onSelectCase={openCase} onNewCase={createCase} />;
      case 'upload':
        return <UploadEvidenceView onAnalyze={() => navigate('ai-processing')} onCancel={() => navigate('dashboard')} />;
      case 'ai-processing':
        return <AIProcessingView onViewResults={() => navigate('results')} onCancel={() => navigate('upload')} />;
      case 'results':
        return <InvestigationResultsView onGenerateReport={() => navigate('reports')} onAnalyzeNew={() => navigate('upload')} />;
      case 'reports':
        return <ReportsView />;
      case 'deepfake':
        return <DeepfakeDetectorView onCreateCase={()=>{ createCase(); }} />;
      case 'apk-scanner':
        return <APKScannerView />;
      case 'fir-converter':
        return <FIRConverterView />;
      case 'field-extractor':
        return <USBFieldExtractorView />;
      case 'analytics':
        return <AnalyticsView />;
      case 'settings':
        return <SettingsView />;
      default:
        return null;
    }
  };

  return (
    <div className="light-liquid-theme min-h-screen flex font-inter relative smooth-transition">

      {/* ── ReactBits GradientWaves — background only ── */}
      <div className="fixed inset-0 z-0 pointer-events-none" aria-hidden="true">
        <GradientWaves
          horizonColor="#5227FF"
          waveColor="#FF9FFC"
          crestColor="#7C3AED"
          speed={0.75}
          amplitude={2.5}
          waveScale={0.8}
          waveRatio={0.9}
          swell={35}
          turbulence={20}
          tilt={1.11}
          zoom={1}
          height={5.5}
          fogDepth={18}
          detail="medium"
          brightness={1}
          opacity={1}
          grain
          grainIntensity={0.05}
          mouseInteraction
          parallaxStrength={0.75}
        />
      </div>

      <Sidebar activeTab={route} setActiveTab={navigate} />

      <div className="flex-1 flex flex-col min-w-0 relative z-10">
        <main className="flex-1 w-full max-w-[1680px] mx-auto px-6 lg:px-8 py-6 lg:py-8">
          <AnimatePresence mode="wait">
            <motion.div key={route} {...MOTION.page}>
              {renderRoute()}
            </motion.div>
          </AnimatePresence>
        </main>

        <footer className="border-t border-[rgba(51,65,85,0.4)] liquid-glass py-3.5 px-6 lg:px-8 mt-8 flex flex-col sm:flex-row items-center justify-between gap-2 text-[10.5px] font-mono text-slate-500">
          <span className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-violet-500 animate-pulse" />
            NoteNext v4.0 — Liquid Glass Intelligence • Deepfake Shield | APK Scanner | FIR Qwen3 | Blockchain Locker • Connected Backend
          </span>
          <span className="flex items-center gap-3 text-center">
            <span className="nn-text-gradient font-semibold">NOTENEXT INTELLIGENCE</span>
            <span className="hidden sm:inline">·</span>
            <span>SECURE • SMOOTH • CONNECTED</span>
          </span>
        </footer>
      </div>

      <CaseDetailModal
        caseItem={selectedCase}
        onClose={() => setSelectedCase(null)}
        onGenerateReport={() => navigate('reports')}
      />
    </div>
  );
};

export default App;
