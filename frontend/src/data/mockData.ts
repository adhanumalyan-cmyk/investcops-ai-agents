import { CaseItem, DigitalEvidence, NotificationItem, InvestigatorProfile } from '../types/investigation';

export const mockInvestigator: InvestigatorProfile = {
  name: "DySP Rajesh V. Kumar",
  rank: "Deputy Superintendent of Police",
  badgeNumber: "KP-CYD-042",
  unit: "Kerala Police Cyberdome - Cyber Operations Unit 04",
  avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=250",
  clearanceLevel: "Level 5 - Top Secret / Cyber Security Enclave",
  activeCases: 14,
  reportsGenerated: 182
};

export const mockCases: CaseItem[] = [
  {
    id: "KPC-2026-8941",
    name: "Op CryptoSiphon - Telegram Financial Syndicate",
    category: "Financial Crypto Fraud",
    risk: "CRITICAL",
    riskScore: 96,
    lastUpdated: "2 mins ago",
    status: "Active Analysis",
    primaryVector: "USDT Tron TRC-20 Laundering & Smishing",
    assignedOfficer: "DySP Rajesh V. Kumar",
    evidenceCount: 14,
    location: "Kochi / Multi-jurisdictional",
    summary: "Large-scale cryptocurrency laundering syndicate operating via automated Telegram bots, siphoning stolen funds from UPI phishing victims across 8 districts in Kerala into mixer wallets.",
    suspects: ["@CyberSiphon_BotAdmin", "Wallet: T9zP...84mQ", "CryptoNode ID #9042"],
    iocs: ["185.220.101.45", "103.253.144.12", "tron-mixer-api.darknet.ru"],
    hashChain: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  },
  {
    id: "KPC-2026-8938",
    name: "Deepfake Identity Extortion Ring #4",
    category: "AI Extortion / Deepfake",
    risk: "HIGH",
    riskScore: 84,
    lastUpdated: "12 mins ago",
    status: "Evidence Pending",
    primaryVector: "Voice Cloning & WhatsApp Business API Hooking",
    assignedOfficer: "Insp. Ananya Nair",
    evidenceCount: 8,
    location: "Thiruvananthapuram",
    summary: "Synthetic voice generation used to impersonate senior government officials and extort targeted victims via spoofed WhatsApp calls. AI audio forensics detected neural synthesizer artifacts.",
    suspects: ["Handle: @VoiceGlitch_KP", "Virtual SIM Cluster #8812"],
    iocs: ["api.eleven-spoof.internal", "45.154.255.82"],
    hashChain: "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284ddd200126d9069"
  },
  {
    id: "KPC-2026-8925",
    name: "Bank API Hooking & APK Spyware 'CyberShield'",
    category: "Mobile Trojan / Banking",
    risk: "HIGH",
    riskScore: 78,
    lastUpdated: "45 mins ago",
    status: "Suspect Identified",
    primaryVector: "Malicious APK Sideload & SMS Accessibility Sniffer",
    assignedOfficer: "DySP Rajesh V. Kumar",
    evidenceCount: 23,
    location: "Kozhikode",
    summary: "Fake Kerala Electricity Board bill pay app distributed via SMS links containing overlay banking Trojan targeting state bank accounts.",
    suspects: ["Developer Alias: 'K-ElectriFix'", "IP Server 194.26.29.112"],
    iocs: ["com.keralabill.payapp.apk", "194.26.29.112", "c2-kerala-hydra.top"],
    hashChain: "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"
  },
  {
    id: "KPC-2026-8912",
    name: "State Utility Ransomware 'BlackByte-KR'",
    category: "Critical Infrastructure Threat",
    risk: "CRITICAL",
    riskScore: 98,
    lastUpdated: "2 hours ago",
    status: "Active Analysis",
    primaryVector: "Unpatched Exchange SMB & Encrypted VHD Dump",
    assignedOfficer: "DySP Rajesh V. Kumar",
    evidenceCount: 42,
    location: "Thiruvananthapuram Headquarters",
    summary: "Ransomware payload attempt caught in dry-run stage on municipal grid telemetry server. Memory dump dump payload reveals breach attempt originating from compromised VPN credentials.",
    suspects: ["BlackByte Ransomware Group", "TOR Node: 185.220.101.5"],
    iocs: ["blackbyte_kr_encryptor.exe", "185.220.101.5", "onion-leak-portal.v3"],
    hashChain: "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"
  },
  {
    id: "KPC-2026-8890",
    name: "Mule Account Network 'DarkVault-Kerala'",
    category: "Cyber Financial Network",
    risk: "MEDIUM",
    riskScore: 56,
    lastUpdated: "4 hours ago",
    status: "Closed - Court Dossier Ready",
    primaryVector: "UPI Mule Ring & Instant Loan App Hawala",
    assignedOfficer: "Insp. Sreejith P.",
    evidenceCount: 19,
    location: "Thrissur",
    summary: "Coordination of 142 mule bank accounts mapped across 12 banks. All assets frozen via Cyber Crime Portal automated API triggers.",
    suspects: ["Account Aggregator Ring Alpha", "7 Mule Handlers Arrested"],
    iocs: ["mule-mesh-tracker.db", "103.111.202.9"],
    hashChain: "2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae"
  },
  {
    id: "KPC-2026-8874",
    name: "Darkweb Credentials Leak - Govt Portal",
    category: "Data Breach / Credential Leak",
    risk: "LOW",
    riskScore: 34,
    lastUpdated: "6 hours ago",
    status: "Closed - Court Dossier Ready",
    primaryVector: "RedLine Stealer Logs Exfiltration",
    assignedOfficer: "Insp. Ananya Nair",
    evidenceCount: 5,
    location: "Kollam",
    summary: "Monitoring bot identified 24 stale admin passwords leaked on Breached Forums. Credential reset executed automatically; MFA enforced.",
    suspects: ["BreachedForums Vendor 'StealerDumpz'"],
    iocs: ["redline_stealer_db_022026.txt"],
    hashChain: "1b1686b15d01172828ff759491a63c0133c94f58c735d45d8123288a705e46c7"
  }
];

export const mockNotifications: NotificationItem[] = [
  {
    id: "N-101",
    title: "High Priority Crypto Movement",
    message: "42,000 USDT moved from suspicious wallet T9zP...84mQ (Case KPC-2026-8941)",
    time: "4 mins ago",
    type: "CRITICAL",
    read: false,
    caseId: "KPC-2026-8941"
  },
  {
    id: "N-102",
    title: "AI Audio Match Found",
    message: "Voice print on new incident matches suspect profile #VP-882 (Accuracy: 98.4%)",
    time: "18 mins ago",
    type: "WARNING",
    read: false,
    caseId: "KPC-2026-8938"
  },
  {
    id: "N-103",
    title: "Evidence Processing Completed",
    message: "RAM Memory Dump scan finished for Case KPC-2026-8912. 12 IOCs extracted.",
    time: "1 hour ago",
    type: "INFO",
    read: true,
    caseId: "KPC-2026-8912"
  },
  {
    id: "N-104",
    title: "Court Dossier Export Ready",
    message: "ISO 27037 compliant forensic report finalized for Case KPC-2026-8890.",
    time: "3 hours ago",
    type: "INFO",
    read: true,
    caseId: "KPC-2026-8890"
  }
];

export const sampleEvidencePresets: { label: string; name: string; size: string; type: string; preset: DigitalEvidence }[] = [
  {
    label: "Ransomware Memory Dump (.RAW)",
    name: "mem_dump_srv_kerala_grid_0226.raw",
    size: "1.4 GB",
    type: "Memory Dump / Volatility 3",
    preset: {
      id: "EVD-2026-9041",
      fileName: "mem_dump_srv_kerala_grid_0226.raw",
      fileSize: "1.4 GB",
      fileType: "Win64 RAM Dump (RAW)",
      uploadDate: "Just now",
      md5: "9e107d9d372bb6826bd81d3542a419d6",
      sha256: "4a821e2501a3574c3e800a747971775e54d80a187d7b1406852a370e7a2b91d2",
      threatScore: 98,
      extractedIPs: ["185.220.101.45", "103.253.144.12", "194.26.29.112"],
      extractedEntities: ["Process: lsass.exe injection", "Mutex: Global\\BlackByte_Mutx", "PowerShell Encoded Script"],
      verdict: "CRITICAL THREAT DETECTED: Active ransomware memory hook with automated C2 heartbeat.",
      caseId: "KPC-2026-8912"
    }
  },
  {
    label: "Crypto Laundering Ledger (.JSON)",
    name: "tron_trc20_syndicate_tx_log.json",
    size: "18.4 MB",
    type: "Blockchain JSON Ledger",
    preset: {
      id: "EVD-2026-9042",
      fileName: "tron_trc20_syndicate_tx_log.json",
      fileSize: "18.4 MB",
      fileType: "JSON Blockchain Trace Log",
      uploadDate: "Just now",
      md5: "3a88c2b512a8497a9f7d4b1a89c3140e",
      sha256: "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9",
      threatScore: 89,
      extractedIPs: ["45.154.255.82", "185.220.101.5"],
      extractedEntities: ["Wallet: T9zP84mQxX921kLm90aP", "Binance Deposit Memo #88129", "Mixing Service: FixedFloat API"],
      verdict: "HIGH CONFIDENCE: Rapid USDT splitting matching darkweb money laundering signature.",
      caseId: "KPC-2026-8941"
    }
  },
  {
    label: "Deepfake Audio Intercept (.WAV)",
    name: "extortion_voip_intercept_cloned.wav",
    size: "8.2 MB",
    type: "Audio / Deepfake Neural Scan",
    preset: {
      id: "EVD-2026-9043",
      fileName: "extortion_voip_intercept_cloned.wav",
      fileSize: "8.2 MB",
      fileType: "Audio / PCM 24-bit WAV",
      uploadDate: "Just now",
      md5: "f2c94301178c1871a2b0a1d3e89f28c1",
      sha256: "1f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284ddd200126d90691",
      threatScore: 85,
      extractedIPs: ["103.111.202.9"],
      extractedEntities: ["Vocal Tract Artifact: ElevenLabs Synthesizer v2", "Background Noise Loop: Synthetic Room Reverb", "Caller ID Spoof: +91 98470 XXXXX"],
      verdict: "AI SYNTHETIC VOICE DETECTED (98.4% Probability): Voice cloning attempt targeting official hierarchy.",
      caseId: "KPC-2026-8938"
    }
  }
];
