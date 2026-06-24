"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/lib/store";
import { api } from "@/lib/api";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { PageSpinner } from "@/components/ui/index";

export default function UserLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace("/auth/login?next=/appointments");
    }
  }, [isAuthenticated, router]);

  if (!isAuthenticated) return <PageSpinner />;

  return (
    <>
      <Header />
      <main className="min-h-[80vh] section">
        <div className="container">{children}</div>
      </main>
      <Footer />
    </>
  );
}
