import { FileText, Upload } from "lucide-react";
import { useRef, useState } from "react";
import { api } from "../api/client";
import type { FileStateResponse, FileUploadResponse } from "../api/types";
import { FileSummaryView } from "../components/blocks/FileSummaryView";
import { t } from "../lib/i18n";
import { useApp } from "../state/store";

export function DocumentsView() {
  const { language } = useApp();
  const [files, setFiles] = useState<
    {
      upload: FileUploadResponse;
      status: FileStateResponse | null;
    }[]
  >([]);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [drag, setDrag] = useState(false);

  async function handleFile(f: File) {
    try {
      const up = await api.uploadFile(f);
      setFiles((s) => [{ upload: up, status: null }, ...s]);
      void pollAndSummarize(up.file_id);
    } catch {
      alert("Upload failed. Please try again.");
    }
  }

  async function pollAndSummarize(id: string) {
    for (let i = 0; i < 30; i++) {
      await new Promise((r) => setTimeout(r, 1200));
      try {
        const r = await api.getFile(id);
        if (r.status === "done" || r.status === "failed") {
          let final: FileStateResponse = r;
          if (r.status === "done") {
            try {
              final = await api.summarizeFile(id, language);
            } catch {
              // keep r
            }
          }
          setFiles((s) =>
            s.map((x) => (x.upload.file_id === id ? { ...x, status: final } : x))
          );
          return;
        }
        // still processing — update status
        setFiles((s) =>
          s.map((x) => (x.upload.file_id === id ? { ...x, status: r } : x))
        );
      } catch {
        return;
      }
    }
  }

  return (
    <div className="flex-1 overflow-y-auto scrollbar-thin p-4 sm:p-8">
      <div className="max-w-3xl mx-auto">
        <h2 className="font-display font-bold text-2xl mb-4 dark:text-slate-100">
          {t("nav_docs", language)}
        </h2>

        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDrag(true);
          }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDrag(false);
            const f = e.dataTransfer.files?.[0];
            if (f) void handleFile(f);
          }}
          className={`card border-dashed border-2 p-8 sm:p-12 text-center transition ${
            drag
              ? "!border-disha-400 !bg-disha-50 dark:!bg-disha-900/20"
              : "border-ink/10 dark:border-white/10"
          }`}
        >
          <div className="mx-auto w-16 h-16 rounded-3xl bg-disha-50 dark:bg-disha-900/40 text-disha-600 dark:text-disha-300 grid place-items-center mb-4">
            <Upload size={26} />
          </div>
          <h3 className="font-display font-bold text-lg dark:text-slate-100">
            {t("empty_docs_title", language)}
          </h3>
          <p className="text-[14px] text-ink-muted dark:text-slate-400 mt-1 mb-4">
            {t("empty_docs_body", language)}
          </p>
          <input
            ref={inputRef}
            type="file"
            accept="image/*,.pdf,.docx"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) void handleFile(f);
              e.currentTarget.value = "";
            }}
          />
          <button
            className="btn-primary !px-5 !py-3"
            onClick={() => inputRef.current?.click()}
          >
            {t("upload_cta", language)}
          </button>
        </div>

        <div className="mt-6 space-y-4">
          {files.map(({ upload, status }) => (
            <div key={upload.file_id} className="card p-4">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 rounded-xl bg-paper-muted dark:bg-slate-700 grid place-items-center text-ink-soft dark:text-slate-300">
                  <FileText size={18} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium truncate dark:text-slate-100">{upload.filename}</div>
                  <div className="text-[11px] text-ink-muted dark:text-slate-400">
                    {(upload.size_bytes / 1024).toFixed(1)} KB ·{" "}
                    {status?.status ?? upload.status}
                  </div>
                </div>
              </div>
              {status?.error && (
                <div className="rounded-xl bg-rose-50 dark:bg-rose-900/30 border border-rose-200 dark:border-rose-900/60 text-rose-800 dark:text-rose-200 text-sm p-2.5">
                  {status.error}
                </div>
              )}
              {status?.summary && (
                <FileSummaryView
                  block={{
                    type: "file_summary",
                    data: {
                      file_id: upload.file_id,
                      filename: upload.filename,
                      key_findings: status.summary.key_findings,
                      what_it_means: status.summary.what_it_means,
                      next_steps: status.summary.next_steps,
                      document_type: status.summary.document_type,
                      detailed_analysis: status.summary.detailed_analysis,
                      full_text: status.summary.full_text,
                    },
                  }}
                />
              )}
              {!status?.summary &&
                !status?.error &&
                status?.status !== "done" && (
                  <div className="shimmer h-[72px] rounded-2xl mt-2" />
                )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
