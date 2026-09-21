import { NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard, Lightbulb, CheckSquare, ScrollText, Bell, FileCog,
  AlertOctagon, Plug, Users, Shield, Settings, LogOut, Terminal, KeyRound,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { StubBanner } from "@/components/StubBanner";

const NAV = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, perm: "dashboard:read", testid: "nav-dashboard" },
  { to: "/recommendations", label: "Recommendations", icon: Lightbulb, perm: "recommendation:list", testid: "nav-recommendations" },
  { to: "/approvals", label: "Approvals", icon: CheckSquare, perm: "approval:list", testid: "nav-approvals" },
  { to: "/audit", label: "Audit Log", icon: ScrollText, perm: "audit:list", testid: "nav-audit" },
  { to: "/notifications", label: "Notifications", icon: Bell, perm: "notification:list", testid: "nav-notifications" },
  { to: "/policies", label: "Policies", icon: FileCog, perm: "policy:list", testid: "nav-policies" },
  { to: "/emergency", label: "Emergency", icon: AlertOctagon, perm: "emergency:read", testid: "nav-emergency" },
  { to: "/connectors", label: "Connectors", icon: Plug, perm: "connector:list", testid: "nav-connectors" },
  { to: "/admin/users", label: "Users", icon: Users, perm: "user:list", testid: "nav-users" },
  { to: "/admin/roles", label: "Roles", icon: Shield, perm: "role:list", testid: "nav-roles" },
  { to: "/settings", label: "Settings", icon: Settings, perm: "setting:read", testid: "nav-settings" },
  { to: "/mfa", label: "MFA (stub)", icon: KeyRound, perm: "dashboard:read", testid: "nav-mfa" },
];

export function Layout({ children }) {
  const { user, logout, can } = useAuth();
  const navigate = useNavigate();

  const doLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-[#0A0D14] text-slate-100">
      <StubBanner />
      <div className="flex">
        <aside className="sticky top-[37px] hidden h-[calc(100vh-37px)] w-64 flex-col justify-between border-r border-slate-800 bg-slate-950 p-4 md:flex">
          <div>
            <div className="mb-6 flex items-center gap-2 px-2">
              <div className="flex h-9 w-9 items-center justify-center rounded-md border border-indigo-500/40 bg-indigo-500/10 text-indigo-300">
                <Terminal className="h-5 w-5" />
              </div>
              <div>
                <div className="font-heading text-sm font-bold tracking-tight text-slate-100">CAUL AI</div>
                <div className="font-mono text-[10px] uppercase tracking-wider text-slate-500">Command Center</div>
              </div>
            </div>
            <nav className="flex flex-col gap-1" data-testid="primary-nav">
              {NAV.filter((n) => can(n.perm)).map((n) => {
                const Icon = n.icon;
                return (
                  <NavLink
                    key={n.to}
                    to={n.to}
                    data-testid={n.testid}
                    className={({ isActive }) =>
                      `flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-all duration-150 ${
                        isActive
                          ? "bg-indigo-500/15 text-indigo-200 shadow-[0_0_15px_rgba(99,102,241,0.15)]"
                          : "text-slate-400 hover:bg-slate-800 hover:text-white"
                      }`
                    }
                  >
                    <Icon className="h-4 w-4" />
                    {n.label}
                  </NavLink>
                );
              })}
            </nav>
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
            <div className="mb-2 flex items-center gap-2">
              <span
                data-testid="stub-user-pill"
                className="inline-flex items-center rounded-md bg-amber-500/15 px-2 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-wider text-amber-300"
              >
                Stub User
              </span>
            </div>
            <div className="truncate text-sm font-medium text-slate-200" data-testid="current-user-name">
              {user?.display_name}
            </div>
            <div className="truncate font-mono text-[11px] text-slate-500" data-testid="current-user-email">
              {user?.email}
            </div>
            <div className="mt-1 flex flex-wrap gap-1">
              {(user?.roles || []).map((r) => (
                <span key={r} className="rounded bg-slate-800 px-1.5 py-0.5 font-mono text-[10px] text-slate-300">
                  {r}
                </span>
              ))}
            </div>
            <button
              data-testid="logout-button"
              onClick={doLogout}
              className="mt-3 flex w-full items-center justify-center gap-2 rounded-md border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-slate-200 transition-colors hover:bg-slate-700 hover:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-slate-950"
            >
              <LogOut className="h-3.5 w-3.5" /> Sign out
            </button>
          </div>
        </aside>

        <main className="min-h-[calc(100vh-37px)] flex-1">{children}</main>
      </div>
    </div>
  );
}
