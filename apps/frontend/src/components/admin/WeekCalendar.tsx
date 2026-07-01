"use client";

import { useState } from "react";
import { format, addDays, startOfWeek, isSameDay } from "date-fns";
import { Button } from "@/components/ui/Button";
import { TimeSlot } from "shared-types";

interface WeekCalendarProps {
  onSelectTime: (date: string, time: string) => void;
  onDeleteTime: (date: string, time: string) => void;
  existingSlots: Record<string, string[]>; // { "2024-01-15": ["09:00", "10:00"] }
  businessHours: { start: number; end: number }; // 9-17
}

export function WeekCalendar({
  onSelectTime,
  onDeleteTime,
  existingSlots,
  businessHours = { start: 9, end: 17 },
}: WeekCalendarProps) {
  const [weekStart, setWeekStart] = useState<Date>(startOfWeek(new Date()));
  const days = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i));
  const timeSlots = Array.from({ length: businessHours.end - businessHours.start }, (_, i) =>
    String(businessHours.start + i).padStart(2, "0") + ":00"
  );

  const handlePrevWeek = () => setWeekStart(addDays(weekStart, -7));
  const handleNextWeek = () => setWeekStart(addDays(weekStart, 7));

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      {/* Navigation */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Availability</h3>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handlePrevWeek}>
            ← Prev
          </Button>
          <span className="text-sm text-gray-600 px-4 py-2">
            {format(weekStart, "MMM d")} - {format(addDays(weekStart, 6), "MMM d, yyyy")}
          </span>
          <Button variant="outline" size="sm" onClick={handleNextWeek}>
            Next →
          </Button>
        </div>
      </div>

      {/* Calendar Grid */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr>
              <th className="px-3 py-2 text-left font-medium text-gray-600 w-20">Time</th>
              {days.map((day) => (
                <th
                  key={day.toISOString()}
                  className="px-3 py-2 text-center font-medium text-gray-900 min-w-32"
                >
                  <div className="font-semibold">{format(day, "EEE")}</div>
                  <div className="text-xs text-gray-500">{format(day, "MMM d")}</div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {timeSlots.map((time) => (
              <tr key={time} className="border-t border-gray-100 hover:bg-gray-50">
                <td className="px-3 py-3 font-medium text-gray-600 bg-gray-50">{time}</td>
                {days.map((day) => {
                  const dateStr = format(day, "yyyy-MM-dd");
                  const isBooked = existingSlots[dateStr]?.includes(time);
                  const isWeekend = day.getDay() === 0 || day.getDay() === 6;

                  return (
                    <td
                      key={`${dateStr}-${time}`}
                      className={`px-3 py-3 text-center ${isWeekend ? "bg-gray-50" : ""}`}
                    >
                      {isBooked ? (
                        <button
                          onClick={() => onDeleteTime(dateStr, time)}
                          className="w-full px-2 py-1.5 bg-green-100 text-green-700 text-xs font-medium rounded hover:bg-green-200 transition cursor-pointer"
                        >
                          ✓ Available
                        </button>
                      ) : (
                        <button
                          onClick={() => onSelectTime(dateStr, time)}
                          disabled={isWeekend}
                          className={`w-full px-2 py-1.5 text-xs font-medium rounded transition ${
                            isWeekend
                              ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                              : "bg-gray-100 text-gray-600 hover:bg-blue-100 hover:text-blue-700 cursor-pointer"
                          }`}
                        >
                          -
                        </button>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="mt-4 flex gap-6 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-green-100" />
          <span>Available</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-gray-100" />
          <span>Not available</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-gray-200" />
          <span>Weekend</span>
        </div>
      </div>
    </div>
  );
}
