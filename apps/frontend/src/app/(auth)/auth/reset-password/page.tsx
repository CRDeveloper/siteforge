"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { api, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Input, FormField, Alert } from "@/components/ui/index";

const schema = z.object({
  password: z.string().min(8, "Password must be at least 8 characters"),
  confirm:  z.string(),
}).refine((d) => d.password === d.confirm, {
  message: "Passwords do not match",
  path: ["confirm"],
});

type FormData = z.infer<typeof schema>;

export default function ResetPasswordPage() {
  const router = useRouter();
  const params = useSearchParams();
  const token = params.get("token") || "";
  const email = params.get("email") || "";
  const [serverError, setServerError] = useState("");

  const { register, handleSubmit, formState: { errors, isSubmitting } } =
    useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    setServerError("");
    try {
      await api.auth.resetPassword({ token, email, password: data.password });
      router.push("/auth/login?reset=1");
    } catch (err) {
      if (err instanceof ApiError) setServerError(err.message);
      else setServerError("Something went wrong. Please try again.");
    }
  };

  if (!token || !email) {
    return (
      <div className="card text-center animate-fade-up">
        <Alert type="error">Invalid or expired reset link. Please request a new one.</Alert>
        <Link href="/auth/forgot-password" className="btn-primary mt-6 w-full justify-center inline-flex">
          Request New Link
        </Link>
      </div>
    );
  }

  return (
    <div className="card animate-fade-up">
      <h1 className="font-display text-3xl text-[var(--color-text)] mb-1">New password</h1>
      <p className="text-[var(--color-muted)] text-sm mb-8">Choose a strong password for your account.</p>

      {serverError && <div className="mb-6"><Alert type="error">{serverError}</Alert></div>}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        <FormField label="New password" error={errors.password?.message} required>
          <Input type="password" placeholder="At least 8 characters" autoComplete="new-password" {...register("password")} />
        </FormField>
        <FormField label="Confirm password" error={errors.confirm?.message} required>
          <Input type="password" placeholder="••••••••" autoComplete="new-password" {...register("confirm")} />
        </FormField>
        <Button type="submit" fullWidth loading={isSubmitting} size="lg">
          Set New Password
        </Button>
      </form>
    </div>
  );
}
