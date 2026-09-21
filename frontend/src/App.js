import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { AuthProvider } from "@/context/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import Login from "@/views/Login";
import Mfa from "@/views/Mfa";
import Dashboard from "@/views/Dashboard";
import Recommendations from "@/views/Recommendations";
import Approvals from "@/views/Approvals";
import ApprovalDetail from "@/views/ApprovalDetail";
import Audit from "@/views/Audit";
import Notifications from "@/views/Notifications";
import Policies from "@/views/Policies";
import Emergency from "@/views/Emergency";
import Connectors from "@/views/Connectors";
import AdminUsers from "@/views/AdminUsers";
import AdminRoles from "@/views/AdminRoles";
import Settings from "@/views/Settings";

const P = (el) => <ProtectedRoute>{el}</ProtectedRoute>;

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/mfa" element={<Mfa />} />
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={P(<Dashboard />)} />
            <Route path="/recommendations" element={P(<Recommendations />)} />
            <Route path="/approvals" element={P(<Approvals />)} />
            <Route path="/approvals/:id" element={P(<ApprovalDetail />)} />
            <Route path="/audit" element={P(<Audit />)} />
            <Route path="/notifications" element={P(<Notifications />)} />
            <Route path="/policies" element={P(<Policies />)} />
            <Route path="/emergency" element={P(<Emergency />)} />
            <Route path="/connectors" element={P(<Connectors />)} />
            <Route path="/admin/users" element={P(<AdminUsers />)} />
            <Route path="/admin/roles" element={P(<AdminRoles />)} />
            <Route path="/settings" element={P(<Settings />)} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
          <Toaster position="top-right" theme="dark" />
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
