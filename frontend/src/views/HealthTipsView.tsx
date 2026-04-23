import { Heart } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../api/client";
import { t } from "../lib/i18n";
import { useApp } from "../state/store";

interface Tip {
  id: string;
  title: string;
  body: string;
  icon?: string;
}

export function HealthTipsView() {
  const { language } = useApp();
  const [tips, setTips] = useState<Tip[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    api
      .healthTips(language)
      .then((r) => {
        if (alive) setTips((r.tips as Tip[]) ?? []);
      })
      .catch(() => alive && setErr("Could not load tips."));
    return () => {
      alive = false;
    };
  }, [language]);

  return (
    <div className="flex-1 overflow-y-auto scrollbar-thin p-4 sm:p-8">
      <div className="max-w-3xl mx-auto">
        <h2 className="font-display font-bold text-2xl mb-5 dark:text-slate-100">
          {t("tips_title", language)}
        </h2>

        {err && <div className="text-rose-700 dark:text-rose-400 text-sm">{err}</div>}

        {!tips && !err && (
          <div className="space-y-3">
            {[0, 1, 2, 3].map((i) => (
              <div key={i} className="shimmer h-[92px] rounded-2xl" />
            ))}
          </div>
        )}

        {tips && tips.length > 0 && (
          <div className="grid gap-3 sm:grid-cols-2">
            {tips.map((tip) => (
              <div key={tip.id} className="card p-4 flex gap-3">
                <div className="shrink-0 w-11 h-11 rounded-2xl bg-leaf/10 dark:bg-emerald-900/30 text-leaf dark:text-emerald-300 grid place-items-center text-xl">
                  {tip.icon ?? <Heart size={18} />}
                </div>
                <div>
                  <div className="font-semibold text-[15px] dark:text-slate-100">{tip.title}</div>
                  <p className="text-[13.5px] text-ink-soft dark:text-slate-300 leading-relaxed mt-1">
                    {tip.body}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
