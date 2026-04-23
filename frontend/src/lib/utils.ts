import clsx, { type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs);
}

export function fmtDistance(km: number): string {
  if (km < 1) return `${Math.round(km * 1000)} m`;
  return `${km.toFixed(km < 10 ? 1 : 0)} km`;
}

export function severityColor(
  sev: "normal" | "carrier" | "affected" | "info" | "warning" | "critical"
): string {
  switch (sev) {
    case "normal":
    case "info":
      return "bg-emerald-50 text-emerald-700 border-emerald-200";
    case "carrier":
      return "bg-amber-50 text-amber-800 border-amber-200";
    case "affected":
    case "warning":
      return "bg-orange-50 text-orange-800 border-orange-200";
    case "critical":
      return "bg-rose-50 text-rose-800 border-rose-200";
    default:
      return "bg-stone-50 text-stone-700 border-stone-200";
  }
}
