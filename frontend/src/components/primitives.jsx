import { useState } from "react";
import { Copy, Check } from "lucide-react";

const STATUS_STYLES = {
  pending: "bg-amber-500/20 text-amber-200 border-amber-500/40",
  approved: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  auto_approved: "bg-emerald-500/10 text-emerald-300 border-emerald-500/25",
  rejected: "bg-rose-500/15 text-rose-300 border-rose-500/30",
  failed: "bg-red-600/20 text-red-300 border-red-500/40",
  prohibited: "bg-red-600/15 text-red-300 border-red-500/40",
  revoked: "bg-slate-500/15 text-slate-300 border-slate-500/30",
  paused: "bg-purple-500/20 text-purple-200 border-purple-500/40",
  not_connected: "bg-slate-600/20 text-slate-300 border-slate-600/40",
  verified: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  broken: "bg-red-600/20 text-red-300 border-red-500/40",
  default: "bg-slate-700/40 text-slate-200 border-slate-600/40",
};

export function StatusBadge({ status, label, testid }) {
  const cls = STATUS_STYLES[status] || STATUS_STYLES.default;
  const pulse = status === "pending" ? "animate-pulse" : "";
  return (
    <span
      data-testid={testid}
      className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-0.5 font-mono text-xs ${cls}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full bg-current ${pulse}`} />
      {label || status}
    </span>
  );
}

export function Hash({ value, testid }) {
  const [copied, setCopied] = useState(false);
  if (!value) return <span className="font-mono text-xs text-slate-400">—</span>;
  const short = value.length > 20 ? `${value.slice(0, 10)}…${value.slice(-6)}` : value;
  const copy = () => {
    navigator.clipboard?.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  };
  return (
    <button
      data-testid={testid}
      onClick={copy}
      title={value}
      className="inline-flex items-center gap-1.5 rounded border border-slate-800 bg-slate-950 px-2 py-1 font-mono text-xs text-emerald-400 transition-colors hover:border-emerald-700 hover:text-emerald-300"
    >
      {short}
      {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3 opacity-60" />}
    </button>
  );
}

export function PageHeader({ title, subtitle, children }) {
  return (
    <div className="flex flex-col gap-3 border-b border-slate-800 bg-slate-900/40 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 className="font-heading text-2xl font-bold tracking-tight text-slate-100">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-slate-400">{subtitle}</p>}
      </div>
      {children}
    </div>
  );
}

export function Card({ children, className = "", testid }) {
  return (
    <div
      data-testid={testid}
      className={`rounded-xl border border-slate-800 bg-[#161C2E] p-5 ${className}`}
    >
      {children}
    </div>
  );
}

export function EmptyState({ message, testid }) {
  return (
    <div data-testid={testid} className="rounded-xl border border-dashed border-slate-700 bg-slate-900/30 p-10 text-center">
      <p className="text-sm text-slate-400">{message}</p>
    </div>
  );
}

export function ErrorState({ message, onRetry, testid }) {
  return (
    <div data-testid={testid} className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-6">
      <p className="font-mono text-sm text-rose-300">Error: {message}</p>
      {onRetry && (
        <button
          data-testid="error-retry"
          onClick={onRetry}
          className="mt-3 rounded-md border border-rose-500/40 bg-rose-500/10 px-3 py-1.5 text-xs text-rose-200 hover:bg-rose-500/20"
        >
          Retry
        </button>
      )}
    </div>
  );
}

export function Loading({ testid }) {
  return (
    <div data-testid={testid} className="space-y-3">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="h-14 animate-pulse rounded-lg border border-slate-800 bg-slate-900/50" />
      ))}
    </div>
  );
}
