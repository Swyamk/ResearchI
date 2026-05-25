"use client";
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip } from "recharts";

interface Props { data?: { deficient_nutrients: any[]; borderline_nutrients: any[]; sufficient_nutrients: string[] }; }

const NUTRIENTS = ["Vitamin C", "Vitamin D", "Calcium", "Iron", "Fiber", "Omega-3"];

export function DeficiencyRadar({ data }: Props) {
  if (!data) return (
    <div className="h-48 flex items-center justify-center text-gray-500 text-sm">Loading...</div>
  );

  const lookup: Record<string, number> = {};
  data.deficient_nutrients?.forEach((n) => { lookup[n.nutrient] = n.pct; });
  data.borderline_nutrients?.forEach((n) => { lookup[n.nutrient] = n.pct; });
  data.sufficient_nutrients?.forEach((n) => { lookup[n] = 100; });

  const chartData = NUTRIENTS.map((name) => ({ name, value: lookup[name] ?? 0, fullMark: 100 }));

  return (
    <ResponsiveContainer width="100%" height={180}>
      <RadarChart data={chartData}>
        <PolarGrid stroke="rgba(255,255,255,0.1)" />
        <PolarAngleAxis dataKey="name" tick={{ fill: "#9ca3af", fontSize: 10 }} />
        <Radar dataKey="value" stroke="#10b981" fill="#10b981" fillOpacity={0.15} strokeWidth={2}
          dot={{ fill: "#10b981", r: 3 }} />
        <Tooltip formatter={(v: number) => [`${v.toFixed(0)}%`, "% of RDI"]}
          contentStyle={{ background: "#111827", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "12px", fontSize: "12px" }} />
      </RadarChart>
    </ResponsiveContainer>
  );
}
