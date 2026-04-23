import { Globe } from "lucide-react";
import { useState } from "react";
import { api } from "../api/client";
import type { Language } from "../api/types";
import { t } from "../lib/i18n";
import { cn } from "../lib/utils";
import { useApp } from "../state/store";

const LANGS: { code: Language; native: string }[] = [
  { code: "en", native: "English" },
  { code: "hi", native: "हिन्दी" },
  { code: "mr", native: "मराठी" },
];

export function LanguageSwitcher({ compact = false }: { compact?: boolean }) {
  const { language, setLanguage } = useApp();
  const [open, setOpen] = useState(false);

  async function pick(code: Language) {
    setLanguage(code);
    setOpen(false);
    document.documentElement.lang = code;
    try {
      await api.switchLanguage(code);
    } catch {
      // offline or pre-session — state already updated locally
    }
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className={cn(
          "btn-ghost !rounded-full !px-3 !py-2",
          compact && "!px-2"
        )}
        aria-label="Change language"
      >
        <Globe size={16} />
        <span className="font-semibold">
          {LANGS.find((l) => l.code === language)?.native}
        </span>
      </button>
      {open && (
        <div
          className="absolute right-0 top-full mt-2 z-20 min-w-[180px] rounded-2xl bg-white dark:bg-slate-800 shadow-card border border-ink/5 dark:border-white/10 p-1.5 animate-fade-in-up"
          onMouseLeave={() => setOpen(false)}
        >
          {LANGS.map((l) => (
            <button
              key={l.code}
              onClick={() => pick(l.code)}
              className={cn(
                "w-full text-left px-3 py-2 rounded-xl hover:bg-paper-warm dark:hover:bg-slate-700 flex items-center justify-between",
                language === l.code
                  ? "bg-disha-50 dark:bg-disha-900/30 text-disha-700 dark:text-disha-300"
                  : "dark:text-slate-200"
              )}
            >
              <span className="font-medium">{l.native}</span>
              <span className="text-xs text-ink-muted dark:text-slate-400">{t(`lang_${l.code}`, "en")}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
