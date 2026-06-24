import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { Home, ChevronLeft } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[var(--color-bg)] flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        {/* 404 Number */}
        <div className="mb-8">
          <div className="font-display text-8xl font-bold text-primary/20 leading-none">
            404
          </div>
        </div>

        <h1 className="font-display text-3xl text-[var(--color-text)] mb-2">
          Page not found
        </h1>
        <p className="text-[var(--color-muted)] mb-8">
          The page you're looking for doesn't exist or has been moved. Let's get you back on track.
        </p>

        {/* Navigation Links */}
        <div className="flex flex-col gap-3">
          <Link href="/" className="btn btn-primary flex items-center justify-center gap-2">
            <Home className="w-4 h-4" />
            Go Home
          </Link>
          <button
            onClick={() => window.history.back()}
            className="btn btn-outline flex items-center justify-center gap-2"
          >
            <ChevronLeft className="w-4 h-4" />
            Go Back
          </button>
        </div>

        {/* Helpful Text */}
        <div className="mt-12 pt-8 border-t border-[var(--color-border)]">
          <p className="text-xs text-[var(--color-muted)]">
            If you think this is a mistake, please{" "}
            <Link href="/#contact" className="text-primary hover:underline">
              contact us
            </Link>
            .
          </p>
        </div>
      </div>
    </div>
  );
}

