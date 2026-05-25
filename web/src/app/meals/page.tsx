"use client";
import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import { useDropzone } from "react-dropzone";
import { Upload, Camera, Clock, Trash2, ChevronRight, Loader2, CheckCircle } from "lucide-react";
import { api } from "@/lib/api";
import { AppLayout } from "@/components/layout/AppLayout";
import toast from "react-hot-toast";
import Image from "next/image";

const MEAL_TYPES = ["breakfast", "lunch", "dinner", "snack", "pre_workout", "post_workout"];

export default function MealsPage() {
  const [uploading, setUploading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [mealType, setMealType] = useState("lunch");
  const [meals, setMeals] = useState<any[]>([]);
  const [loadingMeals, setLoadingMeals] = useState(false);

  const onDrop = useCallback(async (files: File[]) => {
    const file = files[0];
    if (!file) return;
    setPreview(URL.createObjectURL(file));
    setAnalysisResult(null);
    setUploading(true);

    const formData = new FormData();
    formData.append("image", file);
    formData.append("meal_type", mealType);

    try {
      const res = await api.post("/meals/analyze", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setAnalysisResult(res.data);
      toast.success("Meal analyzed successfully!");
    } catch {
      toast.error("Analysis failed. Please try again.");
    } finally {
      setUploading(false);
    }
  }, [mealType]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: { "image/*": [".jpg", ".jpeg", ".png", ".webp"] }, maxFiles: 1,
  });

  return (
    <AppLayout>
      <div className="p-6 max-w-6xl mx-auto space-y-6">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <h1 className="text-2xl font-display font-bold text-white">Log a Meal</h1>
          <p className="text-gray-400 text-sm mt-1">Upload a food photo for AI-powered nutrition analysis</p>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-6">
          {/* Upload Panel */}
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 }}
            className="space-y-4">
            {/* Meal type selector */}
            <div className="bg-gray-900/60 border border-white/10 rounded-2xl p-4">
              <label className="text-sm text-gray-400 font-medium mb-3 block">Meal Type</label>
              <div className="flex flex-wrap gap-2">
                {MEAL_TYPES.map((type) => (
                  <button key={type} onClick={() => setMealType(type)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all capitalize
                      ${mealType === type
                        ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/20"
                        : "bg-white/5 border border-white/10 text-gray-400 hover:text-white"}`}>
                    {type.replace("_", " ")}
                  </button>
                ))}
              </div>
            </div>

            {/* Dropzone */}
            <div {...getRootProps()}
              className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-300
                ${isDragActive ? "border-emerald-500 bg-emerald-500/10" : "border-white/20 hover:border-emerald-500/50 hover:bg-white/5"}`}>
              <input {...getInputProps()} />
              {preview ? (
                <div className="relative h-48 rounded-xl overflow-hidden">
                  <Image src={preview} alt="Meal preview" fill className="object-cover" />
                  {uploading && (
                    <div className="absolute inset-0 bg-black/60 flex items-center justify-center">
                      <Loader2 size={32} className="text-emerald-400 animate-spin" />
                    </div>
                  )}
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="w-16 h-16 mx-auto rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                    <Upload size={24} className="text-emerald-400" />
                  </div>
                  <div>
                    <p className="text-white font-medium">Drop your food photo here</p>
                    <p className="text-gray-400 text-sm">or click to select · JPG, PNG, WebP · Max 20MB</p>
                  </div>
                  <div className="flex items-center justify-center gap-2 text-gray-500 text-xs">
                    <Camera size={12} /> Powered by YOLOv8 + SAM2 + EfficientNetV2
                  </div>
                </div>
              )}
            </div>
          </motion.div>

          {/* Analysis Result */}
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}>
            {analysisResult ? (
              <div className="bg-gray-900/60 border border-white/10 rounded-2xl p-5 space-y-4">
                <div className="flex items-center gap-2 text-emerald-400">
                  <CheckCircle size={18} />
                  <span className="font-semibold">Analysis Complete</span>
                  <span className="text-xs text-gray-500 ml-auto">{analysisResult.processing_time_ms}ms</span>
                </div>

                {/* Totals */}
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { label: "Calories", value: `${analysisResult.total_calories?.toFixed(0)} kcal`, color: "text-orange-400" },
                    { label: "Protein", value: `${analysisResult.total_protein_g?.toFixed(1)}g`, color: "text-blue-400" },
                    { label: "Carbs", value: `${analysisResult.total_carbs_g?.toFixed(1)}g`, color: "text-yellow-400" },
                    { label: "Fat", value: `${analysisResult.total_fat_g?.toFixed(1)}g`, color: "text-pink-400" },
                  ].map(({ label, value, color }) => (
                    <div key={label} className="bg-white/5 rounded-xl p-3">
                      <div className={`text-lg font-bold ${color}`}>{value}</div>
                      <div className="text-xs text-gray-400">{label}</div>
                    </div>
                  ))}
                </div>

                {/* Detected Items */}
                <div>
                  <p className="text-sm text-gray-400 font-medium mb-2">Detected Food Items</p>
                  <div className="space-y-2">
                    {analysisResult.detected_items?.map((item: any, i: number) => (
                      <div key={i} className="flex items-center justify-between bg-white/5 rounded-xl px-3 py-2">
                        <div>
                          <span className="text-white text-sm capitalize font-medium">{item.name}</span>
                          <span className="text-gray-400 text-xs ml-2">{item.portion_g}g</span>
                        </div>
                        <div className="text-right">
                          <span className="text-orange-400 text-sm font-bold">{item.calories?.toFixed(0)}</span>
                          <span className="text-gray-500 text-xs ml-1">kcal</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Suggestions */}
                {analysisResult.suggestions?.length > 0 && (
                  <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-3 text-sm text-emerald-300">
                    💡 {analysisResult.suggestions[0]}
                  </div>
                )}
              </div>
            ) : (
              <div className="h-full bg-gray-900/30 border border-white/5 rounded-2xl flex items-center justify-center min-h-[300px]">
                <div className="text-center text-gray-500">
                  <Camera size={32} className="mx-auto mb-3 opacity-30" />
                  <p className="text-sm">Upload a food photo to see analysis</p>
                </div>
              </div>
            )}
          </motion.div>
        </div>
      </div>
    </AppLayout>
  );
}
