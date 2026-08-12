export type RiskLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

export type CaseStatus = 
  | 'Active Analysis'
  | 'Evidence Pending'
  | 'Suspect Identified'
  | 'Closed - Court Dossier Ready'
  | 'Under Legal Review';

export interface CaseItem {
  id: string;
  name: string;
  category: string;
  risk: RiskLevel;
  riskScore: number;
  lastUpdated: string;
  status: CaseStatus;
  primaryVector: string;
  assignedOfficer: string;
  evidenceCount: number;
  location: string;
  summary: string;
  suspects: string[];
  iocs: string[];
  hashChain: string;
}

export interface DigitalEvidence {
  id: string;
  fileName: string;
  fileSize: string;
  fileType: string;
  uploadDate: string;
  md5: string;
  sha256: string;
  threatScore: number;
  extractedIPs: string[];
  extractedEntities: string[];
  verdict: string;
  caseId?: string;
}

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  time: string;
  type: 'CRITICAL' | 'WARNING' | 'INFO';
  read: boolean;
  caseId?: string;
}

export interface InvestigatorProfile {
  name: string;
  rank: string;
  badgeNumber: string;
  unit: string;
  avatar: string;
  clearanceLevel: string;
  activeCases: number;
  reportsGenerated: number;
}
