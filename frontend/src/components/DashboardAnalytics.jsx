import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";
import { Download, Printer } from "lucide-react";
import { api } from "@/lib/api";
import { Card } from "@/components/primitives";

const TIP = {
  background: "#0f172a", border: "1px solid #334155", borderRadius: 8,
  color: "#e2e8f0", fontSize: 12,
};
const AXIS = { fill: "#94a3b8", fontSize: 10 };
const RANGES = [7, 30, 90];

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
  const [days, setDays] = useState(30);
  const { data } = useQuery({
    queryKey: ["dashboard-analytics", days],
    queryFn: async () => (await api.get("/dashboard/analytics", { params: { days } })).data,
  });

  const exportCsv = async () => {
    const res = await api.get("/dashboard/export", { responseType: "blob" });
    const url = URL.createObjectURL(res.data);
    const a = document.createElement("a");
    a.href = url;
    a.download = "caul_dashboard.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="mt-6" data-testid="analytics-section">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-heading text-lg font-semibold text-slate-200">Trends</h2>
        <div className="flex items-center gap-2">
          <div className="flex rounded-md border border-slate-700 bg-slate-900 p-0.5" role="group" aria-label="Date range">
            {RANGES.map((r) => (
              <button
                key={r}
                data-testid={`range-${r}`}
                onClick={() => setDays(r)}
                className={`rounded px-3 py-1 text-xs font-medium transition-colors ${days === r ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-white"}`}
              >
                {r}d
              </button>
            ))}
          </div>
          <button
            data-testid="dashboard-export-csv"
            onClick={exportCsv}
            className="flex items-center gap-1.5 rounded-md border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs text-slate-200 hover:bg-slate-700"
          >
            <Download className="h-3.5 w-3.5" /> CSV
          </button>
          <button
            data-testid="dashboard-export-pdf"
            onClick={() => window.print()}
            className="flex items-center gap-1.5 rounded-md bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-500"
          >
            <Printer className="h-3.5 w-3.5" /> PDF
          </button>
        </div>
      </div>
      {data && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
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
      )}
    </div>
  );
}
