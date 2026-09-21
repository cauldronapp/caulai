import { ShieldAlert } from "lucide-react";

export function StubBanner() {
  return (
    <div
      data-testid="stub-warning-banner"
      className="sticky top-0 z-50 flex items-center justify-between gap-3 border-b border-amber-500/30 bg-amber-500/10 px-4 py-2 font-mono text-xs text-amber-300"
    >
      <span className="flex items-center gap-2">
        <ShieldAlert className="h-3.5 w-3.5" />
        AUTH STUB — NOT PRODUCTION
      </span>
      <span className="hidden text-amber-400/80 sm:inline">
        Development / staging only · No live identity provider · No live connectors · PostgreSQL system of record
      </span>
    </div>
  );
}
