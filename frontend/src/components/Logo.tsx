import { cn } from "../lib/utils";

export function Logo({ size = 36, className }: { size?: number; className?: string }) {
  return (
    <div className={cn("relative shrink-0", className)} style={{ width: size, height: size }}>
      <svg viewBox="0 0 64 64" width={size} height={size} aria-hidden>
        <defs>
          <linearGradient id="logo-grad" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
            <stop offset="0" stopColor="#ff9933" />
            <stop offset="1" stopColor="#e15518" />
          </linearGradient>
        </defs>
        <rect x="4" y="4" width="56" height="56" rx="16" fill="url(#logo-grad)" />
        <path d="M20 42 V22 h10 a10 10 0 0 1 0 20 Z" fill="#fff" />
        <circle cx="46" cy="32" r="4" fill="#138808" />
      </svg>
    </div>
  );
}
