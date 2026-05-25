"use client";
import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard, UtensilsCrossed, BarChart2, Brain,
  User, Settings, LogOut, Menu, X, Sparkles, ChevronRight,
} from "lucide-react";
import { useAuthStore } from "@/store/authStore";
import { useRouter } from "next/navigation";

const NAV_ITEMS = [
  { href: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/meals", icon: UtensilsCrossed, label: "Log Meal" },
  { href: "/analytics", icon: BarChart2, label: "Analytics" },
  { href: "/ai-coach", icon: Brain, label: "AI Coach" },
  { href: "/profile", icon: User, label: "Profile" },
];

function NavItem({ href, icon: Icon, label, collapsed }: {
  href: string; icon: any; label: string; collapsed: boolean;
}) {
  const pathname = usePathname();
  const active = pathname === href || pathname.startsWith(href + "/");
  return (
    <Link href={href}
      className={`sidebar-item ${active ? "active" : "text-gray-400"}`}>
      <Icon size={18} className={active ? "text-emerald-400" : ""} />
      <AnimatePresence>
        {!collapsed && (
          <motion.span initial={{ opacity: 0, width: 0 }} animate={{ opacity: 1, width: "auto" }}
            exit={{ opacity: 0, width: 0 }} className="overflow-hidden whitespace-nowrap text-sm">
            {label}
          </motion.span>
        )}
      </AnimatePresence>
      {active && !collapsed && (
        <ChevronRight size={14} className="ml-auto text-emerald-400" />
      )}
    </Link>
  );
}

export function AppLayout({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const logout = useAuthStore((s) => s.logout);
  const user = useAuthStore((s) => s.user);
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push("/auth/login");
  };

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="p-4 flex items-center gap-3 border-b border-white/10">
        <div className="w-9 h-9 bg-nutri-gradient rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg shadow-emerald-500/20">
          <Sparkles size={16} className="text-white" />
        </div>
        <AnimatePresence>
          {!collapsed && (
            <motion.span initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="font-display font-bold text-white text-lg whitespace-nowrap">
              NutriMind
            </motion.span>
          )}
        </AnimatePresence>
      </div>

      {/* Nav */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map((item) => (
          <NavItem key={item.href} {...item} collapsed={collapsed} />
        ))}
      </nav>

      {/* User + logout */}
      <div className="p-3 border-t border-white/10 space-y-1">
        {user && !collapsed && (
          <div className="flex items-center gap-3 px-4 py-2.5 rounded-xl bg-white/5 mb-1">
            <div className="w-7 h-7 rounded-full bg-emerald-500 flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
              {user.full_name?.[0]?.toUpperCase() ?? "U"}
            </div>
            <div className="overflow-hidden">
              <div className="text-white text-xs font-medium truncate">{user.full_name}</div>
              <div className="text-gray-500 text-xs truncate">{user.email}</div>
            </div>
          </div>
        )}
        <button onClick={handleLogout}
          className="sidebar-item w-full text-gray-400 hover:text-red-400">
          <LogOut size={18} />
          {!collapsed && <span>Logout</span>}
        </button>
      </div>
    </div>
  );

  return (
    <div className="flex h-screen bg-gray-950 overflow-hidden">
      {/* Desktop Sidebar */}
      <motion.aside
        animate={{ width: collapsed ? 64 : 240 }}
        transition={{ duration: 0.3, ease: "easeInOut" }}
        className="hidden md:flex flex-col bg-gray-900/80 border-r border-white/10 relative flex-shrink-0"
      >
        <SidebarContent />
        {/* Collapse toggle */}
        <button onClick={() => setCollapsed(!collapsed)}
          className="absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 bg-gray-800 border border-white/20 rounded-full flex items-center justify-center text-gray-400 hover:text-white transition-colors z-10">
          <motion.div animate={{ rotate: collapsed ? 0 : 180 }} transition={{ duration: 0.2 }}>
            <ChevronRight size={12} />
          </motion.div>
        </button>
      </motion.aside>

      {/* Mobile Drawer */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              onClick={() => setMobileOpen(false)} className="fixed inset-0 bg-black/60 z-40 md:hidden" />
            <motion.aside initial={{ x: -280 }} animate={{ x: 0 }} exit={{ x: -280 }}
              transition={{ type: "spring", damping: 25 }}
              className="fixed left-0 top-0 bottom-0 w-64 bg-gray-900 border-r border-white/10 z-50 md:hidden">
              <SidebarContent />
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Topbar */}
        <header className="h-14 bg-gray-900/50 border-b border-white/10 flex items-center justify-between px-4 flex-shrink-0">
          <button onClick={() => setMobileOpen(true)} className="md:hidden text-gray-400 hover:text-white">
            <Menu size={20} />
          </button>
          <div className="flex items-center gap-2 md:ml-auto">
            <Link href="/meals"
              className="flex items-center gap-2 px-4 py-1.5 bg-emerald-500 hover:bg-emerald-400 text-white rounded-xl text-sm font-medium transition-all hover:shadow-lg hover:shadow-emerald-500/20">
              <UtensilsCrossed size={14} /> Log Meal
            </Link>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
