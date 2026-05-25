"use client";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { User, Activity, Target, Heart, Save, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { AppLayout } from "@/components/layout/AppLayout";
import toast from "react-hot-toast";

const GOALS = ["weight_loss","muscle_gain","maintenance","diabetes_management","heart_health","general_wellness"];
const ACTIVITY_LEVELS = ["sedentary","lightly_active","moderately_active","very_active","extremely_active"];
const HEALTH_CONDITIONS = ["diabetes_type1","diabetes_type2","hypertension","high_cholesterol","pcos","thyroid","none"];
const DIETARY = ["vegetarian","vegan","gluten_free","dairy_free","halal","kosher","none"];

export default function ProfilePage() {
  const [user, setUser] = useState<any>(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    age: "", gender: "male", height_cm: "", weight_kg: "",
    activity_level: "moderately_active", primary_goal: "maintenance",
    health_conditions: [] as string[], dietary_restrictions: [] as string[],
  });

  useEffect(() => {
    api.get("/users/me").then((r) => {
      setUser(r.data);
      if (r.data.profile) {
        const p = r.data.profile;
        setForm(prev => ({
          ...prev,
          age: p.age ?? "", gender: p.gender ?? "male",
          height_cm: p.height_cm ?? "", weight_kg: p.weight_kg ?? "",
          activity_level: p.activity_level ?? "moderately_active",
          primary_goal: p.primary_goal ?? "maintenance",
          health_conditions: p.health_conditions ?? [],
          dietary_restrictions: p.dietary_restrictions ?? [],
        }));
      }
    });
  }, []);

  const toggle = (field: "health_conditions" | "dietary_restrictions", val: string) => {
    setForm(prev => ({
      ...prev,
      [field]: prev[field].includes(val)
        ? prev[field].filter((v) => v !== val)
        : [...prev[field].filter((v) => v !== "none"), val],
    }));
  };

  const save = async () => {
    setSaving(true);
    try {
      await api.put("/users/me/profile", form);
      toast.success("Profile saved! Your nutrition targets have been updated.");
    } catch {
      toast.error("Save failed. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <AppLayout>
      <div className="p-6 max-w-4xl mx-auto space-y-6">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <h1 className="text-2xl font-display font-bold text-white">Health Profile</h1>
          <p className="text-gray-400 text-sm mt-1">Your profile powers personalized nutrition targets and AI recommendations</p>
        </motion.div>

        {/* Avatar + name */}
        {user && (
          <div className="flex items-center gap-4 bg-gray-900/60 border border-white/10 rounded-2xl p-5">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center text-2xl font-bold text-white">
              {user.full_name?.[0]?.toUpperCase() ?? "U"}
            </div>
            <div>
              <div className="font-display font-bold text-white text-lg">{user.full_name}</div>
              <div className="text-gray-400 text-sm">{user.email}</div>
            </div>
          </div>
        )}

        {/* Biometrics */}
        <Section title="Biometrics" icon={User}>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: "Age", key: "age", placeholder: "25", type: "number" },
              { label: "Height (cm)", key: "height_cm", placeholder: "170", type: "number" },
              { label: "Weight (kg)", key: "weight_kg", placeholder: "70", type: "number" },
            ].map(({ label, key, placeholder, type }) => (
              <div key={key}>
                <label className="text-xs text-gray-400 block mb-1">{label}</label>
                <input type={type} value={(form as any)[key]}
                  onChange={(e) => setForm(prev => ({ ...prev, [key]: e.target.value }))}
                  placeholder={placeholder}
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:border-emerald-500 transition-colors" />
              </div>
            ))}
            <div>
              <label className="text-xs text-gray-400 block mb-1">Gender</label>
              <select value={form.gender} onChange={(e) => setForm(prev => ({ ...prev, gender: e.target.value }))}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:border-emerald-500">
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>
        </Section>

        {/* Goals */}
        <Section title="Primary Goal" icon={Target}>
          <div className="flex flex-wrap gap-2">
            {GOALS.map((g) => (
              <button key={g} onClick={() => setForm(prev => ({ ...prev, primary_goal: g }))}
                className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all capitalize
                  ${form.primary_goal === g ? "bg-emerald-500 text-white" : "bg-white/5 border border-white/10 text-gray-400 hover:text-white"}`}>
                {g.replace(/_/g, " ")}
              </button>
            ))}
          </div>
        </Section>

        {/* Activity */}
        <Section title="Activity Level" icon={Activity}>
          <div className="flex flex-wrap gap-2">
            {ACTIVITY_LEVELS.map((a) => (
              <button key={a} onClick={() => setForm(prev => ({ ...prev, activity_level: a }))}
                className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all capitalize
                  ${form.activity_level === a ? "bg-blue-500 text-white" : "bg-white/5 border border-white/10 text-gray-400 hover:text-white"}`}>
                {a.replace(/_/g, " ")}
              </button>
            ))}
          </div>
        </Section>

        {/* Health Conditions */}
        <Section title="Health Conditions" icon={Heart}>
          <div className="flex flex-wrap gap-2">
            {HEALTH_CONDITIONS.map((c) => (
              <button key={c} onClick={() => toggle("health_conditions", c)}
                className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all capitalize
                  ${form.health_conditions.includes(c) ? "bg-rose-500 text-white" : "bg-white/5 border border-white/10 text-gray-400 hover:text-white"}`}>
                {c.replace(/_/g, " ")}
              </button>
            ))}
          </div>
        </Section>

        {/* Dietary Restrictions */}
        <Section title="Dietary Preferences" icon={Target}>
          <div className="flex flex-wrap gap-2">
            {DIETARY.map((d) => (
              <button key={d} onClick={() => toggle("dietary_restrictions", d)}
                className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all capitalize
                  ${form.dietary_restrictions.includes(d) ? "bg-teal-500 text-white" : "bg-white/5 border border-white/10 text-gray-400 hover:text-white"}`}>
                {d.replace(/_/g, " ")}
              </button>
            ))}
          </div>
        </Section>

        <button onClick={save} disabled={saving}
          className="w-full flex items-center justify-center gap-2 py-3.5 bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-white rounded-2xl font-semibold transition-all hover:shadow-lg hover:shadow-emerald-500/25">
          {saving ? <Loader2 size={18} className="animate-spin" /> : <Save size={18} />}
          {saving ? "Saving..." : "Save Profile & Recalculate Targets"}
        </button>
      </div>
    </AppLayout>
  );
}

function Section({ title, icon: Icon, children }: { title: string; icon: any; children: React.ReactNode }) {
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
      className="bg-gray-900/60 border border-white/10 rounded-2xl p-5">
      <h3 className="font-display font-semibold text-white mb-4 flex items-center gap-2">
        <Icon size={16} className="text-emerald-400" /> {title}
      </h3>
      {children}
    </motion.div>
  );
}
