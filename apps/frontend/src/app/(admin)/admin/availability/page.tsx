"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { WeekCalendar } from "@/components/admin/WeekCalendar";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/index";
import { format } from "date-fns";

export default function AvailabilityPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [slots, setSlots] = useState<Record<string, string[]>>({});

  useEffect(() => {
    fetchAvailability();
  }, []);

  async function fetchAvailability() {
    try {
      setLoading(true);
      setError(null);

      // Fetch slots for next 30 days
      const today = new Date();
      const slots: Record<string, string[]> = {};

      for (let i = 0; i < 30; i++) {
        const date = new Date(today);
        date.setDate(date.getDate() + i);
        const dateStr = format(date, "yyyy-MM-dd");

        try {
          const { slots: daySlots } = await api.admin.availability(dateStr);
          slots[dateStr] = daySlots.map((s) => s.time);
        } catch {
          slots[dateStr] = [];
        }
      }

      setSlots(slots);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load availability");
    } finally {
      setLoading(false);
    }
  }

  async function handleSelectTime(date: string, time: string) {
    try {
      setError(null);
      const times = slots[date] || [];
      if (!times.includes(time)) {
        times.push(time);
        await api.admin.createAvailability(date, times);
        setSlots({ ...slots, [date]: times });
        setSuccess(`Added ${time} on ${date}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add slot");
    }
  }

  async function handleDeleteTime(date: string, time: string) {
    try {
      setError(null);
      const times = (slots[date] || []).filter((t) => t !== time);
      if (times.length === 0) {
        await api.admin.deleteAvailability(date, time);
      } else {
        await api.admin.createAvailability(date, times);
      }
      setSlots({ ...slots, [date]: times });
      setSuccess(`Removed ${time} on ${date}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to remove slot");
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4" />
          <p className="text-gray-600">Loading availability...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Manage Availability</h1>
        <p className="text-gray-600 mt-2">Set your available appointment slots by clicking on time slots.</p>
      </div>

      {error && (
        <Alert variant="destructive">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="ml-auto font-medium">
            ✕
          </button>
        </Alert>
      )}

      {success && (
        <Alert variant="success">
          <span>{success}</span>
          <button onClick={() => setSuccess(null)} className="ml-auto font-medium">
            ✕
          </button>
        </Alert>
      )}

      <WeekCalendar
        existingSlots={slots}
        onSelectTime={handleSelectTime}
        onDeleteTime={handleDeleteTime}
        businessHours={{ start: 9, end: 17 }}
      />

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">💡 Tips</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Green slots are available for booking</li>
          <li>• Click any slot to toggle availability</li>
          <li>• Changes are saved immediately</li>
          <li>• Only weekdays (Mon–Fri) are shown for availability</li>
        </ul>
      </div>

      <div className="flex justify-end gap-3">
        <Button variant="outline" onClick={fetchAvailability}>
          Refresh
        </Button>
        <Button onClick={() => window.history.back()}>Done</Button>
      </div>
    </div>
  );
}
