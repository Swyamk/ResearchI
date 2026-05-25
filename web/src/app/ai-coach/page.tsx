"use client";
import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Bot, Sparkles, RefreshCw, Copy, BookOpen, Zap } from "lucide-react";
import { api } from "@/lib/api";
import toast from "react-hot-toast";
import { AppLayout } from "@/components/layout/AppLayout";

interface Message { role: "user" | "model"; content: string; timestamp: Date; }

const QUICK_PROMPTS = [
  "What did I eat today and was it healthy?",
  "How can I increase my protein intake?",
  "Give me a healthy meal plan for tomorrow",
  "Am I meeting my daily nutrition goals?",
  "What foods should I avoid for my goals?",
  "Generate my weekly nutrition summary",
];

export default function AiCoachPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "model",
      content: "👋 Hi! I'm your NutriMind AI Coach powered by **Gemini 2.5 Pro**.\n\nI can help you:\n• Analyze your meals and nutrition\n• Answer questions about healthy eating\n• Create personalized meal plans\n• Track your goals and progress\n\nWhat would you like to know today?",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => crypto.randomUUID());
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (text?: string) => {
    const msg = text || input.trim();
    if (!msg || loading) return;
    setInput("");

    const userMsg: Message = { role: "user", content: msg, timestamp: new Date() };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await api.post("/ai-coach/chat", { message: msg, session_id: sessionId });
      const aiMsg: Message = { role: "model", content: res.data.response, timestamp: new Date() };
      setMessages((prev) => [...prev, aiMsg]);
    } catch {
      setMessages((prev) => [...prev, {
        role: "model",
        content: "I'm having trouble connecting. Please try again in a moment.",
        timestamp: new Date(),
      }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const copyMessage = (content: string) => {
    navigator.clipboard.writeText(content);
    toast.success("Copied to clipboard");
  };

  const renderContent = (content: string) => {
    return content
      .split("\n")
      .map((line, i) => {
        const formatted = line
          .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
          .replace(/\*(.*?)\*/g, "<em>$1</em>")
          .replace(/^•\s/, "• ");
        return <p key={i} dangerouslySetInnerHTML={{ __html: formatted || "&nbsp;" }} className="leading-relaxed" />;
      });
  };

  return (
    <AppLayout>
      <div className="flex flex-col h-[calc(100vh-64px)] max-w-4xl mx-auto p-4 gap-4">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between bg-gray-900/60 border border-white/10 rounded-2xl p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
              <Bot size={20} className="text-white" />
            </div>
            <div>
              <div className="font-display font-semibold text-white flex items-center gap-2">
                NutriMind AI Coach <Sparkles size={14} className="text-violet-400" />
              </div>
              <div className="text-xs text-emerald-400 flex items-center gap-1">
                <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse" />
                Powered by Gemini 2.5 Pro
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => api.post("/ai-coach/summary/daily").then(r => {
              setMessages(prev => [...prev, { role: "model", content: r.data.summary, timestamp: new Date() }]);
            })} className="flex items-center gap-1.5 px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-xs text-gray-300 transition-colors">
              <BookOpen size={12} /> Daily Summary
            </button>
            <button onClick={() => setMessages([messages[0]])}
              className="p-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-gray-400 transition-colors">
              <RefreshCw size={14} />
            </button>
          </div>
        </motion.div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto space-y-4 pr-1">
          <AnimatePresence>
            {messages.map((msg, i) => (
              <motion.div key={i}
                initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} group`}>
                {msg.role === "model" && (
                  <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center mr-2 flex-shrink-0 mt-1">
                    <Bot size={14} className="text-white" />
                  </div>
                )}
                <div className={msg.role === "user" ? "chat-bubble-user" : "chat-bubble-ai"}>
                  <div className="text-sm space-y-1">{renderContent(msg.content)}</div>
                  <div className="flex items-center justify-between mt-2 pt-2 border-t border-white/10">
                    <span className="text-xs text-gray-500">
                      {msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </span>
                    {msg.role === "model" && (
                      <button onClick={() => copyMessage(msg.content)}
                        className="opacity-0 group-hover:opacity-100 p-1 hover:text-emerald-400 text-gray-500 transition-all">
                        <Copy size={12} />
                      </button>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Typing indicator */}
          {loading && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
                <Bot size={14} className="text-white" />
              </div>
              <div className="chat-bubble-ai">
                <div className="flex gap-1 py-1">
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                </div>
              </div>
            </motion.div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Quick prompts */}
        <div className="flex gap-2 overflow-x-auto pb-1">
          {QUICK_PROMPTS.slice(0, 3).map((p) => (
            <button key={p} onClick={() => sendMessage(p)}
              className="flex-shrink-0 px-3 py-1.5 bg-white/5 hover:bg-emerald-500/10 border border-white/10 hover:border-emerald-500/30 rounded-xl text-xs text-gray-400 hover:text-emerald-400 transition-all whitespace-nowrap">
              {p}
            </button>
          ))}
        </div>

        {/* Input */}
        <div className="flex gap-3 bg-gray-900/80 border border-white/10 rounded-2xl p-3">
          <input ref={inputRef} value={input} onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
            placeholder="Ask your AI nutrition coach anything..."
            className="flex-1 bg-transparent text-white placeholder-gray-500 text-sm outline-none" />
          <button onClick={() => sendMessage()} disabled={!input.trim() || loading}
            className="w-10 h-10 rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center transition-all hover:scale-105">
            <Send size={16} className="text-white" />
          </button>
        </div>
      </div>
    </AppLayout>
  );
}
