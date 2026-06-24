"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/store";
import { api } from "@/lib/api";
import { PageSpinner } from "@/components/ui/index";
import {
  LayoutDashboard, Calendar, Users, Settings,
  Briefcase, Menu, X, LogOut,
} from "lucide-react";
import { clsx } from "clsx";

const siteName = process.env.NEXT_PUBLIC_SITE_NAME || "SiteForge";

const NAV = [
  { href: "/admin",              label: "Dashboard",    icon: LayoutDashboard },
  { href: "/admin/appointments", label: "Appointments", icon: Calendar },
  { href: "/admin/users",        label: "Users",        icon: Users },
  { href: "/admin/services",     label: "Services",     icon: Briefcase },
  { href: "/admin/settings",     label: "Settings",     icon: Settings },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isAdmin, logout } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) router.replace("/auth/login");
    else if (!isAdmin) router.replace("/appointments");
  }, [isAuthenticated, isAdmin, router]);

  if (!isAuthenticated || !isAdmin) return <PageSpinner />;

  const handleLogout = async () => {
    await api.auth.logout().catch(() => {});
    logout();
    router.push("/");
  };

  const Sidebar = ({ mobile = false }) => (
    <aside className={clsx(
      "flex flex-col bg-[var(--color-surface-raised)] border-r border-[var(--color-border)]",
      mobile ? "h-full" : "w-64 min-h-screen sticky top-0"
    )}>
      {/* Logo */}
      <div className="px-6 py-5 border-b border-[var(--color-border)]">
        <Link href="/" className="font-display text-xl text-[var(--color-text)]">
          {siteName}<span className="text-[var(--color-accent)]">.</span>
        </Link>
        <p className="text-xs text-[var(--color-muted)] mt-0.5">Admin Panel</p>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || (href !== "/admin" && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              onClick={() => setSidebarOpen(false)}
              className={clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded text-sm transition-all duration-150",
                active
                  ? "bg-primary text-white"
                  : "text-[var(--color-muted)] hover:text-[var(--color-text)] hover:bg-black/5 dark:hover:bg-white/5"
              )}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Logout */}
      <div className="px-3 pb-4 border-t border-[var(--color-border)] pt-4">
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-3 py-2.5 rounded text-sm text-[var(--color-muted)]
                     hover:text-red-600 hover:bg-red-50 transition-all duration-150 w-full"
        >
          <LogOut className="w-4 h-4" />
          Sign Out
        </button>
      </div>
    </aside>
  );

  return (
    <div className="flex min-h-screen bg-[var(--color-surface)]">
      {/* Desktop sidebar */}
      <div className="hidden md:block">
        <Sidebar />
      </div>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          <div className="w-64 animate-slide-in">
            <Sidebar mobile />
          </div>
          <div className="flex-1 bg-black/40" onClick={() => setSidebarOpen(false)} />
        </div>
      )}

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Mobile topbar */}
        <div className="md:hidden flex items-center justify-between px-4 py-3
                        border-b border-[var(--color-border)] bg-[var(--color-surface-raised)]">
          <button onClick={() => setSidebarOpen(true)} className="p-1">
            <Menu className="w-5 h-5 text-[var(--color-muted)]" />
          </button>
          <span className="font-display text-lg">{siteName}</span>
          <div className="w-7" />
        </div>

        <main className="flex-1 p-6 md:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
