/**
 * TypeScript Data Models matching Phase 10 Backend FastAPI schemas.
 */

export type SeverityLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

export type UserRole = 'ADMIN' | 'PAYROLL_ADMIN' | 'AUDITOR' | 'VIEWER';

export interface AuthUser {
  username: string;
  email: string;
  role: UserRole;
  full_name?: string;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in_seconds: number;
  role: UserRole;
  username: string;
}

export interface AuditEventItem {
  event_id: string;
  timestamp: string;
  analysis_id?: string;
  actor_id: string;
  event_type: string;
  metadata: Record<string, any>;
  request_id?: string;
}

export interface ServiceStatus {
  ai: string;
  rag: string;
  llm: string;
  database?: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
  services: ServiceStatus;
}

export interface ComplianceSourceItem {
  document_id: string;
  title?: string;
  authority_level?: string;
  section?: string;
  page?: number;
  citation: string;
}

export interface ComplianceStatusBlock {
  status: 'FOUND' | 'NO_RELIABLE_SOURCE_FOUND' | 'JURISDICTION_UNKNOWN' | string;
  sources: ComplianceSourceItem[];
  no_answer_reason?: string | null;
}

export interface ExplanationItem {
  title?: string | null;
  summary: string;
  why_flagged: string[];
  recommended_actions: string[];
  uncertainty?: string | null;
  fallback_mode?: boolean;
}

export interface AnomalyRecordResult {
  employee_id: string;
  payroll_month: string;
  department: string;
  designation: string;
  anomaly_types: string[];
  risk_score: number;
  severity: SeverityLevel;
  evidence: string[];
  rule_violations: string[];
  historical_comparison: Record<string, any>;
  peer_comparison: Record<string, any>;
  compliance: ComplianceStatusBlock;
  explanation: ExplanationItem;
}

export interface AnalysisSummary {
  records_analyzed: number;
  records_flagged: number;
  critical_risk: number;
  high_risk: number;
  medium_risk: number;
  low_risk: number;
}

export type AnalysisStatus = 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED';

export interface AnalysisResponse {
  request_id: string;
  analysis_id: string;
  status: AnalysisStatus;
  payroll_period: string;
  summary: AnalysisSummary;
  anomalies: AnomalyRecordResult[];
  model_name?: string;
  model_version: string;
  model_threshold?: number;
  feature_schema_version?: string;
  rag_knowledge_version?: string;
  llm_version?: string;
  disclaimer: string;
  created_at: string;
  duration_ms: number;
}

export interface ComplianceSearchRequest {
  query: string;
  jurisdiction?: string;
  payroll_date?: string;
  topic?: string;
  top_n?: number;
}

export interface ComplianceSearchResult {
  query: string;
  jurisdiction: string;
  payroll_date: string;
  topic?: string | null;
  results: ComplianceSourceItem[];
  total_found: number;
  status: string;
  no_answer_reason?: string | null;
}

export interface AssistantQueryRequest {
  question: string;
  analysis_id?: string;
  employee_id?: string;
}

export interface AssistantQueryResponse {
  question: string;
  answer: string;
  grounded_facts: string[];
  evidence_sources: string[];
  citations: ComplianceSourceItem[];
  category_distinction: Record<string, string[]>;
  suggested_next_steps: string[];
  uncertainty_or_refusal?: string | null;
  disclaimer: string;
}
