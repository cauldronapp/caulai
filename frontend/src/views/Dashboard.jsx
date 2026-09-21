import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  CheckSquare, Lightbulb, ShieldCheck, ShieldAlert, AlertOctagon, Plug, ArrowUpRight,
} from "lucide-react";
import { api } from "@/lib/api";
import { Layout } from "@/components/Layout";
import { PageHeader, Card, Loading, ErrorState } from "@/components/primitives";

function Stat({ icon: Icon, label, value, tone = "slate", to, testid }) {
  const tones = {
    slate: "text-slate-300 border-slate-800",
    amber: "text-amber-300 border-amber-500/30",
    emerald: "text-emerald-300 border-emerald-500/30",
    rose: "text-rose-300 border-rose-500/30",
    indigo: "text-indigo-300 border-indigo-500/30",
  };
  const body = (
    <Card testid={testid} className={`${tones[tone]} transition-transform hover:-translate-y-0.5`}>
      <div className="flex items-start justify-between">
        <Icon className="h-5 w-5 opacity-80" />
        {to && <ArrowUpRight className="h-4 w-4 text-slate-500" />}
      </div>
      <div className="mt-4 font-heading text-3xl font-bold text-slate-100">{value}</div>
      <div className="mt-1 font-mono text-xs uppercase tracking-wider text-slate-400">{label}</div>
    </Card>
  );
  return to ? <Link to={to}>{body}</Link> : body;
}

export default function Dashboard() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["dashboard"],
    queryFn: async () => (await api.get("/dashboard")).data,
  });

  return (
    <Layout>
      <PageHeader title="Governance Dashboard" subtitle="Real-time posture across recommendations, approvals, audit chain and emergency controls." />
      <div className="p-6">
        {isLoading && <Loading testid="dashboard-loading" />}
        {error && <ErrorState testid="dashboard-error" message={error.message} onRetry={refetch} />}
        {data && (
          <>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4" data-testid="dashboard-stats">
              <Stat testid="stat-pending" icon={CheckSquare} label="Pending Approvals" value={data.pending_approvals} tone="amber" to="/approvals" />
              <Stat testid="stat-recs" icon={Lightbulb} label="Recommendations" value={data.recommendations_total} tone="indigo" to="/recommendations" />
              <Stat testid="stat-prohibited" icon={ShieldAlert} label="Permanently Prohibited" value={data.prohibited_count} tone="rose" />
              <Stat testid="stat-audit" icon={ShieldCheck} label="Audit Events" value={data.audit_event_count} tone="emerald" to="/audit" />
            </div>

            <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
              <Card testid="audit-chain-card" className="lg:col-span-1">
                <div className="mb-3 flex items-center gap-2">
                  <ShieldCheck className={`h-4 w-4 ${data.audit_chain_verified ? "text-emerald-400" : "text-rose-400"}`} />
                  <span className="font-heading text-lg font-semibold text-slate-200">Audit Chain</span>
                </div>
                <div className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-0.5 font-mono text-xs ${data.audit_chain_verified ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300" : "border-rose-500/30 bg-rose-500/10 text-rose-300"}`} data-testid="audit-chain-status">
                  {data.audit_chain_verified ? "CHAIN VERIFIED" : "CHAIN BROKEN"}
                </div>
                <p className="mt-3 text-sm text-slate-400">Head sequence <span className="font-mono text-slate-200">#{data.audit_head_seq ?? "—"}</span> · tamper-evident, hash-chained.</p>
              </Card>

              <Card testid="emergency-card">
                <div className="mb-3 flex items-center gap-2">
                  <AlertOctagon className={`h-4 w-4 ${data.emergency.global_paused ? "text-purple-400" : "text-slate-400"}`} />
                  <span className="font-heading text-lg font-semibold text-slate-200">Emergency Controls</span>
                </div>
                <div className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-0.5 font-mono text-xs ${data.emergency.global_paused ? "border-purple-500/30 bg-purple-500/10 text-purple-300" : "border-slate-700 bg-slate-800/60 text-slate-300"}`} data-testid="emergency-status">
                  {data.emergency.global_paused ? "GLOBAL PAUSE ENGAGED" : "OPERATIONAL"}
                </div>
                <p className="mt-3 text-sm text-slate-400">{data.emergency.active_pause_count} active pause(s). Controls operate against stub paths only.</p>
              </Card>

              <Card testid="connectors-card">
                <div className="mb-3 flex items-center gap-2">
                  <Plug className="h-4 w-4 text-slate-400" />
                  <span className="font-heading text-lg font-semibold text-slate-200">Connectors</span>
                </div>
                <div className="inline-flex items-center gap-1.5 rounded-md border border-slate-700 bg-slate-800/60 px-2.5 py-0.5 font-mono text-xs text-slate-400" data-testid="connectors-status">
                  {data.connectors.not_connected} / {data.connectors.total} NOT CONNECTED
                </div>
                <p className="mt-3 text-sm text-slate-400">No live connectors in Phase 1A. No credential fields exposed.</p>
              </Card>
            </div>
          </>
        )}
      </div>
    </Layout>
  );
}
