import { ArrowRight } from "lucide-react";
import type { ReferralBlock } from "../../api/types";
import { fmtDistance } from "../../lib/utils";

export function ReferralView({ block }: { block: ReferralBlock }) {
  const { facility_type, nearest, why } = block.data;
  return (
    <div className="mt-3 rounded-2xl border border-disha-200 dark:border-disha-900/40 bg-disha-50/50 dark:bg-disha-900/20 p-4">
      <div className="text-[11px] uppercase tracking-wider font-semibold text-disha-700 dark:text-disha-300 mb-1">
        Referral · {facility_type.replace(/_/g, " ")}
      </div>
      <p className="text-[15px] leading-relaxed text-ink dark:text-slate-100 mb-3">{why}</p>
      <div className="space-y-1.5">
        {nearest.slice(0, 3).map((f) => (
          <a
            key={f.id}
            href={f.directions_url}
            target="_blank"
            rel="noreferrer"
            className="flex items-center justify-between rounded-xl bg-white dark:bg-slate-800 border border-ink/5 dark:border-white/10 px-3 py-2 hover:border-disha-300 dark:hover:border-disha-900/60"
          >
            <div className="min-w-0">
              <div className="font-medium text-sm truncate dark:text-slate-100">{f.name}</div>
              <div className="text-[11px] text-ink-muted dark:text-slate-400">{fmtDistance(f.distance_km)}</div>
            </div>
            <ArrowRight size={14} className="text-disha-600 dark:text-disha-300 shrink-0" />
          </a>
        ))}
      </div>
    </div>
  );
}
