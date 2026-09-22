import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Check, X, Ban } from "lucide-react";
import { api, formatApiErrorDetail } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Layout } from "@/components/Layout";
import { PageHeader, Card, Loading, ErrorState, StatusBadge, Hash } from "@/components/primitives";

export default function ApprovalDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { can } = useAuth();
  const [comment, setComment] = useState("");
  const [actionError, setActionError] = useState("");

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["approval", id],
    queryFn: async () => (await api.get(`/approvals/${id}`)).data,
  });

  const decide = useMutation({
    mutationFn: async ({ kind }) => {
      const url =
        kind === "revoke"
          ? `/approvals/${id}/revoke`
          : `/approvals/${data.recommendation_id}/${kind}`;
      const body =
        kind === "revoke"
          ? { reason: comment }
          : { decision: kind, payload_digest: data.current_payload_digest, comment };
      return (await api.post(url, body)).data;
    },
    onSuccess: () => {
      setActionError("");
      setComment("");
      qc.invalidateQueries({ queryKey: ["approval", id] });
      qc.invalidateQueries({ queryKey: ["approvals"] });
    },
    onError: (err) => setActionError(formatApiErrorDetail(err.response?.data?.detail) || err.message),
  });

  const canAct = data && data.status === "pending" && !data.revoked;

  return (
    <Layout>
      <PageHeader title="Approval Detail" subtitle="Reviewer safeguards: no self-approval of high-risk, no double-count, digest-bound.">
        <button data-testid="back-to-approvals" onClick={() => navigate("/approvals")} className="flex items-center gap-2 rounded-md border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-slate-200 hover:bg-slate-700 hover:text-white">
          <ArrowLeft className="h-3.5 w-3.5" /> Back
        </button>
      </PageHeader>
      <div className="p-6">
        {isLoading && <Loading testid="approval-detail-loading" />}
        {error && <ErrorState testid="approval-detail-error" message={error.message} onRetry={refetch} />}
        {data && (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div className="space-y-4 lg:col-span-2">
              <Card testid="approval-summary">
                <div className="flex items-center justify-between">
                  <h2 className="font-heading text-xl font-semibold text-slate-100">{data.recommendation_title}</h2>
                  <StatusBadge testid="approval-detail-status" status={data.status} />
                </div>
                <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                  <div><div className="font-mono text-xs uppercase tracking-wider text-slate-400">Risk</div><div className="mt-1 text-slate-200">{data.risk_level}</div></div>
                  <div><div className="font-mono text-xs uppercase tracking-wider text-slate-400">Tier</div><div className="mt-1 text-slate-200">{data.tier}</div></div>
                  <div><div className="font-mono text-xs uppercase tracking-wider text-slate-400">Distinct Approvals</div><div className="mt-1 text-slate-200">{data.distinct_approvals} / {data.required_approvals}</div></div>
                  <div><div className="font-mono text-xs uppercase tracking-wider text-slate-400">Expires</div><div className="mt-1 text-slate-200">{new Date(data.expires_at).toLocaleString()}</div></div>
                </div>
                <div className="mt-4">
                  <div className="font-mono text-xs uppercase tracking-wider text-slate-400">Bound Payload Digest</div>
                  <div className="mt-1 flex items-center gap-2">
                    <Hash value={data.payload_digest} testid="approval-bound-digest" />
                    <span className={`font-mono text-xs ${data.payload_bound ? "text-emerald-400" : "text-rose-400"}`} data-testid="approval-binding-state">
                      {data.payload_bound ? "MATCHES CURRENT PAYLOAD" : "PAYLOAD CHANGED — APPROVAL INVALID"}
                    </span>
                  </div>
                </div>
              </Card>

              <Card testid="approval-decisions">
                <h3 className="mb-3 font-heading text-lg font-semibold text-slate-200">Decision Ledger</h3>
                {data.decisions.length === 0 ? (
                  <p className="text-sm text-slate-400">No decisions recorded yet.</p>
                ) : (
                  <ul className="space-y-2" data-testid="decision-list">
                    {data.decisions.map((d) => (
                      <li key={d.id} className="flex items-center justify-between rounded-md border border-slate-800 bg-slate-900/50 px-3 py-2 text-sm">
                        <span className="font-mono text-xs text-slate-400">{d.reviewer_id.slice(0, 8)}…</span>
                        <StatusBadge status={d.decision === "approve" ? "approved" : "rejected"} label={d.decision} />
                        <span className="text-xs text-slate-400">{new Date(d.created_at).toLocaleString()}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </Card>
            </div>

            <div className="space-y-4">
              <Card testid="approval-actions">
                <h3 className="mb-3 font-heading text-lg font-semibold text-slate-200">Cast Decision</h3>
                {!canAct && <p className="mb-3 text-sm text-slate-400">This approval is {data.status} and cannot accept new decisions.</p>}
                <textarea
                  data-testid="decision-comment"
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="Optional comment / reason…"
                  className="mb-3 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none"
                  rows={3}
                />
                {actionError && <div data-testid="decision-error" className="mb-3 rounded-md border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-300">{actionError}</div>}
                <div className="flex flex-col gap-2">
                  {can("approval:approve") && (
                    <button data-testid="approve-button" disabled={!canAct || decide.isPending} onClick={() => decide.mutate({ kind: "approve" })} className="flex items-center justify-center gap-2 rounded-md bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-40">
                      <Check className="h-4 w-4" /> Approve
                    </button>
                  )}
                  {can("approval:reject") && (
                    <button data-testid="reject-button" disabled={!canAct || decide.isPending} onClick={() => decide.mutate({ kind: "reject" })} className="flex items-center justify-center gap-2 rounded-md bg-rose-600 px-4 py-2 text-sm font-semibold text-white hover:bg-rose-500 disabled:opacity-40">
                      <X className="h-4 w-4" /> Reject
                    </button>
                  )}
                  {can("approval:revoke") && (
                    <button data-testid="revoke-button" disabled={decide.isPending || data.revoked} onClick={() => decide.mutate({ kind: "revoke" })} className="flex items-center justify-center gap-2 rounded-md border border-slate-700 bg-slate-800 px-4 py-2 text-sm text-slate-200 hover:bg-slate-700 disabled:opacity-40">
                      <Ban className="h-4 w-4" /> Revoke
                    </button>
                  )}
                </div>
              </Card>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
