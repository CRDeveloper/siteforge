/**
 * SiteForge API client.
 * All requests go through CloudFront → /api/* → Lambda.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

export class ApiError extends Error {
  constructor(public status: number, message: string, public details?: unknown) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    credentials: "include",      // send httpOnly cookie
    body: body ? JSON.stringify(body) : undefined,
    ...options,
  });

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new ApiError(res.status, data.error || "Request failed", data.details);
  }

  return data as T;
}

// ── Public ────────────────────────────────────────────────────────────────────
export const api = {
  config: () => request<{ config: SiteConfig }>("GET", "/config"),
  services: () => request<{ services: Service[] }>("GET", "/services"),
  availability: (date: string) =>
    request<{ date: string; slots: TimeSlot[] }>("GET", `/availability?date=${date}`),

  // ── Auth ──────────────────────────────────────────────────────────────────
  auth: {
    register: (data: RegisterInput) =>
      request<{ message: string }>("POST", "/auth/register", data),
    login: (data: LoginInput) =>
      request<{ userId: string; firstName: string; role: string }>("POST", "/auth/login", data),
    logout: () => request("POST", "/auth/logout"),
    forgotPassword: (email: string) =>
      request("POST", "/auth/forgot-password", { email }),
    resetPassword: (data: ResetPasswordInput) =>
      request("POST", "/auth/reset-password", data),
  },

  // ── User ──────────────────────────────────────────────────────────────────
  me: {
    get: () => request<{ user: User }>("GET", "/me"),
    update: (data: Partial<User>) => request<{ user: User }>("PATCH", "/me", data),
  },

  // ── Appointments ──────────────────────────────────────────────────────────
  appointments: {
    list: () => request<{ appointments: Appointment[] }>("GET", "/appointments"),
    create: (data: CreateAppointmentInput) =>
      request<{ appointment: Appointment }>("POST", "/appointments", data),
    cancel: (id: string) =>
      request<{ message: string }>("DELETE", `/appointments/${id}`),
  },

  // ── Uploads ───────────────────────────────────────────────────────────────
  uploads: {
    presign: (contentType: string, filename: string) =>
      request<{ uploadUrl: string; key: string }>("POST", "/uploads/presign", {
        contentType,
        filename,
      }),
  },

  // ── Admin ─────────────────────────────────────────────────────────────────
  admin: {
    appointments: (params?: { status?: string; date?: string }) => {
      const qs = new URLSearchParams(params as Record<string, string>).toString();
      return request<{ appointments: Appointment[]; count: number }>(
        "GET", `/admin/appointments${qs ? `?${qs}` : ""}`
      );
    },
    updateAppointment: (id: string, data: UpdateAppointmentInput) =>
      request("PATCH", `/admin/appointments/${id}`, data),
    messageUser: (id: string, message: string) =>
      request("POST", `/admin/appointments/${id}/message`, { message }),
    users: () => request<{ users: User[]; count: number }>("GET", "/admin/users"),
    stats: () => request<{ stats: DashboardStats }>("GET", "/admin/stats"),
    services: () => request<{ services: Service[] }>("GET", "/admin/services"),
    createService: (data: Partial<Service>) =>
      request<{ service: Service }>("POST", "/admin/services", data),
    updateService: (id: string, data: Partial<Service>) =>
      request<{ service: Service }>("PATCH", `/admin/services/${id}`, data),
    deleteService: (id: string) =>
      request("DELETE", `/admin/services/${id}`),
    availability: (date: string) =>
      request<{ slots: TimeSlot[] }>("GET", `/admin/availability?date=${date}`),
    createAvailability: (date: string, times: string[]) =>
      request("POST", "/admin/availability", { date, times }),
    deleteAvailability: (date: string, time: string) =>
      request("DELETE", `/admin/availability/${date}_${time}`),
    config: () => request<{ config: SiteConfig }>("GET", "/admin/config"),
    updateConfig: (data: Partial<SiteConfig>) =>
      request<{ config: SiteConfig }>("PATCH", "/admin/config", data),
  },
};

// ── Types ─────────────────────────────────────────────────────────────────────
export interface SiteConfig {
  siteId: string;
  siteName: string;
  tagline: Record<string, string>;
  defaultLang: string;
  supportedLangs: string[];
  theme: Theme;
  content: Record<string, unknown>;
  seo: Record<string, unknown>;
  appointments: { windowDays: number; cancellationHours: number };
}

export interface Theme {
  primaryColor: string;
  accentColor: string;
  backgroundColor?: string;
  textColor?: string;
  mode: "light" | "dark";
  fontDisplay: string;
  fontBody: string;
}

export interface Service {
  serviceId: string;
  name: Record<string, string>;
  description: Record<string, string>;
  durationMinutes: number;
  active: boolean;
  icon?: string;
}

export interface TimeSlot {
  time: string;
  label: string;
}

export interface User {
  userId: string;
  email: string;
  firstName: string;
  lastName: string;
  phone?: string;
  role: "user" | "admin";
  verified: boolean;
  lang?: string;
  createdAt: string;
}

export interface Appointment {
  apptId: string;
  userId: string;
  userEmail: string;
  userName: string;
  serviceId: string;
  serviceName: Record<string, string>;
  date: string;
  time: string;
  status: "pending" | "accepted" | "declined" | "rescheduled" | "cancelled";
  notes?: string;
  attachmentKey?: string;
  adminMessage?: string;
  reminderSent: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface DashboardStats {
  pendingAppointments: number;
  acceptedThisWeek: number;
  todayAppointments: number;
  totalUsers: number;
}

export interface RegisterInput {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  phone?: string;
}

export interface LoginInput {
  email: string;
  password: string;
}

export interface ResetPasswordInput {
  token: string;
  email: string;
  password: string;
}

export interface CreateAppointmentInput {
  serviceId: string;
  date: string;
  time: string;
  notes?: string;
  attachmentKey?: string;
}

export interface UpdateAppointmentInput {
  status: "accepted" | "declined" | "rescheduled";
  newDate?: string;
  newTime?: string;
  adminMessage?: string;
}
