import { Menu, Moon, Phone, Sun } from "lucide-react";
import { t } from "../lib/i18n";
import { useApp } from "../state/store";
import { LanguageSwitcher } from "./LanguageSwitcher";

const VIEW_TITLES: Record<string, string> = {
  chat: "nav_chat",
  docs: "nav_docs",
  tips: "nav_tips",
  maps: "nav_maps",
  consent: "nav_consent",
  about: "nav_about",
};

export function TopBar() {
  const {
    language,
    view,
    toggleSidebar,
    session,
    setView,
    theme,
    toggleTheme,
  } = useApp();
  const title = t(VIEW_TITLES[view] ?? "nav_chat", language);

  return (
    <header className="sticky top-0 z-20 bg-paper/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-ink/5 dark:border-white/10">
      <div className="flex items-center gap-3 px-4 py-3">
        <button
          className="btn-ghost !p-2 lg:hidden"
          onClick={toggleSidebar}
          aria-label="Open menu"
        >
          <Menu size={20} />
        </button>

        <div className="flex-1 min-w-0">
          <h1 className="font-display font-bold text-lg truncate dark:text-slate-100">
            {title}
          </h1>
          {session?.location && (
            <p className="text-[11px] text-ink-muted dark:text-slate-400 truncate">
              📍{" "}
              {session.location.label ??
                `${session.location.lat.toFixed(3)}, ${session.location.lng.toFixed(3)}`}
            </p>
          )}
        </div>

        <button
          className="btn-ghost !rounded-full !p-2"
          onClick={toggleTheme}
          title={t("theme_toggle", language)}
          aria-label={t("theme_toggle", language)}
        >
          {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
        </button>

        <button
          className="btn-ghost !rounded-full !px-3 !py-2 text-rose-700 dark:text-rose-400"
          onClick={() => setView("consent")}
          title="Helplines"
        >
          <Phone size={16} />
          <span className="hidden sm:inline font-medium">SOS</span>
        </button>

        <LanguageSwitcher />
      </div>
    </header>
  );
}
