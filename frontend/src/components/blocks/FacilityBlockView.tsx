import { ExternalLink, MapPin, Star } from "lucide-react";
import type { FacilityBlock, FacilityItem } from "../../api/types";
import { t } from "../../lib/i18n";
import { fmtDistance } from "../../lib/utils";
import { useApp } from "../../state/store";

export function FacilityBlockView({ block }: { block: FacilityBlock }) {
  const { language } = useApp();
  return (
    <div className="mt-2 space-y-2">
      {block.data.facilities.map((f) => (
        <FacilityCard key={f.id} f={f} lang={language} />
      ))}
    </div>
  );
}

function FacilityCard({
  f,
  lang,
}: {
  f: FacilityItem;
  lang: "en" | "hi" | "mr";
}) {
  return (
    <a
      href={f.directions_url}
      target="_blank"
      rel="noreferrer"
      className="group block rounded-2xl border border-ink/5 dark:border-white/10 bg-white dark:bg-slate-800 p-4 hover:shadow-soft hover:border-disha-200 dark:hover:border-disha-900/40 transition"
    >
      <div className="flex items-start gap-3">
        <div className="shrink-0 w-10 h-10 rounded-xl bg-disha-50 dark:bg-disha-900/40 text-disha-700 dark:text-disha-300 grid place-items-center">
          <MapPin size={18} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-[15px] leading-snug truncate dark:text-slate-100">{f.name}</div>
          <div className="text-[13px] text-ink-muted dark:text-slate-400 mt-0.5 line-clamp-2">{f.address}</div>
          <div className="flex items-center gap-3 mt-2 flex-wrap">
            <span className="text-[12px] font-semibold text-disha-700 dark:text-disha-300">
              {fmtDistance(f.distance_km)} · {t("maps_km", lang)}
            </span>
            {f.rating != null && (
              <span className="text-[12px] flex items-center gap-0.5 text-amber-600 dark:text-amber-400">
                <Star size={12} className="fill-current" />
                {f.rating.toFixed(1)}
              </span>
            )}
            {f.open_now != null && (
              <span
                className={
                  f.open_now
                    ? "text-[12px] font-medium text-emerald-700 dark:text-emerald-400"
                    : "text-[12px] text-ink-muted dark:text-slate-500"
                }
              >
                {f.open_now ? t("maps_open_now", lang) : t("maps_closed", lang)}
              </span>
            )}
          </div>
        </div>
        <ExternalLink
          size={16}
          className="text-ink-muted dark:text-slate-500 group-hover:text-disha-600 dark:group-hover:text-disha-300 shrink-0 mt-1"
        />
      </div>
    </a>
  );
}
