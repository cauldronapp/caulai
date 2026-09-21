import { Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

export function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading || user === null) {
    return (
      <div
        data-testid="auth-loading"
        className="flex min-h-screen items-center justify-center bg-[#0A0D14] font-mono text-sm text-slate-400"
      >
        Establishing secure session…
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  return children;
}
