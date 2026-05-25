"use client";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Lightbulb, Heart, TrendingUp, Star, ChevronRight } from "lucide-react";
import { api } from "@/lib/api";

const ICONS: Record<string, any> = {
  health_condition: Heart,
  goal: TrendingUp,
  deficiency: Lightbulb,
  calorie_low: TrendingUp,
  calorie_high: TrendingUp,
  consistency: Star,
};

const COLORS: Record<string, string> = {
  high: "border-red-500/30 bg-red-500/5",
  medium: "border-amber-500/30 bg-amber-500/5",
  low: "border-emerald-500/30 bg-emerald-500/5",
};

const ICON_COLORS: Record<string, string> = {
  high: "text-red-400 bg-red-500/10",
  medium: "text-amber-400 bg-amber-500/10",
  low: "text-emerald-400 bg-emerald-500/10",
};

export function RecommendationCards() {
  const [recs, setRecs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/recommendations/today?limit=4")
      .then((r) => setRecs(r.data.recommendations))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="space-y-2">
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="h-16 bg-white/5 rounded-xl shimmer-bg" />
      ))}
    </div>
  );

  if (!recs.length) return (
    <p className="text-gray-500 text-sm text-center py-6">Complete your profile to get personalized recommendations</p>
  );

  return (
    <div className="space-y-2">
      {recs.map((rec, i) => {
        const Icon = ICONS[rec.type] ?? Lightbulb;
        const priority = rec.priority ?? "low";
        return (
          <motion.div key={i} initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.08 }}
            className={`flex items-start gap-3 p-3 rounded-xl border ${COLORS[priority]}`}>
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${ICON_COLORS[priority]}`}>
              <Icon size={14} />
            </div>
            <p className="text-xs text-gray-300 leading-relaxed flex-1">{rec.message}</p>
          </motion.div>
        );
      })}
    </div>
  );
}
