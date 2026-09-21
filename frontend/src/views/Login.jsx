import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Terminal, ShieldAlert, ChevronRight } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { formatApiErrorDetail } from "@/lib/api";

const STUB_ACCOUNTS = [
  { email: "execowner@example.invalid", label: "Sean Gaden — Demo ExecOwner" },
  { email: "admin@example.invalid", label: "Demo Admin" },
  { email: "marketing@example.invalid", label: "Demo Marketing Manager" },
  { email: "developer@example.invalid", label: "Demo Developer" },
  { email: "security@example.invalid", label: "Demo Security/Compliance" },
  { email: "analyst@example.invalid", label: "Demo Analyst" },
  { email: "auditor@example.invalid", label: "Demo Auditor" },
  { email: "norole@example.invalid", label: "Demo No-Role (default-deny)" },
];
const STUB_PASSWORD = "StubPass!2026";

export default function Login() {
  const { login, user } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (user) navigate("/dashboard", { replace: true });
  }, [user, navigate]);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(email.trim(), password);
      navigate("/dashboard");
    } catch (err) {
      setError(formatApiErrorDetail(err.response?.data?.detail) || err.message);
    } finally {
      setBusy(false);
    }
  };

  const quick = (acct) => {
    setEmail(acct.email);
    setPassword(STUB_PASSWORD);
  };

  return (
    <div className="flex min-h-screen bg-[#0A0D14] text-slate-100">
      <div className="hidden w-1/2 flex-col justify-between border-r border-slate-800 bg-slate-950 p-12 lg:flex">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-lg border border-indigo-500/40 bg-indigo-500/10 text-indigo-300">
            <Terminal className="h-6 w-6" />
          </div>
          <div>
            <div className="font-heading text-lg font-bold tracking-tight">CAUL AI</div>
            <div className="font-mono text-xs uppercase tracking-wider text-slate-500">Cauldron Growth OS Command Center</div>
          </div>
        </div>
        <div>
          <h2 className="font-heading text-4xl font-extrabold leading-tight tracking-tight text-slate-100">
            Governance, approvals & tamper-evident audit — under one command center.
          </h2>
          <p className="mt-4 max-w-md text-sm leading-relaxed text-slate-400">
            Server-side RBAC with default-deny. Hash-chained audit trail. Hardened approval
            state machine. PostgreSQL system of record.
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 font-mono text-xs text-amber-300">
          <ShieldAlert className="h-4 w-4" /> AUTH STUB — NOT PRODUCTION · Phase 1A · Cauldron Technologies, Inc.
        </div>
      </div>

      <div className="flex w-full items-center justify-center p-6 lg:w-1/2">
        <div className="w-full max-w-md">
          <div className="mb-6 flex items-center gap-2 rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2 font-mono text-xs text-amber-300" data-testid="login-stub-notice">
            <ShieldAlert className="h-3.5 w-3.5" /> AUTH STUB — NOT PRODUCTION (dev/staging only, no MFA)
          </div>
          <h1 className="font-heading text-2xl font-bold tracking-tight">Sign in</h1>
          <p className="mt-1 text-sm text-slate-400">Development authentication stub. Identity only — roles come from PostgreSQL RBAC.</p>

          <form onSubmit={submit} className="mt-6 space-y-4" data-testid="login-form">
            <div>
              <label className="mb-1 block font-mono text-xs uppercase tracking-wider text-slate-400">Email</label>
              <input
                data-testid="login-email-input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="username"
                placeholder="execowner@example.invalid"
                className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2.5 text-sm text-slate-100 placeholder:text-slate-600 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
              />
            </div>
            <div>
              <label className="mb-1 block font-mono text-xs uppercase tracking-wider text-slate-400">Password</label>
              <input
                data-testid="login-password-input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                placeholder="••••••••"
                className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2.5 text-sm text-slate-100 placeholder:text-slate-600 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
              />
            </div>
            {error && (
              <div data-testid="login-error" className="rounded-md border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-300">
                {error}
              </div>
            )}
            <button
              data-testid="login-submit-button"
              type="submit"
              disabled={busy}
              className="flex w-full items-center justify-center gap-2 rounded-md bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-slate-950 disabled:opacity-60"
            >
              {busy ? "Authenticating…" : "Sign in to Command Center"} <ChevronRight className="h-4 w-4" />
            </button>
          </form>

          <div className="mt-8">
            <p className="mb-2 font-mono text-xs uppercase tracking-wider text-slate-500">Quick stub sign-in (password autofilled)</p>
            <div className="grid grid-cols-1 gap-1.5 sm:grid-cols-2" data-testid="stub-quick-accounts">
              {STUB_ACCOUNTS.map((a) => (
                <button
                  key={a.email}
                  data-testid={`stub-account-${a.email.split("@")[0]}`}
                  onClick={() => quick(a)}
                  className="rounded-md border border-slate-800 bg-slate-900/60 px-3 py-2 text-left text-xs text-slate-300 transition-colors hover:border-indigo-500/40 hover:bg-slate-800 hover:text-white"
                >
                  <div className="font-medium">{a.label}</div>
                  <div className="font-mono text-[10px] text-slate-500">{a.email}</div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
