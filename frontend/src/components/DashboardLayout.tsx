import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import {
  Boxes,
  GitBranch,
  Upload,
  MessageSquare,
  Key,
  LogOut,
  Menu,
  X,
  Users,
  Shield,
} from "lucide-react";
import { useAuth } from "../lib/auth";

export default function DashboardLayout() {
  const { user, logout, isAdmin } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const navItems = [
    { to: "/dashboard", icon: Boxes, label: "Parts Explorer", end: true, show: true },
    { to: "/dashboard/trees", icon: GitBranch, label: "Tree Visualizer", show: true },
    { to: "/dashboard/ingest", icon: Upload, label: "BOM Ingest", show: true },
    { to: "/dashboard/agent", icon: MessageSquare, label: "Agent Chat", show: true },
    { to: "/dashboard/api-keys", icon: Key, label: "API Keys", show: true },
    { to: "/dashboard/admin", icon: Users, label: "User Management", show: isAdmin },
  ];

  return (
    <div className="flex h-screen bg-surface text-text-primary">
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-60 flex-col border-r border-border bg-surface-light transition-transform lg:static lg:translate-x-0 ${sidebarOpen ? "translate-x-0" : "-translate-x-full"
          }`}
      >
        <div className="flex h-14 items-center justify-between border-b border-border px-4">
          <span className="font-mono text-lg font-bold uppercase tracking-widest text-primary">
            INTERLOCK
          </span>
          <button
            onClick={() => setSidebarOpen(false)}
            className="rounded-md p-1 text-text-muted hover:text-text-primary lg:hidden"
          >
            <X size={20} />
          </button>
        </div>

        <nav className="flex-1 space-y-1 p-3">
          {navItems.filter(item => item.show).map(({ to, icon: Icon, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors no-underline ${isActive
                  ? "border-l-2 border-primary bg-white/5 text-primary"
                  : "border-l-2 border-transparent text-text-secondary hover:bg-white/5 hover:text-text-primary"
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-14 items-center justify-between border-b border-border bg-surface-light px-4">
          <button
            onClick={() => setSidebarOpen(true)}
            className="rounded-md p-1 text-text-muted hover:text-text-primary lg:hidden"
          >
            <Menu size={20} />
          </button>
          <span className="hidden font-mono text-lg font-bold uppercase tracking-widest text-primary lg:block">
            Dashboard
          </span>
          <div className="flex items-center gap-4">
            {isAdmin && (
              <span className="flex items-center gap-1 rounded-full border border-primary/40 bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary">
                <Shield size={12} />
                Admin
              </span>
            )}
            <span className="text-sm text-text-secondary">
              {user?.email}
            </span>
            <button
              onClick={logout}
              className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm text-text-muted transition-colors hover:bg-white/5 hover:text-text-primary"
            >
              <LogOut size={16} />
              Logout
            </button>
          </div>
        </header>

        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
