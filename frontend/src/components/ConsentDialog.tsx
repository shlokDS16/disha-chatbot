import { ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../api/client";
import { t } from "../lib/i18n";
import { useApp } from "../state/store";
import { LanguageSwitcher } from "./LanguageSwitcher";
import { Logo } from "./Logo";

interface Props {
  onAccept: () => void | Promise<void>;
  onDecline: () => void;
}

export function ConsentDialog({ onAccept, onDecline }: Props) {
  const { language } = useApp();
  const [copy, setCopy] = useState<{
    title: string;
    body: string;
    bullets: string[];
    accept: string;
    decline: string;
  } | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let alive = true;
    api
      .consentCopy(language)
      .then((c) => {
        if (alive) setCopy(c);
      })
      .catch(() => {
        if (alive)
          setCopy({
            title: t("consent_title", language),
            body: t("consent_body", language),
            bullets: [],
            accept: t("consent_accept", language),
            decline: t("consent_decline", language),
          });
      });
    return () => {
      alive = false;
    };
  }, [language]);

  async function handleAccept() {
    setBusy(true);
    try {
      await onAccept();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-paper/80 dark:bg-slate-900/80 backdrop-blur-md grid place-items-center p-4 animate-fade-in-up">
      <div className="card max-w-lg w-full p-6 sm:p-8 relative">
        <div className="absolute top-4 right-4">
          <LanguageSwitcher />
        </div>

        <div className="flex items-center gap-3 mb-5">
          <Logo size={48} />
          <div>
            <div className="font-display font-extrabold text-2xl dark:text-slate-100">
              {t("appName", language)}
            </div>
            <div className="text-xs text-ink-muted dark:text-slate-400">{t("tagline", language)}</div>
          </div>
        </div>

        <div className="flex items-center gap-2 mb-2 text-leaf dark:text-emerald-400">
          <ShieldCheck size={18} />
          <h2 className="font-display font-bold text-lg dark:text-slate-100">
            {copy?.title ?? t("consent_title", language)}
          </h2>
        </div>
        <p className="text-[15px] leading-relaxed text-ink-soft dark:text-slate-300 mb-4">
          {copy?.body ?? t("consent_body", language)}
        </p>

        {copy?.bullets && copy.bullets.length > 0 && (
          <ul className="space-y-1.5 mb-5 text-[13.5px] text-ink-soft dark:text-slate-300">
            {copy.bullets.map((b, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-disha-500 mt-2 shrink-0" />
                <span>{b}</span>
              </li>
            ))}
          </ul>
        )}

        <div className="flex flex-col-reverse sm:flex-row gap-2 sm:gap-3">
          <button className="btn-ghost flex-1" onClick={onDecline} disabled={busy}>
            {copy?.decline ?? t("consent_decline", language)}
          </button>
          <button className="btn-primary flex-1 !py-3" onClick={handleAccept} disabled={busy}>
            {copy?.accept ?? t("consent_accept", language)}
          </button>
        </div>
      </div>
    </div>
  );
}
