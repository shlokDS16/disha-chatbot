import { CheckCircle2, ChevronDown, ChevronUp, FileText } from "lucide-react";
import { useState } from "react";
import type { FileSummaryBlock } from "../../api/types";
import { t } from "../../lib/i18n";
import { severityColor } from "../../lib/utils";
import { useApp } from "../../state/store";

export function FileSummaryView({ block }: { block: FileSummaryBlock }) {
  const {
    key_findings,
    what_it_means,
    next_steps,
    document_type,
    detailed_analysis,
    full_text,
    filename,
  } = block.data;
  const { language } = useApp();
  const [showText, setShowText] = useState(false);

  return (
    <div className="mt-3 card p-5 space-y-4">
      <div className="flex items-center gap-2 text-ink-soft dark:text-slate-300">
        <FileText size={18} />
        <span className="font-semibold text-sm">
          {filename || document_type || t("file_summary_title", language)}
        </span>
        {document_type && (
          <span className="ml-auto text-[11px] px-2 py-0.5 rounded-full bg-disha-50 dark:bg-disha-900/40 text-disha-700 dark:text-disha-200 font-medium">
            {document_type}
          </span>
        )}
      </div>

      {key_findings.length > 0 && (
        <div className="space-y-1.5">
          {key_findings.map((f, i) => (
            <div
              key={i}
              className={`flex items-center justify-between rounded-xl border px-3 py-2 ${severityColor(
                f.severity
              )}`}
            >
              <span className="text-[13px] font-medium">
                {f.label_native}
                <span className="opacity-60 ml-1.5">({f.label_en})</span>
              </span>
              <span className="font-mono font-bold">{f.value}</span>
            </div>
          ))}
        </div>
      )}

      {detailed_analysis && (
        <div>
          <div className="text-[11px] uppercase tracking-wider font-semibold text-ink-muted dark:text-slate-400 mb-1">
            {t("file_detailed_analysis", language)}
          </div>
          <p className="text-[15px] leading-relaxed whitespace-pre-line">
            {detailed_analysis}
          </p>
        </div>
      )}

      {what_it_means && (
        <div>
          <div className="text-[11px] uppercase tracking-wider font-semibold text-ink-muted dark:text-slate-400 mb-1">
            {t("file_what_it_means", language)}
          </div>
          <p className="text-[15px] leading-relaxed">{what_it_means}</p>
        </div>
      )}

      {next_steps.length > 0 && (
        <div>
          <div className="text-[11px] uppercase tracking-wider font-semibold text-ink-muted dark:text-slate-400 mb-2">
            {t("file_next_steps", language)}
          </div>
          <ul className="space-y-1.5">
            {next_steps.map((s, i) => (
              <li key={i} className="flex items-start gap-2 text-[14.5px]">
                <CheckCircle2 size={16} className="text-leaf mt-0.5 shrink-0" />
                <span>{s}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {full_text && (
        <div className="border-t border-ink/5 dark:border-white/10 pt-3">
          <button
            className="flex items-center gap-1.5 text-[12.5px] font-medium text-ink-muted dark:text-slate-400 hover:text-disha-700 dark:hover:text-disha-300"
            onClick={() => setShowText((v) => !v)}
          >
            {showText ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            {showText
              ? t("file_hide_text", language)
              : t("file_show_text", language)}
          </button>
          {showText && (
            <pre className="mt-2 text-[12.5px] leading-relaxed whitespace-pre-wrap bg-paper/60 dark:bg-slate-900/50 rounded-xl p-3 max-h-72 overflow-y-auto scrollbar-thin font-mono">
              {full_text}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
