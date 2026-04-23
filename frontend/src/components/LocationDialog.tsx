import { MapPin } from "lucide-react";
import { useState } from "react";
import { t } from "../lib/i18n";
import { useApp } from "../state/store";

export function LocationDialog({
  onAllow,
  onSkip,
}: {
  onAllow: () => Promise<void>;
  onSkip: () => void;
}) {
  const { language } = useApp();
  const [busy, setBusy] = useState(false);

  async function handle() {
    setBusy(true);
    try {
      await onAllow();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-paper/80 dark:bg-slate-900/80 backdrop-blur-md grid place-items-center p-4 animate-fade-in-up">
      <div className="card max-w-md w-full p-6 sm:p-8 text-center">
        <div className="mx-auto w-16 h-16 rounded-3xl bg-disha-50 dark:bg-disha-900/40 text-disha-600 dark:text-disha-300 grid place-items-center mb-4">
          <MapPin size={28} />
        </div>
        <h2 className="font-display font-bold text-xl mb-2 dark:text-slate-100">
          {t("location_ask_title", language)}
        </h2>
        <p className="text-[14.5px] leading-relaxed text-ink-soft dark:text-slate-300 mb-6">
          {t("location_ask_body", language)}
        </p>
        <div className="flex flex-col gap-2">
          <button className="btn-primary !py-3" onClick={handle} disabled={busy}>
            {t("location_allow", language)}
          </button>
          <button className="btn-ghost" onClick={onSkip} disabled={busy}>
            {t("location_skip", language)}
          </button>
        </div>
      </div>
    </div>
  );
}
