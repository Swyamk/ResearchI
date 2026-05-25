import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCalories(cal: number | undefined): string {
  if (!cal) return "0";
  return cal >= 1000 ? `${(cal / 1000).toFixed(1)}k` : cal.toFixed(0);
}

export function formatGrams(g: number | undefined): string {
  if (!g) return "0g";
  return `${g.toFixed(1)}g`;
}

export function getPct(actual: number, target: number): number {
  if (!target || target === 0) return 0;
  return Math.min(100, Math.round((actual / target) * 100));
}

export function getColorForPct(pct: number): string {
  if (pct >= 90) return "text-emerald-400";
  if (pct >= 70) return "text-yellow-400";
  return "text-red-400";
}

export function getMacroColor(macro: "protein" | "carbs" | "fat"): string {
  return { protein: "#6366f1", carbs: "#f59e0b", fat: "#ec4899" }[macro];
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-IN", {
    weekday: "short", month: "short", day: "numeric",
  });
}

export function calculateBMI(weight: number, height: number): number {
  const heightM = height / 100;
  return Math.round((weight / (heightM * heightM)) * 10) / 10;
}

export function getBMICategory(bmi: number): { label: string; color: string } {
  if (bmi < 18.5) return { label: "Underweight", color: "text-blue-400" };
  if (bmi < 25) return { label: "Normal", color: "text-emerald-400" };
  if (bmi < 30) return { label: "Overweight", color: "text-yellow-400" };
  return { label: "Obese", color: "text-red-400" };
}
