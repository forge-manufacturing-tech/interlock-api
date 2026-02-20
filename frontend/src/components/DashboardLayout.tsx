import { useState, useRef, useCallback, useEffect } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import {
  Boxes,
  GitBranch,
  Upload,
  Key,
  LogOut,
  Menu,
  X,
  Users,
  Shield,
  Sparkles,
} from "lucide-react";
import { useAuth } from "../lib/auth";
import AgentChat from "./AgentChat";

export default function DashboardLayout() {
  const { user, logout, isAdmin } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isAgentOpen, setIsAgentOpen] = useState(false); // Default to false as per user request to reduce "clutter"
  const location = useLocation();

  const showAgentSidebar =
    location.pathname === "/dashboard" ||
    location.pathname.startsWith("/dashboard/parts/");

  const navItems = [
    {
      to: "/dashboard",
      icon: Boxes,
      label: "Parts Explorer",
      end: true,
      show: true,
    },
  ];

  return (
    <div className="flex h-screen bg-surface text-text-primary">
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Left Sidebar */}
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
          {navItems
            .filter((item) => item.show)
            .map(({ to, icon: Icon, label, end }) => (
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

      {/* Main Content Area */}
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
            <span className="text-sm text-text-secondary">{user?.email}</span>
            <button
              onClick={logout}
              className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm text-text-muted transition-colors hover:bg-white/5 hover:text-text-primary"
            >
              <LogOut size={16} />
              Logout
            </button>

            {showAgentSidebar && (
              <button
                onClick={() => setIsAgentOpen(!isAgentOpen)}
                className={`flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-all ${isAgentOpen
                    ? "bg-primary text-white shadow-md hover:bg-primary/90"
                    : "bg-surface-light border border-border text-text-secondary hover:text-primary hover:border-primary"
                  }`}
              >
                <Sparkles size={16} className={isAgentOpen ? "animate-pulse" : ""} />
                {isAgentOpen ? "Agent Active" : "Ask Agent"}
              </button>
            )}
          </div>
        </header>

        {showAgentSidebar && isAgentOpen ? (
          <ResizableLayout
            mainContent={<Outlet />}
            sidebar={<AgentChat className="h-full" />}
          />
        ) : (
          <div className={`flex-1 overflow-auto scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent ${location.pathname.startsWith('/dashboard/parts/') ? '' : 'p-6'}`}>
            <Outlet />
          </div>
        )}
      </div>
    </div>
  );
}

function ResizableLayout({
  mainContent,
  sidebar,
}: {
  mainContent: React.ReactNode;
  sidebar: React.ReactNode;
}) {
  const [sidebarWidth, setSidebarWidth] = useState(35); // percentage
  const containerRef = useRef<HTMLDivElement>(null);
  const isDragging = useRef(false);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    isDragging.current = true;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  }, []);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isDragging.current || !containerRef.current) return;

    const container = containerRef.current;
    const rect = container.getBoundingClientRect();
    const x = e.clientX - rect.left;
    // Invert: dragging right increases sidebar, dragging left decreases it
    const percentage = 100 - (x / rect.width) * 100;

    // Clamp between 30% and 60%
    const clamped = Math.min(Math.max(percentage, 30), 60);
    setSidebarWidth(clamped);
  }, []);

  const handleMouseUp = useCallback(() => {
    isDragging.current = false;
    document.body.style.cursor = "";
    document.body.style.userSelect = "";
  }, []);

  useEffect(() => {
    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [handleMouseMove, handleMouseUp]);

  return (
    <div ref={containerRef} className="flex flex-1 overflow-hidden">
      <div
        className="h-full overflow-hidden"
        style={{ width: `${100 - sidebarWidth}%`, flexShrink: 0 }}
      >
        {mainContent}
      </div>
      <div
        className="w-1 flex-shrink-0 cursor-col-resize bg-border hover:bg-primary transition-colors"
        onMouseDown={handleMouseDown}
      />
      <div
        className="h-full overflow-hidden border-l border-border bg-surface-light"
        style={{ width: `${sidebarWidth}%`, flexShrink: 0 }}
      >
        {sidebar}
      </div>
    </div>
  );
}
