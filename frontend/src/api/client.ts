import type {
  ChatMessageResponse,
  ContentBlock,
  FileStateResponse,
  FileUploadResponse,
  Language,
  NearbyFacilitiesResponse,
  Persona,
  PunnettResponse,
  SessionStartResponse,
  SessionState,
} from "./types";

// In dev we leave VITE_API_URL unset so requests go through the Vite proxy
// at `/api` (see vite.config.ts). In production (Vercel) we set it to the
// backend's absolute URL, e.g. "https://disha-backend.onrender.com".
const API_ROOT = (import.meta.env.VITE_API_URL ?? "").replace(/\/+$/, "");
const BASE = `${API_ROOT}/api/v1`;

function sid(): string | null {
  return localStorage.getItem("disha.session_id");
}

async function jsonReq<T>(
  path: string,
  options: RequestInit = {},
  withSession = true
): Promise<T> {
  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }
  if (withSession) {
    const s = sid();
    if (s) headers.set("X-Session-Id", s);
  }
  if (!headers.has("X-User-Language")) {
    const lang = localStorage.getItem("disha.lang");
    if (lang) headers.set("X-User-Language", lang);
  }
  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    let detail: unknown = null;
    try {
      detail = await res.json();
    } catch {
      detail = await res.text().catch(() => null);
    }
    throw new ApiError(res.status, detail);
  }
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return (await res.json()) as T;
  return (await res.text()) as unknown as T;
}

export class ApiError extends Error {
  status: number;
  detail: unknown;
  constructor(status: number, detail: unknown) {
    super(`API ${status}`);
    this.status = status;
    this.detail = detail;
  }
}

// ── Session ────────────────────────────────────────────────────────

export const api = {
  startSession(language: Language, persona?: Persona) {
    return jsonReq<SessionStartResponse>(
      "/session/start",
      {
        method: "POST",
        body: JSON.stringify({ language, persona_hint: persona }),
      },
      false
    );
  },

  getSession() {
    return jsonReq<SessionState>("/session", { method: "GET" });
  },

  switchLanguage(language: Language) {
    return jsonReq<SessionState>("/session/language", {
      method: "POST",
      body: JSON.stringify({ language }),
    });
  },

  setLocation(lat: number, lng: number, label?: string) {
    return jsonReq<SessionState>("/session/location", {
      method: "POST",
      body: JSON.stringify({ lat, lng, label: label ?? null }),
    });
  },

  recordConsent(
    accepted: boolean,
    method: "tap" | "verbal",
    scopes: string[]
  ) {
    return jsonReq<{ session_id: string; consent: SessionState["consent"] }>(
      "/session/consent",
      {
        method: "POST",
        body: JSON.stringify({ accepted, method, scopes }),
      }
    );
  },

  deleteSession(purge = true) {
    return jsonReq<{ session_id: string; purged: boolean }>("/session", {
      method: "DELETE",
      body: JSON.stringify({ purge_data: purge }),
    });
  },

  // ── Chat ────────────────────────────────────────────────────────
  sendChat(
    text: string,
    persona?: Persona,
    attachments: { file_id: string }[] = []
  ) {
    return jsonReq<ChatMessageResponse>("/chat/message", {
      method: "POST",
      body: JSON.stringify({
        text,
        attachments,
        persona_hint: persona,
      }),
    });
  },

  sendFeedback(
    message_id: string,
    feedback_id: string,
    rating: "up" | "down",
    reason?: string
  ) {
    return jsonReq<{ recorded: boolean }>("/chat/feedback", {
      method: "POST",
      body: JSON.stringify({ message_id, feedback_id, rating, reason }),
    });
  },

  listHistory() {
    return jsonReq<{
      session_id: string;
      messages: {
        message_id: string;
        role: "user" | "assistant";
        language: Language;
        text: string;
        source?: string | null;
        created_at: string;
      }[];
    }>("/chat/history", { method: "GET" });
  },

  clearHistory() {
    return jsonReq<{ session_id: string; removed: number }>("/chat/history", {
      method: "DELETE",
    });
  },

  exportHistory() {
    return jsonReq<{
      session_id: string;
      markdown: string;
      raw: unknown;
    }>("/chat/export", { method: "GET" });
  },

  // ── Files ───────────────────────────────────────────────────────
  async uploadFile(file: File): Promise<FileUploadResponse> {
    const fd = new FormData();
    fd.append("file", file);
    const s = sid();
    const lang = localStorage.getItem("disha.lang");
    const headers: Record<string, string> = {};
    if (s) headers["X-Session-Id"] = s;
    if (lang) headers["X-User-Language"] = lang;
    const res = await fetch(`${BASE}/files/upload`, {
      method: "POST",
      body: fd,
      headers,
    });
    if (!res.ok) throw new ApiError(res.status, await res.text());
    return res.json();
  },

  getFile(file_id: string) {
    return jsonReq<FileStateResponse>(`/files/${file_id}`, { method: "GET" });
  },

  summarizeFile(file_id: string, language: Language) {
    return jsonReq<FileStateResponse>(`/files/${file_id}/summarize`, {
      method: "POST",
      body: JSON.stringify({ language }),
    });
  },

  // ── Facilities ──────────────────────────────────────────────────
  nearbyFacilities(lat: number, lng: number, service = "any", radius = 15) {
    const params = new URLSearchParams({
      lat: String(lat),
      lng: String(lng),
      service,
      radius_km: String(radius),
    });
    return jsonReq<NearbyFacilitiesResponse>(
      `/facilities/nearby?${params.toString()}`,
      { method: "GET" }
    );
  },

  // ── Tools ───────────────────────────────────────────────────────
  punnett(parent1_hb: string, parent2_hb: string, language: Language) {
    return jsonReq<PunnettResponse>("/tools/punnett", {
      method: "POST",
      body: JSON.stringify({ parent1_hb, parent2_hb, language }),
    });
  },

  // ── Content ─────────────────────────────────────────────────────
  async starterChips(language: Language) {
    const res = await jsonReq<{
      language: Language;
      block: {
        type: "starter_chips";
        data: { chips: { id: string; text: string }[] };
      };
    }>(`/content/starter-chips?language=${language}`, { method: "GET" });
    return res.block;
  },

  healthTips(language: Language) {
    return jsonReq<{ language: Language; tips: unknown[] }>(
      `/content/health-tips?language=${language}`,
      { method: "GET" }
    );
  },

  crisisHelplines(language: Language) {
    return jsonReq<{ language: Language; helplines: unknown[] }>(
      `/content/crisis-helplines?language=${language}`,
      { method: "GET" }
    );
  },

  consentCopy(language: Language) {
    return jsonReq<{
      language: Language;
      title: string;
      body: string;
      bullets: string[];
      accept: string;
      decline: string;
    }>(`/content/consent-copy?language=${language}`, { method: "GET" });
  },

  // ── Voice ───────────────────────────────────────────────────────
  synthesizeVoice(text: string, language: Language) {
    return jsonReq<{ audio_url: string; duration_sec: number }>(
      "/voice/synthesize",
      {
        method: "POST",
        body: JSON.stringify({ text, language }),
      }
    );
  },
};

export function setSessionId(id: string) {
  localStorage.setItem("disha.session_id", id);
}

export function clearSessionId() {
  localStorage.removeItem("disha.session_id");
}

export function hasSession(): boolean {
  return !!sid();
}

// Unwrap content array — backend currently returns ContentBlock[] inside chat responses
export function extractText(blocks: ContentBlock[]): string {
  const t = blocks.find((b) => b.type === "text") as
    | { type: "text"; text: string }
    | undefined;
  return t?.text ?? "";
}
