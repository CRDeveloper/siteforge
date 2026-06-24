import { forwardRef, type InputHTMLAttributes, type TextareaHTMLAttributes } from "react";
import { clsx } from "clsx";

// ── Input ──────────────────────────────────────────────────────────────────

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, error, ...props }, ref) => (
    <input
      ref={ref}
      className={clsx(
        "input",
        error && "border-red-400 focus:border-red-400 focus:ring-red-200",
        className
      )}
      {...props}
    />
  )
);
Input.displayName = "Input";

// ── Textarea ───────────────────────────────────────────────────────────────

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, error, ...props }, ref) => (
    <textarea
      ref={ref}
      className={clsx(
        "input resize-none",
        error && "border-red-400 focus:border-red-400 focus:ring-red-200",
        className
      )}
      {...props}
    />
  )
);
Textarea.displayName = "Textarea";

// ── FormField ──────────────────────────────────────────────────────────────

interface FormFieldProps {
  label: string;
  error?: string;
  required?: boolean;
  children: React.ReactNode;
  hint?: string;
}

export function FormField({ label, error, required, children, hint }: FormFieldProps) {
  return (
    <div className="space-y-1.5">
      <label className="label">
        {label}
        {required && <span className="text-red-500 ml-0.5">*</span>}
      </label>
      {children}
      {hint && !error && (
        <p className="text-xs text-[var(--color-muted)]">{hint}</p>
      )}
      {error && (
        <p className="text-xs text-red-500 flex items-center gap-1">
          <span>⚠</span> {error}
        </p>
      )}
    </div>
  );
}

// ── Alert ──────────────────────────────────────────────────────────────────

interface AlertProps {
  type?: "error" | "success" | "info" | "warning";
  children: React.ReactNode;
}

export function Alert({ type = "error", children }: AlertProps) {
  const styles = {
    error: "bg-red-50 border-red-200 text-red-700",
    success: "bg-green-50 border-green-200 text-green-700",
    info: "bg-blue-50 border-blue-200 text-blue-700",
    warning: "bg-amber-50 border-amber-200 text-amber-700",
  };
  const icons = { error: "⚠", success: "✓", info: "ℹ", warning: "⚠" };

  return (
    <div className={clsx("flex gap-2 p-4 rounded border text-sm", styles[type])}>
      <span className="flex-shrink-0">{icons[type]}</span>
      <span>{children}</span>
    </div>
  );
}

// ── Badge ──────────────────────────────────────────────────────────────────

type BadgeVariant = "pending" | "accepted" | "declined" | "rescheduled" | "cancelled" | "default";

const BADGE_STYLES: Record<BadgeVariant, string> = {
  pending:     "bg-amber-100 text-amber-800",
  accepted:    "bg-green-100 text-green-800",
  declined:    "bg-red-100 text-red-800",
  rescheduled: "bg-blue-100 text-blue-800",
  cancelled:   "bg-gray-100 text-gray-600",
  default:     "bg-gray-100 text-gray-700",
};

export function Badge({ status }: { status: BadgeVariant | string }) {
  const style = BADGE_STYLES[status as BadgeVariant] ?? BADGE_STYLES.default;
  const label = status.charAt(0).toUpperCase() + status.slice(1);
  return (
    <span className={clsx("inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium", style)}>
      {label}
    </span>
  );
}

// ── Modal ──────────────────────────────────────────────────────────────────

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export function Modal({ open, onClose, title, children }: ModalProps) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="relative bg-[var(--color-surface-raised)] rounded-lg shadow-elevated
                      w-full max-w-lg max-h-[90vh] overflow-y-auto animate-fade-in">
        <div className="flex items-center justify-between p-6 border-b border-[var(--color-border)]">
          <h2 className="font-display text-xl text-[var(--color-text)]">{title}</h2>
          <button
            onClick={onClose}
            className="btn-ghost p-1.5 rounded-full text-[var(--color-muted)]"
          >
            ✕
          </button>
        </div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  );
}

// ── Spinner ────────────────────────────────────────────────────────────────

export function Spinner({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const sizes = { sm: "w-4 h-4", md: "w-8 h-8", lg: "w-12 h-12" };
  return (
    <div className={clsx("animate-spin rounded-full border-2 border-primary/20 border-t-primary", sizes[size])} />
  );
}

export function PageSpinner() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <Spinner size="lg" />
    </div>
  );
}
