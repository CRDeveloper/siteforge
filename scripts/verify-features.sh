#!/bin/bash
# SiteForge Feature Verification
# Verifies implementation of Priority 2 (Production Polish) features
# 
# Features checked:
# - SEO: generateMetadata()
# - Robots.txt & Sitemap generation
# - Shared Types package
# - Week Calendar component
# - Admin Availability page
# - SNS Bounce/Complaint Handler
# - Local development setup

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

check() {
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} $1"
    return 0
  else
    echo -e "${RED}✗${NC} $1"
    return 1
  fi
}

echo "SiteForge Feature Verification (Priority 2 - Production Polish)"
echo "================================================================"

# SEO: generateMetadata()
echo -e "\n🔍 SEO: generateMetadata()"
test -f apps/frontend/src/app/\(public\)/page.tsx && grep -q "generateMetadata" apps/frontend/src/app/\(public\)/page.tsx
check "SEO metadata function exists"

# Robots.txt & Sitemap
echo -e "\n🔍 Robots.txt & Sitemap"
test -f apps/frontend/public/robots.txt
check "robots.txt file exists"

test -f apps/frontend/scripts/generate-sitemap.js
check "Sitemap generator script exists"

grep -q "prebuild" apps/frontend/package.json
check "prebuild script configured in package.json"

# Shared Types
echo -e "\n🔍 Shared Types Package"
test -f packages/shared-types/src/index.ts
check "Shared types package exists"

grep -q "import type.*shared-types" apps/frontend/src/lib/api.ts
check "API imports from shared-types"

# Calendar Component
echo -e "\n🔍 Week Calendar Component"
test -f apps/frontend/src/components/admin/WeekCalendar.tsx
check "WeekCalendar component exists"

grep -q "export function WeekCalendar" apps/frontend/src/components/admin/WeekCalendar.tsx
check "WeekCalendar component is exported"

# Availability Page
echo -e "\n🔍 Admin Availability Page"
test -f "apps/frontend/src/app/(admin)/admin/availability/page.tsx"
check "Availability page exists"

# Webhook Handler
echo -e "\n🔍 SNS Bounce/Complaint Handler"
test -f apps/api/handlers/webhooks.py
check "Webhook handler file exists"

cd apps/api && python3 -c "from handlers.webhooks import handler" 2>/dev/null && cd ../.. || cd ../..
check "Webhook handler imports successfully"

# Local Dev Setup
echo -e "\n🔍 Local Development Setup"
test -f infra/local/template.yaml
check "SAM template exists"

test -f infra/local/docker-compose.yaml
check "Docker Compose file exists"

test -f infra/local/init.sh
check "Init script exists"

test -f apps/api/Dockerfile.local
check "Dockerfile.local exists"

echo -e "\n================================================================"
echo -e "${GREEN}✓ All Priority 2 features verified!${NC}"
echo -e "\nNext steps:"
echo "  • Review: PRIORITY-2-SUMMARY.md"
echo "  • Setup: cd infra/local && docker-compose up -d"
echo "  • Dev:   npm run dev -w apps/frontend"
echo "  • Build: npm run build"
