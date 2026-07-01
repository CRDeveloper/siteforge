const path = require("path");
const fs = require("fs");

// Load site config — injected at build time via SITE_ID env var
function loadSiteConfig() {
  const siteId = process.env.SITE_ID || "serenity-therapy";
  const configPath = path.join(__dirname, "../../sites", siteId, "site-config.json");
  if (fs.existsSync(configPath)) {
    return JSON.parse(fs.readFileSync(configPath, "utf-8"));
  }
  console.warn(`[siteforge] No site-config.json found for SITE_ID="${siteId}"`);
  return {};
}

const siteConfig = loadSiteConfig();

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",           // Static export → S3
  trailingSlash: true,        // S3-friendly URLs
  images: {
    unoptimized: true,        // No Next.js image server in static mode
  },
  env: {
    // Inject site config values as build-time env vars
    NEXT_PUBLIC_SITE_ID: siteConfig.siteId || "",
    NEXT_PUBLIC_SITE_NAME: siteConfig.siteName || "",
    NEXT_PUBLIC_API_URL: process.env.API_URL || "",
    NEXT_PUBLIC_DEFAULT_LANG: siteConfig.defaultLang || "en",
    NEXT_PUBLIC_SUPPORTED_LANGS: JSON.stringify(siteConfig.supportedLangs || ["en"]),
    NEXT_PUBLIC_THEME: JSON.stringify(siteConfig.theme || {}),
    NEXT_PUBLIC_GA_TRACKING_ID: siteConfig.analytics?.gaTrackingId || process.env.GA_TRACKING_ID || "",
  },
  // next-intl config
  experimental: {},
};

const withNextIntl = require("next-intl/plugin")("./src/i18n/request.ts");

module.exports = withNextIntl(nextConfig);
