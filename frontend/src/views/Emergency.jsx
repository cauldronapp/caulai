import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AlertOctagon, Pause, Play, Ban, Undo2, ShieldAlert } from "lucide-react";
import { api, formatApiErrorDetail } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Layout } from "@/components/Layout";
import { PageHeader, Card, Loading, ErrorState, EmptyState, StatusBadge } from "@/components/primitives";

export default function Emergency() {
  const qc = useQueryClient();
  const { can } = useAuth();
  const [err, setErr] = useState("");
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["emergency"],
    queryFn: async () => (await api.get("/emergency")).data,
  });

  const act = useMutation({
    mutationFn: async ({ url, body }) => (await api.post(url, body || {})).data,
    onSuccess: () => { setErr(""); qc.invalidateQueries({ queryKey: ["emergency"] }); },
    onError: (e) => setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message),
  });

  const globalPaused = data?.global_paused;

  return (
    <Layout>
      <PageHeader title="Emergency Controls" subtitle="Global & granular pause, revocation, queue drain, rollback. Operates against STUB paths only." />
      <div className="space-y-4 p-6">
        <div className="flex items-center gap-2 rounded-md border border-purple-500/30 bg-purple-500/10 px-3 py-2 font-mono text-xs text-purple-300" data-testid="emergency-stub-note">
          <ShieldAlert className="h-3.5 w-3.5" /> STUB PATHS ONLY — not proven for live connectors.
        </div>
        {isLoading && <Loading testid="emergency-loading" />}
        {error && <ErrorState testid="emergency-error" message={error.message} onRetry={refetch} />}
        {err && <div data-testid="emergency-action-error" className="rounded-md border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-300">{err}</div>}
        {data && (
          <>
            <Card testid="global-pause-card" className={globalPaused ? "border-purple-500/40" : ""}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <AlertOctagon className={`h-6 w-6 ${globalPaused ? "text-purple-400" : "text-slate-400"}`} />
                  <div>
                    <div className="font-heading text-lg font-semibold text-slate-200">Global Pause</div>
                    <StatusBadge testid="global-pause-status" status={globalPaused ? "paused" : "verified"} label={globalPaused ? "ENGAGED" : "OPERATIONAL"} />
                  </div>
                </div>
                <div className="flex gap-2">
                  {can("emergency:pause") && !globalPaused && (
                    <button data-testid="global-pause-button" onClick={() => act.mutate({ url: "/emergency/pause", body: { scope: "global", target: "*", reason: "Manual global pause" } })} className="flex items-center gap-2 rounded-md bg-purple-600 px-4 py-2 text-sm font-semibold text-white hover:bg-purple-500">
                      <Pause className="h-4 w-4" /> Engage Global Pause
                    </button>
                  )}
                  {can("emergency:resume") && globalPaused && (
                    <button data-testid="global-resume-button" onClick={() => act.mutate({ url: "/emergency/resume", body: { scope: "global", target: "*" } })} className="flex items-center gap-2 rounded-md bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500">
                      <Play className="h-4 w-4" /> Release Global Pause
                    </button>
                  )}
                </div>
              </div>
            </Card>

            <Card testid="granular-pause-card">
              <h3 className="mb-3 font-heading text-lg font-semibold text-slate-200">Granular Pauses</h3>
              <div className="space-y-2" data-testid="granular-pause-list">
                {data.pauses.filter((p) => p.scope === "granular").length === 0 && (
                  <p className="text-sm text-slate-500">No granular pauses configured.</p>
                )}
                {data.pauses.filter((p) => p.scope === "granular").map((p) => (
                  <div key={p.id} className="flex items-center justify-between rounded-md border border-slate-800 bg-slate-900/50 px-3 py-2">
                    <span className="font-mono text-xs text-slate-300">{p.target}</span>
                    <StatusBadge status={p.active ? "paused" : "verified"} label={p.active ? "PAUSED" : "ACTIVE"} />
                  </div>
                ))}
              </div>
            </Card>

            <Card testid="execution-queue-card">
              <h3 className="mb-3 font-heading text-lg font-semibold text-slate-200">Execution Queue (stub)</h3>
              {can("emergency:revoke") && data.queue.some((q) => ["queued", "executing"].includes(q.status)) && (
                <button data-testid="queue-drain-button" onClick={() => act.mutate({ url: "/emergency/queue/drain" })} className="mb-3 flex items-center gap-2 rounded-md border border-rose-500/40 bg-rose-500/10 px-3 py-1.5 text-xs text-rose-200 hover:bg-rose-500/20">
                  <Ban className="h-3.5 w-3.5" /> Drain Queue
                </button>
              )}
              {data.queue.length === 0 ? (
                <EmptyState testid="queue-empty" message="Execution queue is empty." />
              ) : (
                <div className="space-y-2" data-testid="queue-list">
                  {data.queue.map((q) => (
                    <div key={q.id} data-testid={`queue-item-${q.id}`} className="flex items-center justify-between rounded-md border border-slate-800 bg-slate-900/50 px-3 py-2">
                      <div className="flex items-center gap-3">
                        <span className="font-mono text-xs text-slate-400">{q.id.slice(0, 8)}</span>
                        {q.irreversible && (
                          <span data-testid={`irreversible-warning-${q.id}`} className="inline-flex items-center gap-1 rounded bg-rose-500/15 px-2 py-0.5 font-mono text-[10px] text-rose-300">
                            <ShieldAlert className="h-3 w-3" /> IRREVERSIBLE
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <StatusBadge status={q.status === "executed" ? "approved" : q.status === "queued" ? "pending" : "revoked"} label={q.status} />
                        {can("emergency:revoke") && ["queued", "executing"].includes(q.status) && (
                          <button data-testid={`queue-cancel-${q.id}`} onClick={() => act.mutate({ url: `/emergency/queue/${q.id}/cancel` })} className="rounded border border-slate-700 px-2 py-1 text-xs text-slate-300 hover:bg-slate-700 hover:text-white">Cancel</button>
                        )}
                        {can("emergency:revoke") && q.status === "executed" && q.rollback_eligible && (
                          <button data-testid={`queue-rollback-${q.id}`} onClick={() => act.mutate({ url: `/emergency/rollback/${q.id}` })} className="flex items-center gap-1 rounded border border-amber-500/40 px-2 py-1 text-xs text-amber-300 hover:bg-amber-500/10">
                            <Undo2 className="h-3 w-3" /> Rollback
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </>
        )}
      </div>
    </Layout>
  );
}
