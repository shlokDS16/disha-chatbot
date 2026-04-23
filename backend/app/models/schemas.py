from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# ── Enums ──────────────────────────────────────────────────────────

class Language(str, Enum):
    EN = "en"
    HI = "hi"
    MR = "mr"


class Persona(str, Enum):
    ASHA = "asha"
    COUPLE = "couple"
    PATIENT = "patient"
    DOCTOR = "doctor"


class HbGenotype(str, Enum):
    AA = "AA"
    AS = "AS"
    SS = "SS"
    SC = "SC"
    S_BETA_THAL = "S_beta_thal"


class Disease(str, Enum):
    SICKLE_CELL = "sickle_cell"
    THALASSEMIA = "thalassemia"


class ConsentMethod(str, Enum):
    TAP = "tap"
    VERBAL = "verbal"


class ConsentScope(str, Enum):
    STORE_SESSION = "store_session"
    AUTO_RAG_ENRICH = "auto_rag_enrich"
    VOICE_PLAYBACK = "voice_playback"


class MessageSource(str, Enum):
    RAG = "rag"
    LLM = "llm"
    TOOL = "tool"
    HYBRID = "hybrid"


class FeedbackRating(str, Enum):
    UP = "up"
    DOWN = "down"


class FacilityService(str, Enum):
    HPLC_CENTRE = "HPLC_centre"
    CVS_AMNIO = "CVS_amnio"
    HAEMATOLOGY = "haematology"
    HU_DISPENSING = "HU_dispensing"
    GENERAL_HOSPITAL = "general_hospital"
    ANY = "any"


class Severity(str, Enum):
    NORMAL = "normal"
    CARRIER = "carrier"
    AFFECTED = "affected"
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


# ── Content Blocks (discriminated union) ───────────────────────────

class BaseBlock(BaseModel):
    model_config = ConfigDict(use_enum_values=True)


class TextBlock(BaseBlock):
    type: Literal["text"] = "text"
    text: str


class PunnettProbabilities(BaseModel):
    AA: float = 0.0
    AS: float = 0.0
    SS: float = 0.0
    SC: float = 0.0
    S_beta_thal: float = 0.0


class PunnettCell(BaseModel):
    genotype: HbGenotype
    probability: float
    severity: Severity


class PunnettData(BaseModel):
    p1: HbGenotype
    p2: HbGenotype
    probabilities: PunnettProbabilities
    grid: list[list[PunnettCell]] = Field(default_factory=list)


class PunnettBlock(BaseBlock):
    type: Literal["punnett"] = "punnett"
    data: PunnettData


class FacilityItem(BaseModel):
    id: str
    name: str
    type: FacilityService
    address: str
    distance_km: float
    rating: float | None = None
    open_now: bool | None = None
    directions_url: str


class FacilityData(BaseModel):
    user_location: dict[str, float]
    facilities: list[FacilityItem]


class FacilityBlock(BaseBlock):
    type: Literal["facility"] = "facility"
    data: FacilityData


class KeyFinding(BaseModel):
    label_native: str
    label_en: str
    value: str
    severity: Severity


class FileSummaryData(BaseModel):
    file_id: str
    key_findings: list[KeyFinding]
    what_it_means: str
    next_steps: list[str]
    document_type: str | None = None
    detailed_analysis: str | None = None
    full_text: str | None = None
    filename: str | None = None


class FileSummaryBlock(BaseBlock):
    type: Literal["file_summary"] = "file_summary"
    data: FileSummaryData


class CrisisHelpline(BaseModel):
    name: str
    number: str


class CrisisData(BaseModel):
    severity: Severity
    helplines: list[CrisisHelpline]
    message: str


class CrisisBannerBlock(BaseBlock):
    type: Literal["crisis_banner"] = "crisis_banner"
    data: CrisisData


class ConsentGateData(BaseModel):
    action: str
    scopes: list[ConsentScope]
    description: str


class ConsentGateBlock(BaseBlock):
    type: Literal["consent_gate"] = "consent_gate"
    data: ConsentGateData


class ReferralData(BaseModel):
    facility_type: FacilityService
    nearest: list[FacilityItem]
    why: str


class ReferralBlock(BaseBlock):
    type: Literal["referral"] = "referral"
    data: ReferralData


class StarterChip(BaseModel):
    id: str
    text: str


class StarterChipsBlock(BaseBlock):
    type: Literal["starter_chips"] = "starter_chips"
    data: dict[str, list[StarterChip]]


ContentBlock = Annotated[
    TextBlock
    | PunnettBlock
    | FacilityBlock
    | FileSummaryBlock
    | CrisisBannerBlock
    | ConsentGateBlock
    | ReferralBlock
    | StarterChipsBlock,
    Field(discriminator="type"),
]


# ── Session ────────────────────────────────────────────────────────

class SessionStartRequest(BaseModel):
    language: Language = Language.EN
    persona_hint: Persona | None = None


class SessionStartResponse(BaseModel):
    session_id: str
    language: Language
    consent_required: bool
    created_at: datetime


class ConsentRecord(BaseModel):
    accepted: bool
    method: ConsentMethod | None = None
    scopes: list[ConsentScope] = Field(default_factory=list)
    recorded_at: datetime | None = None


class ConsentRequest(BaseModel):
    accepted: bool
    method: ConsentMethod = ConsentMethod.TAP
    scopes: list[ConsentScope] = Field(default_factory=list)


class ConsentResponse(BaseModel):
    session_id: str
    consent: ConsentRecord


class UserLocation(BaseModel):
    lat: float
    lng: float
    label: str | None = None


class SessionState(BaseModel):
    session_id: str
    language: Language
    persona: Persona | None = None
    consent: ConsentRecord
    message_count: int = 0
    location: UserLocation | None = None
    created_at: datetime
    last_activity: datetime


class LocationUpdateRequest(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    label: str | None = Field(default=None, max_length=120)


class LanguageSwitchRequest(BaseModel):
    language: Language


class SessionDeleteRequest(BaseModel):
    purge_data: bool = True


class SessionDeleteResponse(BaseModel):
    session_id: str
    purged: bool


# ── Chat ───────────────────────────────────────────────────────────

class Attachment(BaseModel):
    file_id: str


class ChatMessageRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    attachments: list[Attachment] = Field(default_factory=list)
    persona_hint: Persona | None = None


class SuggestedReply(BaseModel):
    id: str
    text: str


class SourceMeta(BaseModel):
    chunk_ids: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    model: str | None = None
    reranker_score: float | None = None


class ChatMessageResponse(BaseModel):
    message_id: str
    role: Literal["assistant"] = "assistant"
    language: Language
    source: MessageSource
    source_meta: SourceMeta
    content: list[ContentBlock]
    audio_url: str | None = None
    feedback_id: str
    suggested_replies: list[SuggestedReply] = Field(default_factory=list)
    timestamp: datetime


class ChatFeedbackRequest(BaseModel):
    message_id: str
    feedback_id: str
    rating: FeedbackRating
    reason: str | None = None
    comment: str | None = Field(default=None, max_length=500)


class ChatFeedbackResponse(BaseModel):
    recorded: bool = True


# ── Punnett tool ───────────────────────────────────────────────────

class PunnettRequest(BaseModel):
    parent1_hb: HbGenotype
    parent2_hb: HbGenotype
    language: Language = Language.EN


class PunnettNarrative(BaseModel):
    headline: str
    body: str
    risk_level: Literal["none", "low", "moderate", "high", "very_high", "certain"]


class PunnettResponse(BaseModel):
    probabilities: PunnettProbabilities
    narrative: PunnettNarrative
    visual_data: PunnettData


# ── Files + OCR ────────────────────────────────────────────────────

class FileType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    IMAGE = "image"


class FileStatus(str, Enum):
    QUEUED = "queued"
    OCR_PROCESSING = "ocr_processing"
    SUMMARIZING = "summarizing"
    DONE = "done"
    FAILED = "failed"


class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    size_bytes: int
    type: FileType
    status: FileStatus


class FileSummary(BaseModel):
    language: Language
    key_findings: list[KeyFinding]
    what_it_means: str
    next_steps: list[str]
    document_type: str | None = None
    detailed_analysis: str | None = None
    full_text: str | None = None


class FileStateResponse(BaseModel):
    file_id: str
    status: FileStatus
    ocr_text: str | None = None
    summary: FileSummary | None = None
    error: str | None = None


class FileSummarizeRequest(BaseModel):
    language: Language


# ── Facilities ─────────────────────────────────────────────────────

class NearbyFacilitiesResponse(BaseModel):
    user_location: dict[str, float]
    facilities: list[FacilityItem]


class DirectionsResponse(BaseModel):
    directions_url: str


# ── Voice ──────────────────────────────────────────────────────────

class VoiceTranscribeResponse(BaseModel):
    text: str
    detected_language: Language
    confidence: float


class VoiceSynthesizeRequest(BaseModel):
    text: str
    language: Language


class VoiceSynthesizeResponse(BaseModel):
    audio_url: str
    duration_sec: float


# ── Meta ───────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    version: str


class LanguageInfo(BaseModel):
    code: Language
    name_native: str
    name_english: str


class LanguagesListResponse(BaseModel):
    languages: list[LanguageInfo]


class DiseaseInfo(BaseModel):
    id: Disease
    name_en: str
    active: bool
    faq_count: int


class DiseasesListResponse(BaseModel):
    diseases: list[DiseaseInfo]


# ── Language detect ────────────────────────────────────────────────

class LanguageDetectRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


class LanguageDetectResponse(BaseModel):
    language: Language
    confidence: float


# ── RAG admin ──────────────────────────────────────────────────────

class RagChunkMetadata(BaseModel):
    audience: list[Persona] = Field(default_factory=list)
    scenario: str | None = None
    topic: str | None = None
    language: Language = Language.EN
    source: str = "manual"
    confidence: float = 1.0


class RagChunkInput(BaseModel):
    text: str
    metadata: RagChunkMetadata


class RagIngestRequest(BaseModel):
    disease: Disease
    chunks: list[RagChunkInput]


class RagIngestResponse(BaseModel):
    ingested: int
    failed: int
    chunk_ids: list[str]


class RagSearchResult(BaseModel):
    chunk_id: str
    text: str
    score: float
    reranker_score: float | None = None
    metadata: dict[str, Any]


class RagSearchResponse(BaseModel):
    query: str
    results: list[RagSearchResult]


class RagCollectionStats(BaseModel):
    disease: Disease
    total_chunks: int
    by_language: dict[str, int]
    by_source: dict[str, int]


class RagStatsResponse(BaseModel):
    collections: list[RagCollectionStats]


class RagReviewAction(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    EDIT = "edit"


class RagReviewRequest(BaseModel):
    chunk_id: str
    action: RagReviewAction
    edited_text: str | None = None
    new_confidence: float | None = None


# ── Error response ─────────────────────────────────────────────────

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorDetail
