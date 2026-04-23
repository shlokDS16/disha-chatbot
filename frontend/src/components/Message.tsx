import { Pause, Play, ThumbsDown, ThumbsUp, Volume2 } from "lucide-react";
import { useRef, useState } from "react";
import { api } from "../api/client";
import type { MessageSource } from "../api/types";
import { t } from "../lib/i18n";
import { cn } from "../lib/utils";
import { useApp, type ChatMsg } from "../state/store";
import { Logo } from "./Logo";
import { MessageContent } from "./MessageContent";

export function Message({
  msg,
  onChipPick,
}: {
  msg: ChatMsg;
  onChipPick: (text: string) => void;
}) {
  const { language } = useApp();
  if (msg.role === "user") {
    return (
      <div className="flex justify-end animate-fade-in-up">
        <div className="max-w-[78%] rounded-3xl rounded-tr-lg bg-disha-600 dark:bg-disha-500 text-white px-4 py-3 shadow-soft">
          <div className="text-[15.5px] leading-7 whitespace-pre-wrap">{msg.text}</div>
          <div className="text-[10px] opacity-70 mt-1 text-right">
            {t("you", language)}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-2.5 animate-fade-in-up">
      <Logo size={32} className="mt-0.5" />
      <div className="max-w-[92%] flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-semibold text-[13px] dark:text-slate-200">{t("disha", language)}</span>
          <SourceTag source={msg.source} lang={language} />
        </div>
        <div className="rounded-3xl rounded-tl-lg bg-white dark:bg-slate-800 border border-ink/5 dark:border-white/10 px-4 py-3 shadow-soft text-ink dark:text-slate-100">
          <MessageContent blocks={msg.content} onChipPick={onChipPick} />
        </div>
        <MessageFooter msg={msg} />
      </div>
    </div>
  );
}

function SourceTag({
  source,
  lang,
}: {
  source: MessageSource;
  lang: "en" | "hi" | "mr";
}) {
  const map: Record<MessageSource, { key: string; cls: string }> = {
    rag: { key: "source_rag", cls: "bg-leaf/10 text-leaf border-leaf/20" },
    llm: { key: "source_llm", cls: "bg-disha-50 text-disha-700 border-disha-200" },
    hybrid: { key: "source_hybrid", cls: "bg-amber-50 text-amber-800 border-amber-200" },
    tool: { key: "source_tool", cls: "bg-sky-50 text-sky-800 border-sky-200" },
  };
  const m = map[source];
  if (!m) return null;
  return (
    <span className={cn("text-[10px] px-2 py-0.5 rounded-full border font-semibold", m.cls)}>
      {t(m.key, lang)}
    </span>
  );
}

function MessageFooter({ msg }: { msg: Extract<ChatMsg, { role: "assistant" }> }) {
  const { language } = useApp();
  const [voted, setVoted] = useState<"up" | "down" | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(msg.audio_url ?? null);
  const [playing, setPlaying] = useState(false);
  const [loadingAudio, setLoadingAudio] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  async function vote(r: "up" | "down") {
    setVoted(r);
    try {
      await api.sendFeedback(msg.id, msg.feedback_id, r);
    } catch {
      // silently swallow
    }
  }

  async function togglePlay() {
    if (!audioUrl) {
      setLoadingAudio(true);
      try {
        const { audio_url } = await api.synthesizeVoice(
          msg.text.slice(0, 500),
          language
        );
        setAudioUrl(audio_url);
        setTimeout(() => audioRef.current?.play(), 50);
      } catch {
        // fallback to browser TTS
        if ("speechSynthesis" in window) {
          const utt = new SpeechSynthesisUtterance(msg.text);
          utt.lang = language === "hi" ? "hi-IN" : language === "mr" ? "mr-IN" : "en-US";
          window.speechSynthesis.speak(utt);
        }
      } finally {
        setLoadingAudio(false);
      }
      return;
    }
    if (audioRef.current) {
      if (playing) audioRef.current.pause();
      else void audioRef.current.play();
    }
  }

  return (
    <div className="flex items-center gap-1.5 mt-1.5 ml-1">
      <button
        className={cn(
          "btn-ghost !p-1.5 !rounded-full",
          voted === "up" && "!text-leaf !bg-leaf/10"
        )}
        onClick={() => vote("up")}
        title={t("feedback_helpful", language)}
      >
        <ThumbsUp size={13} />
      </button>
      <button
        className={cn(
          "btn-ghost !p-1.5 !rounded-full",
          voted === "down" && "!text-rose-700 !bg-rose-50"
        )}
        onClick={() => vote("down")}
        title={t("feedback_not", language)}
      >
        <ThumbsDown size={13} />
      </button>
      <button
        className="btn-ghost !p-1.5 !rounded-full"
        onClick={togglePlay}
        disabled={loadingAudio}
        title={playing ? t("pause_audio", language) : t("play_audio", language)}
      >
        {loadingAudio ? (
          <Volume2 size={13} className="animate-pulse" />
        ) : playing ? (
          <Pause size={13} />
        ) : (
          <Play size={13} />
        )}
      </button>
      {msg.source_meta.reranker_score != null && (
        <span className="text-[10px] text-ink-muted dark:text-slate-500 ml-1">
          score {msg.source_meta.reranker_score.toFixed(2)}
        </span>
      )}
      {audioUrl && (
        <audio
          ref={audioRef}
          src={audioUrl}
          onPlay={() => setPlaying(true)}
          onPause={() => setPlaying(false)}
          onEnded={() => setPlaying(false)}
          className="hidden"
        />
      )}
    </div>
  );
}
