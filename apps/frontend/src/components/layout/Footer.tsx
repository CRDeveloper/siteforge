import Link from "next/link";

const siteName = process.env.NEXT_PUBLIC_SITE_NAME || "SiteForge";

export function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer className="border-t border-[var(--color-border)] bg-[var(--color-surface)]">
      <div className="container section py-10">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="font-display text-xl text-[var(--color-text)]">
            {siteName}<span className="text-[var(--color-accent)]">.</span>
          </div>
          <div className="flex gap-6 text-sm text-[var(--color-muted)]">
            <Link href="/privacy" className="hover:text-[var(--color-text)] transition-colors">
              Privacy Policy
            </Link>
            <Link href="/terms" className="hover:text-[var(--color-text)] transition-colors">
              Terms of Service
            </Link>
          </div>
          <p className="text-sm text-[var(--color-muted)]">
            © {year} {siteName}. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
