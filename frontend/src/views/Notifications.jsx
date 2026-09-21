import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Bell, CheckCheck } from "lucide-react";
import { api } from "@/lib/api";
import { Layout } from "@/components/Layout";
import { PageHeader, Card, Loading, ErrorState, EmptyState } from "@/components/primitives";

export default function Notifications() {
  const qc = useQueryClient();
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["notifications"],
    queryFn: async () => (await api.get("/notifications")).data,
  });
  const readAll = useMutation({
    mutationFn: async () => (await api.post("/notifications/read-all")).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });

  return (
    <Layout>
      <PageHeader title="Notifications" subtitle="System and governance notifications.">
        <button data-testid="mark-all-read" onClick={() => readAll.mutate()} className="flex items-center gap-2 rounded-md border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-slate-200 hover:bg-slate-700 hover:text-white">
          <CheckCheck className="h-3.5 w-3.5" /> Mark all read
        </button>
      </PageHeader>
      <div className="space-y-3 p-6">
        {isLoading && <Loading testid="notifications-loading" />}
        {error && <ErrorState testid="notifications-error" message={error.message} onRetry={refetch} />}
        {data && data.length === 0 && <EmptyState testid="notifications-empty" message="You're all caught up. No notifications." />}
        {data && data.map((n) => (
          <Card key={n.id} testid={`notification-${n.id}`} className={n.read ? "opacity-60" : "border-indigo-500/30"}>
            <div className="flex items-start gap-3">
              <Bell className={`mt-0.5 h-4 w-4 ${n.read ? "text-slate-500" : "text-indigo-400"}`} />
              <div>
                <div className="font-medium text-slate-200">{n.title}</div>
                <div className="text-sm text-slate-400">{n.body}</div>
                <div className="mt-1 font-mono text-[11px] text-slate-500">{new Date(n.created_at).toLocaleString()}</div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </Layout>
  );
}
