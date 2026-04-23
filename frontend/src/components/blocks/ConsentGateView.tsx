import { ShieldCheck } from "lucide-react";
import type { ConsentGateBlock } from "../../api/types";

export function ConsentGateView({ block }: { block: ConsentGateBlock }) {
  return (
    <div className="mt-3 rounded-2xl border border-leaf/30 dark:border-emerald-900/40 bg-leaf/5 dark:bg-emerald-900/20 p-4">
      <div className="flex items-start gap-3">
        <div className="shrink-0 w-10 h-10 rounded-xl bg-leaf/15 dark:bg-emerald-900/40 text-leaf dark:text-emerald-300 grid place-items-center">
          <ShieldCheck size={18} />
        </div>
        <div className="flex-1">
          <div className="font-semibold text-[15px] mb-1 dark:text-slate-100">{block.data.action}</div>
          <p className="text-[13.5px] leading-relaxed text-ink-soft dark:text-slate-300">
            {block.data.description}
          </p>
          {block.data.scopes.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-2">
              {block.data.scopes.map((s) => (
                <span key={s} className="chip text-[10px]">
                  {s.replace(/_/g, " ")}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
