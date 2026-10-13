import { useQuery } from "@tanstack/react-query";
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";
import { api } from "@/lib/api";
import { Card } from "@/components/primitives";

const TIP = {
  background: "#0f172a", border: "1px solid #334155", borderRadius: 8,
  color: "#e2e8f0", fontSize: 12,
};
const AXIS = { fill: "#94a3b8", fontSize: 10 };

function ChartCard({ title, testid, children }) {
  return (
    <Card testid={testid}>
      <div className="mb-3 font-heading text-lg font-semibold text-slate-200">{title}</div>
      <ResponsiveContainer width="100%" height={200}>
        {children}
      </ResponsiveContainer>
    </Card>
  );
}

function StatusBars({ data, color }) {
  return (
    <BarChart data={data}>
      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
      <XAxis dataKey="key" tick={AXIS} />
      <YAxis tick={AXIS} allowDecimals={false} />
      <Tooltip contentStyle={TIP} cursor={{ fill: "#1e293b55" }} />
      <Bar dataKey="count" fill={color} radius={[4, 4, 0, 0]} />
    </BarChart>
  );
}

export function DashboardAnalytics() {
  const { data } = useQuery({
    queryKey: ["dashboard-analytics"],
    queryFn: async () => (await api.get("/dashboard/analytics")).data,
  });
  if (!data) return null;
  return (
    <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3" data-testid="analytics-section">
      <ChartCard title="Audit Events / Day" testid="chart-audit-daily">
        <LineChart data={data.audit_daily}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey="date" tick={AXIS} />
          <YAxis tick={AXIS} allowDecimals={false} />
          <Tooltip contentStyle={TIP} />
          <Line type="monotone" dataKey="count" stroke="#34d399" strokeWidth={2} dot={false} />
        </LineChart>
      </ChartCard>
      <ChartCard title="Recommendations by Status" testid="chart-recs-status">
        <StatusBars data={data.recommendations_by_status} color="#818cf8" />
      </ChartCard>
      <ChartCard title="Approvals by Status" testid="chart-approvals-status">
        <StatusBars data={data.approvals_by_status} color="#fbbf24" />
      </ChartCard>
    </div>
  );
}
