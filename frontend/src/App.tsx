import { useEffect } from "react";
import { ConsentDialog } from "./components/ConsentDialog";
import { LocationDialog } from "./components/LocationDialog";
import { Sidebar } from "./components/Sidebar";
import { TopBar } from "./components/TopBar";
import { useBootstrap } from "./hooks/useBootstrap";
import { useApp } from "./state/store";
import { AboutView } from "./views/AboutView";
import { ChatView } from "./views/ChatView";
import { ConsentView } from "./views/ConsentView";
import { DocumentsView } from "./views/DocumentsView";
import { HealthTipsView } from "./views/HealthTipsView";
import { MapsView } from "./views/MapsView";

export default function App() {
  const { language, view } = useApp();
  const {
    phase,
    error,
    acceptConsent,
    declineConsent,
    requestLocation,
    skipLocation,
  } = useBootstrap();

  useEffect(() => {
    document.documentElement.lang = language;
  }, [language]);

  return (
    <div className="h-full flex">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 min-h-0">
        <TopBar />
        <main className="flex-1 flex flex-col min-h-0">
          {view === "chat" && <ChatView />}
          {view === "docs" && <DocumentsView />}
          {view === "tips" && <HealthTipsView />}
          {view === "maps" && <MapsView />}
          {view === "consent" && <ConsentView />}
          {view === "about" && <AboutView />}
        </main>
      </div>

      {phase === "consent" && (
        <ConsentDialog onAccept={acceptConsent} onDecline={declineConsent} />
      )}
      {phase === "locating" && (
        <LocationDialog onAllow={requestLocation} onSkip={skipLocation} />
      )}
      {phase === "starting" && (
        <div className="fixed inset-0 bg-paper dark:bg-slate-900 grid place-items-center z-50">
          <div className="text-ink-muted dark:text-slate-400 animate-pulse text-sm">Loading Disha…</div>
        </div>
      )}
      {phase === "error" && (
        <div className="fixed inset-0 bg-paper/90 dark:bg-slate-900/90 backdrop-blur grid place-items-center z-50 p-4">
          <div className="card p-6 max-w-md text-center">
            <div className="text-rose-700 dark:text-rose-400 font-semibold mb-1">Unable to start</div>
            <p className="text-sm text-ink-soft dark:text-slate-300 mb-4">
              {error ?? "The backend is unreachable. Is it running on port 8000?"}
            </p>
            <button
              className="btn-primary"
              onClick={() => window.location.reload()}
            >
              Retry
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
