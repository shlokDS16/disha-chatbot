import {
  Activity,
  FileText,
  Info,
  type LucideIcon,
  MapPin,
  MessageSquare,
  ShieldCheck,
  Plus,
  X,
} from "lucide-react";
import { api } from "../api/client";
import { t } from "../lib/i18n";
import { cn } from "../lib/utils";
import { useApp, type ViewKey } from "../state/store";
import { ChatHistoryPanel } from "./ChatHistoryPanel";
import { FaqPanel } from "./FaqPanel";
import { Logo } from "./Logo";

interface Item {
  key: ViewKey;
  labelKey: string;
  Icon: LucideIcon;
}

const ITEMS: Item[] = [
  { key: "chat", labelKey: "nav_chat", Icon: MessageSquare },
  { key: "docs", labelKey: "nav_docs", Icon: FileText },
  { key: "tips", labelKey: "nav_tips", Icon: Activity },
  { key: "maps", labelKey: "nav_maps", Icon: MapPin },
  { key: "consent", labelKey: "nav_consent", Icon: ShieldCheck },
  { key: "about", labelKey: "nav_about", Icon: Info },
];

export function Sidebar() {
  const { view, setView, language, sidebarOpen, setSidebar, clearMessages } = useApp();

  async function openChat() {
    try {
      await api.clearHistory();
    } catch {
      // non-fatal — still clear local state
    }
    clearMessages();
    setView("chat");
  }

  function handleChipPick(text: string) {
    // switch to chat and populate a pending message via a custom event
    setView("chat");
    window.dispatchEvent(new CustomEvent("disha:chip-pick", { detail: { text } }));
  }

  return (
    <>
      {/* mobile backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-ink/30 dark:bg-black/50 backdrop-blur-sm z-30 lg:hidden"
          onClick={() => setSidebar(false)}
        />
      )}

      <aside
        className={cn(
          "fixed lg:static z-40 top-0 left-0 h-full w-[280px] shrink-0",
          "bg-paper/95 dark:bg-slate-900/95 backdrop-blur-md border-r border-ink/5 dark:border-white/10",
          "flex flex-col overflow-hidden transition-transform duration-200",
          "lg:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        <div className="flex-shrink-0 flex items-center gap-3 px-5 py-4 border-b border-ink/5 dark:border-white/10">
          <Logo size={40} />
          <div className="flex-1">
            <div className="font-display font-extrabold text-xl leading-none dark:text-slate-100">
              {t("appName", language)}
            </div>
            <div className="text-[11px] text-ink-muted dark:text-slate-400 mt-1 leading-tight">
              {t("tagline", language)}
            </div>
          </div>
          <button
            className="btn-ghost !p-1.5 lg:hidden"
            onClick={() => setSidebar(false)}
            aria-label="Close menu"
          >
            <X size={18} />
          </button>
        </div>

        <div className="flex-shrink-0 px-4 pt-4">
          <button onClick={openChat} className="btn-primary w-full !py-3">
            <Plus size={16} />
            {t("new_chat", language)}
          </button>
        </div>

        <nav className="flex-shrink-0 px-3 py-3">
          {ITEMS.map(({ key, labelKey, Icon }) => {
            const active = view === key;
            return (
              <button
                key={key}
                onClick={() => setView(key)}
                className={cn(
                  "w-full text-left flex items-center gap-3 px-3 py-2.5 rounded-2xl mb-1 transition",
                  active
                    ? "bg-white dark:bg-slate-800 shadow-soft text-disha-700 dark:text-disha-300 border border-disha-100 dark:border-disha-900/40"
                    : "text-ink-soft dark:text-slate-300 hover:bg-paper-muted dark:hover:bg-slate-800"
                )}
              >
                <Icon size={18} />
                <span className="font-medium text-[15px]">{t(labelKey, language)}</span>
              </button>
            );
          })}
        </nav>

        <div className="flex-1 min-h-0 overflow-y-auto scrollbar-thin flex flex-col">
          <FaqPanel onPick={handleChipPick} />
          <ChatHistoryPanel />
        </div>

        <div className="flex-shrink-0 p-4 text-[11px] text-ink-muted dark:text-slate-500 leading-snug border-t border-ink/5 dark:border-white/10">
          Disha does not replace a doctor. In an emergency, call the helpline
          from the sidebar.
        </div>
      </aside>
    </>
  );
}
