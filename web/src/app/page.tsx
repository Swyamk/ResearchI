"use client";
import Link from "next/link";
import { motion } from "framer-motion";
import { Brain, Camera, ChartBar, Sparkles, Shield, Zap, ArrowRight, Star } from "lucide-react";

const features = [
  { icon: Camera, title: "AI Food Detection", desc: "YOLOv8 + SAM2 instantly detect and segment every food item in your photo", color: "from-emerald-500 to-teal-500" },
  { icon: Brain, title: "Gemini AI Coach", desc: "Chat with your personal Gemini 2.5 Pro nutrition coach anytime, anywhere", color: "from-violet-500 to-purple-500" },
  { icon: ChartBar, title: "Nutrition Analytics", desc: "Daily, weekly & monthly trends with smart deficiency detection", color: "from-orange-500 to-amber-500" },
  { icon: Sparkles, title: "Smart Recommendations", desc: "LightGBM-powered suggestions tailored to your goals and health conditions", color: "from-pink-500 to-rose-500" },
  { icon: Shield, title: "Health Conditions", desc: "Personalized for diabetes, PCOS, hypertension, thyroid and more", color: "from-blue-500 to-indigo-500" },
  { icon: Zap, title: "Instant Analysis", desc: "Get complete macro & micro nutrition breakdown in under 3 seconds", color: "from-yellow-500 to-lime-500" },
];

const stats = [
  { value: "256+", label: "Food Categories" },
  { value: "4", label: "AI Models" },
  { value: "3", label: "Nutrition Databases" },
  { value: "1M+", label: "Recipes Indexed" },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gray-950 text-white overflow-hidden">
      {/* Animated background */}
      <div className="fixed inset-0 -z-10">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-emerald-500/20 rounded-full blur-3xl animate-float" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-teal-500/15 rounded-full blur-3xl animate-float" style={{ animationDelay: "1s" }} />
        <div className="absolute top-1/2 left-1/2 w-64 h-64 bg-violet-500/10 rounded-full blur-3xl animate-float" style={{ animationDelay: "2s" }} />
      </div>

      {/* Navbar */}
      <nav className="sticky top-0 z-50 bg-gray-950/80 backdrop-blur-xl border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-nutri-gradient rounded-xl flex items-center justify-center text-white font-bold text-sm">N</div>
            <span className="font-display font-bold text-xl">NutriMind</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm text-gray-400">
            <Link href="#features" className="hover:text-white transition-colors">Features</Link>
            <Link href="#stats" className="hover:text-white transition-colors">Stats</Link>
            <Link href="/auth/login" className="hover:text-white transition-colors">Login</Link>
          </div>
          <Link href="/auth/register"
            className="px-5 py-2 bg-emerald-500 hover:bg-emerald-400 text-white rounded-xl text-sm font-semibold transition-all duration-200 hover:shadow-lg hover:shadow-emerald-500/25">
            Get Started
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-7xl mx-auto px-6 pt-24 pb-20 text-center">
        <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7 }}>
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-full text-emerald-400 text-sm font-medium mb-8">
            <Sparkles size={14} /> Powered by Gemini 2.5 Pro + YOLOv8
          </div>
          <h1 className="text-5xl md:text-7xl font-display font-bold mb-6 leading-tight">
            Your Personal
            <br />
            <span className="nutri-gradient-text">AI Nutrition</span>
            <br />
            Intelligence
          </h1>
          <p className="text-xl text-gray-400 max-w-3xl mx-auto mb-10 leading-relaxed">
            Snap a photo of any meal. Our 4-model AI stack detects every food item, estimates portions,
            calculates complete nutrition, and your Gemini AI coach gives personalized advice — all in seconds.
          </p>
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <Link href="/auth/register"
              className="flex items-center gap-2 px-8 py-4 bg-emerald-500 hover:bg-emerald-400 text-white rounded-2xl font-semibold text-lg transition-all duration-200 hover:shadow-2xl hover:shadow-emerald-500/30 hover:scale-105">
              Start Free <ArrowRight size={20} />
            </Link>
            <Link href="/dashboard"
              className="px-8 py-4 bg-white/10 hover:bg-white/20 border border-white/20 text-white rounded-2xl font-semibold text-lg transition-all duration-200">
              View Dashboard
            </Link>
          </div>
        </motion.div>

        {/* Stats bar */}
        <motion.div id="stats"
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4, duration: 0.6 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-20 max-w-3xl mx-auto">
          {stats.map((s) => (
            <div key={s.label} className="glass-card p-5 text-center">
              <div className="text-3xl font-display font-bold nutri-gradient-text">{s.value}</div>
              <div className="text-sm text-gray-400 mt-1">{s.label}</div>
            </div>
          ))}
        </motion.div>
      </section>

      {/* Features */}
      <section id="features" className="max-w-7xl mx-auto px-6 py-20">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-display font-bold mb-4">Everything You Need</h2>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto">
            A complete nutrition intelligence platform built with cutting-edge AI
          </p>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((f, i) => (
            <motion.div key={f.title}
              initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }} viewport={{ once: true }}
              className="glass-card p-6 hover:bg-white/10 transition-all duration-300 group hover:scale-[1.02]">
              <div className={`w-12 h-12 rounded-2xl bg-gradient-to-br ${f.color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                <f.icon size={22} className="text-white" />
              </div>
              <h3 className="font-display font-semibold text-lg mb-2">{f.title}</h3>
              <p className="text-gray-400 text-sm leading-relaxed">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-4xl mx-auto px-6 py-20 text-center">
        <div className="glass-card p-12 relative overflow-hidden">
          <div className="absolute inset-0 bg-nutri-gradient opacity-10 rounded-2xl" />
          <h2 className="text-4xl font-display font-bold mb-4 relative z-10">Ready to Transform Your Nutrition?</h2>
          <p className="text-gray-400 mb-8 relative z-10">Join thousands tracking smarter with NutriMind AI</p>
          <Link href="/auth/register"
            className="relative z-10 inline-flex items-center gap-2 px-8 py-4 bg-emerald-500 hover:bg-emerald-400 text-white rounded-2xl font-semibold text-lg transition-all hover:scale-105 hover:shadow-2xl hover:shadow-emerald-500/30">
            Start Your Journey <ArrowRight size={20} />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 py-8 text-center text-gray-500 text-sm">
        <p>© 2026 NutriMind. Built with ❤️ using Gemini 2.5 Pro, YOLOv8, SAM2 & EfficientNetV2</p>
      </footer>
    </div>
  );
}
