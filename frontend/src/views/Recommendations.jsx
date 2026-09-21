import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Lightbulb } from "lucide-react";
import { api, formatApiErrorDetail } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Layout } from "@/components/Layout";
import { PageHeader, Card, Loading, ErrorState, EmptyState, StatusBadge, Hash } from "@/components/primitives";

const TIER_LABEL = { auto: "Auto (post-policy)", requires_approval: "Requires Approval", permanently_prohibited: "Permanently Prohibited" };

export default function Recommendations() {
  const qc = useQueryClient();
  const { can } = useAuth();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ title: "", tier: "requires_approval", risk_level: "high", category: "marketing", payload: '{"example":"value"}' });
  const [err, setErr] = useState("");

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["recommendations"],
    queryFn: async () => (await api.get("/recommendations")).data,
  });

  const create = useMutation({
    mutationFn: async () => {
      let action_payload = {};
      try { action_payload = JSON.parse(form.payload || "{}"); } catch { throw new Error("Action payload must be valid JSON"); }
      return (await api.post("/recommendations", { title: form.title, tier: form.tier, risk_level: form.risk_level, category: form.category, action_payload })).data;
    },
    onSuccess: () => { setOpen(false); setErr(""); qc.invalidateQueries({ queryKey: ["recommendations"] }); qc.invalidateQueries({ queryKey: ["approvals"] }); },
    onError: (e) => setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message),
  });

  return (
    <Layout>
      <PageHeader title="Recommendations" subtitle="AI-style recommendations flow through auto / requires-approval / prohibited tiers.">
        {can("recommendation:create") && (
          <button data-testid="new-recommendation-button" onClick={() => setOpen((v) => !v)} className="flex items-center gap-2 rounded-md bg-indigo-600 px-3 py-2 text-xs font-semibold text-white hover:bg-indigo-500">
            <Plus className="h-4 w-4" /> New Recommendation
          </button>
        )}
      </PageHeader>
      <div className="space-y-4 p-6">
        {open && (
          <Card testid="recommendation-form">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <input data-testid="rec-title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Title" className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" />
              <input data-testid="rec-category" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} placeholder="Category" className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100" />
              <select data-testid="rec-tier" value={form.tier} onChange={(e) => setForm({ ...form, tier: e.target.value })} className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100">
                <option value="auto">auto</option>
                <option value="requires_approval">requires_approval</option>
                <option value="permanently_prohibited">permanently_prohibited</option>
              </select>
              <select data-testid="rec-risk" value={form.risk_level} onChange={(e) => setForm({ ...form, risk_level: e.target.value })} className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100">
                <option value="low">low</option>
                <option value="medium">medium</option>
                <option value="high">high</option>
              </select>
              <textarea data-testid="rec-payload" value={form.payload} onChange={(e) => setForm({ ...form, payload: e.target.value })} rows={3} className="font-mono sm:col-span-2 rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-emerald-300" />
            </div>
            {err && <div data-testid="rec-form-error" className="mt-2 rounded-md border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-300">{err}</div>}
            <button data-testid="rec-submit" disabled={create.isPending} onClick={() => create.mutate()} className="mt-3 rounded-md bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-50">Submit</button>
          </Card>
        )}
        {isLoading && <Loading testid="recommendations-loading" />}
        {error && <ErrorState testid="recommendations-error" message={error.message} onRetry={refetch} />}
        {data && data.length === 0 && <EmptyState testid="recommendations-empty" message="No recommendations yet." />}
        {data && data.length > 0 && (
          <div className="overflow-hidden rounded-xl border border-slate-800">
            <table className="w-full text-left text-sm" data-testid="recommendations-table">
              <thead className="bg-slate-900/60 font-mono text-xs uppercase tracking-wider text-slate-400">
                <tr><th className="px-4 py-3">Title</th><th className="px-4 py-3">Tier</th><th className="px-4 py-3">Risk</th><th className="px-4 py-3">Status</th><th className="px-4 py-3">Digest</th></tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {data.map((r) => (
                  <tr key={r.id} data-testid={`rec-row-${r.id}`} className="bg-[#111622] hover:bg-slate-800/50">
                    <td className="px-4 py-3 font-medium text-slate-200"><span className="mr-2 inline-flex"><Lightbulb className="h-4 w-4 text-amber-400" /></span>{r.title}</td>
                    <td className="px-4 py-3 text-xs text-slate-400">{TIER_LABEL[r.tier] || r.tier}</td>
                    <td className="px-4 py-3"><span className={`font-mono text-xs ${r.risk_level === "high" ? "text-rose-300" : r.risk_level === "medium" ? "text-amber-300" : "text-slate-400"}`}>{r.risk_level}</span></td>
                    <td className="px-4 py-3"><StatusBadge testid={`rec-status-${r.id}`} status={r.status} /></td>
                    <td className="px-4 py-3"><Hash value={r.payload_digest} testid={`rec-digest-${r.id}`} /></td>
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
