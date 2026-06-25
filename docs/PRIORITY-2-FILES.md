# Priority 2 — File Index

## Core Implementation

| Feature | File | LOC |
|---------|------|-----|
| SEO Metadata | `apps/frontend/src/app/(public)/page.tsx` | 50 |
| Sitemap Generator | `apps/frontend/scripts/generate-sitemap.js` | 40 |
| Robots.txt | `apps/frontend/public/robots.txt` | 10 |
| Shared Types | `packages/shared-types/src/index.ts` | 200 |
| Week Calendar | `apps/frontend/src/components/admin/WeekCalendar.tsx` | 150 |
| Availability Page | `apps/frontend/src/app/(admin)/admin/availability/page.tsx` | 120 |
| Webhook Handler | `apps/api/handlers/webhooks.py` | 130 |
| SAM Template | `infra/local/template.yaml` | 100 |
| Docker Compose | `infra/local/docker-compose.yaml` | 60 |
| Init Script | `infra/local/init.sh` | 50 |
| Dockerfile | `apps/api/Dockerfile.local` | 10 |

**Total: 1,200+ LOC**

## Documentation

- `docs/PRIORITY-2-SUMMARY.md` — Overview & quick start
- `docs/08-local-development-setup.md` — Local dev guide
- `scripts/verify-features.sh` — Feature verification (Priority 2)

## Updated Files

- `apps/frontend/src/app/(public)/page.tsx` — Added `generateMetadata()`
- `apps/frontend/src/lib/api.ts` — Imports from shared-types
- `apps/frontend/package.json` — Added prebuild script

---

**Quick Links:**
- Start local dev: `cd infra/local && docker-compose up -d`
- Run frontend: `npm run dev -w apps/frontend`
- Build with SEO: `npm run build`
- Verify features: `bash scripts/verify-features.sh`
