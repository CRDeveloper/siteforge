"use client";

export const dynamic = "force-dynamic";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { api, ApiError } from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import { Button } from "@/components/ui/Button";
import { Input, FormField, Alert } from "@/components/ui/index";

const schema = z.object({
  email: z.string().email("Please enter a valid email"),
  password: z.string().min(1, "Password is required"),
});

type FormData = z.infer<typeof schema>;

export default function LoginPage() {
  const router = useRouter();
  const setUser = useAuthStore((s) => s.setUser);
  const [serverError, setServerError] = useState("");

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    setServerError("");
    try {
      const result = await api.auth.login(data);
      setUser({
        userId: result.userId,
        firstName: result.firstName,
        role: result.role as "user" | "admin",
      });
      router.push(result.role === "admin" ? "/admin" : "/appointments");
    } catch (err) {
      if (err instanceof ApiError) {
        setServerError(err.message);
      } else {
        setServerError("Something went wrong. Please try again.");
      }
    }
  };

  return (
    <div className="card animate-fade-up">
      <h1 className="font-display text-3xl text-[var(--color-text)] mb-1">Welcome back</h1>
      <p className="text-[var(--color-muted)] text-sm mb-8">Sign in to your account</p>

      {serverError && (
        <div className="mb-6">
          <Alert type="error">{serverError}</Alert>
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        <FormField label="Email address" error={errors.email?.message} required>
          <Input
            type="email"
            placeholder="you@example.com"
            autoComplete="email"
            {...register("email")}
          />
        </FormField>

        <FormField label="Password" error={errors.password?.message} required>
          <Input
            type="password"
            placeholder="••••••••"
            autoComplete="current-password"
            {...register("password")}
          />
        </FormField>

        <div className="flex justify-end">
          <Link
            href="/auth/forgot-password"
            className="text-sm text-primary hover:underline"
          >
            Forgot password?
          </Link>
        </div>

        <Button type="submit" fullWidth loading={isSubmitting} size="lg">
          Sign In
        </Button>
      </form>

      <p className="text-center text-sm text-[var(--color-muted)] mt-6">
        Don&apos;t have an account?{" "}
        <Link href="/auth/register" className="text-primary hover:underline font-medium">
          Sign up
        </Link>
      </p>
    </div>
  );
}
