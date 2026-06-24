"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Calendar, Users, Clock, CheckCircle, ChevronRight } from "lucide-react";
import { api, type Appointment } from "@/lib/api";
import { Badge, PageSpinner, Alert } from "@/components/ui/index";
import { format } from "date-fns";
import { useAuthStore } from "@/lib/store";

export default function AdminDashboardPage() {
  const { user } = useAuthStore();

  const { data: statsData, isLoading: loadingStats } = useQuery({
    queryKey: ["admin-stats"],
    queryFn: () => api.admin.stats(),
    refetchInterval: 60_000, // refresh every minute
  });

  const { data: pendingData, isLoading: loadingPending } = useQuery({
    queryKey: ["admin-appointments", "pending"],
    queryFn: () => api.admin.appointments({ status: "pending" }),
    refetchInterval: 30_000,
  });

  const stats = statsData?.stats;
  const pending = pendingData?.appointments ?? [];

  return (
    <div>
      {/* Greeting */}
      <div className="mb-8">
        <h1 className="heading-section">
          Good {getTimeOfDay()}, {user?.firstName} 👋
        </h1>
        <p className="text-[var(--color-muted)] mt-1">
          Here&apos;s what&apos;s happening today.
        </p>
      </div>

      {/* Stat cards */}
      {loadingStats ? (
        <div className="flex justify-center py-8"><PageSpinner /></div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard
            label="Pending"
            value={stats?.pendingAppointments ?? 0}
            icon={<Clock className="w-5 h-5" />}
            color="amber"
            href="/admin/appointments?status=pending"
          />
          <StatCard
            label="Confirmed This Week"
            value={stats?.acceptedThisWeek ?? 0}
            icon={<CheckCircle className="w-5 h-5" />}
            color="green"
            href="/admin/appointments?status=accepted"
          />
          <StatCard
            label="Today"
            value={stats?.todayAppointments ?? 0}
            icon={<Calendar className="w-5 h-5" />}
            color="blue"
            href="/admin/appointments"
          />
          <StatCard
            label="Total Users"
            value={stats?.totalUsers ?? 0}
            icon={<Users className="w-5 h-5" />}
            color="purple"
            href="/admin/users"
          />
        </div>
      )}

      {/* Pending appointments */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <h2 className="font-display text-xl text-[var(--color-text)]">
            Pending Appointments
            {pending.length > 0 && (
              <span className="ml-2 text-sm font-body text-amber-600 bg-amber-100
                               px-2 py-0.5 rounded-full">
                {pending.length} new
              </span>
            )}
          </h2>
          <Link href="/admin/appointments" className="text-sm text-primary hover:underline flex items-center gap-1">
            View all <ChevronRight className="w-4 h-4" />
          </Link>
        </div>

        {loadingPending ? (
          <div className="flex justify-center py-6"><PageSpinner /></div>
        ) : pending.length === 0 ? (
          <div className="text-center py-8">
            <CheckCircle className="w-10 h-10 text-green-400 mx-auto mb-3" />
            <p className="text-[var(--color-muted)]">All caught up — no pending appointments.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {pending.slice(0, 5).map((appt) => (
              <PendingRow key={appt.apptId} appt={appt} />
            ))}
            {pending.length > 5 && (
              <Link href="/admin/appointments?status=pending"
                className="block text-center text-sm text-primary hover:underline pt-2">
                + {pending.length - 5} more pending
              </Link>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({
  label, value, icon, color, href,
}: {
  label: string; value: number; icon: React.ReactNode;
  color: "amber" | "green" | "blue" | "purple"; href: string;
}) {
  const colors = {
    amber:  "bg-amber-50  text-amber-600",
    green:  "bg-green-50  text-green-600",
    blue:   "bg-blue-50   text-blue-600",
    purple: "bg-purple-50 text-purple-600",
  };
  return (
    <Link href={href} className="card hover:shadow-elevated transition-all duration-200 group block">
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 ${colors[color]}`}>
        {icon}
      </div>
      <div className="text-2xl font-display text-[var(--color-text)] mb-1">{value}</div>
      <div className="text-sm text-[var(--color-muted)] group-hover:text-primary transition-colors">{label}</div>
    </Link>
  );
}

function PendingRow({ appt }: { appt: Appointment }) {
  const lang = process.env.NEXT_PUBLIC_DEFAULT_LANG || "en";
  const serviceName = typeof appt.serviceName === "object"
    ? appt.serviceName[lang] || appt.serviceName["en"]
    : appt.serviceName;

  return (
    <Link
      href={`/admin/appointments?highlight=${appt.apptId}`}
      className="flex items-center justify-between p-4 rounded-lg border border-[var(--color-border)]
                 hover:border-primary hover:bg-primary/5 transition-all duration-150"
    >
      <div>
        <div className="font-medium text-sm text-[var(--color-text)]">{appt.userName}</div>
        <div className="text-xs text-[var(--color-muted)] mt-0.5">
          {serviceName} · {format(new Date(appt.date + "T12:00:00"), "MMM d")} at {appt.time}
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Badge status={appt.status} />
        <ChevronRight className="w-4 h-4 text-[var(--color-muted)]" />
      </div>
    </Link>
  );
}

function getTimeOfDay() {
  const h = new Date().getHours();
  if (h < 12) return "morning";
  if (h < 17) return "afternoon";
  return "evening";
}
