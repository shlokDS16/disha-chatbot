import { Phone, ShieldCheck, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { api, clearSessionId } from "../api/client";
import { t } from "../lib/i18n";
import { useApp } from "../state/store";

interface Helpline {
  name: string;
  number: string;
  notes?: string;
}

export function ConsentView() {
  const { language, session, clearMessages, setSession } = useApp();
  const [helplines, setHelplines] = useState<Helpline[]>([]);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    api
      .crisisHelplines(language)
      .then((r) => setHelplines((r.helplines as Helpline[]) ?? []))
      .catch(() => {
        // ignore
      });
  }, [language]);

  async function handleDelete() {
    if (!window.confirm(t("delete_confirm", language))) return;
    setDeleting(true);
    try {
      await api.deleteSession(true);
    } catch {
      // ignore
    } finally {
      clearSessionId();
      clearMessages();
      setSession(null);
      setDeleting(false);
      window.location.reload();
    }
  }

  return (
    <div className="flex-1 overflow-y-auto scrollbar-thin p-4 sm:p-8">
      <div className="max-w-3xl mx-auto space-y-6">
        <h2 className="font-display font-bold text-2xl dark:text-slate-100">
          {t("nav_consent", language)}
        </h2>

        <div className="card p-5">
          <div className="flex items-start gap-3">
            <div className="shrink-0 w-11 h-11 rounded-2xl bg-leaf/10 dark:bg-emerald-900/30 text-leaf dark:text-emerald-300 grid place-items-center">
              <ShieldCheck size={20} />
            </div>
            <div>
              <h3 className="font-display font-bold text-lg dark:text-slate-100">
                {t("consent_title", language)}
              </h3>
              <p className="text-[14.5px] text-ink-soft dark:text-slate-300 leading-relaxed mt-1">
                {t("consent_body", language)}
              </p>
              {session && (
                <div className="mt-3 flex flex-wrap gap-2">
                  <span className="chip">
                    Session: {session.session_id.slice(0, 8)}…
                  </span>
                  <span className="chip">
                    Consent: {session.consent.accepted ? "accepted" : "not given"}
                  </span>
                  {session.location && <span className="chip">Location shared</span>}
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="card p-5">
          <h3 className="font-display font-bold text-lg mb-3 dark:text-slate-100">
            {t("crisis_title", language)}
          </h3>
          <div className="space-y-2">
            {helplines.map((h) => (
              <a
                key={h.number}
                href={`tel:${h.number}`}
                className="flex items-center gap-3 rounded-2xl border border-ink/5 dark:border-white/10 bg-white dark:bg-slate-800 p-3 hover:border-rose-200 dark:hover:border-rose-900/40 hover:bg-rose-50/40 dark:hover:bg-rose-900/20 transition"
              >
                <div className="shrink-0 w-10 h-10 rounded-xl bg-rose-50 dark:bg-rose-900/30 text-rose-600 dark:text-rose-300 grid place-items-center">
                  <Phone size={16} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-sm dark:text-slate-100">{h.name}</div>
                  {h.notes && (
                    <div className="text-[12px] text-ink-muted dark:text-slate-400">{h.notes}</div>
                  )}
                </div>
                <div className="font-mono font-bold text-disha-700 dark:text-disha-300">{h.number}</div>
              </a>
            ))}
          </div>
        </div>

        <div className="card p-5 border-rose-200 dark:border-rose-900/40">
          <h3 className="font-display font-bold text-lg mb-2 text-rose-700 dark:text-rose-400">
            {t("delete_all", language)}
          </h3>
          <p className="text-[13.5px] text-ink-soft dark:text-slate-300 mb-3">
            {t("delete_confirm", language)}
          </p>
          <button
            onClick={handleDelete}
            disabled={deleting}
            className="btn-outline !border-rose-200 dark:!border-rose-900/40 !text-rose-700 dark:!text-rose-400 hover:!bg-rose-50 dark:hover:!bg-rose-900/20"
          >
            <Trash2 size={14} />
            {t("delete_all", language)}
          </button>
        </div>
      </div>
    </div>
  );
}
