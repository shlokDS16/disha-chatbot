export type Language = "en" | "hi" | "mr";
export type Persona = "asha" | "couple" | "patient" | "doctor";
export type HbGenotype = "AA" | "AS" | "SS" | "SC" | "S_beta_thal";
export type Disease = "sickle_cell" | "thalassemia";
export type ConsentMethod = "tap" | "verbal";
export type ConsentScope = "store_session" | "auto_rag_enrich" | "voice_playback";
export type MessageSource = "rag" | "llm" | "tool" | "hybrid";
export type FeedbackRating = "up" | "down";
export type FacilityService =
  | "HPLC_centre"
  | "CVS_amnio"
  | "haematology"
  | "HU_dispensing"
  | "general_hospital"
  | "any";
export type Severity =
  | "normal"
  | "carrier"
  | "affected"
  | "info"
  | "warning"
  | "critical";

export interface ConsentRecord {
  accepted: boolean;
  method?: ConsentMethod | null;
  scopes: ConsentScope[];
  recorded_at?: string | null;
}

export interface UserLocation {
  lat: number;
  lng: number;
  label?: string | null;
}

export interface SessionState {
  session_id: string;
  language: Language;
  persona?: Persona | null;
  consent: ConsentRecord;
  message_count: number;
  location?: UserLocation | null;
  created_at: string;
  last_activity: string;
}

export interface SessionStartResponse {
  session_id: string;
  language: Language;
  consent_required: boolean;
  created_at: string;
}

// ── Content blocks ─────────────────────────────────────────────────

export interface TextBlock {
  type: "text";
  text: string;
}

export interface PunnettProbabilities {
  AA: number;
  AS: number;
  SS: number;
  SC: number;
  S_beta_thal: number;
}

export interface PunnettCell {
  genotype: HbGenotype;
  probability: number;
  severity: Severity;
}

export interface PunnettData {
  p1: HbGenotype;
  p2: HbGenotype;
  probabilities: PunnettProbabilities;
  grid: PunnettCell[][];
}

export interface PunnettBlock {
  type: "punnett";
  data: PunnettData;
}

export interface FacilityItem {
  id: string;
  name: string;
  type: FacilityService;
  address: string;
  distance_km: number;
  rating?: number | null;
  open_now?: boolean | null;
  directions_url: string;
}

export interface FacilityData {
  user_location: { lat: number; lng: number };
  facilities: FacilityItem[];
}

export interface FacilityBlock {
  type: "facility";
  data: FacilityData;
}

export interface KeyFinding {
  label_native: string;
  label_en: string;
  value: string;
  severity: Severity;
}

export interface FileSummaryData {
  file_id: string;
  key_findings: KeyFinding[];
  what_it_means: string;
  next_steps: string[];
  document_type?: string | null;
  detailed_analysis?: string | null;
  full_text?: string | null;
  filename?: string | null;
}

export interface FileSummaryBlock {
  type: "file_summary";
  data: FileSummaryData;
}

export interface CrisisHelpline {
  name: string;
  number: string;
}

export interface CrisisData {
  severity: Severity;
  helplines: CrisisHelpline[];
  message: string;
}

export interface CrisisBannerBlock {
  type: "crisis_banner";
  data: CrisisData;
}

export interface ConsentGateData {
  action: string;
  scopes: ConsentScope[];
  description: string;
}

export interface ConsentGateBlock {
  type: "consent_gate";
  data: ConsentGateData;
}

export interface ReferralData {
  facility_type: FacilityService;
  nearest: FacilityItem[];
  why: string;
}

export interface ReferralBlock {
  type: "referral";
  data: ReferralData;
}

export interface StarterChip {
  id: string;
  text: string;
}

export interface StarterChipsBlock {
  type: "starter_chips";
  data: { chips: StarterChip[] };
}

export type ContentBlock =
  | TextBlock
  | PunnettBlock
  | FacilityBlock
  | FileSummaryBlock
  | CrisisBannerBlock
  | ConsentGateBlock
  | ReferralBlock
  | StarterChipsBlock;

// ── Chat ───────────────────────────────────────────────────────────

export interface SourceMeta {
  chunk_ids: string[];
  confidence: number;
  model?: string | null;
  reranker_score?: number | null;
}

export interface SuggestedReply {
  id: string;
  text: string;
}

export interface ChatMessageResponse {
  message_id: string;
  role: "assistant";
  language: Language;
  source: MessageSource;
  source_meta: SourceMeta;
  content: ContentBlock[];
  audio_url?: string | null;
  feedback_id: string;
  suggested_replies: SuggestedReply[];
  timestamp: string;
}

// ── Files ──────────────────────────────────────────────────────────

export type FileStatus =
  | "queued"
  | "ocr_processing"
  | "summarizing"
  | "done"
  | "failed";

export type FileType = "pdf" | "docx" | "image";

export interface FileUploadResponse {
  file_id: string;
  filename: string;
  size_bytes: number;
  type: FileType;
  status: FileStatus;
}

export interface FileSummaryPayload {
  language: Language;
  key_findings: KeyFinding[];
  what_it_means: string;
  next_steps: string[];
  document_type?: string | null;
  detailed_analysis?: string | null;
  full_text?: string | null;
}

export interface FileStateResponse {
  file_id: string;
  status: FileStatus;
  ocr_text?: string | null;
  summary?: FileSummaryPayload | null;
  error?: string | null;
}

// ── Facilities ─────────────────────────────────────────────────────

export interface NearbyFacilitiesResponse {
  user_location: { lat: number; lng: number };
  facilities: FacilityItem[];
}

// ── Punnett ────────────────────────────────────────────────────────

export interface PunnettNarrative {
  headline: string;
  body: string;
  risk_level: "none" | "low" | "moderate" | "high" | "very_high" | "certain";
}

export interface PunnettResponse {
  probabilities: PunnettProbabilities;
  narrative: PunnettNarrative;
  visual_data: PunnettData;
}

// ── Content ─────────────────────────────────────────────────────────

export interface HealthTip {
  id: string;
  title: string;
  body: string;
  icon?: string;
}

export interface CrisisHelplineInfo {
  name: string;
  number: string;
  notes?: string;
}
