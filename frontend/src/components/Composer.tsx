import { Loader2, Mic, MicOff, Paperclip, Send, Square } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { t } from "../lib/i18n";
import { cn } from "../lib/utils";
import { useApp } from "../state/store";

interface Props {
  onSend: (text: string) => void;
  onAttach: (file: File) => void;
  busy: boolean;
}

export function Composer({ onSend, onAttach, busy }: Props) {
  const { language } = useApp();
  const [text, setText] = useState("");
  const [listening, setListening] = useState(false);
  const taRef = useRef<HTMLTextAreaElement | null>(null);
  const fileRef = useRef<HTMLInputElement | null>(null);
  const recRef = useRef<SpeechRecognitionLike | null>(null);

  useEffect(() => {
    autoResize();
  }, [text]);

  function autoResize() {
    const ta = taRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 180) + "px";
  }

  function submit() {
    const v = text.trim();
    if (!v || busy) return;
    onSend(v);
    setText("");
    setTimeout(autoResize, 10);
  }

  function toggleMic() {
    if (listening) {
      recRef.current?.stop();
      setListening(false);
      return;
    }
    const SR =
      (window as unknown as { SpeechRecognition?: unknown; webkitSpeechRecognition?: unknown })
        .SpeechRecognition ??
      (window as unknown as { SpeechRecognition?: unknown; webkitSpeechRecognition?: unknown })
        .webkitSpeechRecognition;
    if (!SR) {
      alert("Voice input is not supported in this browser.");
      return;
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const rec: SpeechRecognitionLike = new (SR as any)();
    rec.lang = language === "hi" ? "hi-IN" : language === "mr" ? "mr-IN" : "en-IN";
    rec.interimResults = true;
    rec.continuous = false;
    rec.onresult = (ev) => {
      let transcript = "";
      for (let i = 0; i < ev.results.length; i++) {
        transcript += ev.results[i][0].transcript;
      }
      setText(transcript);
    };
    rec.onend = () => setListening(false);
    rec.onerror = () => setListening(false);
    rec.start();
    recRef.current = rec;
    setListening(true);
  }

  return (
    <div className="px-3 sm:px-5 pb-4 pt-2 bg-gradient-to-t from-paper via-paper/90 to-transparent dark:from-slate-900 dark:via-slate-900/90">
      <div className="max-w-3xl mx-auto">
        <div className="card p-2 sm:p-2.5 flex items-end gap-2">
          <input
            ref={fileRef}
            type="file"
            accept="image/*,.pdf,.docx"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) onAttach(f);
              e.currentTarget.value = "";
            }}
          />
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            className="btn-ghost !p-2.5 shrink-0"
            title={t("attach", language)}
          >
            <Paperclip size={18} />
          </button>

          <textarea
            ref={taRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submit();
              }
            }}
            placeholder={
              listening ? t("listening", language) : t("composer_placeholder", language)
            }
            rows={1}
            className="flex-1 resize-none bg-transparent border-0 focus:outline-none px-1 py-2 text-[15.5px] leading-6 max-h-[180px] dark:text-slate-100 dark:placeholder:text-slate-500"
          />

          <button
            type="button"
            onClick={toggleMic}
            className={cn(
              "btn-ghost !p-2.5 shrink-0",
              listening && "!bg-rose-50 !text-rose-600"
            )}
            title={t("mic", language)}
          >
            {listening ? <MicOff size={18} /> : <Mic size={18} />}
          </button>

          <button
            type="button"
            onClick={submit}
            disabled={busy || !text.trim()}
            className={cn(
              "btn-primary !rounded-full !p-2.5 !min-w-[44px] !w-[44px] !h-[44px] shrink-0 grid place-items-center",
              busy && "!bg-disha-400"
            )}
          >
            {busy ? (
              <Loader2 size={18} className="animate-spin" />
            ) : listening ? (
              <Square size={18} />
            ) : (
              <Send size={18} />
            )}
          </button>
        </div>
        <div className="text-[10px] text-ink-muted dark:text-slate-500 text-center mt-1.5">
          Disha is informational — please consult your doctor for medical decisions.
        </div>
      </div>
    </div>
  );
}

// Minimal typing shim so we don't depend on lib.dom for SpeechRecognition
interface SpeechRecognitionLike {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  onresult: (ev: {
    results: { [index: number]: { [index: number]: { transcript: string } }; length: number };
  }) => void;
  onend: () => void;
  onerror: () => void;
  start: () => void;
  stop: () => void;
}
