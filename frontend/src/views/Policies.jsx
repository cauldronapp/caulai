import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Layout } from "@/components/Layout";
import { PageHeader, Card, Loading, ErrorState, EmptyState, StatusBadge } from "@/components/primitives";

export default function Policies() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["policies"],
    queryFn: async () => (await api.get("/policies")).data,
  });
  return (
    <Layout>
      <PageHeader title="Policies" subtitle="Governance policies drive approval tiers and prohibitions. Server-evaluated." />
      <div className="space-y-4 p-6">
        {isLoading && <Loading testid="policies-loading" />}
        {error && <ErrorState testid="policies-error" message={error.message} onRetry={refetch} />}
        {data && data.length === 0 && <EmptyState testid="policies-empty" message="No policies defined." />}
        {data && data.map((p) => (
          <Card key={p.id} testid={`policy-${p.id}`}>
            <div className="flex items-center justify-between">
              <h3 className="font-heading text-lg font-semibold text-slate-200">{p.name}</h3>
              <StatusBadge status={p.enabled ? "verified" : "revoked"} label={p.enabled ? "ENABLED" : "DISABLED"} />
            </div>
            <p className="mt-1 text-sm text-slate-400">{p.description}</p>
            <pre className="mt-3 overflow-x-auto rounded-md border border-slate-800 bg-slate-950 p-3 font-mono text-xs text-emerald-300">{JSON.stringify(p.rules, null, 2)}</pre>
            <div className="mt-2 font-mono text-xs text-slate-400">version {p.version}</div>
          </Card>
        ))}
      </div>
    </Layout>
  );
}
