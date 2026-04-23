import { AlertTriangle, Phone } from "lucide-react";
import type { CrisisBannerBlock } from "../../api/types";

export function CrisisBannerView({ block }: { block: CrisisBannerBlock }) {
  const { severity, message, helplines } = block.data;
  const critical = severity === "critical";
  return (
    <div
      className={`mt-2 rounded-2xl border p-4 ${
        critical
          ? "bg-rose-50 border-rose-200 text-rose-900"
          : "bg-amber-50 border-amber-200 text-amber-900"
      }`}
    >
      <div className="flex items-start gap-3">
        <AlertTriangle className="shrink-0 mt-0.5" size={20} />
        <div className="flex-1">
          <div className="font-semibold text-[15px] mb-1">{message}</div>
          <div className="flex flex-wrap gap-2 mt-2">
            {helplines.map((h) => (
              <a
                key={h.number}
                href={`tel:${h.number}`}
                className="chip !bg-white !border-current"
              >
                <Phone size={12} />
                <span className="font-semibold">{h.name}</span>
                <span className="opacity-70">{h.number}</span>
              </a>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
