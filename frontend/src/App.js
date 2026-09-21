import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { AuthProvider } from "@/context/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import Login from "@/views/Login";
import Dashboard from "@/views/Dashboard";
import Approvals from "@/views/Approvals";
import ApprovalDetail from "@/views/ApprovalDetail";
import Audit from "@/views/Audit";
import ComingSoon from "@/views/ComingSoon";

const P = (el) => <ProtectedRoute>{el}</ProtectedRoute>;

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={P(<Dashboard />)} />
            <Route path="/approvals" element={P(<Approvals />)} />
            <Route path="/approvals/:id" element={P(<ApprovalDetail />)} />
            <Route path="/audit" element={P(<Audit />)} />
            <Route path="/recommendations" element={P(<ComingSoon title="Recommendations" note="AI recommendation intake and lifecycle UI is delivered in the next milestone." />)} />
            <Route path="/notifications" element={P(<ComingSoon title="Notifications" />)} />
            <Route path="/policies" element={P(<ComingSoon title="Policies" />)} />
            <Route path="/emergency" element={P(<ComingSoon title="Emergency Controls" note="Global/granular pause, revocation and queue drain operate against stub paths only." />)} />
            <Route path="/connectors" element={P(<ComingSoon title="Connectors" note="All connectors are Not Connected in Phase 1A. No credential fields are exposed." />)} />
            <Route path="/admin/users" element={P(<ComingSoon title="Users" />)} />
            <Route path="/admin/roles" element={P(<ComingSoon title="Roles" />)} />
            <Route path="/settings" element={P(<ComingSoon title="Settings" note="Subscription $24.99/mo and 2.30% fee are versioned and editable in the next milestone." />)} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
          <Toaster position="top-right" theme="dark" />
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
