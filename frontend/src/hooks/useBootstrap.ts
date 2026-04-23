import { useEffect, useRef, useState } from "react";
import { api, hasSession, setSessionId } from "../api/client";
import { useApp } from "../state/store";

const LOC_CACHE = "disha.location";

export type BootstrapPhase =
  | "idle"
  | "starting"
  | "consent"
  | "locating"
  | "ready"
  | "error";

export function useBootstrap() {
  const { language, setSession } = useApp();
  const [phase, setPhase] = useState<BootstrapPhase>("idle");
  const [error, setError] = useState<string | null>(null);
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    void run();
    async function run() {
      try {
        setPhase("starting");
        if (!hasSession()) {
          const r = await api.startSession(language);
          setSessionId(r.session_id);
        }
        const state = await api.getSession();
        setSession(state);
        if (!state.consent.accepted) setPhase("consent");
        else if (!state.location) setPhase("locating");
        else setPhase("ready");
      } catch (e) {
        setPhase("error");
        setError(e instanceof Error ? e.message : "Could not reach server");
      }
    }
  }, [language, setSession]);

  async function acceptConsent() {
    await api.recordConsent(true, "tap", ["store_session"]);
    const s = await api.getSession();
    setSession(s);
    setPhase(s.location ? "ready" : "locating");
  }

  async function declineConsent() {
    // treat decline as ready-but-no-store; session still exists in memory
    setPhase("ready");
  }

  async function requestLocation() {
    return new Promise<void>((resolve) => {
      if (!("geolocation" in navigator)) {
        setPhase("ready");
        resolve();
        return;
      }
      navigator.geolocation.getCurrentPosition(
        async (pos) => {
          const { latitude, longitude } = pos.coords;
          try {
            const s = await api.setLocation(latitude, longitude);
            setSession(s);
            localStorage.setItem(
              LOC_CACHE,
              JSON.stringify({ lat: latitude, lng: longitude })
            );
          } catch {
            // ignore — not blocking
          }
          setPhase("ready");
          resolve();
        },
        () => {
          setPhase("ready");
          resolve();
        },
        { enableHighAccuracy: false, maximumAge: 600_000, timeout: 8000 }
      );
    });
  }

  function skipLocation() {
    setPhase("ready");
  }

  return {
    phase,
    error,
    acceptConsent,
    declineConsent,
    requestLocation,
    skipLocation,
  };
}

export function getCachedLocation(): { lat: number; lng: number } | null {
  try {
    const raw = localStorage.getItem(LOC_CACHE);
    if (!raw) return null;
    const o = JSON.parse(raw);
    if (typeof o.lat === "number" && typeof o.lng === "number") return o;
  } catch {
    // ignore
  }
  return null;
}
