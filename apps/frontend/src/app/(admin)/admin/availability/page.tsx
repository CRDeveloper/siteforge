"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Alert, PageSpinner, Button } from "@/components/ui/index";
import { ChevronLeft, ChevronRight, Plus, X } from "lucide-react";
import { format, addDays, startOfWeek, getDay } from "date-fns";

export default function AvailabilityPage() {
  const queryClient = useQueryClient();
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [showAddForm, setShowAddForm] = useState(false);
  const [newTimes, setNewTimes] = useState<string[]>([]);

  const weekStart = startOfWeek(selectedDate);

  // Fetch availability for selected week
  const dates = Array.from({ length: 7 }, (_, i) => {
    const date = addDays(weekStart, i);
    return format(date, "yyyy-MM-dd");
  });

  const slotsQueries = dates.map((date) =>
    useQuery({
      queryKey: ["admin-availability", date],
      queryFn: () => api.admin.availability(date),
      staleTime: 1000 * 60, // 1 minute
    })
  );

  const createSlotMutation = useMutation({
    mutationFn: (data: { date: string; times: string[] }) =>
      api.admin.createAvailability(data.date, data.times),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-availability"] });
      setShowAddForm(false);
      setNewTimes([]);
    },
  });

  const deleteSlotMutation = useMutation({
    mutationFn: ({ date, time }: { date: string; time: string }) =>
      api.admin.deleteAvailability(date, time),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-availability"] });
    },
  });

  const handleAddSlots = async (date: string) => {
    if (newTimes.length === 0) return;
    createSlotMutation.mutate({ date, times: newTimes });
  };

  const handlePrevWeek = () => {
    setSelectedDate(addDays(selectedDate, -7));
  };

  const handleNextWeek = () => {
    setSelectedDate(addDays(selectedDate, 7));
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="heading-section">Availability Schedule</h1>
        <p className="text-[var(--color-muted)] mt-1">
          Manage appointment time slots for each day
        </p>
      </div>

      {/* Week Navigation */}
      <div className="card mb-6">
        <div className="flex items-center justify-between mb-6">
          <button
            onClick={handlePrevWeek}
            className="flex items-center gap-2 text-sm text-primary hover:underline"
          >
            <ChevronLeft className="w-4 h-4" />
            Previous Week
          </button>
          <div className="text-center">
            <div className="font-display text-lg text-[var(--color-text)]">
              {format(weekStart, "MMM d")} – {format(addDays(weekStart, 6), "MMM d, yyyy")}
            </div>
          </div>
          <button
            onClick={handleNextWeek}
            className="flex items-center gap-2 text-sm text-primary hover:underline"
          >
            Next Week
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {/* 7-Day Grid */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-7">
          {dates.map((date, idx) => {
            const dayName = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][idx];
            const dateObj = addDays(weekStart, idx);
            const isToday = format(new Date(), "yyyy-MM-dd") === date;
            const isWeekend = idx === 0 || idx === 6;

            const query = slotsQueries[idx];
            const slots = query.data?.slots ?? [];
            const isLoading = query.isLoading;
            const error = query.error;

            return (
              <div
                key={date}
                className={`rounded-lg border p-4 ${
                  isToday
                    ? "border-primary bg-primary/5"
                    : isWeekend
                      ? "border-[var(--color-border)] bg-[var(--color-bg-secondary)]"
                      : "border-[var(--color-border)]"
                }`}
              >
                <div className="mb-4">
                  <div className="text-xs font-medium text-[var(--color-muted)] uppercase">
                    {dayName}
                  </div>
                  <div className="text-lg font-display text-[var(--color-text)]">
                    {format(dateObj, "d")}
                  </div>
                  {isToday && (
                    <div className="text-xs text-primary font-medium">Today</div>
                  )}
                </div>

                {isWeekend ? (
                  <div className="text-xs text-[var(--color-muted)] py-4 text-center">
                    Closed
                  </div>
                ) : isLoading ? (
                  <div className="flex justify-center py-4">
                    <div className="w-4 h-4 rounded-full bg-primary/30 animate-pulse" />
                  </div>
                ) : error ? (
                  <div className="text-xs text-red-500">Error loading</div>
                ) : (
                  <div className="space-y-2">
                    {slots.length === 0 ? (
                      <div className="text-xs text-[var(--color-muted)] py-2">
                        No slots available
                      </div>
                    ) : (
                      <div className="space-y-1.5 max-h-48 overflow-y-auto">
                        {slots.map((slot) => (
                          <div
                            key={slot.time}
                            className="flex items-center justify-between text-xs bg-[var(--color-bg-secondary)] 
                                     rounded px-2 py-1.5 hover:bg-red-50 dark:hover:bg-red-900/20 group transition-colors"
                          >
                            <span className="text-[var(--color-text)] font-medium">
                              {slot.time}
                            </span>
                            <button
                              onClick={() =>
                                deleteSlotMutation.mutate({
                                  date,
                                  time: slot.time,
                                })
                              }
                              disabled={deleteSlotMutation.isPending}
                              className="opacity-0 group-hover:opacity-100 text-red-500 hover:text-red-700 
                                       transition-opacity disabled:opacity-50"
                              title="Remove slot"
                            >
                              <X className="w-3 h-3" />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}

                    <button
                      onClick={() => setShowAddForm(true)}
                      className="text-xs text-primary hover:underline flex items-center gap-1 mt-3 pt-2 
                               border-t border-[var(--color-border)]"
                    >
                      <Plus className="w-3 h-3" />
                      Add Time
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Add Time Slots Modal */}
      {showAddForm && (
        <AddTimeSlotsModal
          onClose={() => {
            setShowAddForm(false);
            setNewTimes([]);
          }}
          onSubmit={handleAddSlots}
          isLoading={createSlotMutation.isPending}
        />
      )}
    </div>
  );
}

function AddTimeSlotsModal({
  onClose,
  onSubmit,
  isLoading,
}: {
  onClose: () => void;
  onSubmit: (date: string) => void;
  isLoading: boolean;
}) {
  const [selectedDate, setSelectedDate] = useState(format(new Date(), "yyyy-MM-dd"));
  const [times, setTimes] = useState<string[]>([]);
  const [newTime, setNewTime] = useState("");

  const handleAddTime = () => {
    if (!newTime) return;
    if (times.includes(newTime)) {
      alert("Time already added");
      return;
    }
    setTimes([...times, newTime].sort());
    setNewTime("");
  };

  const handleRemoveTime = (time: string) => {
    setTimes(times.filter((t) => t !== time));
  };

  const handleSubmit = () => {
    if (times.length === 0) {
      alert("Add at least one time slot");
      return;
    }
    onSubmit(selectedDate);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="card max-w-md w-full animate-fade-up">
        <div className="flex items-center justify-between mb-6">
          <h2 className="font-display text-xl text-[var(--color-text)]">Add Time Slots</h2>
          <button
            onClick={onClose}
            className="text-[var(--color-muted)] hover:text-[var(--color-text)]"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-4">
          {/* Date Picker */}
          <div>
            <label className="block text-sm font-medium text-[var(--color-text)] mb-2">
              Date
            </label>
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="input w-full"
            />
          </div>

          {/* Time Input */}
          <div>
            <label className="block text-sm font-medium text-[var(--color-text)] mb-2">
              Time (24h format)
            </label>
            <div className="flex gap-2">
              <input
                type="time"
                value={newTime}
                onChange={(e) => setNewTime(e.target.value)}
                className="input flex-1"
              />
              <Button
                size="sm"
                variant="secondary"
                onClick={handleAddTime}
                disabled={!newTime || isLoading}
              >
                <Plus className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* Added Times */}
          {times.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-[var(--color-text)] mb-2">
                Added Times ({times.length})
              </label>
              <div className="grid grid-cols-3 gap-2">
                {times.map((time) => (
                  <div
                    key={time}
                    className="flex items-center justify-between bg-primary/10 rounded px-2 py-1"
                  >
                    <span className="text-xs font-medium">{time}</span>
                    <button
                      onClick={() => handleRemoveTime(time)}
                      className="text-red-500 hover:text-red-700"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <button
              onClick={onClose}
              disabled={isLoading}
              className="btn btn-outline flex-1"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={times.length === 0 || isLoading}
              className="btn btn-primary flex-1"
            >
              {isLoading ? "Adding..." : "Add Slots"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

