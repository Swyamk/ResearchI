"use client";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine,
} from "recharts";
import { format, parseISO } from "date-fns";

interface Props { data?: { dates: string[]; calories: number[] }; days?: number; }

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload?.length) {
    return (
      <div className="bg-gray-900 border border-white/10 rounded-xl px-3 py-2 text-xs">
        <p className="text-gray-400 mb-1">{label}</p>
        <p className="text-emerald-400 font-bold">{payload[0]?.value?.toFixed(0)} kcal</p>
      </div>
    );
  }
  return null;
};

export function WeeklyTrendChart({ data, days = 7 }: Props) {
  if (!data?.dates?.length) {
    return (
      <div className="h-48 flex items-center justify-center text-gray-500 text-sm">
        Start logging meals to see your trend
      </div>
    );
  }

  const chartData = data.dates.map((d, i) => ({
    date: (() => { try { return format(parseISO(d), "MMM d"); } catch { return d; } })(),
    calories: data.calories[i] || 0,
  }));

  const avg = chartData.reduce((a, b) => a + b.calories, 0) / chartData.length;

  return (
    <ResponsiveContainer width="100%" height={200}>
      <AreaChart data={chartData} margin={{ top: 5, right: 5, bottom: 0, left: -20 }}>
        <defs>
          <linearGradient id="calGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
        <XAxis dataKey="date" tick={{ fill: "#6b7280", fontSize: 11 }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fill: "#6b7280", fontSize: 11 }} axisLine={false} tickLine={false} />
        <Tooltip content={<CustomTooltip />} />
        <ReferenceLine y={avg} stroke="#10b981" strokeDasharray="4 4" strokeOpacity={0.5}
          label={{ value: `Avg ${avg.toFixed(0)}`, fill: "#10b981", fontSize: 10, position: "right" }} />
        <Area type="monotone" dataKey="calories" stroke="#10b981" strokeWidth={2}
          fill="url(#calGradient)" dot={{ fill: "#10b981", r: 3, strokeWidth: 0 }}
          activeDot={{ r: 5, fill: "#10b981" }} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
