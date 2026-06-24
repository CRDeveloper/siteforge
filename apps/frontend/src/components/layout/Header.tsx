"use client";

import { useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { Menu, X, Moon, Sun, Globe } from "lucide-react";
import { useAuthStore } from "@/lib/store";
import { api } from "@/lib/api";
import { useDarkMode } from "./ThemeProvider";

const siteName = process.env.NEXT_PUBLIC_SITE_NAME || "SiteForge";
const supportedLangs: string[] = JSON.parse(
  process.env.NEXT_PUBLIC_SUPPORTED_LANGS || '["en"]'
);

export function Header() {
  const t = useTranslations("nav");
  const { user, isAuthenticated, isAdmin, logout } = useAuthStore();
  const { toggle: toggleDark } = useDarkMode();
  const [menuOpen, setMenuOpen] = useState(false);
  const [darkMode, setDarkMode] = useState(false);

  const handleLogout = async () => {
    await api.auth.logout().catch(() => {});
    logout();
    window.location.href = "/";
  };

  const handleDarkToggle = () => {
    toggleDark();
    setDarkMode((d) => !d);
  };

  const switchLang = (lang: string) => {
    document.cookie = `sf_lang=${lang};path=/;max-age=31536000`;
    window.location.reload();
  };

  const navLinks = [
    { href: "/#services", label: t("services") },
    { href: "/#about", label: t("about") },
    { href: "/#contact", label: t("contact") },
  ];

  return (
    <header className="sticky top-0 z-50 bg-[var(--color-surface)]/90 backdrop-blur-sm
                       border-b border-[var(--color-border)] h-[var(--header-height)]">
      <div className="container flex items-center justify-between h-full px-4">

        {/* Logo */}
        <Link href="/" className="font-display text-2xl text-[var(--color-text)] tracking-tight">
          {siteName}
          <span className="text-[var(--color-accent)]">.</span>
        </Link>

        {/* Desktop Nav */}
        <nav className="hidden md:flex items-center gap-8">
          {navLinks.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className="text-sm text-[var(--color-muted)] hover:text-[var(--color-text)]
                         transition-colors duration-150"
            >
              {label}
            </Link>
          ))}
        </nav>

        {/* Desktop Actions */}
        <div className="hidden md:flex items-center gap-3">
          {/* Language switcher */}
          {supportedLangs.length > 1 && (
            <div className="relative group">
              <button className="btn-ghost p-2 rounded-full" aria-label="Switch language">
                <Globe className="w-4 h-4 text-[var(--color-muted)]" />
              </button>
              <div className="absolute right-0 top-full mt-1 bg-[var(--color-surface-raised)]
                              border border-[var(--color-border)] rounded shadow-elevated
                              opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none
                              group-hover:pointer-events-auto min-w-[80px]">
                {supportedLangs.map((lang) => (
                  <button
                    key={lang}
                    onClick={() => switchLang(lang)}
                    className="block w-full text-left px-4 py-2 text-sm uppercase
                               hover:bg-primary/10 text-[var(--color-muted)]
                               hover:text-[var(--color-text)] transition-colors"
                  >
                    {lang}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Dark mode toggle */}
          <button
            onClick={handleDarkToggle}
            className="btn-ghost p-2 rounded-full"
            aria-label="Toggle dark mode"
          >
            {darkMode
              ? <Sun className="w-4 h-4 text-[var(--color-muted)]" />
              : <Moon className="w-4 h-4 text-[var(--color-muted)]" />}
          </button>

          {isAuthenticated ? (
            <>
              {isAdmin && (
                <Link href="/admin" className="btn-ghost text-sm">
                  {t("admin")}
                </Link>
              )}
              <Link href="/appointments" className="btn-ghost text-sm">
                {t("dashboard")}
              </Link>
              <button onClick={handleLogout} className="btn-ghost text-sm">
                {t("logout")}
              </button>
            </>
          ) : (
            <>
              <Link href="/auth/login" className="btn-ghost text-sm">
                {t("login")}
              </Link>
              <Link href="/book" className="btn-primary text-sm">
                {t("book")}
              </Link>
            </>
          )}
        </div>

        {/* Mobile menu toggle */}
        <button
          className="md:hidden btn-ghost p-2"
          onClick={() => setMenuOpen((o) => !o)}
          aria-label="Toggle menu"
        >
          {menuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="md:hidden border-t border-[var(--color-border)]
                        bg-[var(--color-surface)] px-4 pb-4 space-y-1 animate-fade-in">
          {navLinks.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              onClick={() => setMenuOpen(false)}
              className="block py-3 text-[var(--color-muted)] hover:text-[var(--color-text)]
                         border-b border-[var(--color-border)] text-sm"
            >
              {label}
            </Link>
          ))}
          <div className="pt-3 flex flex-col gap-2">
            {isAuthenticated ? (
              <>
                <Link href="/appointments" className="btn-outline text-sm justify-center">
                  {t("dashboard")}
                </Link>
                <button onClick={handleLogout} className="btn-ghost text-sm">
                  {t("logout")}
                </button>
              </>
            ) : (
              <>
                <Link href="/auth/login" className="btn-outline text-sm justify-center">
                  {t("login")}
                </Link>
                <Link href="/book" className="btn-primary text-sm justify-center">
                  {t("book")}
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
