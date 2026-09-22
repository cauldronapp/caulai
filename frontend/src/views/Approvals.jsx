import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { Layout } from "@/components/Layout";
import { PageHeader, Card, Loading, ErrorState, EmptyState, StatusBadge, Hash } from "@/components/primitives";

export default function Approvals() {
  const navigate = useNavigate();
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["approvals"],
    queryFn: async () => (await api.get("/approvals")).data,
  });

  return (
    <Layout>
      <PageHeader title="Approvals" subtitle="Approval decisions are bound to the exact action-payload digest. Default-deny, quorum-enforced." />
      <div className="p-6">
        {isLoading && <Loading testid="approvals-loading" />}
        {error && <ErrorState testid="approvals-error" message={error.message} onRetry={refetch} />}
        {data && data.length === 0 && <EmptyState testid="approvals-empty" message="No approvals in queue." />}
        {data && data.length > 0 && (
          <div className="overflow-hidden rounded-xl border border-slate-800">
            <table className="w-full text-left text-sm" data-testid="approvals-table">
              <thead className="bg-slate-900/60 font-mono text-xs uppercase tracking-wider text-slate-400">
                <tr>
                  <th scope="col" className="px-4 py-3">Recommendation</th>
                  <th scope="col" className="px-4 py-3">Risk</th>
                  <th scope="col" className="px-4 py-3">Status</th>
                  <th scope="col" className="px-4 py-3">Approvals</th>
                  <th scope="col" className="px-4 py-3">Payload Bound</th>
                  <th scope="col" className="px-4 py-3">Digest</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {data.map((a) => (
                  <tr
                    key={a.id}
                    data-testid={`approval-row-${a.id}`}
                    onClick={() => navigate(`/approvals/${a.id}`)}
                    onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); navigate(`/approvals/${a.id}`); } }}
                    tabIndex={0}
                    role="button"
                    aria-label={`Open approval for ${a.recommendation_title}, status ${a.status}`}
                    className="cursor-pointer bg-[#111622] transition-colors hover:bg-slate-800/60 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-500"
                  >
                    <td className="px-4 py-3 font-medium text-slate-200">{a.recommendation_title}</td>
                    <td className="px-4 py-3">
                      <span className={`font-mono text-xs ${a.risk_level === "high" ? "text-rose-300" : a.risk_level === "medium" ? "text-amber-300" : "text-slate-400"}`}>
                        {a.risk_level}
                      </span>
                    </td>
                    <td className="px-4 py-3"><StatusBadge testid={`approval-status-${a.id}`} status={a.status} /></td>
                    <td className="px-4 py-3 font-mono text-xs text-slate-300">{a.distinct_approvals}/{a.required_approvals}</td>
                    <td className="px-4 py-3">
                      <span className={`font-mono text-xs ${a.payload_bound ? "text-emerald-400" : "text-rose-400"}`} data-testid={`approval-bound-${a.id}`}>
                        {a.payload_bound ? "BOUND" : "UNBOUND"}
                      </span>
                    </td>
                    <td className="px-4 py-3"><Hash value={a.payload_digest} testid={`approval-digest-${a.id}`} /></td>
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
