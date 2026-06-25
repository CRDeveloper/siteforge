/**
 * Shared TypeScript types for SiteForge platform.
 * Used across frontend (Next.js) and backend (Python/Lambda type hints via comments).
 */

// ── Domain Models ─────────────────────────────────────────────────────────

export interface SiteConfig {
  siteId: string;
  siteName: string;
  tagline: Record<string, string>;
  domain: string;
  defaultLang: string;
  supportedLangs: string[];
  theme: Theme;
  content: SiteContent;
  seo: Record<string, SEOMetadata>;
  appointments: AppointmentSettings;
  modules: string[];
  services?: Service[];
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

export interface SiteContent {
  hero: Record<string, { title: string; subtitle: string; cta: string }>;
  about: Record<string, { title: string; body: string }>;
  contact: {
    address: string;
    phone: string;
    hours: Record<string, string>;
  };
}

export interface SEOMetadata {
  title: string;
  description: string;
}

export interface AppointmentSettings {
  windowDays: number;
  cancellationHours: number;
  reminderHoursBefore: number;
}

export interface Service {
  serviceId?: string;
  id?: string; // for create input
  icon?: string;
  name: Record<string, string>;
  description: Record<string, string>;
  durationMinutes: number;
  active: boolean;
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
  updatedAt: string;
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

// ── Input DTOs ────────────────────────────────────────────────────────────

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

// ── API Response Types ────────────────────────────────────────────────────

export interface ApiResponse<T = unknown> {
  data?: T;
  error?: string;
  details?: unknown;
}
