"use client";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";

interface MacroData { protein_g: number; carbs_g: number; fat_g: number; }

const MACROS = [
  { key: "protein_g", label: "Protein", color: "#6366f1", cal_per_g: 4 },
  { key: "carbs_g",   label: "Carbs",   color: "#f59e0b", cal_per_g: 4 },
  { key: "fat_g",     label: "Fat",     color: "#ec4899", cal_per_g: 9 },
];

export function MacroChart({ data }: { data?: MacroData }) {
  if (!data) return (
    <div className="h-36 flex items-center justify-center text-gray-500 text-sm">No data yet</div>
  );

  const chartData = MACROS.map((m) => ({
    name: m.label,
    value: ((data as any)[m.key] || 0) * m.cal_per_g,
    grams: (data as any)[m.key] || 0,
    color: m.color,
  })).filter((d) => d.value > 0);

  if (chartData.length === 0) return (
    <div className="h-36 flex items-center justify-center text-gray-500 text-sm">Log a meal to see breakdown</div>
  );

  return (
    <div className="space-y-4">
      <ResponsiveContainer width="100%" height={120}>
        <PieChart>
          <Pie data={chartData} cx="50%" cy="50%" outerRadius={52} dataKey="value" paddingAngle={3}>
            {chartData.map((entry, i) => (
              <Cell key={i} fill={entry.color} strokeWidth={0} />
            ))}
          </Pie>
          <Tooltip formatter={(v: number, name: string) => [`${v.toFixed(0)} kcal`, name]} />
        </PieChart>
      </ResponsiveContainer>
      <div className="space-y-2">
        {MACROS.map((m) => {
          const grams = (data as any)[m.key] || 0;
          return (
            <div key={m.key} className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full" style={{ background: m.color }} />
                <span className="text-gray-400">{m.label}</span>
              </div>
              <span className="text-white font-medium">{grams.toFixed(1)}g</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
