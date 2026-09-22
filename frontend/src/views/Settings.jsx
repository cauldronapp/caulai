import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Layout } from "@/components/Layout";
import { PageHeader, Card, Loading, ErrorState } from "@/components/primitives";

export default function Settings() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["settings"],
    queryFn: async () => (await api.get("/settings")).data,
  });
  const byKey = Object.fromEntries((data || []).map((s) => [s.key, s]));
  const sub = byKey.subscription?.value;
  const fee = byKey.platform_fee?.value;

  return (
    <Layout>
      <PageHeader title="Settings" subtitle="Versioned platform settings. Every change is audited." />
      <div className="grid grid-cols-1 gap-4 p-6 md:grid-cols-2">
        {isLoading && <Loading testid="settings-loading" />}
        {error && <ErrorState testid="settings-error" message={error.message} onRetry={refetch} />}
        {sub && (
          <Card testid="setting-subscription">
            <div className="font-mono text-xs uppercase tracking-wider text-slate-400">Subscription</div>
            <div className="mt-2 font-heading text-3xl font-bold text-slate-100">${sub.amount}<span className="text-base text-slate-400">/{sub.period}</span></div>
            <div className="mt-1 text-sm text-slate-400">{sub.label} · {sub.currency}</div>
            <div className="mt-3 font-mono text-xs text-slate-400">version {byKey.subscription.version}</div>
          </Card>
        )}
        {fee && (
          <Card testid="setting-fee">
            <div className="font-mono text-xs uppercase tracking-wider text-slate-400">Platform Fee</div>
            <div className="mt-2 font-heading text-3xl font-bold text-slate-100">{fee.percent}%</div>
            <div className="mt-1 text-sm text-slate-400">{fee.label}</div>
            <div className="mt-3 font-mono text-xs text-slate-400">version {byKey.platform_fee.version}</div>
          </Card>
        )}
      </div>
    </Layout>
  );
}
