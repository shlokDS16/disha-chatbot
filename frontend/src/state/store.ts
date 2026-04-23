import { create } from "zustand";
import type {
  ChatMessageResponse,
  ContentBlock,
  Language,
  Persona,
  SessionState,
} from "../api/types";

export type ChatMsg =
  | {
      id: string;
      role: "user";
      text: string;
      timestamp: string;
    }
  | {
      id: string;
      role: "assistant";
      content: ContentBlock[];
      text: string;
      source: ChatMessageResponse["source"];
      source_meta: ChatMessageResponse["source_meta"];
      feedback_id: string;
      suggested_replies: ChatMessageResponse["suggested_replies"];
      audio_url?: string | null;
      timestamp: string;
    };

export type ViewKey = "chat" | "docs" | "tips" | "maps" | "consent" | "about";
export type Theme = "light" | "dark";

interface AppState {
  session: SessionState | null;
  language: Language;
  persona: Persona | null;
  messages: ChatMsg[];
  isSending: boolean;
  view: ViewKey;
  sidebarOpen: boolean;
  theme: Theme;

  setSession: (s: SessionState | null) => void;
  setLanguage: (l: Language) => void;
  setPersona: (p: Persona | null) => void;
  pushMessage: (m: ChatMsg) => void;
  replaceMessage: (id: string, m: ChatMsg) => void;
  clearMessages: () => void;
  setSending: (v: boolean) => void;
  setView: (v: ViewKey) => void;
  toggleSidebar: () => void;
  setSidebar: (v: boolean) => void;
  setTheme: (t: Theme) => void;
  toggleTheme: () => void;
}

const LANG_KEY = "disha.lang";
const PERSONA_KEY = "disha.persona";
const THEME_KEY = "disha.theme";

function readLang(): Language {
  const v = localStorage.getItem(LANG_KEY);
  if (v === "en" || v === "hi" || v === "mr") return v;
  return "en";
}

function readPersona(): Persona | null {
  const v = localStorage.getItem(PERSONA_KEY);
  if (v === "asha" || v === "couple" || v === "patient" || v === "doctor")
    return v;
  return null;
}

function readTheme(): Theme {
  const v = localStorage.getItem(THEME_KEY);
  if (v === "light" || v === "dark") return v;
  if (typeof window !== "undefined" && window.matchMedia) {
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }
  return "light";
}

function applyTheme(t: Theme) {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  if (t === "dark") root.classList.add("dark");
  else root.classList.remove("dark");
}

const initialTheme = readTheme();
applyTheme(initialTheme);

export const useApp = create<AppState>((set, get) => ({
  session: null,
  language: readLang(),
  persona: readPersona(),
  messages: [],
  isSending: false,
  view: "chat",
  sidebarOpen: false,
  theme: initialTheme,

  setSession: (s) => set({ session: s }),
  setLanguage: (l) => {
    localStorage.setItem(LANG_KEY, l);
    set({ language: l });
  },
  setPersona: (p) => {
    if (p) localStorage.setItem(PERSONA_KEY, p);
    else localStorage.removeItem(PERSONA_KEY);
    set({ persona: p });
  },
  pushMessage: (m) => set((s) => ({ messages: [...s.messages, m] })),
  replaceMessage: (id, m) =>
    set((s) => ({
      messages: s.messages.map((x) => (x.id === id ? m : x)),
    })),
  clearMessages: () => set({ messages: [] }),
  setSending: (v) => set({ isSending: v }),
  setView: (v) => set({ view: v, sidebarOpen: false }),
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setSidebar: (v) => set({ sidebarOpen: v }),
  setTheme: (t) => {
    localStorage.setItem(THEME_KEY, t);
    applyTheme(t);
    set({ theme: t });
  },
  toggleTheme: () => {
    const next: Theme = get().theme === "dark" ? "light" : "dark";
    localStorage.setItem(THEME_KEY, next);
    applyTheme(next);
    set({ theme: next });
  },
}));
