import { MapPin, RefreshCcw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import type { FacilityItem, FacilityService } from "../api/types";
import { FacilityBlockView } from "../components/blocks/FacilityBlockView";
import { t } from "../lib/i18n";
import { cn } from "../lib/utils";
import { useApp } from "../state/store";

const SERVICES: { key: FacilityService; labelKey: string }[] = [
  { key: "any", labelKey: "maps_service_any" },
  { key: "HPLC_centre", labelKey: "maps_service_hplc" },
  { key: "CVS_amnio", labelKey: "maps_service_cvs" },
  { key: "haematology", labelKey: "maps_service_haem" },
  { key: "HU_dispensing", labelKey: "maps_service_hu" },
  { key: "general_hospital", labelKey: "maps_service_hospital" },
];

export function MapsView() {
  const { language, session, setSession } = useApp();
  const [service, setService] = useState<FacilityService>("any");
  const [items, setItems] = useState<FacilityItem[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(
    async (svc: FacilityService) => {
      if (!session?.location) return;
      setLoading(true);
      setErr(null);
      try {
        const r = await api.nearbyFacilities(
          session.location.lat,
          session.location.lng,
          svc
        );
        setItems(r.facilities);
      } catch (e) {
        setErr(e instanceof Error ? e.message : "Could not fetch facilities.");
      } finally {
        setLoading(false);
      }
    },
    [session?.location]
  );

  useEffect(() => {
    void load(service);
  }, [service, load]);

  function askLocation() {
    if (!("geolocation" in navigator)) return;
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const s = await api.setLocation(pos.coords.latitude, pos.coords.longitude);
        setSession(s);
      },
      () => setErr("Could not read your location.")
    );
  }

  return (
    <div className="flex-1 overflow-y-auto scrollbar-thin p-4 sm:p-8">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-start justify-between gap-3 mb-5">
          <div>
            <h2 className="font-display font-bold text-2xl dark:text-slate-100">{t("maps_title", language)}</h2>
            {session?.location ? (
              <p className="text-[12.5px] text-ink-muted dark:text-slate-400 mt-1">
                📍 {session.location.lat.toFixed(4)}, {session.location.lng.toFixed(4)}
              </p>
            ) : (
              <button className="btn-outline mt-2 !py-1.5" onClick={askLocation}>
                <MapPin size={14} /> {t("location_allow", language)}
              </button>
            )}
          </div>
          <button
            className="btn-ghost !rounded-full !p-2"
            onClick={() => load(service)}
            disabled={loading || !session?.location}
            title={t("maps_refresh", language)}
          >
            <RefreshCcw size={16} className={cn(loading && "animate-spin")} />
          </button>
        </div>

        <div className="flex flex-wrap gap-2 mb-4">
          {SERVICES.map((s) => (
            <button
              key={s.key}
              onClick={() => setService(s.key)}
              className={cn(
                "chip",
                service === s.key &&
                  "!bg-disha-600 !text-white !border-disha-600 hover:!bg-disha-700"
              )}
            >
              {t(s.labelKey, language)}
            </button>
          ))}
        </div>

        {err && (
          <div className="rounded-2xl bg-rose-50 dark:bg-rose-900/30 border border-rose-200 dark:border-rose-900/60 text-rose-800 dark:text-rose-200 p-3 text-sm mb-3">
            {err}
          </div>
        )}

        {!session?.location && !err && (
          <div className="card p-6 text-center text-ink-muted dark:text-slate-400">
            {t("location_denied", language)}
          </div>
        )}

        {loading && !items && (
          <div className="space-y-2">
            {[0, 1, 2].map((i) => (
              <div key={i} className="shimmer h-[88px] rounded-2xl" />
            ))}
          </div>
        )}

        {items && items.length > 0 && session?.location && (
          <FacilityBlockView
            block={{
              type: "facility",
              data: {
                user_location: {
                  lat: session.location.lat,
                  lng: session.location.lng,
                },
                facilities: items,
              },
            }}
          />
        )}

        {items && items.length === 0 && (
          <div className="card p-6 text-center text-ink-muted dark:text-slate-400">
            No facilities found within range. Try a different service.
          </div>
        )}
      </div>
    </div>
  );
}
