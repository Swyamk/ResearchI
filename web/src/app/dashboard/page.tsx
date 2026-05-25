"use client";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Flame, Dumbbell, Wheat, Droplets, Target, TrendingUp, Award, Calendar } from "lucide-react";
import { CalorieRing } from "@/components/charts/CalorieRing";
import { MacroChart } from "@/components/charts/MacroChart";
import { WeeklyTrendChart } from "@/components/charts/WeeklyTrendChart";
import { RecommendationCards } from "@/components/dashboard/RecommendationCards";
import { MealTimeline } from "@/components/dashboard/MealTimeline";
import { api } from "@/lib/api";
import type { Metadata } from "next";

interface MetricCardProps {
  icon: React.ElementType;
  label: string;
  value: string;
  unit: string;
  target?: string;
  pct?: number;
  color: string;
  delay?: number;
}

function MetricCard({ icon: Icon, label, value, unit, target, pct, color, delay = 0 }: MetricCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.4 }}
      className="metric-card bg-gray-900/60 border border-white/10 p-5"
    >
      <div className="flex items-start justify-between mb-4">
        <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center`}>
          <Icon size={18} className="text-white" />
        </div>
        {pct !== undefined && (
          <span className="text-xs font-medium text-gray-400 bg-white/5 px-2 py-1 rounded-lg">
            {pct}%
          </span>
        )}
      </div>
      <div className="text-2xl font-display font-bold text-white">
        {value} <span className="text-sm font-normal text-gray-400">{unit}</span>
      </div>
      <div className="text-sm text-gray-400 mt-1">{label}</div>
      {target && <div className="text-xs text-gray-500 mt-1">Target: {target}</div>}
      {pct !== undefined && (
        <div className="nutrition-bar mt-3">
          <div
            className={`nutrition-bar-fill bg-gradient-to-r ${color}`}
            style={{ width: `${Math.min(100, pct)}%` }}
          />
        </div>
      )}
    </motion.div>
  );
}

export default function DashboardPage() {
  const [dashboard, setDashboard] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/analytics/dashboard")
      .then((res) => setDashboard(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const metrics = dashboard ? [
    { icon: Flame, label: "Calories", value: dashboard.today_calories?.toFixed(0) ?? "0", unit: "kcal",
      target: `${dashboard.calorie_target ?? "–"} kcal`, pct: dashboard.calorie_pct,
      color: "from-orange-500 to-amber-500" },
    { icon: Dumbbell, label: "Protein", value: dashboard.today_protein_g?.toFixed(1) ?? "0", unit: "g",
      color: "from-blue-500 to-indigo-500" },
    { icon: Wheat, label: "Carbs", value: dashboard.today_carbs_g?.toFixed(1) ?? "0", unit: "g",
      color: "from-yellow-500 to-orange-500" },
    { icon: Droplets, label: "Fat", value: dashboard.today_fat_g?.toFixed(1) ?? "0", unit: "g",
      color: "from-pink-500 to-rose-500" },
  ] : [];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-white">Good evening! 👋</h1>
          <p className="text-gray-400 text-sm mt-1">Here's your nutrition summary for today</p>
        </div>
        <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 rounded-xl px-4 py-2">
          <Award size={16} className="text-emerald-400" />
          <span className="text-emerald-400 text-sm font-medium">
            {dashboard?.streak?.current_streak ?? 0} Day Streak 🔥
          </span>
        </div>
      </motion.div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {loading
          ? Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-40 bg-gray-900/60 rounded-2xl shimmer-bg" />
            ))
          : metrics.map((m, i) => <MetricCard key={m.label} {...m} delay={i * 0.1} />)
        }
      </div>

      {/* Main Grid */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Calorie Ring + Macro Donut */}
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-gray-900/60 border border-white/10 rounded-2xl p-5">
            <h3 className="font-display font-semibold text-white mb-4 flex items-center gap-2">
              <Target size={16} className="text-emerald-400" /> Today's Goal
            </h3>
            <CalorieRing
              consumed={dashboard?.today_calories ?? 0}
              target={dashboard?.calorie_target ?? 2000}
            />
          </div>
          <div className="bg-gray-900/60 border border-white/10 rounded-2xl p-5">
            <h3 className="font-display font-semibold text-white mb-4">Macro Split</h3>
            <MacroChart data={dashboard?.macro_breakdown} />
          </div>
        </div>

        {/* Weekly Trend */}
        <div className="lg:col-span-2">
          <div className="bg-gray-900/60 border border-white/10 rounded-2xl p-5 h-full">
            <h3 className="font-display font-semibold text-white mb-4 flex items-center gap-2">
              <TrendingUp size={16} className="text-emerald-400" /> 7-Day Calorie Trend
            </h3>
            <WeeklyTrendChart data={dashboard?.weekly_trend} />
          </div>
        </div>
      </div>

      {/* Bottom Grid */}
      <div className="grid lg:grid-cols-2 gap-6">
        <div className="bg-gray-900/60 border border-white/10 rounded-2xl p-5">
          <h3 className="font-display font-semibold text-white mb-4 flex items-center gap-2">
            <Calendar size={16} className="text-emerald-400" /> Today's Meals
          </h3>
          <MealTimeline />
        </div>
        <div className="bg-gray-900/60 border border-white/10 rounded-2xl p-5">
          <h3 className="font-display font-semibold text-white mb-4 flex items-center gap-2">
            <Award size={16} className="text-emerald-400" /> Recommendations
          </h3>
          <RecommendationCards />
        </div>
      </div>
    </div>
  );
}
