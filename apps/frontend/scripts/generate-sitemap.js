/**
 * Sitemap generator — runs at build time to create sitemap.xml
 * Add to package.json scripts: "prebuild": "node scripts/generate-sitemap.js"
 */

const fs = require("fs");
const path = require("path");

async function generateSitemap() {
  const domain = process.env.NEXT_PUBLIC_DOMAIN || "serenity-therapy.com";
  const baseUrl = `https://${domain}`;

  const pages = [
    "",           // homepage
    "/book",      // booking page
    "/auth/login",
    "/auth/register",
    "/auth/forgot-password",
  ];

  const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${pages
  .map(
    (page) => `
  <url>
    <loc>${baseUrl}${page}</loc>
    <lastmod>${new Date().toISOString().split("T")[0]}</lastmod>
    <changefreq>${page === "" ? "weekly" : "monthly"}</changefreq>
    <priority>${page === "" ? "1.0" : "0.8"}</priority>
  </url>`
  )
  .join("")}
</urlset>`;

  const publicDir = path.join(__dirname, "../public");
  if (!fs.existsSync(publicDir)) {
    fs.mkdirSync(publicDir, { recursive: true });
  }

  fs.writeFileSync(path.join(publicDir, "sitemap.xml"), sitemap);
  console.log("✓ sitemap.xml generated");
}

generateSitemap().catch(console.error);
