import { BookOpen, Heart, ShieldCheck, Sparkles } from "lucide-react";
import { Logo } from "../components/Logo";
import { t } from "../lib/i18n";
import { useApp } from "../state/store";

export function AboutView() {
  const { language } = useApp();
  return (
    <div className="flex-1 overflow-y-auto scrollbar-thin p-4 sm:p-8">
      <div className="max-w-3xl mx-auto space-y-6">
        <div className="card p-6 sm:p-8">
          <div className="flex items-center gap-4 mb-4">
            <Logo size={56} />
            <div>
              <div className="font-display font-extrabold text-2xl sm:text-3xl dark:text-slate-100">
                {t("about_title", language)}
              </div>
              <div className="text-xs text-ink-muted dark:text-slate-400">{t("tagline", language)}</div>
            </div>
          </div>
          <p className="text-[15.5px] leading-relaxed text-ink-soft dark:text-slate-300">
            {t("about_body", language)}
          </p>
        </div>

        <div className="grid sm:grid-cols-2 gap-3">
          <Pill
            icon={<BookOpen size={18} />}
            title="Grounded in verified knowledge"
            body="Answers are retrieved from vetted sickle cell sources first, with LLM used only to explain and translate."
          />
          <Pill
            icon={<Sparkles size={18} />}
            title="Explains in your language"
            body="English, हिन्दी, and मराठी — tuned for ASHA workers and families in tribal Maharashtra."
          />
          <Pill
            icon={<ShieldCheck size={18} />}
            title="Private by default"
            body="Nothing leaves your device without consent. You can delete everything anytime."
          />
          <Pill
            icon={<Heart size={18} />}
            title="Built for SickleSetu"
            body="Part of the SickleSetu platform — connecting people to HPLC centres, haematologists and helplines."
          />
        </div>

        <div className="text-center text-xs text-ink-muted dark:text-slate-500 pt-4">
          Disha is informational. It does not replace a doctor or geneticist.
        </div>
      </div>
    </div>
  );
}

function Pill({
  icon,
  title,
  body,
}: {
  icon: React.ReactNode;
  title: string;
  body: string;
}) {
  return (
    <div className="card p-4 flex gap-3">
      <div className="shrink-0 w-10 h-10 rounded-2xl bg-disha-50 dark:bg-disha-900/40 text-disha-600 dark:text-disha-300 grid place-items-center">
        {icon}
      </div>
      <div>
        <div className="font-semibold text-[14.5px] dark:text-slate-100">{title}</div>
        <p className="text-[13px] text-ink-soft dark:text-slate-300 leading-relaxed mt-0.5">{body}</p>
      </div>
    </div>
  );
}
