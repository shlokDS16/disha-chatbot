import { useEffect, useState } from "react";
import { Copy, Download, History, Share2, Trash2 } from "lucide-react";
import { api, ApiError } from "../api/client";
import { t } from "../lib/i18n";
import { useApp } from "../state/store";

interface HistoryMsg {
  message_id: string;
  role: "user" | "assistant";
  text: string;
  created_at: string;
}

export function ChatHistoryPanel() {
  const { language, messages: liveMessages, clearMessages } = useApp();
  const [rows, setRows] = useState<HistoryMsg[]>([]);
  const [loading, setLoading] = useState(false);
  const [copiedAt, setCopiedAt] = useState<number | null>(null);

  async function refresh() {
    setLoading(true);
    try {
      const r = await api.listHistory();
      setRows(
        r.messages.map((m) => ({
          message_id: m.message_id,
          role: m.role,
          text: m.text,
          created_at: m.created_at,
        }))
      );
    } catch (e) {
      if (!(e instanceof ApiError)) {
        // silent
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [liveMessages.length]);

  async function handleClear() {
    if (!confirm(t("history_delete_confirm", language))) return;
    try {
      await api.clearHistory();
      clearMessages();
      setRows([]);
    } catch {
      // silent
    }
  }

  async function handleExport() {
    try {
      const r = await api.exportHistory();
      const blob = new Blob([r.markdown], { type: "text/markdown" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `disha-chat-${new Date().toISOString().slice(0, 10)}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      // silent
    }
  }

  async function handleShare() {
    try {
      const r = await api.exportHistory();
      if (navigator.share) {
        await navigator.share({
          title: "Disha chat",
          text: r.markdown,
        });
      } else {
        await navigator.clipboard.writeText(r.markdown);
        setCopiedAt(Date.now());
        setTimeout(() => setCopiedAt(null), 1500);
      }
    } catch {
      // silent
    }
  }

  async function handleCopy() {
    try {
      const r = await api.exportHistory();
      await navigator.clipboard.writeText(r.markdown);
      setCopiedAt(Date.now());
      setTimeout(() => setCopiedAt(null), 1500);
    } catch {
      // silent
    }
  }

  const canShare =
    typeof navigator !== "undefined" && typeof navigator.share === "function";

  return (
    <div className="flex flex-col border-t border-ink/5 dark:border-white/10 min-h-0 flex-1">
      <div className="px-4 pt-3 pb-2 flex items-center gap-2">
        <History size={14} className="text-ink-muted dark:text-slate-400" />
        <div className="text-[11px] uppercase tracking-wider text-ink-muted dark:text-slate-400 font-semibold flex-1">
          {t("history_title", language)}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin px-3">
        {loading && rows.length === 0 && (
          <div className="text-[12px] text-ink-muted dark:text-slate-500 px-2 py-2">
            …
          </div>
        )}
        {!loading && rows.length === 0 && (
          <div className="text-[12px] text-ink-muted dark:text-slate-500 px-2 py-2 leading-relaxed">
            {t("history_empty", language)}
          </div>
        )}
        <ul className="space-y-1">
          {rows.map((m) => (
            <li
              key={m.message_id}
              className="rounded-xl px-2.5 py-1.5 hover:bg-paper-muted dark:hover:bg-slate-800 cursor-default"
            >
              <div className="text-[10.5px] uppercase tracking-wider text-ink-muted dark:text-slate-500 font-semibold">
                {m.role === "user" ? t("you", language) : t("disha", language)}
              </div>
              <div className="text-[12.5px] leading-snug text-ink-soft dark:text-slate-300 line-clamp-2">
                {m.text}
              </div>
            </li>
          ))}
        </ul>
      </div>

      <div className="px-3 py-2 flex flex-wrap gap-1.5 border-t border-ink/5 dark:border-white/10">
        {canShare ? (
          <button
            onClick={handleShare}
            className="chip !text-[11px]"
            title={t("history_share", language)}
          >
            <Share2 size={12} />
            {t("history_share", language)}
          </button>
        ) : (
          <button
            onClick={handleCopy}
            className="chip !text-[11px]"
            title={t("history_copy", language)}
          >
            <Copy size={12} />
            {copiedAt ? t("history_copied", language) : t("history_copy", language)}
          </button>
        )}
        <button
          onClick={handleExport}
          className="chip !text-[11px]"
          title={t("history_export", language)}
        >
          <Download size={12} />
          {t("history_export", language)}
        </button>
        <button
          onClick={handleClear}
          className="chip !text-[11px] !text-rose-700 dark:!text-rose-400 !border-rose-200 dark:!border-rose-900/40"
          title={t("history_delete_all", language)}
        >
          <Trash2 size={12} />
          {t("history_delete_all", language)}
        </button>
      </div>
    </div>
  );
}
