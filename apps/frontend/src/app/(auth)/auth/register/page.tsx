"use client";

import { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { api, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Input, FormField, Alert } from "@/components/ui/index";

const schema = z.object({
  firstName: z.string().min(1, "First name is required"),
  lastName:  z.string().min(1, "Last name is required"),
  email:     z.string().email("Please enter a valid email"),
  phone:     z.string().optional(),
  password:  z.string().min(8, "Password must be at least 8 characters"),
  confirm:   z.string(),
}).refine((d) => d.password === d.confirm, {
  message: "Passwords do not match",
  path: ["confirm"],
});

type FormData = z.infer<typeof schema>;

export default function RegisterPage() {
  const [success, setSuccess] = useState(false);
  const [email, setEmail] = useState("");
  const [serverError, setServerError] = useState("");

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    setServerError("");
    try {
      await api.auth.register({
        email: data.email,
        password: data.password,
        firstName: data.firstName,
        lastName: data.lastName,
        phone: data.phone,
      });
      setEmail(data.email);
      setSuccess(true);
    } catch (err) {
      if (err instanceof ApiError) {
        setServerError(err.message);
      } else {
        setServerError("Something went wrong. Please try again.");
      }
    }
  };

  if (success) {
    return (
      <div className="card text-center animate-fade-up">
        <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-6">
          <span className="text-3xl">✉️</span>
        </div>
        <h1 className="font-display text-3xl text-[var(--color-text)] mb-2">Check your email</h1>
        <p className="text-[var(--color-muted)] mb-6">
          We sent a verification link to <strong>{email}</strong>.
          Please check your inbox and click the link to activate your account.
        </p>
        <p className="text-sm text-[var(--color-muted)]">
          Already verified?{" "}
          <Link href="/auth/login" className="text-primary hover:underline font-medium">
            Sign in
          </Link>
        </p>
      </div>
    );
  }

  return (
    <div className="card animate-fade-up">
      <h1 className="font-display text-3xl text-[var(--color-text)] mb-1">Create account</h1>
      <p className="text-[var(--color-muted)] text-sm mb-8">
        Book and manage your appointments online
      </p>

      {serverError && (
        <div className="mb-6">
          <Alert type="error">{serverError}</Alert>
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        <div className="grid grid-cols-2 gap-4">
          <FormField label="First name" error={errors.firstName?.message} required>
            <Input placeholder="Jane" autoComplete="given-name" {...register("firstName")} />
          </FormField>
          <FormField label="Last name" error={errors.lastName?.message} required>
            <Input placeholder="Doe" autoComplete="family-name" {...register("lastName")} />
          </FormField>
        </div>

        <FormField label="Email address" error={errors.email?.message} required>
          <Input
            type="email"
            placeholder="you@example.com"
            autoComplete="email"
            {...register("email")}
          />
        </FormField>

        <FormField label="Phone number" error={errors.phone?.message} hint="Optional — for appointment reminders">
          <Input
            type="tel"
            placeholder="+1 (305) 555-0100"
            autoComplete="tel"
            {...register("phone")}
          />
        </FormField>

        <FormField label="Password" error={errors.password?.message} required>
          <Input
            type="password"
            placeholder="At least 8 characters"
            autoComplete="new-password"
            {...register("password")}
          />
        </FormField>

        <FormField label="Confirm password" error={errors.confirm?.message} required>
          <Input
            type="password"
            placeholder="••••••••"
            autoComplete="new-password"
            {...register("confirm")}
          />
        </FormField>

        <Button type="submit" fullWidth loading={isSubmitting} size="lg">
          Create Account
        </Button>
      </form>

      <p className="text-center text-sm text-[var(--color-muted)] mt-6">
        Already have an account?{" "}
        <Link href="/auth/login" className="text-primary hover:underline font-medium">
          Sign in
        </Link>
      </p>
    </div>
  );
}
