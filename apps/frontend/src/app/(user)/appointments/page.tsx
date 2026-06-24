"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { format } from "date-fns";
import { CalendarDays, Clock, Plus, AlertCircle } from "lucide-react";
import { api, type Appointment } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Badge, Modal, Alert, PageSpinner } from "@/components/ui/index";

export default function AppointmentsPage() {
  const queryClient = useQueryClient();
  const [cancelTarget, setCancelTarget] = useState<Appointment | null>(null);
  const [cancelError, setCancelError] = useState("");

  const { data, isLoading, error } = useQuery({
    queryKey: ["appointments"],
    queryFn: () => api.appointments.list(),
  });

  const cancelMutation = useMutation({
    mutationFn: (id: string) => api.appointments.cancel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["appointments"] });
      setCancelTarget(null);
    },
    onError: (err: Error) => setCancelError(err.message),
  });

  if (isLoading) return <PageSpinner />;
  if (error) return <Alert type="error">Could not load your appointments.</Alert>;

  const appointments = data?.appointments ?? [];
  const today = new Date().toISOString().split("T")[0];
  const upcoming = appointments.filter((a) => a.date >= today && a.status !== "cancelled" && a.status !== "declined");
  const past     = appointments.filter((a) => a.date < today || a.status === "cancelled" || a.status === "declined");

  return (
    <div className="max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-10">
        <div>
          <h1 className="heading-section">My Appointments</h1>
          <p className="text-[var(--color-muted)] mt-1">Manage your upcoming sessions</p>
        </div>
        <Link href="/book">
          <Button size="md">
            <Plus className="w-4 h-4" />
            Book Session
          </Button>
        </Link>
      </div>

      {/* Upcoming */}
      <section className="mb-10">
        <h2 className="font-display text-xl text-[var(--color-text)] mb-4">
          Upcoming <span className="text-[var(--color-muted)] text-base font-body">({upcoming.length})</span>
        </h2>

        {upcoming.length === 0 ? (
          <div className="card text-center py-12">
            <CalendarDays className="w-12 h-12 text-[var(--color-muted)] mx-auto mb-4" />
            <p className="text-[var(--color-muted)] mb-4">No upcoming appointments.</p>
            <Link href="/book"><Button size="sm">Book your first session</Button></Link>
          </div>
        ) : (
          <div className="space-y-4">
            {upcoming.map((appt) => (
              <AppointmentCard
                key={appt.apptId}
                appt={appt}
                onCancel={() => { setCancelError(""); setCancelTarget(appt); }}
              />
            ))}
          </div>
        )}
      </section>

      {/* Past */}
      {past.length > 0 && (
        <section>
          <h2 className="font-display text-xl text-[var(--color-text)] mb-4">
            Past <span className="text-[var(--color-muted)] text-base font-body">({past.length})</span>
          </h2>
          <div className="space-y-3 opacity-70">
            {past.map((appt) => (
              <AppointmentCard key={appt.apptId} appt={appt} past />
            ))}
          </div>
        </section>
      )}

      {/* Cancel modal */}
      <Modal
        open={!!cancelTarget}
        onClose={() => setCancelTarget(null)}
        title="Cancel Appointment"
      >
        <p className="text-[var(--color-muted)] mb-2">
          Are you sure you want to cancel your{" "}
          <strong>{cancelTarget?.serviceName?.en}</strong> session on{" "}
          <strong>{cancelTarget && format(new Date(cancelTarget.date + "T12:00:00"), "MMMM d, yyyy")}</strong>?
        </p>
        <p className="text-sm text-amber-600 flex gap-2 items-start mb-6">
          <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          Cancellations must be made at least 24 hours in advance.
        </p>

        {cancelError && <div className="mb-4"><Alert type="error">{cancelError}</Alert></div>}

        <div className="flex gap-3">
          <Button variant="ghost" fullWidth onClick={() => setCancelTarget(null)}>
            Keep Appointment
          </Button>
          <Button
            variant="danger"
            fullWidth
            loading={cancelMutation.isPending}
            onClick={() => cancelTarget && cancelMutation.mutate(cancelTarget.apptId)}
          >
            Yes, Cancel
          </Button>
        </div>
      </Modal>
    </div>
  );
}

function AppointmentCard({
  appt,
  past = false,
  onCancel,
}: {
  appt: Appointment;
  past?: boolean;
  onCancel?: () => void;
}) {
  const lang = process.env.NEXT_PUBLIC_DEFAULT_LANG || "en";
  const serviceName =
    typeof appt.serviceName === "object"
      ? appt.serviceName[lang] || appt.serviceName["en"]
      : appt.serviceName;

  const canCancel = !past && appt.status !== "cancelled" && appt.status !== "declined";

  return (
    <div className="card flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div className="flex gap-4 items-start">
        <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
          <CalendarDays className="w-5 h-5 text-primary" />
        </div>
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-medium text-[var(--color-text)]">{serviceName}</h3>
            <Badge status={appt.status} />
          </div>
          <div className="flex items-center gap-3 text-sm text-[var(--color-muted)]">
            <span className="flex items-center gap-1">
              <CalendarDays className="w-3.5 h-3.5" />
              {format(new Date(appt.date + "T12:00:00"), "EEEE, MMMM d, yyyy")}
            </span>
            <span className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />
              {appt.time}
            </span>
          </div>
          {appt.adminMessage && (
            <p className="text-xs text-blue-600 mt-2 bg-blue-50 px-3 py-1.5 rounded">
              Note from therapist: {appt.adminMessage}
            </p>
          )}
        </div>
      </div>

      {canCancel && (
        <Button variant="ghost" size="sm" onClick={onCancel} className="flex-shrink-0">
          Cancel
        </Button>
      )}
    </div>
  );
}
