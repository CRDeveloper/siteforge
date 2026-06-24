"use client";

import { useEffect } from "react";
import Link from "next/link";
import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/Button";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log error for debugging
    console.error("Application error:", error);
  }, [error]);

  return (
    <html lang="en">
      <body>
        <div className="min-h-screen bg-[var(--color-bg)] flex items-center justify-center px-4">
          <div className="max-w-md w-full text-center">
            <div className="flex justify-center mb-6">
              <AlertTriangle className="w-16 h-16 text-amber-500" />
            </div>
            <h1 className="font-display text-3xl text-[var(--color-text)] mb-2">
              Something went wrong
            </h1>
            <p className="text-[var(--color-muted)] mb-6">
              We encountered an unexpected error. Please try again or go back to the homepage.
            </p>
            {process.env.NODE_ENV === "development" && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 
                            rounded-lg p-4 mb-6 text-left">
                <p className="text-xs font-mono text-red-700 dark:text-red-300 break-words">
                  {error.message}
                </p>
              </div>
            )}
            <div className="flex gap-3 flex-col">
              <Button onClick={reset} fullWidth size="lg" variant="primary">
                Try Again
              </Button>
              <Link href="/" className="btn btn-outline block">
                Go Home
              </Link>
            </div>
          </div>
        </div>
      </body>
    </html>
  );
}

