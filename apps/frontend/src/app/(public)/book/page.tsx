"use client";

export const dynamic = "force-dynamic";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useQuery, useMutation } from "@tanstack/react-query";
import { format, addDays, isWeekend } from "date-fns";
import { ChevronLeft, ChevronRight, Check } from "lucide-react";
import { api, type Service } from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import { Button } from "@/components/ui/Button";
import { Textarea, FormField, Alert, Spinner } from "@/components/ui/index";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";

type Step = "service" | "datetime" | "confirm" | "success";

export default function BookPage() {
  const router = useRouter();
  const params = useSearchParams();
  const { isAuthenticated } = useAuthStore();
  const lang = process.env.NEXT_PUBLIC_DEFAULT_LANG || "en";

  const [step, setStep] = useState<Step>("service");
  const [selectedService, setSelectedService] = useState<Service | null>(null);
  const [selectedDate, setSelectedDate] = useState("");
  const [selectedTime, setSelectedTime] = useState("");
  const [notes, setNotes] = useState("");
  const [bookingError, setBookingError] = useState("");

  // Pre-select service from query param
  const preselectedId = params.get("service");

  const { data: servicesData } = useQuery({
    queryKey: ["services"],
    queryFn: () => api.services(),
  });

  const { data: availabilityData, isLoading: loadingSlots } = useQuery({
    queryKey: ["availability", selectedDate],
    queryFn: () => api.availability(selectedDate),
    enabled: !!selectedDate,
  });

  useEffect(() => {
    if (preselectedId && servicesData?.services) {
      const svc = servicesData.services.find((s) => s.serviceId === preselectedId);
      if (svc) { setSelectedService(svc); setStep("datetime"); }
    }
  }, [preselectedId, servicesData]);

  const bookMutation = useMutation({
    mutationFn: () =>
      api.appointments.create({
        serviceId: selectedService!.serviceId!,
        date: selectedDate!,
        time: selectedTime!,
        notes,
      }),
    onSuccess: () => setStep("success"),
    onError: (err: Error) => setBookingError(err.message),
  });

  // Build next 30 days excluding weekends (configurable)
  const availableDates = Array.from({ length: 30 }, (_, i) => {
    const d = addDays(new Date(), i + 1);
    return format(d, "yyyy-MM-dd");
  }).filter((d) => !isWeekend(new Date(d + "T12:00:00")));

  const STEPS: { key: Step; label: string }[] = [
    { key: "service", label: "Service" },
    { key: "datetime", label: "Date & Time" },
    { key: "confirm", label: "Confirm" },
  ];

  const stepIndex = STEPS.findIndex((s) => s.key === step);

  if (!isAuthenticated && step !== "service") {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="card text-center max-w-sm">
          <p className="text-[var(--color-muted)] mb-6">Please sign in to book an appointment.</p>
          <Button onClick={() => router.push("/auth/login?next=/book")} fullWidth>
            Sign In
          </Button>
        </div>
      </div>
    );
  }

  return (
    <>
      <Header />
      <main className="section">
        <div className="container max-w-2xl">

          {/* Progress bar */}
          {step !== "success" && (
            <div className="mb-10">
              <div className="flex items-center justify-between mb-2">
                {STEPS.map((s, i) => (
                  <div key={s.key} className="flex items-center flex-1 last:flex-none">
                    <div className={`flex items-center gap-2 ${i <= stepIndex ? "text-primary" : "text-[var(--color-muted)]"}`}>
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium border-2 transition-all
                        ${i < stepIndex  ? "bg-primary border-primary text-white"
                        : i === stepIndex ? "border-primary text-primary"
                        : "border-[var(--color-border)] text-[var(--color-muted)]"}`}>
                        {i < stepIndex ? <Check className="w-4 h-4" /> : i + 1}
                      </div>
                      <span className="text-sm font-medium hidden sm:block">{s.label}</span>
                    </div>
                    {i < STEPS.length - 1 && (
                      <div className={`flex-1 h-px mx-3 ${i < stepIndex ? "bg-primary" : "bg-[var(--color-border)]"}`} />
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Step: Service */}
          {step === "service" && (
            <div className="animate-fade-up">
              <h1 className="heading-section mb-2">Choose a service</h1>
              <p className="text-[var(--color-muted)] mb-8">Select the type of session you'd like to book.</p>
              <div className="grid gap-4">
                {servicesData?.services.map((svc) => (
                  <button
                    key={svc.serviceId}
                    onClick={() => { setSelectedService(svc); setStep("datetime"); }}
                    className={`card text-left hover:border-primary hover:shadow-elevated
                                transition-all duration-200 cursor-pointer
                                ${selectedService?.serviceId === svc.serviceId ? "border-primary ring-1 ring-primary" : ""}`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium text-[var(--color-text)] mb-1">
                          {svc.name[lang] || svc.name["en"]}
                        </h3>
                        <p className="text-sm text-[var(--color-muted)]">
                          {svc.description[lang] || svc.description["en"]}
                        </p>
                      </div>
                      <div className="text-right flex-shrink-0 ml-4">
                        <span className="text-sm text-[var(--color-muted)]">{svc.durationMinutes} min</span>
                        <ChevronRight className="w-5 h-5 text-primary mt-1 ml-auto" />
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Step: Date & Time */}
          {step === "datetime" && (
            <div className="animate-fade-up">
              <button onClick={() => setStep("service")} className="flex items-center gap-1 text-sm text-[var(--color-muted)] hover:text-primary mb-6">
                <ChevronLeft className="w-4 h-4" /> Back
              </button>
              <h1 className="heading-section mb-2">Pick a date & time</h1>
              <p className="text-[var(--color-muted)] mb-8">
                {selectedService?.name[lang]} · {selectedService?.durationMinutes} min
              </p>

              {/* Date picker */}
              <div className="mb-8">
                <label className="label">Select date</label>
                <div className="grid grid-cols-4 sm:grid-cols-6 gap-2 max-h-48 overflow-y-auto pr-1">
                  {availableDates.map((d) => (
                    <button
                      key={d}
                      onClick={() => { setSelectedDate(d); setSelectedTime(""); }}
                      className={`p-2 rounded text-center text-sm border transition-all
                        ${selectedDate === d
                          ? "bg-primary text-white border-primary"
                          : "border-[var(--color-border)] hover:border-primary hover:text-primary"}`}
                    >
                      <div className="font-medium">{format(new Date(d + "T12:00:00"), "d")}</div>
                      <div className="text-xs opacity-75">{format(new Date(d + "T12:00:00"), "MMM")}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Time slots */}
              {selectedDate && (
                <div className="mb-8">
                  <label className="label">Select time</label>
                  {loadingSlots ? (
                    <div className="flex items-center gap-2 text-[var(--color-muted)] text-sm">
                      <Spinner size="sm" /> Loading available times...
                    </div>
                  ) : availabilityData?.slots.length === 0 ? (
                    <p className="text-[var(--color-muted)] text-sm">No available slots for this date. Please choose another.</p>
                  ) : (
                    <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
                      {availabilityData?.slots.map((slot) => (
                        <button
                          key={slot.time}
                          onClick={() => setSelectedTime(slot.time)}
                          className={`py-3 rounded text-sm font-medium border transition-all
                            ${selectedTime === slot.time
                              ? "bg-primary text-white border-primary"
                              : "border-[var(--color-border)] hover:border-primary hover:text-primary"}`}
                        >
                          {slot.time}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <Button
                fullWidth
                size="lg"
                disabled={!selectedDate || !selectedTime}
                onClick={() => { if (!isAuthenticated) router.push("/auth/login?next=/book"); else setStep("confirm"); }}
              >
                Continue
              </Button>
            </div>
          )}

          {/* Step: Confirm */}
          {step === "confirm" && (
            <div className="animate-fade-up">
              <button onClick={() => setStep("datetime")} className="flex items-center gap-1 text-sm text-[var(--color-muted)] hover:text-primary mb-6">
                <ChevronLeft className="w-4 h-4" /> Back
              </button>
              <h1 className="heading-section mb-2">Confirm your booking</h1>
              <p className="text-[var(--color-muted)] mb-8">Review the details below before confirming.</p>

              <div className="card mb-6 space-y-4">
                {[
                  { label: "Service", value: selectedService?.name[lang] || "" },
                  { label: "Duration", value: `${selectedService?.durationMinutes} minutes` },
                  { label: "Date", value: format(new Date(selectedDate + "T12:00:00"), "EEEE, MMMM d, yyyy") },
                  { label: "Time", value: selectedTime },
                ].map(({ label, value }) => (
                  <div key={label} className="flex justify-between text-sm">
                    <span className="text-[var(--color-muted)]">{label}</span>
                    <span className="font-medium text-[var(--color-text)]">{value}</span>
                  </div>
                ))}
              </div>

              <FormField label="Notes for your therapist" hint="Optional — anything you'd like them to know beforehand">
                <Textarea
                  rows={4}
                  placeholder="Any relevant background or topics you'd like to focus on..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                />
              </FormField>

              {bookingError && (
                <div className="mt-4"><Alert type="error">{bookingError}</Alert></div>
              )}

              <Button
                fullWidth size="lg"
                loading={bookMutation.isPending}
                onClick={() => bookMutation.mutate()}
                className="mt-6"
              >
                Confirm Booking
              </Button>
            </div>
          )}

          {/* Step: Success */}
          {step === "success" && (
            <div className="card text-center py-12 animate-fade-up">
              <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-6">
                <Check className="w-8 h-8 text-green-600" />
              </div>
              <h1 className="font-display text-3xl text-[var(--color-text)] mb-2">Booking Confirmed!</h1>
              <p className="text-[var(--color-muted)] mb-2">
                Your <strong>{selectedService?.name[lang]}</strong> session is booked for{" "}
                <strong>{format(new Date(selectedDate + "T12:00:00"), "MMMM d")}</strong> at <strong>{selectedTime}</strong>.
              </p>
              <p className="text-sm text-[var(--color-muted)] mb-8">
                A confirmation has been sent to your email. Your therapist will be in touch shortly.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <Button variant="outline" onClick={() => router.push("/appointments")}>
                  View My Appointments
                </Button>
                <Button onClick={() => { setStep("service"); setSelectedDate(""); setSelectedTime(""); setNotes(""); }}>
                  Book Another
                </Button>
              </div>
            </div>
          )}
        </div>
      </main>
      <Footer />
    </>
  );
}
