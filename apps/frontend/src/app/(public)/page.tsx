import { Metadata } from "next";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { api } from "@/lib/api";
import type { SiteConfig } from "shared-types";
import { ServiceCard } from "@/components/ui/ServiceCard";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";

// Loaded at build time (SSG)
async function getSiteConfig(): Promise<SiteConfig | null> {
  try {
    const { config } = await api.config();
    return config;
  } catch {
    return null;
  }
}

async function getServices() {
  try {
    const { services } = await api.services();
    return services;
  } catch {
    return [];
  }
}

export async function generateMetadata(): Promise<Metadata> {
  const config = await getSiteConfig();
  const lang = process.env.NEXT_PUBLIC_DEFAULT_LANG || "en";
  const seoData = (config?.seo as Record<string, { title: string; description: string; image?: string }> | undefined)?.[lang];
  const domain = config?.domain || "example.com";
  const baseUrl = `https://${domain}`;
  const ogImage = seoData?.image || `${baseUrl}/og-image.jpg`;

  return {
    title: seoData?.title || config?.siteName || "SiteForge",
    description: seoData?.description || "",
    openGraph: {
      title: seoData?.title || config?.siteName,
      description: seoData?.description || "",
      url: baseUrl,
      type: "website",
      siteName: config?.siteName || "SiteForge",
      locale: lang,
      images: [
        {
          url: ogImage,
          width: 1200,
          height: 630,
          alt: seoData?.title || config?.siteName || "SiteForge",
        },
      ],
    },
    alternates: {
      canonical: baseUrl,
    },
    robots: {
      index: true,
      follow: true,
      "max-image-preview": "large",
      "max-snippet": -1,
      "max-video-preview": -1,
    },
  };
}

export default async function HomePage() {
  const config = await getSiteConfig();
  const services = await getServices();
  const lang = process.env.NEXT_PUBLIC_DEFAULT_LANG || "en";
  const domain = config?.domain || "example.com";

  const hero = (config?.content as any)?.hero as Record<string, Record<string, string>> | undefined;
  const about = (config?.content as any)?.about as Record<string, Record<string, string>> | undefined;
  const contact = (config?.content as any)?.contact as Record<string, unknown> | undefined;

  // JSON-LD structured data
  const schemaData = {
    "@context": "https://schema.org",
    "@type": "LocalBusiness",
    name: config?.siteName || "SiteForge",
    description: config?.seo?.[lang]?.description || "",
    url: `https://${domain}`,
    image: config?.seo?.[lang]?.image || `https://${domain}/og-image.jpg`,
    telephone: (contact?.phone as string) || "",
    address: {
      "@type": "PostalAddress",
      streetAddress: (contact?.address as string) || "",
      addressCountry: "US",
    },
    contactPoint: {
      "@type": "ContactPoint",
      contactType: "Customer Service",
      email: config?.email?.adminEmail || "",
    },
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(schemaData) }}
      />
      <Header />
      <main>
        {/* ── Hero ─────────────────────────────────────────────── */}
        <section className="relative min-h-[90vh] flex items-center overflow-hidden bg-[var(--color-surface)]">
          {/* Decorative background blob */}
          <div
            className="absolute inset-0 opacity-[0.06] pointer-events-none"
            style={{
              background:
                "radial-gradient(ellipse 80% 60% at 60% 40%, var(--color-primary), transparent)",
            }}
          />
          <div className="absolute top-0 right-0 w-[45%] h-full opacity-10 pointer-events-none"
            style={{
              background: "radial-gradient(ellipse at top right, var(--color-accent), transparent 70%)"
            }}
          />

          <div className="container section relative z-10 grid md:grid-cols-2 gap-16 items-center">
            <div className="animate-fade-up">
              <p className="text-[var(--color-accent)] font-body font-medium tracking-widest uppercase text-sm mb-6">
                {config?.siteName}
              </p>
              <h1 className="heading-display text-[var(--color-text)] mb-6 leading-[1.1]">
                {hero?.[lang]?.title ?? "Find Your Peace"}
              </h1>
              <p className="text-lg text-[var(--color-muted)] mb-10 max-w-md leading-relaxed font-body">
                {hero?.[lang]?.subtitle ?? "Professional therapy tailored to your journey."}
              </p>
              <div className="flex flex-wrap gap-4">
                <Link href="/book" className="btn-primary text-base px-8 py-4">
                  {hero?.[lang]?.cta ?? "Book a Session"}
                </Link>
                <Link href="#services" className="btn-outline text-base px-8 py-4">
                  Our Services
                </Link>
              </div>
            </div>

            {/* Decorative card */}
            <div className="hidden md:block animate-fade-up animate-delay-200">
              <div className="relative">
                <div className="card p-10 text-center space-y-6"
                  style={{ background: "var(--color-surface-raised)" }}>
                  <div className="w-20 h-20 rounded-full bg-primary/10 mx-auto flex items-center justify-center">
                    <svg className="w-10 h-10 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                        d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                    </svg>
                  </div>
                  <div>
                    <p className="font-display text-2xl text-[var(--color-text)] mb-2">
                      "Growth begins at the edge of comfort."
                    </p>
                    <p className="text-[var(--color-muted)] text-sm">Serenity Therapy</p>
                  </div>
                  <div className="grid grid-cols-3 gap-4 pt-4 border-t border-[var(--color-border)]">
                    {["Individual", "Couples", "Trauma"].map((tag) => (
                      <span key={tag} className="text-xs font-medium text-primary bg-primary/10 px-3 py-1.5 rounded-full">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
                {/* Floating accent dot */}
                <div className="absolute -top-4 -right-4 w-8 h-8 rounded-full bg-accent opacity-60" />
                <div className="absolute -bottom-6 -left-6 w-14 h-14 rounded-full bg-primary/20" />
              </div>
            </div>
          </div>
        </section>

        {/* ── Services ──────────────────────────────────────────── */}
        <section id="services" className="section bg-[var(--color-surface-raised)]">
          <div className="container">
            <div className="text-center mb-16 animate-fade-up">
              <p className="text-[var(--color-accent)] font-medium tracking-widest uppercase text-sm mb-3">
                What We Offer
              </p>
              <h2 className="heading-section text-[var(--color-text)] mb-4">Our Services</h2>
              <p className="text-[var(--color-muted)] max-w-xl mx-auto">
                Compassionate, evidence-based care for every stage of your healing journey.
              </p>
            </div>

            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {services.map((service, i) => (
                <ServiceCard
                  key={service.serviceId}
                  service={service}
                  lang={lang}
                  delay={i * 100}
                />
              ))}
            </div>

            <div className="text-center mt-12">
              <Link href="/book" className="btn-primary px-10 py-4 text-base">
                Book an Appointment
              </Link>
            </div>
          </div>
        </section>

        {/* ── About ─────────────────────────────────────────────── */}
        <section id="about" className="section">
          <div className="container grid md:grid-cols-2 gap-16 items-center">
            <div>
              <p className="text-[var(--color-accent)] font-medium tracking-widest uppercase text-sm mb-3">
                About Us
              </p>
              <h2 className="heading-section mb-6">
                {about?.[lang]?.title ?? "About Our Practice"}
              </h2>
              <p className="text-[var(--color-muted)] leading-relaxed mb-8">
                {about?.[lang]?.body ?? "We offer a safe, confidential space for individuals and couples seeking support."}
              </p>
              <div className="grid grid-cols-2 gap-4">
                {[
                  { label: "Licensed Therapists", value: "4+" },
                  { label: "Years of Practice", value: "12+" },
                  { label: "Sessions Completed", value: "2,000+" },
                  { label: "Languages", value: "EN · ES" },
                ].map(({ label, value }) => (
                  <div key={label} className="card text-center py-6">
                    <div className="font-display text-3xl text-primary mb-1">{value}</div>
                    <div className="text-[var(--color-muted)] text-sm">{label}</div>
                  </div>
                ))}
              </div>
            </div>
            <div className="relative">
              <div className="aspect-[4/5] rounded-[var(--radius)] overflow-hidden bg-primary/10 flex items-center justify-center">
                <svg className="w-24 h-24 text-primary/30" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 7.2 4.5 7.2 7.2 9.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 4.8v2.4h19.2v-2.4c0-3.2-6.4-4.8-9.6-4.8z"/>
                </svg>
              </div>
              <div className="absolute -bottom-6 -right-6 card p-6 max-w-[200px]">
                <div className="text-[var(--color-accent)] text-4xl font-display mb-1">✦</div>
                <p className="text-sm text-[var(--color-muted)]">Confidential &amp; caring environment</p>
              </div>
            </div>
          </div>
        </section>

        {/* ── Contact ───────────────────────────────────────────── */}
        <section id="contact" className="section bg-[var(--color-surface-raised)]">
          <div className="container">
            <div className="text-center mb-12">
              <h2 className="heading-section mb-4">Find Us</h2>
            </div>
            <div className="grid md:grid-cols-3 gap-8 mb-12">
              {[
                {
                  icon: "📍",
                  label: "Address",
                  value: (contact?.address as string) || "123 Wellness Ave, Miami FL",
                },
                {
                  icon: "📞",
                  label: "Phone",
                  value: (contact?.phone as string) || "+1 (305) 555-0180",
                },
                {
                  icon: "🕐",
                  label: "Hours",
                  value: ((contact?.hours as Record<string, string>)?.[lang]) || "Mon–Fri 9am–7pm",
                },
              ].map(({ icon, label, value }) => (
                <div key={label} className="card text-center">
                  <div className="text-3xl mb-3">{icon}</div>
                  <div className="font-medium text-[var(--color-text)] mb-1">{label}</div>
                  <div className="text-[var(--color-muted)] text-sm">{value}</div>
                </div>
              ))}
            </div>

            <div className="text-center">
              <Link href="/book" className="btn-primary px-12 py-4 text-lg">
                Book Your Session Today
              </Link>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
