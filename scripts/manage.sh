#!/bin/bash

# SiteForge Management Script
# Handles site creation, deployment, local development, and cleanup
# Includes Slack integration for deployment notifications

set -o pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ============================================================================
# Utility Functions
# ============================================================================

print_header() {
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_subheader() {
    echo ""
    echo -e "${CYAN}── $1${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Slack notification wrapper
slack_notify() {
    local message=$1
    
    if [ "$SLACK_NOTIFICATIONS_ENABLED" = "true" ]; then
        python3 scripts/slack_notifier.py --message "$message" 2>/dev/null || true
    fi
}

# Load environment
load_env() {
    if [ ! -f ".env" ]; then
        print_error ".env not found"
        print_info "Run: ./scripts/setup.sh"
        exit 1
    fi
    source .env
}

# Check if site config exists
check_site_exists() {
    local site_id=$1
    if [ ! -f "sites/$site_id/site-config.json" ]; then
        print_error "Site '$site_id' not found"
        return 1
    fi
    return 0
}

# ============================================================================
# Help/Usage
# ============================================================================

print_usage() {
    cat << 'EOF'

USAGE: ./scripts/manage.sh [COMMAND] [OPTIONS]

COMMANDS:

  init
    Bootstrap AWS CDK and deploy shared stack (one-time setup)

  create <site-id> [OPTIONS]
    Create a new site
    OPTIONS:
      --domain DOMAIN              Domain name (e.g., example.com)
      --admin EMAIL                Admin email address
      --name NAME                  Site display name
      --color COLOR                Primary theme color (hex, e.g., #5c7a6e)

  deploy <site-id>
    Deploy frontend to S3 and invalidate CloudFront cache

  local <site-id>
    Start local development environment (frontend + optional backend)

  status
    Show all configured sites and deployment status

  logs <site-id>
    View recent logs for a site

  config <site-id> [--set KEY=VALUE]
    View or edit site configuration

  cleanup
    Stop local servers and free ports

  destroy <site-id>
    Destroy a site (⚠️ irreversible, with confirmation)

  help
    Show this help message

EXAMPLES:

  # Initial setup (run once)
  ./scripts/manage.sh init

  # Create a demo site
  ./scripts/manage.sh create serenity-therapy \
    --domain serenity-therapy.com \
    --admin admin@serenity-therapy.com \
    --name "Serenity Therapy" \
    --color "#5c7a6e"

  # Deploy site
  ./scripts/manage.sh deploy serenity-therapy

  # Local development
  ./scripts/manage.sh local serenity-therapy

  # View all sites
  ./scripts/manage.sh status

EOF
}

# ============================================================================
# Commands: Init
# ============================================================================

cmd_init() {
    print_header "🚀 Initializing SiteForge"
    
    print_info "Running bootstrap setup..."
    print_info "This is a one-time operation"
    echo ""
    
    if [ ! -f "scripts/setup.sh" ]; then
        print_error "setup.sh not found"
        return 1
    fi
    
    # Run setup script
    bash scripts/setup.sh
    
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        print_error "Setup failed"
        return $exit_code
    fi
    
    print_success "Initialization complete"
}

# ============================================================================
# Commands: Create Site
# ============================================================================

cmd_create() {
    local site_id=$1
    shift
    
    if [ -z "$site_id" ]; then
        print_error "Site ID required"
        print_info "Usage: ./scripts/manage.sh create <site-id> [--domain DOMAIN] [--admin EMAIL] [--name NAME]"
        return 1
    fi
    
    # Parse arguments
    local domain=""
    local admin=""
    local name=""
    local color="#3b82f6"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --domain) domain="$2"; shift 2 ;;
            --admin) admin="$2"; shift 2 ;;
            --name) name="$2"; shift 2 ;;
            --color) color="$2"; shift 2 ;;
            *) print_error "Unknown option: $1"; return 1 ;;
        esac
    done
    
    # Validate inputs
    if [ -z "$domain" ] || [ -z "$admin" ] || [ -z "$name" ]; then
        print_error "Missing required options"
        print_info "Usage: ./scripts/manage.sh create $site_id --domain DOMAIN --admin EMAIL --name NAME [--color COLOR]"
        return 1
    fi
    
    print_header "Creating Site: $site_id"
    
    print_info "Site ID:        $site_id"
    print_info "Domain:         $domain"
    print_info "Admin Email:    $admin"
    print_info "Display Name:   $name"
    print_info "Theme Color:    $color"
    echo ""
    
    # Run siteforge CLI create
    print_info "Running siteforge create command..."
    if python -m cli.siteforge create \
        --id "$site_id" \
        --domain "$domain" \
        --admin "$admin" \
        --name "$name" \
        --color "$color"; then
        
        print_success "Site created successfully"
        
        # Send Slack notification - site created
        if [ "$SLACK_NOTIFICATIONS_ENABLED" = "true" ]; then
            python3 << EOF
from scripts.slack_notifier import SlackNotifier
notifier = SlackNotifier(
    secret_name="${SLACK_SECRET_NAME}",
    region_name="${SLACK_REGION}",
    enabled=True
)
notifier.send_site_created("$site_id", "$domain", "$name")
EOF
        fi
        
        # Next steps
        echo ""
        print_info "Next steps:"
        echo "  1. Set up Brevo email (see docs/02-brevo-setup-guide.md)"
        echo "  2. Deploy: ./scripts/manage.sh deploy $site_id"
        echo "  3. Local dev: ./scripts/manage.sh local $site_id"
        echo ""
        
        return 0
    else
        print_error "Site creation failed"
        return 1
    fi
}

# ============================================================================
# Commands: Deploy Site
# ============================================================================

cmd_deploy() {
    local site_id=$1
    
    if [ -z "$site_id" ]; then
        print_error "Site ID required"
        return 1
    fi
    
    if ! check_site_exists "$site_id"; then
        return 1
    fi
    
    print_header "Deploying Site: $site_id"
    
    # Send Slack notification - started
    if [ "$SLACK_NOTIFICATIONS_ENABLED" = "true" ]; then
        python3 << EOF
from scripts.slack_notifier import SlackNotifier
notifier = SlackNotifier(
    secret_name="${SLACK_SECRET_NAME}",
    region_name="${SLACK_REGION}",
    enabled=True
)
notifier.send_deployment_started("$site_id")
EOF
    fi
    
    # Run siteforge CLI deploy
    print_info "Building and deploying frontend..."
    if python -m cli.siteforge deploy --id "$site_id"; then
        print_success "Site deployed successfully"
        
        echo ""
        print_info "Deployment complete:"
        local domain=$(grep -o '"domain":"[^"]*"' "sites/$site_id/site-config.json" | cut -d'"' -f4)
        echo "  Site URL: https://$domain"
        echo "  Admin:    https://$domain/admin"
        echo ""
        
        # Send Slack notification - completed
        if [ "$SLACK_NOTIFICATIONS_ENABLED" = "true" ]; then
            python3 << EOF
from scripts.slack_notifier import SlackNotifier
notifier = SlackNotifier(
    secret_name="${SLACK_SECRET_NAME}",
    region_name="${SLACK_REGION}",
    enabled=True
)
notifier.send_deployment_completed("$site_id", domain="$domain")
EOF
        fi
        
        return 0
    else
        print_error "Deployment failed"
        
        # Send Slack notification - failed
        if [ "$SLACK_NOTIFICATIONS_ENABLED" = "true" ]; then
            python3 << EOF
from scripts.slack_notifier import SlackNotifier
notifier = SlackNotifier(
    secret_name="${SLACK_SECRET_NAME}",
    region_name="${SLACK_REGION}",
    enabled=True
)
notifier.send_deployment_failed("$site_id", step="Frontend Build & Deploy", error="siteforge deploy command failed")
EOF
        fi
        
        return 1
    fi
}

# ============================================================================
# Commands: Local Development
# ============================================================================

cmd_local() {
    local site_id=$1
    
    if [ -z "$site_id" ]; then
        print_error "Site ID required"
        return 1
    fi
    
    if ! check_site_exists "$site_id"; then
        return 1
    fi
    
    print_header "🎨 Local Development Environment: $site_id"
    
    # Cleanup function
    cleanup_local() {
        echo ""
        echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${YELLOW}Shutting down local environment...${NC}"
        echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        
        # Kill next.js dev server on port 7000
        if lsof -Pi :7000 -sTCP:LISTEN -t >/dev/null 2>&1; then
            print_info "Stopping Next.js on port 7000..."
            fuser -k 7000/tcp 2>/dev/null || true
            sleep 1
            if ! lsof -Pi :7000 -sTCP:LISTEN -t >/dev/null 2>&1; then
                print_success "Port 7000 freed ✓"
            else
                print_warning "Port 7000 still in use, forcing..."
                fuser -9k 7000/tcp 2>/dev/null || true
                sleep 1
                print_success "Port 7000 freed ✓"
            fi
        else
            print_success "Port 7000 already free"
        fi
        
        # Kill npm dev processes
        if pgrep -f "npm.*dev" >/dev/null 2>&1; then
            print_info "Stopping npm dev processes..."
            pkill -f "npm.*dev" 2>/dev/null || true
            sleep 1
            print_success "npm processes stopped ✓"
        fi
        
        # Kill Next.js build process if still running
        if pgrep -f "node.*next" >/dev/null 2>&1; then
            print_info "Stopping Node.js processes..."
            pkill -f "node.*next" 2>/dev/null || true
            sleep 1
            print_success "Node.js processes stopped ✓"
        fi
        
        echo ""
        echo -e "${GREEN}✓ Local environment stopped${NC}"
        echo -e "${GREEN}✓ All ports freed${NC}"
        echo ""
    }
    
    # Set trap for cleanup on EXIT (Ctrl+C, 'q', or normal exit)
    trap cleanup_local SIGINT SIGTERM EXIT
    
    # Kill any existing process on port 7000
    if lsof -Pi :7000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Port 7000 already in use, freeing..."
        fuser -k 7000/tcp 2>/dev/null || true
        sleep 1
    fi
    
    # Set environment
    export SITE_ID="$site_id"
    
    print_info "Starting Next.js development server..."
    print_info "SITE_ID=$site_id"
    print_info "Port: 7000"
    echo ""
    
    # Check for HTTPS certificates
    if [ -f "nextjs-admin-cms/localhost.pem" ] && [ -f "nextjs-admin-cms/localhost-key.pem" ]; then
        print_success "HTTPS certificates found"
        HTTPS_ENABLED=true
    else
        print_warning "HTTPS certificates not found (will run on HTTP)"
        HTTPS_ENABLED=false
    fi
    
    # Start dev server
    cd apps/frontend
    
    # Clean .next
    rm -rf .next 2>/dev/null || true
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        print_info "Installing dependencies..."
        npm install >/dev/null 2>&1
    fi
    
    print_header "Next.js Dev Server Running"
    echo ""
    echo "🎨 Frontend Dev Server"
    if [ "$HTTPS_ENABLED" = true ]; then
        echo "  HTTPS: https://localhost:7000"
    else
        echo "  HTTP:  http://localhost:7000"
    fi
    echo ""
    echo "📚 Keyboard Shortcuts:"
    echo "  - Press 'r'       → Rebuild on file changes"
    echo "  - Press 'o'       → Open in browser"
    echo "  - Press 'q'       → Stop dev server"
    echo "  - Ctrl+C          → Stop dev server"
    echo ""
    echo "🧹 Cleanup:"
    echo "  - When you exit (q or Ctrl+C), port 7000 will be automatically freed"
    echo "  - All processes will be stopped cleanly"
    echo ""
    
    # Start Next.js dev on port 7000
    SITE_ID="$site_id" PORT=7000 npm run dev
    
    cd ../..
}

# ============================================================================
# Commands: Status
# ============================================================================

cmd_status() {
    print_header "📊 SiteForge Status"
    
    load_env
    
    # Count sites
    local site_count=$(find sites -maxdepth 1 -mindepth 1 -type d | wc -l)
    
    if [ $site_count -eq 0 ]; then
        print_warning "No sites configured yet"
        print_info "Create a site: ./scripts/manage.sh create <site-id>"
        return 0
    fi
    
    print_info "Total sites: $site_count"
    echo ""
    
    # List sites using existing CLI
    python -m cli.siteforge list
    
    echo ""
    print_info "AWS Infrastructure:"
    echo "  Region:  $AWS_REGION"
    echo "  Account: $AWS_ACCOUNT_ID"
    echo ""
}

# ============================================================================
# Commands: Logs
# ============================================================================

cmd_logs() {
    local site_id=$1
    
    if [ -z "$site_id" ]; then
        print_error "Site ID required"
        return 1
    fi
    
    if ! check_site_exists "$site_id"; then
        return 1
    fi
    
    print_header "📋 Logs: $site_id"
    
    # Check for CloudFront logs
    local domain=$(grep -o '"domain":"[^"]*"' "sites/$site_id/site-config.json" | cut -d'"' -f4)
    
    print_info "CloudFront Domain: $domain"
    print_info "View full logs in AWS CloudWatch"
    echo ""
    
    print_info "Getting recent errors from CloudWatch..."
    
    # Try to get Lambda logs
    aws logs tail "/aws/lambda/$site_id-api" --follow --since 1h 2>/dev/null || print_warning "No logs found"
}

# ============================================================================
# Commands: Config
# ============================================================================

cmd_config() {
    local site_id=$1
    shift
    
    if [ -z "$site_id" ]; then
        print_error "Site ID required"
        return 1
    fi
    
    if ! check_site_exists "$site_id"; then
        return 1
    fi
    
    # If no arguments, show config
    if [ $# -eq 0 ]; then
        print_header "Configuration: $site_id"
        cat "sites/$site_id/site-config.json" | python -m json.tool
        return 0
    fi
    
    # Otherwise, use CLI config command
    python -m cli.siteforge config --id "$site_id" "$@"
}

# ============================================================================
# Commands: Cleanup
# ============================================================================

cmd_cleanup() {
    print_header "🧹 Cleanup: Freeing Ports & Stopping Servers"
    
    # Free port 7000 (Next.js - SiteForge)
    if lsof -Pi :7000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_info "Freeing port 7000..."
        fuser -k 7000/tcp 2>/dev/null && print_success "Port 7000 freed" || print_warning "Could not free port 7000"
    else
        print_success "Port 7000 already free"
    fi
    
    # Free port 8200 (API - SiteForge)
    if lsof -Pi :8200 -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_info "Freeing port 8200..."
        fuser -k 8200/tcp 2>/dev/null && print_success "Port 8200 freed" || print_warning "Could not free port 8200"
    else
        print_success "Port 8200 already free"
    fi
    
    # Kill npm processes
    if pgrep -f "npm.*dev" >/dev/null 2>&1; then
        print_info "Stopping npm dev processes..."
        pkill -f "npm.*dev" 2>/dev/null && print_success "npm processes stopped"
    else
        print_success "No npm dev processes"
    fi
    
    echo ""
    print_success "Cleanup complete"
}

# ============================================================================
# Commands: Destroy Site
# ============================================================================

cmd_destroy() {
    local site_id=$1
    
    if [ -z "$site_id" ]; then
        print_error "Site ID required"
        return 1
    fi
    
    if ! check_site_exists "$site_id"; then
        return 1
    fi
    
    print_header "🔴 DESTROYING SITE: $site_id"
    print_error "This action is IRREVERSIBLE"
    echo ""
    echo "This will:"
    echo "  - Delete CloudFormation stack for $site_id"
    echo "  - Delete all AWS resources (Lambda, S3, DynamoDB, etc.)"
    echo "  - Delete site configuration"
    echo ""
    
    # Confirmation
    read -p "Type the site ID to confirm: " confirm
    if [ "$confirm" != "$site_id" ]; then
        print_warning "Cancelled"
        return 1
    fi
    
    print_info "Running siteforge destroy..."
    python -m cli.siteforge destroy --id "$site_id"
    
    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        print_success "Site destroyed"
        
        # Send Slack notification - site destroyed
        if [ "$SLACK_NOTIFICATIONS_ENABLED" = "true" ]; then
            python3 << EOF
from scripts.slack_notifier import SlackNotifier
notifier = SlackNotifier(
    secret_name="${SLACK_SECRET_NAME}",
    region_name="${SLACK_REGION}",
    enabled=True
)
notifier.send_site_destroyed("$site_id")
EOF
        fi
    else
        print_error "Destruction failed"
        return $exit_code
    fi
}

# ============================================================================
# Main Router
# ============================================================================

main() {
    local cmd=$1
    shift
    
    # Load environment for most commands
    case "$cmd" in
        init|help|"") ;;
        *) load_env ;;
    esac
    
    case "$cmd" in
        init)       cmd_init "$@" ;;
        create)     cmd_create "$@" ;;
        deploy)     cmd_deploy "$@" ;;
        local)      cmd_local "$@" ;;
        status)     cmd_status "$@" ;;
        logs)       cmd_logs "$@" ;;
        config)     cmd_config "$@" ;;
        cleanup)    cmd_cleanup "$@" ;;
        destroy)    cmd_destroy "$@" ;;
        help|"")    print_usage ;;
        *)          print_error "Unknown command: $cmd"; print_usage; exit 1 ;;
    esac
}

# ============================================================================
# Run
# ============================================================================

if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    cd "$(dirname "$0")/.." || exit 1
    main "$@"
fi
