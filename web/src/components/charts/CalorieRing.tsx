"use client";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";

interface Props {
  consumed: number;
  target: number;
}

export function CalorieRing({ consumed, target }: Props) {
  const pct = Math.min(100, target > 0 ? (consumed / target) * 100 : 0);
  const remaining = Math.max(0, target - consumed);
  const data = [
    { name: "Consumed", value: consumed },
    { name: "Remaining", value: remaining },
  ];
  const COLORS = ["#10b981", "#1f2937"];

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-40 h-40">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} cx="50%" cy="50%" innerRadius={50} outerRadius={68}
              startAngle={90} endAngle={-270} paddingAngle={2} dataKey="value">
              {data.map((_, i) => (
                <Cell key={i} fill={COLORS[i]} strokeWidth={0} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-display font-bold text-white">{consumed.toFixed(0)}</span>
          <span className="text-xs text-gray-400">/ {target} kcal</span>
        </div>
      </div>
      <div className="flex items-center gap-4 mt-3 text-xs">
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
          <span className="text-gray-400">Consumed</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-gray-700" />
          <span className="text-gray-400">Remaining</span>
        </div>
      </div>
      <div className="text-emerald-400 text-sm font-semibold mt-1">{pct.toFixed(0)}% of goal</div>
    </div>
  );
}
