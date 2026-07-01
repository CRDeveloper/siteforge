"use client";

export const dynamic = "force-dynamic";

import { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { api, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Input, FormField, Alert } from "@/components/ui/index";

const schema = z.object({ email: z.string().email("Please enter a valid email") });
type FormData = z.infer<typeof schema>;

export default function ForgotPasswordPage() {
  const [sent, setSent] = useState(false);
  const [serverError, setServerError] = useState("");

  const { register, handleSubmit, formState: { errors, isSubmitting } } =
    useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    setServerError("");
    try {
      await api.auth.forgotPassword(data.email);
      setSent(true);
    } catch {
      setServerError("Something went wrong. Please try again.");
    }
  };

  if (sent) {
    return (
      <div className="card text-center animate-fade-up">
        <div className="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center mx-auto mb-6">
          <span className="text-3xl">📬</span>
        </div>
        <h1 className="font-display text-3xl text-[var(--color-text)] mb-2">Check your inbox</h1>
        <p className="text-[var(--color-muted)] mb-6">
          If an account exists for that email, we sent a password reset link.
          Check your spam folder if you don&apos;t see it.
        </p>
        <Link href="/auth/login" className="btn-outline w-full justify-center inline-flex">
          Back to Sign In
        </Link>
      </div>
    );
  }

  return (
    <div className="card animate-fade-up">
      <h1 className="font-display text-3xl text-[var(--color-text)] mb-1">Reset password</h1>
      <p className="text-[var(--color-muted)] text-sm mb-8">
        Enter your email and we&apos;ll send you a reset link.
      </p>

      {serverError && <div className="mb-6"><Alert type="error">{serverError}</Alert></div>}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        <FormField label="Email address" error={errors.email?.message} required>
          <Input type="email" placeholder="you@example.com" {...register("email")} />
        </FormField>
        <Button type="submit" fullWidth loading={isSubmitting} size="lg">
          Send Reset Link
        </Button>
      </form>

      <p className="text-center text-sm text-[var(--color-muted)] mt-6">
        <Link href="/auth/login" className="text-primary hover:underline">
          ← Back to Sign In
        </Link>
      </p>
    </div>
  );
}
