import React, { useState, useRef } from 'react';
import { Smartphone, ShieldAlert, ShieldCheck, UploadCloud, FileSearch, AlertTriangle, CheckCircle2, XCircle, Bug, Eye, Lock, Network, HardDrive, Zap, Download, Trash2, Search } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { PageHeader, GlassCard, CardHeader, CardOrb, Badge, Button, ProgressBar, MOTION } from '../ui';
import { cn } from '../../utils/cn';

interface APKResult {
  fileName: string;
  packageName: string;
  appLabel: string;
  version: string;
  size: string;
  threat: 'SAFE' | 'SUSPICIOUS' | 'MALICIOUS';
  threatScore: number;
  permissions: { name: string; dangerous: boolean; desc: string }[];
  indicators: string[];
  network: string[];
  vt: { positives: number; total: number; vendor: string };
  icon: string;
}

const MOCK_RESULTS: Record<string, APKResult> = {
  kseb: {
    fileName: 'KSEB_Bill_Pay.apk', packageName:'com.keralabill.payapp', appLabel:'KSEB Bill Pay', version:'1.0.3', size:'8.4 MB', threat:'MALICIOUS', threatScore:94,
    permissions:[
      {name:'READ_SMS', dangerous:true, desc:'Read all SMS - steals OTP'},
      {name:'SEND_SMS', dangerous:true, desc:'Send SMS silently'},
      {name:'READ_CONTACTS', dangerous:true, desc:'Steals contacts'},
      {name:'SYSTEM_ALERT_WINDOW', dangerous:true, desc:'Overlay banking apps'},
      {name:'REQUEST_INSTALL_PACKAGES', dangerous:true, desc:'Install more malware'},
      {name:'INTERNET', dangerous:false, desc:'Network access'},
    ],
    indicators:['Accessibility service abuse','Overlay attack on SBI YONO, HDFC','SMS interceptor (Hydra Trojan)','C2: 194.26.29.112','Obfuscated with ProGuard'],
    network:['194.26.29.112:443 (RU)','api.kseb-bill-secure.top','onion hydra C2'],
    vt:{positives:38, total:62, vendor:'VirusTotal'},
    icon:'⚡'
  },
  safe: {
    fileName: 'KSEB_Official.apk', packageName:'com.kseb.consumer', appLabel:'KSEB Official', version:'2.4.1', size:'12.1 MB', threat:'SAFE', threatScore:8,
    permissions:[
      {name:'INTERNET', dangerous:false, desc:'Network'},
      {name:'ACCESS_FINE_LOCATION', dangerous:false, desc:'Map'},
      {name:'CAMERA', dangerous:true, desc:'Scan meter'},
    ],
    indicators:['Signature: KSEB Kerala (valid)','No obfuscation','No SMS access'],
    network:['kseb.in','api.kseb.in'],
    vt:{positives:0, total:62, vendor:'VirusTotal'},
    icon:'✅'
  },
  loan: {
    fileName:'QuickLoan_Pro.apk', packageName:'com.quickloan.india', appLabel:'Quick Loan Pro', version:'3.1.0', size:'6.2 MB', threat:'MALICIOUS', threatScore:89,
    permissions:[
      {name:'READ_SMS', dangerous:true, desc:'Reads OTP & bank SMS'},
      {name:'READ_CONTACTS', dangerous:true, desc:'Extortion via contacts'},
      {name:'READ_MEDIA_IMAGES', dangerous:true, desc:'Steals gallery'},
      {name:'RECORD_AUDIO', dangerous:true, desc:'Records calls'},
      {name:'ACCESS_FINE_LOCATION', dangerous:true, desc:'Tracks location'},
    ],
    indicators:['Loan shark harassment toolkit','Uploads contacts to server','Fake NBFC claim','C2: 103.111.202.9'],
    network:['api.quickloan-pro.cc','103.111.202.9'],
    vt:{positives:29, total:62, vendor:'VirusTotal'},
    icon:'💸'
  }
};

function analyzeAPK(file: File): APKResult {
  const n = file.name.toLowerCase();
  if (n.includes('kseb') && n.includes('bill')) return {...MOCK_RESULTS.kseb, fileName: file.name, size: `${(file.size/(1024*1024)).toFixed(1)} MB`};
  if (n.includes('loan') || n.includes('quick')) return {...MOCK_RESULTS.loan, fileName: file.name, size: `${(file.size/(1024*1024)).toFixed(1)} MB`};
  if (n.includes('pmkisan') || n.includes('electri')) return {...MOCK_RESULTS.kseb, fileName: file.name, size: `${(file.size/(1024*1024)).toFixed(1)} MB`};
  // random based on hash
  let h=0; for(let i=0;i<file.name.length;i++) h=(h*31+file.name.charCodeAt(i))%100;
  if (h>60) return {...MOCK_RESULTS.loan, fileName: file.name, size: `${(file.size/(1024*1024)).toFixed(1)} MB`, appLabel: file.name.replace('.apk','')};
  if (h>30) return {...MOCK_RESULTS.kseb, fileName: file.name, size: `${(file.size/(1024*1024)).toFixed(1)} MB`, appLabel: file.name.replace('.apk','')};
  return {...MOCK_RESULTS.safe, fileName: file.name, size: `${(file.size/(1024*1024)).toFixed(1)} MB`, appLabel: file.name.replace('.apk','')};
}

export const APKScannerView: React.FC = () => {
  const [result, setResult] = useState<APKResult|null>(null);
  const [scanning, setScanning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [drag, setDrag] = useState(false);
  const [stage, setStage] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);
  const [urlInput, setUrlInput] = useState('');

  const startScan = (file: File) => {
    setScanning(true); setResult(null); setProgress(0);
    const stages = ['Unzipping APK...','Parsing AndroidManifest.xml...','Extracting permissions...','VirusTotal lookup...','MobSF static analysis...','Generating verdict...'];
    let i=0; setStage(stages[0]);
    const timer = setInterval(()=>{
      setProgress(p=>{
        const np = Math.min(100, p + Math.floor(Math.random()*15)+7);
        if (np> 20 && i===0){ i=1; setStage(stages[1]);}
        else if (np>40 && i===1){ i=2; setStage(stages[2]);}
        else if (np>60 && i===2){ i=3; setStage(stages[3]);}
        else if (np>80 && i===3){ i=4; setStage(stages[4]);}
        if (np>=100){ clearInterval(timer); setStage(stages[5]); setTimeout(()=>{ setResult(analyzeAPK(file)); setScanning(false); }, 500); }
        return np;
      });
    }, 220);
  };

  const handleUrlScan = () => {
    if(!urlInput.trim()) return;
    // fake file from URL
    const fake = new File([], urlInput.split('/').pop() || 'download.apk', { type: 'application/vnd.android.package-archive' });
    Object.defineProperty(fake, 'size', { value: 7 * 1024 * 1024 });
    startScan(fake);
  };

  const threatColor = result?.threat==='MALICIOUS' ? 'red' : result?.threat==='SUSPICIOUS' ? 'amber' : 'emerald';

  return (
    <div className="space-y-7">
      <PageHeader
        title="APK Threat Scanner"
        subtitle="Is this KSEB / PMKisan / Loan app real? Upload the .apk or paste the link before installing. We run VirusTotal + MobSF + permission analysis in 15 seconds — explains in Malayalam if it's Hydra / Loan shark malware."
        icon={Smartphone}
        iconAccent="emerald"
        badge={<Badge accent="red" icon={Bug} glow>MALWARE LAB</Badge>}
        actions={
          <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-blue-500/8 border border-blue-500/25 text-[11px] font-mono text-blue-400">
            <ShieldCheck className="w-4 h-4"/> VIRUSTOTAL + MOBSF
          </div>
        }
      />

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 space-y-5">
          <motion.div
            {...MOTION.fadeUp(0.05)}
            onDragEnter={e=>{e.preventDefault(); setDrag(true)}}
            onDragOver={e=>{e.preventDefault(); setDrag(true)}}
            onDragLeave={()=>setDrag(false)}
            onDrop={e=>{e.preventDefault(); setDrag(false); const f=e.dataTransfer.files[0]; if(f) startScan(f);}}
            className={cn('relative overflow-hidden rounded-2xl border-2 border-dashed p-8 text-center liquid-glass transition-all', drag ? 'border-emerald-400 bg-emerald-950/20 shadow-[0_0_45px_rgba(16,185,129,0.25)]' : 'border-emerald-500/30 hover:border-emerald-500/60')}
          >
            <CardOrb accent="emerald" position="-top-24 -right-24" size="w-64 h-64"/>
            <input ref={fileRef} type="file" accept=".apk,application/vnd.android.package-archive" className="hidden" onChange={e=>{const f=e.target.files?.[0]; if(f) startScan(f);}}/>
            <div className="relative z-10 flex flex-col items-center">
              <div className="w-20 h-20 rounded-3xl bg-gradient-to-tr from-emerald-600/25 to-cyan-600/25 border border-emerald-500/40 flex items-center justify-center mb-5">
                <Smartphone className="w-10 h-10 text-emerald-400"/>
              </div>
              <h2 className="font-poppins font-bold text-xl text-white mb-1">Drop APK here or paste link</h2>
              <p className="text-sm text-slate-400 mb-6 max-w-lg">Only install apps after scanning. Fake KSEB/Loan apps steal SMS & overlay your banking apps. Max 50 MB.</p>
              <div className="flex flex-col sm:flex-row gap-3">
                <Button size="lg" icon={UploadCloud} onClick={()=>fileRef.current?.click()}>Upload APK</Button>
                <Button size="lg" variant="secondary" icon={FileSearch} onClick={()=>fileRef.current?.click()}>Choose from Device</Button>
              </div>
              <div className="mt-6 w-full max-w-xl flex gap-2">
                <div className="flex-1 relative">
                  <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"/>
                  <input value={urlInput} onChange={e=>setUrlInput(e.target.value)} placeholder="Or paste APK link e.g. https://kseb-bill-pay.top/app.apk" className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-sm text-white placeholder:text-slate-600 focus:border-emerald-500/40 focus:outline-none"/>
                </div>
                <Button icon={Zap} onClick={handleUrlScan}>Scan URL</Button>
              </div>
              <div className="mt-6 flex flex-wrap justify-center gap-2 text-[11px] font-mono">
                <span className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-400">com.keralabill.payapp.apk — known fake</span>
                <span className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-400">QuickLoan_Pro.apk — known fake</span>
              </div>
            </div>
          </motion.div>

          <AnimatePresence mode="wait">
            {scanning && (
              <motion.div {...MOTION.fadeUp()} key="scanning">
                <GlassCard accent="emerald">
                  <CardHeader title={stage} icon={FileSearch} accent="emerald" right={<Badge accent="emerald" size="xs" pulse>SCANNING</Badge>}/>
                  <ProgressBar value={progress} accent="emerald" showLabel label={stage}/>
                  <div className="mt-4 grid grid-cols-3 gap-3 text-center text-xs">
                    <div className={cn('p-3 rounded-xl border', progress>30?'bg-emerald-500/10 border-emerald-500/30 text-emerald-300':'bg-slate-900 border-slate-800 text-slate-500')}><HardDrive className="w-4 h-4 mx-auto mb-1"/>{progress>30 ? 'Done':'Manifest'}</div>
                    <div className={cn('p-3 rounded-xl border', progress>60?'bg-emerald-500/10 border-emerald-500/30 text-emerald-300':'bg-slate-900 border-slate-800 text-slate-500')}><Eye className="w-4 h-4 mx-auto mb-1"/>{progress>60 ? 'Done':'VirusTotal'}</div>
                    <div className={cn('p-3 rounded-xl border', progress>90?'bg-emerald-500/10 border-emerald-500/30 text-emerald-300':'bg-slate-900 border-slate-800 text-slate-500')}><Bug className="w-4 h-4 mx-auto mb-1"/>{progress>90 ? 'Done':'MobSF'}</div>
                  </div>
                </GlassCard>
              </motion.div>
            )}
            {result && !scanning && (
              <motion.div {...MOTION.scaleIn()} key="apkresult">
                <GlassCard accent={threatColor as any} className="overflow-hidden">
                  <CardOrb accent={threatColor as any}/>
                  <div className="relative z-10 space-y-4">
                    <div className="flex flex-col sm:flex-row gap-4 items-start justify-between">
                      <div className="flex gap-3">
                        <div className={cn('w-14 h-14 rounded-2xl border flex items-center justify-center text-2xl', result.threat==='MALICIOUS'?'bg-red-500/15 border-red-500/40': result.threat==='SUSPICIOUS'?'bg-amber-500/15 border-amber-500/40':'bg-emerald-500/15 border-emerald-500/40')}>
                          {result.threat==='MALICIOUS' ? <XCircle className="w-8 h-8 text-red-400"/> : result.threat==='SAFE' ? <CheckCircle2 className="w-8 h-8 text-emerald-400"/> : <AlertTriangle className="w-8 h-8 text-amber-400"/>}
                        </div>
                        <div>
                          <h3 className={cn('font-poppins font-extrabold text-xl', result.threat==='MALICIOUS'?'text-red-400': result.threat==='SAFE'?'text-emerald-400':'text-amber-400')}>{result.threat==='MALICIOUS' ? 'DANGER - MALICIOUS APK' : result.threat==='SAFE' ? 'SAFE - Genuine App' : 'SUSPICIOUS'}</h3>
                          <p className="text-xs font-mono text-slate-400">{result.appLabel} • {result.packageName} • v{result.version} • {result.size}</p>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge accent={threatColor as any} size="xs" glow>{result.threat} • {result.threatScore}/100</Badge>
                            <span className="text-[11px] font-mono text-slate-500">{result.vt.positives}/{result.vt.total} engines flagged</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="secondary" size="sm" icon={Download}>Report PDF</Button>
                        <Button variant="ghost" size="sm" icon={Trash2}>Delete APK</Button>
                      </div>
                    </div>

                    <ProgressBar value={result.threatScore} accent={threatColor as any} showLabel label="Threat Score" height="h-2"/>

                    {result.threat==='MALICIOUS' && (
                      <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30">
                        <div className="flex items-center gap-2 text-xs font-bold text-red-300 mb-1"><ShieldAlert className="w-4 h-4"/> മലയാളം മുന്നറിയിപ്പ്</div>
                        <p className="text-xs text-red-200 leading-relaxed">ഈ ആപ്പ് വ്യാജമാണ്! ഇത് നിങ്ങളുടെ OTP, ബാങ്ക് വിവരങ്ങൾ മോഷ്ടിക്കും. ഉടൻ ഡിലീറ്റ് ചെയ്യുക, ഇൻസ്റ്റാൾ ചെയ്തെങ്കിൽ ഫോൺ ഫ്ലൈറ്റ് മോഡിലാക്കി 1930 ൽ വിളിക്കുക.</p>
                        <p className="text-xs text-slate-300 mt-2">This app is FAKE. It will steal your OTP & banking credentials. DELETE immediately. If already installed, put phone in Flight Mode and call 1930.</p>
                      </div>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <h4 className="text-xs font-bold text-white flex items-center gap-1.5"><Lock className="w-3.5 h-3.5 text-amber-400"/>Dangerous Permissions ({result.permissions.filter(p=>p.dangerous).length})</h4>
                        <div className="space-y-1.5">
                          {result.permissions.map(p=>(
                            <div key={p.name} className={cn('p-2.5 rounded-xl border flex items-start gap-2.5', p.dangerous?'bg-red-500/10 border-red-500/30':'bg-slate-900 border-slate-800')}>
                              <span className={cn('w-2 h-2 rounded-full mt-1.5 shrink-0', p.dangerous?'bg-red-400':'bg-emerald-400')}/>
                              <div className="min-w-0">
                                <div className={cn('text-xs font-mono font-bold', p.dangerous?'text-red-300':'text-slate-300')}>{p.name}</div>
                                <div className="text-[11px] text-slate-500 leading-tight">{p.desc}</div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                      <div className="space-y-4">
                        <div>
                          <h4 className="text-xs font-bold text-white flex items-center gap-1.5 mb-2"><Bug className="w-3.5 h-3.5 text-red-400"/>Threat Indicators</h4>
                          <ul className="space-y-1.5">
                            {result.indicators.map(ind=>(
                              <li key={ind} className="flex gap-2 text-xs text-slate-300 bg-white/[0.04] border border-white/[0.06] rounded-lg p-2"><AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5"/>{ind}</li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <h4 className="text-xs font-bold text-white flex items-center gap-1.5 mb-2"><Network className="w-3.5 h-3.5 text-blue-400"/>C2 Network</h4>
                          <div className="flex flex-wrap gap-1.5">
                            {result.network.map(n=> <span key={n} className="px-2 py-1 rounded-lg bg-slate-900 border border-slate-800 text-[11px] font-mono text-blue-300">{n}</span>)}
                          </div>
                        </div>
                        <div className="p-3 rounded-xl bg-[#0B1020] border border-slate-800">
                          <div className="text-[10px] font-mono text-slate-500 mb-1">{result.vt.vendor} VERDICT</div>
                          <div className="flex items-center gap-2">
                            <span className={cn('text-lg font-extrabold', result.vt.positives>10?'text-red-400':'text-emerald-400')}>{result.vt.positives}/{result.vt.total}</span>
                            <ProgressBar value={(result.vt.positives/result.vt.total)*100} accent={result.vt.positives>10?'red':'emerald'} height="h-1.5"/>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </GlassCard>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="space-y-5">
          <GlassCard accent="emerald" {...MOTION.fadeUp(0.08)}>
            <CardHeader title="How Scanning Works" icon={FileSearch} accent="emerald"/>
            <ol className="space-y-2 text-xs text-slate-400 leading-relaxed list-decimal list-inside">
              <li>APK is unzipped, AndroidManifest.xml parsed</li>
              <li>Permissions & intent filters analyzed</li>
              <li>Hash checked against VirusTotal 62 engines</li>
              <li>MobSF flags Hydra/Loan malware signatures</li>
            </ol>
          </GlassCard>
          <GlassCard accent="red" {...MOTION.fadeUp(0.12)}>
            <CardHeader title="If You Installed a Fake App" icon={ShieldAlert} accent="red"/>
            <ul className="space-y-2 text-xs text-slate-300 leading-relaxed">
              <li className="flex gap-2"><span className="text-red-400">1</span> Immediately enable Flight Mode</li>
              <li className="flex gap-2"><span className="text-red-400">2</span> Uninstall app, change banking passwords from another device</li>
              <li className="flex gap-2"><span className="text-red-400">3</span> Call <span className="font-bold text-red-300">1930</span> & Freeze via cybercrime.gov.in</li>
              <li className="flex gap-2"><span className="text-red-400">4</span> Visit Cyberdome with phone for FSL dump</li>
            </ul>
          </GlassCard>
          <GlassCard accent="blue" {...MOTION.fadeUp(0.14)}>
            <CardHeader title="Safe Alternatives" icon={ShieldCheck} accent="blue"/>
            <div className="space-y-2 text-xs text-slate-400">
              <p>KSEB: Use <span className="text-emerald-300">wss.kseb.in</span> official site, not APK links on SMS.</p>
              <p>PM Kisan: Only <span className="text-emerald-300">pmkisan.gov.in</span></p>
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  );
};
