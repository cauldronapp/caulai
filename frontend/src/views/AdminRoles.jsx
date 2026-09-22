import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Layout } from "@/components/Layout";
import { PageHeader, Card, Loading, ErrorState } from "@/components/primitives";

export default function AdminRoles() {
  const roles = useQuery({ queryKey: ["admin-roles"], queryFn: async () => (await api.get("/admin/roles")).data });
  const perms = useQuery({ queryKey: ["admin-perms"], queryFn: async () => (await api.get("/admin/permissions")).data });

  return (
    <Layout>
      <PageHeader title="Roles & Permission Matrix" subtitle="Server-side RBAC, default-deny. Authorization resolved from PostgreSQL." />
      <div className="space-y-4 p-6">
        {(roles.isLoading || perms.isLoading) && <Loading testid="roles-loading" />}
        {roles.error && <ErrorState testid="roles-error" message={roles.error.message} onRetry={roles.refetch} />}
        {perms.data && (
          <Card testid="permission-matrix">
            <h3 className="mb-3 font-heading text-lg font-semibold text-slate-200">Permission Catalog ({perms.data.count})</h3>
            <div className="grid grid-cols-1 gap-1.5 sm:grid-cols-2 lg:grid-cols-3">
              {perms.data.matrix.map((p) => (
                <div key={p.name} data-testid={`perm-${p.name}`} className="flex items-center justify-between rounded border border-slate-800 bg-slate-900/50 px-2 py-1.5">
                  <span className="font-mono text-xs text-slate-300">{p.name}</span>
                  {p.high_risk && <span className="rounded bg-rose-500/15 px-1.5 py-0.5 font-mono text-[9px] text-rose-300">HIGH-RISK</span>}
                </div>
              ))}
            </div>
          </Card>
        )}
        {roles.data && roles.data.map((r) => (
          <Card key={r.id} testid={`role-${r.name}`}>
            <div className="flex items-center justify-between">
              <h3 className="font-heading text-lg font-semibold text-slate-200">{r.name}</h3>
              <span className="font-mono text-xs text-slate-400">{r.permissions.length} permissions</span>
            </div>
            <p className="mt-1 text-sm text-slate-400">{r.description}</p>
            <div className="mt-3 flex flex-wrap gap-1">
              {r.permissions.length === 0 ? <span className="font-mono text-xs text-rose-300">EMPTY — default-deny</span> : r.permissions.map((p) => (
                <span key={p} className="rounded bg-slate-800 px-1.5 py-0.5 font-mono text-[10px] text-slate-300">{p}</span>
              ))}
            </div>
          </Card>
        ))}
      </div>
    </Layout>
  );
}
