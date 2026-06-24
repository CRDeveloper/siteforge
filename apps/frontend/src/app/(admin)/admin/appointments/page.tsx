"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { format } from "date-fns";
import { api, type Appointment } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Badge, Modal, Alert, PageSpinner, Input, FormField, Textarea } from "@/components/ui/index";
import { Check, X, RefreshCw, MessageSquare, Filter } from "lucide-react";
import { clsx } from "clsx";

type StatusFilter = "pending" | "accepted" | "declined" | "rescheduled" | "cancelled" | "all";

const FILTERS: { label: string; value: StatusFilter }[] = [
  { label: "Pending",    value: "pending"     },
  { label: "Confirmed",  value: "accepted"    },
  { label: "Rescheduled",value: "rescheduled" },
  { label: "Declined",   value: "declined"    },
  { label: "Cancelled",  value: "cancelled"   },
  { label: "All",        value: "all"         },
];

export default function AdminAppointmentsPage() {
  const qc = useQueryClient();
  const params = useSearchParams();
  const [filter, setFilter] = useState<StatusFilter>(
    (params.get("status") as StatusFilter) || "pending"
  );
  const [actionAppt, setActionAppt] = useState<Appointment | null>(null);
  const [actionType, setActionType] = useState<"accept" | "decline" | "reschedule" | "message" | null>(null);
  const [adminMessage, setAdminMessage] = useState("");
  const [newDate, setNewDate] = useState("");
  const [newTime, setNewTime] = useState("");
  const [actionError, setActionError] = useState("");
  const lang = process.env.NEXT_PUBLIC_DEFAULT_LANG || "en";

  const { data, isLoading } = useQuery({
    queryKey: ["admin-appointments", filter],
    queryFn: () => api.admin.appointments({ status: filter === "all" ? undefined : filter }),
    refetchInterval: 30_000,
  });

  const updateMutation = useMutation({
    mutationFn: (vars: { id: string; status: string; newDate?: string; newTime?: string; adminMessage?: string }) =>
      api.admin.updateAppointment(vars.id, {
        status: vars.status as "accepted" | "declined" | "rescheduled",
        newDate: vars.newDate,
        newTime: vars.newTime,
        adminMessage: vars.adminMessage,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin-appointments"] });
      qc.invalidateQueries({ queryKey: ["admin-stats"] });
      closeModal();
    },
    onError: (e: Error) => setActionError(e.message),
  });

  const messageMutation = useMutation({
    mutationFn: (vars: { id: string; message: string }) =>
      api.admin.messageUser(vars.id, vars.message),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["admin-appointments"] }); closeModal(); },
    onError: (e: Error) => setActionError(e.message),
  });

  const openAction = (appt: Appointment, type: typeof actionType) => {
    setActionAppt(appt); setActionType(type);
    setAdminMessage(""); setNewDate(""); setNewTime(""); setActionError("");
  };

  const closeModal = () => { setActionAppt(null); setActionType(null); };

  const handleConfirmAction = () => {
    if (!actionAppt || !actionType) return;
    if (actionType === "message") {
      messageMutation.mutate({ id: actionAppt.apptId, message: adminMessage });
    } else {
      const statusMap = { accept: "accepted", decline: "declined", reschedule: "rescheduled" } as const;
      updateMutation.mutate({
        id: actionAppt.apptId,
        status: statusMap[actionType as keyof typeof statusMap],
        newDate: actionType === "reschedule" ? newDate : undefined,
        newTime: actionType === "reschedule" ? newTime : undefined,
        adminMessage,
      });
    }
  };

  const appointments = data?.appointments ?? [];

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="heading-section">Appointments</h1>
          <p className="text-[var(--color-muted)] mt-1">{data?.count ?? 0} records</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-2 flex-wrap mb-6">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={clsx(
              "px-4 py-2 rounded-full text-sm font-medium border transition-all",
              filter === f.value
                ? "bg-primary text-white border-primary"
                : "border-[var(--color-border)] text-[var(--color-muted)] hover:border-primary hover:text-primary"
            )}
          >
            {f.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <PageSpinner />
      ) : appointments.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-[var(--color-muted)]">No appointments found for this filter.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {appointments.map((appt) => {
            const serviceName = typeof appt.serviceName === "object"
              ? appt.serviceName[lang] || appt.serviceName["en"]
              : appt.serviceName;

            return (
              <div
                key={appt.apptId}
                className={clsx(
                  "card flex flex-col sm:flex-row sm:items-center justify-between gap-4",
                  params.get("highlight") === appt.apptId && "ring-2 ring-primary"
                )}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-[var(--color-text)]">{appt.userName}</span>
                    <Badge status={appt.status} />
                  </div>
                  <p className="text-sm text-[var(--color-muted)]">
                    {serviceName} · {format(new Date(appt.date + "T12:00:00"), "MMM d, yyyy")} at {appt.time}
                  </p>
                  <p className="text-xs text-[var(--color-muted)] mt-0.5">{appt.userEmail}</p>
                  {appt.notes && (
                    <p className="text-xs text-[var(--color-muted)] mt-1 italic">"{appt.notes}"</p>
                  )}
                </div>

                {/* Action buttons */}
                <div className="flex items-center gap-2 flex-shrink-0">
                  {appt.status === "pending" && (
                    <>
                      <Button size="sm" onClick={() => openAction(appt, "accept")}
                        className="gap-1"><Check className="w-3.5 h-3.5" />Accept</Button>
                      <Button size="sm" variant="outline" onClick={() => openAction(appt, "reschedule")}
                        className="gap-1"><RefreshCw className="w-3.5 h-3.5" />Reschedule</Button>
                      <Button size="sm" variant="danger" onClick={() => openAction(appt, "decline")}
                        className="gap-1"><X className="w-3.5 h-3.5" />Decline</Button>
                    </>
                  )}
                  <Button size="sm" variant="ghost" onClick={() => openAction(appt, "message")}
                    className="gap-1"><MessageSquare className="w-3.5 h-3.5" />Message</Button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Action Modal */}
      <Modal
        open={!!actionAppt && !!actionType}
        onClose={closeModal}
        title={
          actionType === "accept"     ? "Accept Appointment"     :
          actionType === "decline"    ? "Decline Appointment"    :
          actionType === "reschedule" ? "Reschedule Appointment" :
          "Message Client"
        }
      >
        {actionAppt && (
          <div className="space-y-4">
            <div className="p-4 bg-[var(--color-surface)] rounded-lg text-sm space-y-1">
              <p><strong>Client:</strong> {actionAppt.userName} ({actionAppt.userEmail})</p>
              <p><strong>Service:</strong> {typeof actionAppt.serviceName === "object"
                ? actionAppt.serviceName[lang] || actionAppt.serviceName["en"]
                : actionAppt.serviceName}</p>
              <p><strong>Requested:</strong> {format(new Date(actionAppt.date + "T12:00:00"), "MMMM d, yyyy")} at {actionAppt.time}</p>
            </div>

            {actionType === "reschedule" && (
              <div className="grid grid-cols-2 gap-3">
                <FormField label="New date" required>
                  <Input type="date" value={newDate} onChange={(e) => setNewDate(e.target.value)} />
                </FormField>
                <FormField label="New time" required>
                  <Input type="time" value={newTime} onChange={(e) => setNewTime(e.target.value)} />
                </FormField>
              </div>
            )}

            <FormField
              label={actionType === "message" ? "Message to client" : "Note to client (optional)"}
              required={actionType === "message"}
            >
              <Textarea
                rows={3}
                placeholder={
                  actionType === "accept"     ? "e.g. Please arrive 5 minutes early." :
                  actionType === "decline"    ? "e.g. Unfortunately we're fully booked. Please try another date." :
                  actionType === "reschedule" ? "e.g. We need to move your session. New time above." :
                  "Type your message..."
                }
                value={adminMessage}
                onChange={(e) => setAdminMessage(e.target.value)}
              />
            </FormField>

            {actionError && <Alert type="error">{actionError}</Alert>}

            <div className="flex gap-3 pt-2">
              <Button variant="ghost" fullWidth onClick={closeModal}>Cancel</Button>
              <Button
                fullWidth
                variant={actionType === "decline" ? "danger" : "primary"}
                loading={updateMutation.isPending || messageMutation.isPending}
                disabled={
                  (actionType === "reschedule" && (!newDate || !newTime)) ||
                  (actionType === "message" && !adminMessage.trim())
                }
                onClick={handleConfirmAction}
              >
                {actionType === "accept"     ? "Confirm Acceptance"  :
                 actionType === "decline"    ? "Confirm Decline"     :
                 actionType === "reschedule" ? "Confirm Reschedule"  :
                 "Send Message"}
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
