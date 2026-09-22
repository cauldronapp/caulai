import { useQuery, useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { Plug, PlayCircle, CheckCircle2, XCircle } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Layout } from "@/components/Layout";
import { PageHeader, Card, Loading, ErrorState, EmptyState, StatusBadge } from "@/components/primitives";

export default function Connectors() {
  const { can } = useAuth();
  const [contract, setContract] = useState(null);
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["connectors"],
    queryFn: async () => (await api.get("/connectors")).data,
  });

  const runContract = useMutation({
    mutationFn: async () => (await api.post("/connectors/contract-test")).data,
    onSuccess: (d) => setContract(d),
  });

  return (
    <Layout>
      <PageHeader title="Connectors" subtitle="All connectors are Not Connected in Phase 1A. No credential fields are exposed.">
        {can("connector:test") && (
          <button data-testid="run-contract-button" onClick={() => runContract.mutate()} className="flex items-center gap-2 rounded-md bg-indigo-600 px-3 py-2 text-xs font-semibold text-white hover:bg-indigo-500">
            <PlayCircle className="h-4 w-4" /> Run Contract Tests
          </button>
        )}
      </PageHeader>
      <div className="space-y-4 p-6">
        {contract && (
          <Card testid="contract-results" className={contract.all_passed ? "border-emerald-500/30" : "border-rose-500/40"}>
            <div className="mb-3 flex items-center gap-2">
              <StatusBadge testid="contract-verdict" status={contract.all_passed ? "verified" : "failed"} label={contract.all_passed ? "CONTRACT PASSED" : "CONTRACT FAILED"} />
              <span className="font-mono text-xs text-slate-400">reference: {contract.connector}</span>
            </div>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {contract.checks.map((c) => (
                <div key={c.check} data-testid={`contract-check-${c.check}`} className="flex items-center gap-2 rounded-md border border-slate-800 bg-slate-900/50 px-3 py-2 text-sm">
                  {c.passed ? <CheckCircle2 className="h-4 w-4 text-emerald-400" /> : <XCircle className="h-4 w-4 text-rose-400" />}
                  <span className="font-mono text-xs text-slate-300">{c.check}</span>
                </div>
              ))}
            </div>
          </Card>
        )}
        {isLoading && <Loading testid="connectors-loading" />}
        {error && <ErrorState testid="connectors-error" message={error.message} onRetry={refetch} />}
        {data && data.length === 0 && <EmptyState testid="connectors-empty" message="No connectors registered." />}
        {data && data.length > 0 && (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3" data-testid="connectors-grid">
            {data.map((c) => (
              <Card key={c.id} testid={`connector-${c.id}`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Plug className="h-5 w-5 text-slate-400" />
                    <span className="font-heading text-base font-semibold text-slate-200">{c.name}</span>
                  </div>
                  <StatusBadge testid={`connector-status-${c.id}`} status="not_connected" label="NOT CONNECTED" />
                </div>
                <div className="mt-2 font-mono text-xs uppercase tracking-wider text-slate-400">{c.category}</div>
                <p className="mt-3 text-xs text-slate-400">No credential fields shown. Activation requires passing the connector contract suite (Phase 1B, separate approval).</p>
              </Card>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
