import Link from "next/link";

const siteName = process.env.NEXT_PUBLIC_SITE_NAME || "SiteForge";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col bg-[var(--color-surface)]">
      {/* Minimal header */}
      <header className="py-6 px-4 border-b border-[var(--color-border)]">
        <div className="max-w-md mx-auto">
          <Link href="/" className="font-display text-2xl text-[var(--color-text)]">
            {siteName}<span className="text-[var(--color-accent)]">.</span>
          </Link>
        </div>
      </header>

      {/* Centered content */}
      <main className="flex-1 flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-md">{children}</div>
      </main>

      <footer className="py-6 text-center text-xs text-[var(--color-muted)]">
        © {new Date().getFullYear()} {siteName}
      </footer>
    </div>
  );
}
