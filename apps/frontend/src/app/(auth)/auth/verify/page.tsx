"use client";

export const dynamic = "force-dynamic";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { Alert, PageSpinner } from "@/components/ui/index";
import { CheckCircle, AlertCircle } from "lucide-react";
import Link from "next/link";

export default function VerifyPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const token = searchParams.get("token");
    const email = searchParams.get("email");

    if (!token || !email) {
      setStatus("error");
      setMessage("Missing verification token or email");
      return;
    }

    const verify = async () => {
      try {
        const result = await api.auth.verify(token, email);
        setStatus("success");
        setMessage(result.message || "Email verified successfully!");
        // Redirect to login after 3 seconds
        setTimeout(() => {
          router.push("/auth/login");
        }, 3000);
      } catch (err) {
        setStatus("error");
        if (err instanceof ApiError) {
          setMessage(err.message);
        } else {
          setMessage("Verification failed. Please try again or contact support.");
        }
      }
    };

    verify();
  }, [searchParams, router]);

  if (status === "loading") {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px]">
        <PageSpinner />
        <p className="mt-4 text-[var(--color-muted)]">Verifying your email...</p>
      </div>
    );
  }

  if (status === "success") {
    return (
      <div className="card animate-fade-up">
        <div className="text-center">
          <div className="flex justify-center mb-4">
            <CheckCircle className="w-16 h-16 text-green-500" />
          </div>
          <h1 className="font-display text-3xl text-[var(--color-text)] mb-2">
            Email Verified!
          </h1>
          <p className="text-[var(--color-muted)] mb-6">
            {message}
          </p>
          <div className="space-y-3">
            <p className="text-sm text-[var(--color-muted)]">
              Redirecting to login in 3 seconds...
            </p>
            <Link
              href="/auth/login"
              className="btn btn-primary inline-block"
            >
              Sign In Now
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card animate-fade-up">
      <div className="text-center">
        <div className="flex justify-center mb-4">
          <AlertCircle className="w-16 h-16 text-amber-500" />
        </div>
        <h1 className="font-display text-3xl text-[var(--color-text)] mb-2">
          Verification Failed
        </h1>
        <Alert type="error" className="mb-6">
          {message}
        </Alert>
        <div className="space-y-3">
          <p className="text-sm text-[var(--color-muted)] mb-4">
            If your link has expired, you can request a new one by signing up again.
          </p>
          <div className="flex flex-col gap-3 sm:flex-row justify-center">
            <Link
              href="/auth/register"
              className="btn btn-secondary"
            >
              Try Again
            </Link>
            <Link
              href="/auth/login"
              className="btn btn-outline"
            >
              Back to Login
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

