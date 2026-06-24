import Link from "next/link";
import { type Service } from "@/lib/api";

const ICONS: Record<string, React.ReactNode> = {
  user: (
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
      d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
  ),
  users: (
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
      d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
  ),
  heart: (
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
      d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" />
  ),
  shield: (
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
      d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
  ),
};

interface ServiceCardProps {
  service: Service;
  lang: string;
  delay?: number;
}

export function ServiceCard({ service, lang, delay = 0 }: ServiceCardProps) {
  const name = service.name[lang] || service.name["en"] || "";
  const description = service.description[lang] || service.description["en"] || "";
  const icon = service.icon || "heart";

  return (
    <div
      className="card group hover:shadow-elevated transition-all duration-300
                 hover:-translate-y-1 animate-fade-up flex flex-col"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4
                      group-hover:bg-primary/20 transition-colors duration-200">
        <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          {ICONS[icon] ?? ICONS["heart"]}
        </svg>
      </div>

      <h3 className="font-display text-xl text-[var(--color-text)] mb-2">{name}</h3>
      <p className="text-[var(--color-muted)] text-sm leading-relaxed mb-4 flex-1">
        {description}
      </p>

      <div className="flex items-center justify-between mt-auto pt-4
                      border-t border-[var(--color-border)]">
        <span className="text-xs text-[var(--color-muted)]">
          {service.durationMinutes} min
        </span>
        <Link
          href={`/book?service=${service.serviceId}`}
          className="text-sm text-primary font-medium hover:underline"
        >
          Book →
        </Link>
      </div>
    </div>
  );
}
