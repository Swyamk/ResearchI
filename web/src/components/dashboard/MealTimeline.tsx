"use client";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Coffee, Sun, Moon, Dumbbell, Clock } from "lucide-react";
import { api } from "@/lib/api";

const MEAL_ICONS: Record<string, any> = {
  breakfast: Coffee, lunch: Sun, dinner: Moon,
  snack: Coffee, pre_workout: Dumbbell, post_workout: Dumbbell,
};

const MEAL_COLORS: Record<string, string> = {
  breakfast: "from-amber-500 to-orange-500",
  lunch: "from-emerald-500 to-teal-500",
  dinner: "from-blue-500 to-indigo-500",
  snack: "from-pink-500 to-rose-500",
  pre_workout: "from-violet-500 to-purple-500",
  post_workout: "from-cyan-500 to-blue-500",
};

export function MealTimeline() {
  const [meals, setMeals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const today = new Date().toISOString().slice(0, 10);
    api.get(`/meals?date_from=${today}&date_to=${today}&page_size=6`)
      .then((r) => setMeals(r.data.meals ?? []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="space-y-3">
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="h-14 bg-white/5 rounded-xl shimmer-bg" />
      ))}
    </div>
  );

  if (!meals.length) return (
    <div className="text-center py-8 text-gray-500">
      <Coffee size={28} className="mx-auto mb-2 opacity-30" />
      <p className="text-sm">No meals logged today</p>
      <p className="text-xs mt-1">Use the Log Meal button to get started</p>
    </div>
  );

  return (
    <div className="space-y-2">
      {meals.map((meal, i) => {
        const Icon = MEAL_ICONS[meal.meal_type] ?? Coffee;
        const colorClass = MEAL_COLORS[meal.meal_type] ?? "from-gray-500 to-gray-600";
        const time = new Date(meal.meal_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
        return (
          <motion.div key={meal.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.06 }}
            className="flex items-center gap-3 p-3 bg-white/5 hover:bg-white/10 rounded-xl transition-colors cursor-default">
            <div className={`w-9 h-9 rounded-xl bg-gradient-to-br ${colorClass} flex items-center justify-center flex-shrink-0`}>
              <Icon size={16} className="text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <span className="text-white text-sm font-medium capitalize">{meal.meal_type.replace("_", " ")}</span>
                <span className="text-orange-400 text-sm font-bold">{meal.total_calories?.toFixed(0)} kcal</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-500 mt-0.5">
                <Clock size={10} /> {time}
                <span>·</span>
                <span>{meal.food_items?.length ?? 0} item{meal.food_items?.length !== 1 ? "s" : ""}</span>
              </div>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}
