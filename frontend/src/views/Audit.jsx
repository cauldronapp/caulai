import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Search, Download, ShieldCheck, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Layout } from "@/components/Layout";
import { PageHeader, Card, Loading, ErrorState, EmptyState, Hash } from "@/components/primitives";

export default function Audit() {
  const { can } = useAuth();
  const [q, setQ] = useState("");
  const [query, setQuery] = useState("");

  const events = useQuery({
    queryKey: ["audit", query],
    queryFn: async () => (await api.get("/audit", { params: query ? { q: query } : {} })).data,
  });

  const verify = useQuery({
    queryKey: ["audit-verify"],
    queryFn: async () => (await api.get("/audit/verify")).data,
  });

  const exportCsv = useMutation({
    mutationFn: async () => {
      const res = await api.get("/audit/export", { params: { fmt: "csv" }, responseType: "blob" });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = "caul_audit_export.csv";
      a.click();
      URL.revokeObjectURL(url);
    },
  });

  const v = verify.data;

  return (
    <Layout>
      <PageHeader title="Tamper-Evident Audit Log" subtitle="Hash-chained, read-only. Deterministic canonical serialization. Not immutable — tamper-evident.">
        <div className="flex gap-2">
          <button data-testid="audit-verify-button" onClick={() => verify.refetch()} className="flex items-center gap-2 rounded-md border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-slate-200 hover:bg-slate-700 hover:text-white">
            <RefreshCw className="h-3.5 w-3.5" /> Re-verify
          </button>
          {can("audit:export") && (
            <button data-testid="audit-export-button" onClick={() => exportCsv.mutate()} className="flex items-center gap-2 rounded-md bg-indigo-600 px-3 py-2 text-xs font-semibold text-white hover:bg-indigo-500">
              <Download className="h-3.5 w-3.5" /> Export CSV
            </button>
          )}
        </div>
      </PageHeader>

      <div className="space-y-4 p-6">
        {v && (
          <Card testid="audit-chain-banner" className={v.verified ? "border-emerald-500/30" : "border-rose-500/40"}>
            <div className="flex flex-wrap items-center gap-4">
              <div className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-0.5 font-mono text-xs ${v.verified ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300" : "border-rose-500/30 bg-rose-500/10 text-rose-300"}`} data-testid="audit-chain-verdict" role="status" aria-live="polite">
                <ShieldCheck className="h-3.5 w-3.5" /> {v.verified ? "CHAIN VERIFIED" : "BROKEN LINK DETECTED"}
              </div>
              <span className="font-mono text-xs text-slate-400">Events: <span className="text-slate-200">{v.event_count}</span></span>
              <span className="font-mono text-xs text-slate-400">Head #: <span className="text-slate-200">{v.head_seq ?? "—"}</span></span>
              <span className="font-mono text-xs text-slate-400">Genesis: <span className={v.genesis_ok ? "text-emerald-300" : "text-rose-300"}>{v.genesis_ok ? "OK" : "FAIL"}</span></span>
              {v.issues?.length > 0 && <span className="font-mono text-xs text-rose-300" data-testid="audit-issues">Issues: {v.issues.length}</span>}
            </div>
          </Card>
        )}

        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              data-testid="audit-search-input"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && setQuery(q)}
              placeholder="Search action, actor, resource, hash…"
              className="w-full rounded-md border border-slate-700 bg-slate-900 py-2.5 pl-10 pr-3 text-sm text-slate-100 placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none"
            />
          </div>
          <button data-testid="audit-search-button" onClick={() => setQuery(q)} className="rounded-md bg-slate-800 px-4 py-2 text-sm text-slate-200 hover:bg-slate-700">Search</button>
          {query && <button data-testid="audit-clear-search" onClick={() => { setQ(""); setQuery(""); }} className="rounded-md border border-slate-700 px-4 py-2 text-sm text-slate-400 hover:text-white">Clear</button>}
        </div>

        {events.isLoading && <Loading testid="audit-loading" />}
        {events.error && <ErrorState testid="audit-error" message={events.error.message} onRetry={events.refetch} />}
        {events.data && events.data.events.length === 0 && <EmptyState testid="audit-empty" message="No audit events match your search." />}
        {events.data && events.data.events.length > 0 && (
          <div className="overflow-x-auto rounded-xl border border-slate-800">
            <table className="w-full text-left text-sm" data-testid="audit-table">
              <thead className="bg-slate-900/60 font-mono text-xs uppercase tracking-wider text-slate-400">
                <tr>
                  <th scope="col" className="px-4 py-3">Seq</th>
                  <th scope="col" className="px-4 py-3">Timestamp</th>
                  <th scope="col" className="px-4 py-3">Actor</th>
                  <th scope="col" className="px-4 py-3">Action</th>
                  <th scope="col" className="px-4 py-3">Resource</th>
                  <th scope="col" className="px-4 py-3">Prev</th>
                  <th scope="col" className="px-4 py-3">Hash</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {events.data.events.map((e) => (
                  <tr key={e.id} data-testid={`audit-row-${e.seq}`} className="bg-[#111622] hover:bg-slate-800/50">
                    <td className="px-4 py-3 font-mono text-xs text-slate-400">
                      {e.seq === 0 ? <span className="rounded bg-emerald-950/60 px-1.5 py-0.5 text-emerald-400">GENESIS</span> : `#${e.seq}`}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-slate-400">{new Date(e.timestamp).toLocaleString()}</td>
                    <td className="px-4 py-3 text-slate-300">{e.actor_label}</td>
                    <td className="px-4 py-3 font-mono text-xs text-indigo-300">{e.action}</td>
                    <td className="px-4 py-3 text-slate-400">{e.resource_type}{e.resource_id ? `:${String(e.resource_id).slice(0, 8)}` : ""}</td>
                    <td className="px-4 py-3"><Hash value={e.prev_hash} testid={`audit-prev-${e.seq}`} /></td>
                    <td className="px-4 py-3"><Hash value={e.hash} testid={`audit-hash-${e.seq}`} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Layout>
  );
}
