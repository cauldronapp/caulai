import { Layout } from "@/components/Layout";
import { PageHeader, Card } from "@/components/primitives";
import { Construction } from "lucide-react";

export default function ComingSoon({ title, note }) {
  return (
    <Layout>
      <PageHeader title={title} subtitle="Phase 1A foundation milestone — this page is scoped for the next milestone." />
      <div className="p-6">
        <Card testid="coming-soon">
          <div className="flex items-center gap-3">
            <Construction className="h-6 w-6 text-amber-400" />
            <div>
              <div className="font-heading text-lg font-semibold text-slate-200">Reserved for the next milestone</div>
              <p className="mt-1 text-sm text-slate-400">{note || "Navigation and RBAC gating are wired. Full interface is delivered after foundation approval."}</p>
            </div>
          </div>
        </Card>
      </div>
    </Layout>
  );
}
