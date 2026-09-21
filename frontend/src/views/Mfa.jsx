import { ShieldAlert } from "lucide-react";
import { Layout } from "@/components/Layout";
import { PageHeader, Card } from "@/components/primitives";

export default function Mfa() {
  return (
    <Layout>
      <PageHeader title="Multi-Factor Authentication" subtitle="AUTH STUB — MFA is not implemented in Phase 1A." />
      <div className="p-6">
        <Card testid="mfa-stub">
          <div className="flex items-center gap-3">
            <ShieldAlert className="h-6 w-6 text-amber-400" />
            <div>
              <div className="font-heading text-lg font-semibold text-slate-200">MFA STUB — NOT PRODUCTION</div>
              <p className="mt-1 text-sm text-slate-400">
                No MFA is provided by the development authentication stub. A real MFA flow requires a
                connected identity provider (Phase 1B, separate approval). This page exists to reserve the route and state.
              </p>
            </div>
          </div>
        </Card>
      </div>
    </Layout>
  );
}
