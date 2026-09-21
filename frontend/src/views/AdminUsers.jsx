import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Layout } from "@/components/Layout";
import { PageHeader, Card, Loading, ErrorState } from "@/components/primitives";

export default function AdminUsers() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["admin-users"],
    queryFn: async () => (await api.get("/admin/users")).data,
  });
  return (
    <Layout>
      <PageHeader title="Users" subtitle="Synthetic stub identities (AUTH STUB — NOT PRODUCTION). Dev/staging only." />
      <div className="p-6">
        {isLoading && <Loading testid="users-loading" />}
        {error && <ErrorState testid="users-error" message={error.message} onRetry={refetch} />}
        {data && (
          <div className="overflow-hidden rounded-xl border border-slate-800">
            <table className="w-full text-left text-sm" data-testid="users-table">
              <thead className="bg-slate-900/60 font-mono text-xs uppercase tracking-wider text-slate-400">
                <tr><th className="px-4 py-3">Name</th><th className="px-4 py-3">Email</th><th className="px-4 py-3">Roles</th><th className="px-4 py-3">Type</th><th className="px-4 py-3">Status</th></tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {data.map((u) => (
                  <tr key={u.id} data-testid={`user-row-${u.id}`} className="bg-[#111622]">
                    <td className="px-4 py-3 text-slate-200">{u.display_name}</td>
                    <td className="px-4 py-3 font-mono text-xs text-slate-400">{u.email}</td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {u.roles.length === 0 ? <span className="font-mono text-xs text-rose-300">NO ROLE (default-deny)</span> : u.roles.map((r) => (
                          <span key={r} className="rounded bg-slate-800 px-1.5 py-0.5 font-mono text-[10px] text-slate-300">{r}</span>
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      {u.is_service_identity ? <span className="font-mono text-xs text-purple-300">SERVICE</span> : <span className="font-mono text-xs text-slate-400">human</span>}
                    </td>
                    <td className="px-4 py-3">{u.disabled ? <span className="font-mono text-xs text-rose-300">DISABLED</span> : <span className="font-mono text-xs text-emerald-300">ACTIVE</span>}</td>
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
