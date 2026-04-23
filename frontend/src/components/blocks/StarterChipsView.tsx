import type { StarterChipsBlock } from "../../api/types";
import { t } from "../../lib/i18n";
import { useApp } from "../../state/store";

export function StarterChipsView({
  block,
  onPick,
}: {
  block: StarterChipsBlock;
  onPick: (text: string) => void;
}) {
  const { language } = useApp();
  const chips = block.data?.chips ?? [];

  if (chips.length === 0) return null;

  return (
    <div className="mt-2">
      <div className="text-[11px] uppercase tracking-wider text-ink-muted dark:text-slate-400 mb-2 font-semibold">
        {t("suggested", language)}
      </div>
      <div className="flex flex-wrap gap-2">
        {chips.map((c) => (
          <button
            key={c.id}
            onClick={() => onPick(c.text)}
            className="chip !bg-white dark:!bg-slate-800 !border-disha-200 dark:!border-disha-900/40 !text-disha-700 dark:!text-disha-300 hover:!bg-disha-50 dark:hover:!bg-slate-700"
          >
            {c.text}
          </button>
        ))}
      </div>
    </div>
  );
}
