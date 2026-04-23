import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "../api/client";
import type { StarterChipsBlock } from "../api/types";
import { MessageContent } from "../components/MessageContent";
import { Composer } from "../components/Composer";
import { Logo } from "../components/Logo";
import { Message } from "../components/Message";
import { t } from "../lib/i18n";
import { useApp, type ChatMsg } from "../state/store";

export function ChatView() {
  const {
    language,
    persona,
    setPersona,
    messages,
    pushMessage,
    isSending,
    setSending,
  } = useApp();
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const [starterChips, setStarterChips] = useState<StarterChipsBlock | null>(null);
  const [showPersonaPicker, setShowPersonaPicker] = useState(!persona);

  useEffect(() => {
    let alive = true;
    api
      .starterChips(language)
      .then((b) => {
        if (!alive) return;
        setStarterChips(b as StarterChipsBlock);
      })
      .catch(() => {
        // non-fatal
      });
    return () => {
      alive = false;
    };
  }, [language]);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [messages, isSending]);

  useEffect(() => {
    function onChip(e: Event) {
      const ev = e as CustomEvent<{ text: string }>;
      if (ev.detail?.text) send(ev.detail.text);
    }
    window.addEventListener("disha:chip-pick", onChip);
    return () => window.removeEventListener("disha:chip-pick", onChip);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [persona]);

  async function send(text: string) {
    const userMsg: ChatMsg = {
      id: crypto.randomUUID(),
      role: "user",
      text,
      timestamp: new Date().toISOString(),
    };
    pushMessage(userMsg);
    setSending(true);
    try {
      const res = await api.sendChat(text, persona ?? undefined);
      const textBlock = res.content.find((b) => b.type === "text") as
        | { type: "text"; text: string }
        | undefined;
      pushMessage({
        id: res.message_id,
        role: "assistant",
        content: res.content,
        text: textBlock?.text ?? "",
        source: res.source,
        source_meta: res.source_meta,
        feedback_id: res.feedback_id,
        suggested_replies: res.suggested_replies,
        audio_url: res.audio_url,
        timestamp: res.timestamp,
      });
    } catch (e) {
      const msg =
        e instanceof ApiError
          ? `Server error (${e.status}). Please try again.`
          : "Could not reach Disha. Check your connection.";
      pushMessage({
        id: crypto.randomUUID(),
        role: "assistant",
        content: [{ type: "text", text: msg }],
        text: msg,
        source: "llm",
        source_meta: { chunk_ids: [], confidence: 0 },
        feedback_id: "",
        suggested_replies: [],
        timestamp: new Date().toISOString(),
      });
    } finally {
      setSending(false);
    }
  }

  async function attach(file: File) {
    try {
      const up = await api.uploadFile(file);
      pushMessage({
        id: crypto.randomUUID(),
        role: "user",
        text: `📎 ${file.name}`,
        timestamp: new Date().toISOString(),
      });
      // show a placeholder while OCR + LLM summary complete
      const placeholderId = crypto.randomUUID();
      pushMessage({
        id: placeholderId,
        role: "assistant",
        content: [
          { type: "text", text: t("file_processing", language) },
        ],
        text: t("file_processing", language),
        source: "tool",
        source_meta: { chunk_ids: [], confidence: 0 },
        feedback_id: "",
        suggested_replies: [],
        timestamp: new Date().toISOString(),
      });
      const sum = await pollFile(up.file_id);
      if (sum?.summary) {
        pushMessage({
          id: crypto.randomUUID(),
          role: "assistant",
          content: [
            {
              type: "file_summary",
              data: {
                file_id: up.file_id,
                filename: file.name,
                key_findings: sum.summary.key_findings,
                what_it_means: sum.summary.what_it_means,
                next_steps: sum.summary.next_steps,
                document_type: sum.summary.document_type,
                detailed_analysis: sum.summary.detailed_analysis,
                full_text: sum.summary.full_text,
              },
            },
          ],
          text:
            sum.summary.detailed_analysis ||
            sum.summary.what_it_means ||
            "Document processed.",
          source: "tool",
          source_meta: { chunk_ids: [], confidence: 1 },
          feedback_id: "",
          suggested_replies: [],
          timestamp: new Date().toISOString(),
        });
      } else {
        pushMessage({
          id: crypto.randomUUID(),
          role: "assistant",
          content: [
            { type: "text", text: t("file_failed", language) },
          ],
          text: t("file_failed", language),
          source: "llm",
          source_meta: { chunk_ids: [], confidence: 0 },
          feedback_id: "",
          suggested_replies: [],
          timestamp: new Date().toISOString(),
        });
      }
    } catch {
      // show in chat
      pushMessage({
        id: crypto.randomUUID(),
        role: "assistant",
        content: [{ type: "text", text: t("file_failed", language) }],
        text: t("file_failed", language),
        source: "llm",
        source_meta: { chunk_ids: [], confidence: 0 },
        feedback_id: "",
        suggested_replies: [],
        timestamp: new Date().toISOString(),
      });
    }
  }

  async function pollFile(file_id: string) {
    for (let i = 0; i < 90; i++) {
      try {
        const r = await api.getFile(file_id);
        if (r.status === "done") {
          // Re-request summary in the user's current language (the background
          // task might have summarised in a different one).
          return await api.summarizeFile(file_id, language);
        }
        if (r.status === "failed") return null;
      } catch {
        return null;
      }
      await new Promise((r) => setTimeout(r, 1500));
    }
    return null;
  }

  return (
    <div className="flex-1 flex flex-col min-h-0">
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto scrollbar-thin px-3 sm:px-5 py-6"
      >
        <div className="max-w-3xl mx-auto space-y-5">
          {messages.length === 0 && (
            <EmptyHero
              onPick={send}
              showPersona={showPersonaPicker}
              onPersona={(p) => {
                setPersona(p);
                setShowPersonaPicker(false);
              }}
              starterChips={starterChips}
            />
          )}
          {messages.map((m) => (
            <Message key={m.id} msg={m} onChipPick={send} />
          ))}
          {isSending && <Thinking />}
        </div>
      </div>
      <Composer onSend={send} onAttach={attach} busy={isSending} />
    </div>
  );
}

function EmptyHero({
  onPick,
  showPersona,
  onPersona,
  starterChips,
}: {
  onPick: (text: string) => void;
  showPersona: boolean;
  onPersona: (p: "asha" | "couple" | "patient" | "doctor") => void;
  starterChips: StarterChipsBlock | null;
}) {
  const { language, persona } = useApp();
  return (
    <div className="pt-6 sm:pt-12">
      <div className="flex items-center gap-4 mb-6">
        <Logo size={60} />
        <div>
          <div className="font-display font-extrabold text-3xl sm:text-4xl leading-tight dark:text-slate-100">
            {t("hello_hero_a", language)}
          </div>
        </div>
      </div>
      <p className="text-[17px] leading-8 text-ink-soft dark:text-slate-300 max-w-xl mb-6">
        {t("hello_hero_b", language)}
      </p>

      {showPersona && (
        <div className="card p-4 mb-6">
          <div className="text-[12px] uppercase tracking-wider text-ink-muted dark:text-slate-400 font-semibold mb-3">
            {t("persona_pick", language)}
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {(["asha", "couple", "patient", "doctor"] as const).map((p) => (
              <button
                key={p}
                onClick={() => onPersona(p)}
                className="rounded-2xl border border-ink/5 dark:border-white/10 bg-white dark:bg-slate-800 hover:bg-disha-50 dark:hover:bg-slate-700 hover:border-disha-200 dark:hover:border-disha-900/40 transition px-3 py-3 text-center text-ink dark:text-slate-200"
              >
                <div className="text-lg mb-0.5">
                  {p === "asha" ? "🎽" : p === "couple" ? "👫" : p === "patient" ? "🧑‍⚕️" : "👨‍⚕️"}
                </div>
                <div className="text-[12.5px] font-medium">
                  {t(`persona_${p}`, language)}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {starterChips && (
        <div className="card p-4">
          <MessageContent
            blocks={[
              {
                type: "starter_chips",
                data: starterChips.data,
              },
            ]}
            onChipPick={onPick}
          />
        </div>
      )}

      {!persona && !showPersona && (
        <button
          className="btn-ghost mt-4"
          onClick={() => onPersona("patient")}
        >
          {t("persona_pick", language)}
        </button>
      )}
    </div>
  );
}

function Thinking() {
  const { language } = useApp();
  return (
    <div className="flex items-center gap-2.5 animate-fade-in-up">
      <Logo size={28} />
      <div className="bg-white dark:bg-slate-800 rounded-2xl rounded-tl-lg border border-ink/5 dark:border-white/10 px-4 py-3 shadow-soft flex items-center gap-2">
        <span className="flex gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-disha-500 animate-bounce-dot" />
          <span
            className="w-1.5 h-1.5 rounded-full bg-disha-500 animate-bounce-dot"
            style={{ animationDelay: "160ms" }}
          />
          <span
            className="w-1.5 h-1.5 rounded-full bg-disha-500 animate-bounce-dot"
            style={{ animationDelay: "320ms" }}
          />
        </span>
        <span className="text-[13px] text-ink-muted dark:text-slate-400">{t("thinking", language)}</span>
      </div>
    </div>
  );
}
