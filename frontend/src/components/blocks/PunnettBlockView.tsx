import type { PunnettBlock } from "../../api/types";
import { severityColor } from "../../lib/utils";

export function PunnettBlockView({ block }: { block: PunnettBlock }) {
  const { p1, p2, grid, probabilities } = block.data;
  return (
    <div className="mt-3 card p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="text-sm font-semibold text-ink dark:text-slate-100">
          Punnett: {p1} × {p2}
        </div>
        <div className="text-[11px] text-ink-muted dark:text-slate-400">Each cell = 25%</div>
      </div>

      {grid.length > 0 && (
        <div className="grid grid-cols-2 gap-2 mb-4">
          {grid.flat().map((cell, i) => (
            <div
              key={i}
              className={`rounded-xl border px-3 py-2.5 text-center ${severityColor(cell.severity)}`}
            >
              <div className="font-bold text-lg">{cell.genotype}</div>
              <div className="text-[11px] opacity-80">
                {Math.round(cell.probability * 100)}%
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="space-y-1.5">
        {Object.entries(probabilities)
          .filter(([, v]) => (v as number) > 0)
          .map(([k, v]) => (
            <div key={k} className="flex items-center gap-3 text-[13px]">
              <div className="w-24 font-medium dark:text-slate-200">{k}</div>
              <div className="flex-1 h-2 bg-paper-muted dark:bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-disha-500 rounded-full"
                  style={{ width: `${Math.round((v as number) * 100)}%` }}
                />
              </div>
              <div className="w-10 text-right text-ink-muted dark:text-slate-400 font-mono text-xs">
                {Math.round((v as number) * 100)}%
              </div>
            </div>
          ))}
      </div>
    </div>
  );
}
