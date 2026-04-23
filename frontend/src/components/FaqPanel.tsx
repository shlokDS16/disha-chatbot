import { useEffect, useState } from "react";
import { Lightbulb } from "lucide-react";
import { api } from "../api/client";
import type { StarterChipsBlock } from "../api/types";
import { t } from "../lib/i18n";
import { useApp } from "../state/store";

export function FaqPanel({ onPick }: { onPick: (text: string) => void }) {
  const { language } = useApp();
  const [chips, setChips] = useState<StarterChipsBlock | null>(null);

  useEffect(() => {
    let alive = true;
    api
      .starterChips(language)
      .then((b) => {
        if (!alive) return;
        setChips(b as StarterChipsBlock);
      })
      .catch(() => {
        // non-fatal
      });
    return () => {
      alive = false;
    };
  }, [language]);

  if (!chips || chips.data.chips.length === 0) return null;

  return (
    <div className="px-4 py-3 border-t border-ink/5 dark:border-white/10">
      <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-wider text-ink-muted dark:text-slate-400 font-semibold mb-2">
        <Lightbulb size={12} />
        {t("faq_always_title", language)}
      </div>
      <div className="flex flex-col gap-1.5">
        {chips.data.chips.slice(0, 6).map((c) => (
          <button
            key={c.id}
            onClick={() => onPick(c.text)}
            className="text-left text-[13px] leading-snug rounded-xl border border-disha-200 dark:border-disha-900/40 bg-white dark:bg-slate-800 text-disha-700 dark:text-disha-300 hover:bg-disha-50 dark:hover:bg-slate-700 px-3 py-2 transition"
          >
            {c.text}
          </button>
        ))}
      </div>
    </div>
  );
}
