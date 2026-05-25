"use client";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { TrendingUp, Calendar, BarChart2, Target, AlertTriangle } from "lucide-react";
import { WeeklyTrendChart } from "@/components/charts/WeeklyTrendChart";
import { DeficiencyRadar } from "@/components/charts/DeficiencyRadar";
import { api } from "@/lib/api";
import { AppLayout } from "@/components/layout/AppLayout";

export default function AnalyticsPage() {
  const [weekly, setWeekly] = useState<any>(null);
  const [monthly, setMonthly] = useState<any>(null);
  const [trend, setTrend] = useState<any>(null);
  const [deficiencies, setDeficiencies] = useState<any>(null);
  const [tab, setTab] = useState<"weekly" | "monthly">("weekly");

  useEffect(() => {
    Promise.all([
      api.get("/analytics/weekly"),
      api.get("/analytics/monthly"),
      api.get("/analytics/trend?days=30"),
      api.get("/analytics/deficiencies?days=7"),
    ]).then(([w, m, t, d]) => {
      setWeekly(w.data);
      setMonthly(m.data);
      setTrend(t.data);
      setDeficiencies(d.data);
    }).catch(() => {});
  }, []);

  const current = tab === "weekly" ? weekly : monthly;

  return (
    <AppLayout>
      <div className="p-6 max-w-6xl mx-auto space-y-6">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-display font-bold text-white">Nutrition Analytics</h1>
            <p className="text-gray-400 text-sm mt-1">Track your progress and spot trends</p>
          </div>
          <div className="flex bg-gray-900/60 border border-white/10 rounded-xl p-1">
            {(["weekly", "monthly"] as const).map((t) => (
              <button key={t} onClick={() => setTab(t)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all capitalize
                  ${tab === t ? "bg-emerald-500 text-white" : "text-gray-400 hover:text-white"}`}>
                {t}
              </button>
            ))}
          </div>
        </motion.div>

        {/* Summary Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { icon: Target, label: "Avg Calories", value: current?.avg_daily_calories?.toFixed(0) ?? "–", unit: "kcal", color: "from-orange-500 to-amber-500" },
            { icon: TrendingUp, label: "Avg Protein", value: current?.avg_daily_protein_g?.toFixed(1) ?? "–", unit: "g", color: "from-blue-500 to-indigo-500" },
            { icon: Calendar, label: "Days Logged", value: current?.days_logged ?? "–", unit: `/ ${tab === "weekly" ? "7" : "30"}`, color: "from-emerald-500 to-teal-500" },
            { icon: BarChart2, label: "Consistency", value: current?.consistency_score?.toFixed(0) ?? "–", unit: "%", color: "from-violet-500 to-purple-500" },
          ].map((card, i) => (
            <motion.div key={card.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="bg-gray-900/60 border border-white/10 rounded-2xl p-5">
              <div className={`w-9 h-9 rounded-xl bg-gradient-to-br ${card.color} flex items-center justify-center mb-3`}>
                <card.icon size={16} className="text-white" />
              </div>
              <div className="text-xl font-display font-bold text-white">
                {card.value} <span className="text-sm font-normal text-gray-400">{card.unit}</span>
              </div>
              <div className="text-xs text-gray-400 mt-1">{card.label}</div>
            </motion.div>
          ))}
        </div>

        {/* Charts */}
        <div className="grid lg:grid-cols-2 gap-6">
          <div className="bg-gray-900/60 border border-white/10 rounded-2xl p-5">
            <h3 className="font-display font-semibold text-white mb-4">30-Day Calorie Trend</h3>
            <WeeklyTrendChart data={trend} days={30} />
          </div>
          <div className="bg-gray-900/60 border border-white/10 rounded-2xl p-5">
            <h3 className="font-display font-semibold text-white mb-1 flex items-center gap-2">
              <AlertTriangle size={16} className="text-amber-400" /> Nutrient Deficiencies
            </h3>
            <p className="text-xs text-gray-500 mb-4">Based on last 7 days average vs RDI</p>
            <DeficiencyRadar data={deficiencies} />
          </div>
        </div>

        {/* Deficiency list */}
        {deficiencies?.deficient_nutrients?.length > 0 && (
          <div className="bg-red-500/5 border border-red-500/20 rounded-2xl p-5">
            <h3 className="font-semibold text-red-400 mb-3 flex items-center gap-2">
              <AlertTriangle size={16} /> Critical Deficiencies
            </h3>
            <div className="space-y-2">
              {deficiencies.deficient_nutrients.map((d: any) => (
                <div key={d.nutrient} className="flex items-center justify-between bg-white/5 rounded-xl px-4 py-2">
                  <span className="text-white text-sm font-medium">{d.nutrient}</span>
                  <div className="flex items-center gap-3">
                    <div className="w-32 h-1.5 bg-white/10 rounded-full overflow-hidden">
                      <div className="h-full bg-red-400 rounded-full" style={{ width: `${d.pct}%` }} />
                    </div>
                    <span className="text-red-400 text-xs font-bold">{d.pct}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
