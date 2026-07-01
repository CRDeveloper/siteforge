import type { Metadata } from "next";
import { NextIntlClientProvider } from "next-intl";
import { getLocale, getMessages } from "next-intl/server";
import { ThemeProvider } from "@/components/layout/ThemeProvider";
import { GoogleAnalytics } from "@/components/layout/GoogleAnalytics";
import { Providers } from "@/lib/providers";
import "@/styles/globals.css";

const siteName = process.env.NEXT_PUBLIC_SITE_NAME || "SiteForge";
const theme = JSON.parse(process.env.NEXT_PUBLIC_THEME || "{}");
const gaTrackingId = process.env.NEXT_PUBLIC_GA_TRACKING_ID || "";

export const metadata: Metadata = {
  title: siteName,
  description: "",
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const locale = await getLocale();
  const messages = await getMessages();

  const fontDisplay = theme.fontDisplay || "Cormorant Garamond";
  const fontBody = theme.fontBody || "DM Sans";

  // Build Google Fonts URL from site config fonts
  const googleFontsUrl = `https://fonts.googleapis.com/css2?family=${encodeURIComponent(
    fontDisplay
  )}:ital,wght@0,300;0,400;0,500;1,300;1,400&family=${encodeURIComponent(
    fontBody
  )}:wght@300;400;500;600&display=swap`;

  return (
    <html lang={locale} suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link href={googleFontsUrl} rel="stylesheet" />
      </head>
      <body>
        <GoogleAnalytics trackingId={gaTrackingId} />
        <ThemeProvider theme={theme}>
          <Providers>
            <NextIntlClientProvider locale={locale} messages={messages}>
              {children}
            </NextIntlClientProvider>
          </Providers>
        </ThemeProvider>
      </body>
    </html>
  );
}
