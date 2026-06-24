"use client";

import { useEffect } from "react";

interface Theme {
  primaryColor?: string;
  accentColor?: string;
  backgroundColor?: string;
  textColor?: string;
  mode?: "light" | "dark";
  fontDisplay?: string;
  fontBody?: string;
}

interface ThemeProviderProps {
  theme: Theme;
  children: React.ReactNode;
}

function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16),
      }
    : null;
}

function lighten(hex: string, amount: number): string {
  const rgb = hexToRgb(hex);
  if (!rgb) return hex;
  return `#${Math.min(255, rgb.r + amount).toString(16).padStart(2, "0")}${Math.min(255, rgb.g + amount).toString(16).padStart(2, "0")}${Math.min(255, rgb.b + amount).toString(16).padStart(2, "0")}`;
}

function darken(hex: string, amount: number): string {
  const rgb = hexToRgb(hex);
  if (!rgb) return hex;
  return `#${Math.max(0, rgb.r - amount).toString(16).padStart(2, "0")}${Math.max(0, rgb.g - amount).toString(16).padStart(2, "0")}${Math.max(0, rgb.b - amount).toString(16).padStart(2, "0")}`;
}

export function ThemeProvider({ theme, children }: ThemeProviderProps) {
  useEffect(() => {
    const root = document.documentElement;
    const primary = theme.primaryColor || "#5c7a6e";
    const accent = theme.accentColor || "#c9a96e";
    const bg = theme.backgroundColor || "#faf7f4";
    const text = theme.textColor || "#2c2c2c";

    root.style.setProperty("--color-primary", primary);
    root.style.setProperty("--color-primary-light", lighten(primary, 30));
    root.style.setProperty("--color-primary-dark", darken(primary, 25));
    root.style.setProperty("--color-accent", accent);
    root.style.setProperty("--color-surface", bg);
    root.style.setProperty("--color-text", text);

    if (theme.fontDisplay) {
      root.style.setProperty("--font-display", `"${theme.fontDisplay}"`);
    }
    if (theme.fontBody) {
      root.style.setProperty("--font-body", `"${theme.fontBody}"`);
    }

    // Apply dark mode class
    if (theme.mode === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
  }, [theme]);

  return <>{children}</>;
}

// Hook for toggling dark mode at runtime
export function useDarkMode() {
  const toggle = () => {
    document.documentElement.classList.toggle("dark");
    const isDark = document.documentElement.classList.contains("dark");
    localStorage.setItem("sf_dark_mode", isDark ? "1" : "0");
  };
  return { toggle };
}
