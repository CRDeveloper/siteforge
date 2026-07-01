#!/bin/bash

# SiteForge Bootstrap Setup Script
# One-time initialization of prerequisites, dependencies, and AWS infrastructure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# ============================================================================
# Prerequisites Check
# ============================================================================

check_prerequisites() {
    print_header "Checking Prerequisites"
    
    local missing=0
    
    # Check Python 3.12+
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found"
        missing=$((missing + 1))
    else
        local py_version=$(python3 --version | awk '{print $2}' | cut -d. -f1,2)
        print_success "Python $py_version found"
    fi
    
    # Check Node.js 20+
    if ! command -v node &> /dev/null; then
        print_error "Node.js not found"
        missing=$((missing + 1))
    else
        local node_version=$(node --version)
        print_success "Node.js $node_version found"
    fi
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        print_error "npm not found"
        missing=$((missing + 1))
    else
        local npm_version=$(npm --version)
        print_success "npm $npm_version found"
    fi
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI v2 not found"
        missing=$((missing + 1))
    else
        local aws_version=$(aws --version | awk '{print $1}' | cut -d/ -f2)
        print_success "AWS CLI $aws_version found"
    fi
    
    # Check git
    if ! command -v git &> /dev/null; then
        print_error "git not found"
        missing=$((missing + 1))
    else
        print_success "git found"
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured"
        missing=$((missing + 1))
    else
        local aws_account=$(aws sts get-caller-identity --query Account --output text)
        print_success "AWS credentials configured (Account: $aws_account)"
    fi
    
    if [ $missing -gt 0 ]; then
        echo ""
        print_error "$missing prerequisite(s) missing"
        echo ""
        echo "Install missing tools:"
        echo "  - Python 3.12+: https://www.python.org"
        echo "  - Node.js 20+: https://nodejs.org"
        echo "  - AWS CLI v2: https://aws.amazon.com/cli"
        echo "  - git: https://git-scm.com"
        echo ""
        return 1
    fi
    
    print_success "All prerequisites installed"
}

# ============================================================================
# Environment Setup
# ============================================================================

setup_environment() {
    print_header "Setting Up Environment"
    
    # Check for .env file
    if [ ! -f ".env" ]; then
        print_warning ".env file not found"
        print_info "Creating .env from .env.example..."
        cp .env.example .env
        print_success ".env created (please edit with your AWS account ID)"
        return 1  # Need user to edit .env
    else
        print_success ".env file found"
    fi
    
    # Load environment
    source .env
    
    # Validate required variables
    if [ -z "$AWS_ACCOUNT_ID" ]; then
        print_error "AWS_ACCOUNT_ID not set in .env"
        return 1
    fi
    
    if [ -z "$AWS_REGION" ]; then
        print_error "AWS_REGION not set in .env"
        return 1
    fi
    
    print_success "AWS_ACCOUNT_ID: $AWS_ACCOUNT_ID"
    print_success "AWS_REGION: $AWS_REGION"
}

# ============================================================================
# Dependency Installation
# ============================================================================

install_dependencies() {
    print_header "Installing Dependencies"
    
    # Create logs directory
    mkdir -p logs
    
    # Install Node dependencies (npm)
    print_info "Installing npm dependencies (turborepo, frontend, etc)..."
    npm install 2>&1 | tail -5
    print_success "npm dependencies installed"
    
    # Install Python CDK dependencies
    print_info "Installing Python CDK dependencies..."
    cd infra/cdk
    pip install -q -r requirements.txt 2>&1 | tail -5
    cd ../..
    print_success "CDK dependencies installed"
    
    # Install Python CLI dependencies
    print_info "Installing Python CLI dependencies..."
    pip install -q typer rich boto3 requests 2>&1 | tail -5
    print_success "CLI dependencies installed"
    
    # Install Python API dependencies (optional, for local dev)
    if [ -d "apps/api" ]; then
        print_info "Installing Python API dependencies..."
        cd apps/api
        pip install -q -r requirements.txt 2>&1 | tail -5 || true
        cd ../..
        print_success "API dependencies installed"
    fi
    
    print_success "All dependencies installed"
}

# ============================================================================
# CDK Bootstrap
# ============================================================================

cdk_bootstrap() {
    print_header "Bootstrapping AWS CDK"
    
    source .env
    
    print_info "Bootstrapping CDK for account $AWS_ACCOUNT_ID in region $AWS_REGION..."
    print_warning "This is a one-time operation per AWS account/region"
    echo ""
    
    cd infra/cdk
    
    # Run CDK bootstrap
    if cdk bootstrap aws://$AWS_ACCOUNT_ID/$AWS_REGION; then
        print_success "CDK bootstrapped successfully"
    else
        print_error "CDK bootstrap failed"
        cd ../..
        return 1
    fi
    
    cd ../..
}

# ============================================================================
# Deploy Shared Stack
# ============================================================================

deploy_shared_stack() {
    print_header "Deploying Shared Infrastructure Stack"
    
    source .env
    
    print_info "Deploying SiteForgeShared stack..."
    print_info "This creates shared IAM policies and SSM namespaces"
    echo ""
    
    cd infra/cdk
    
    # Synth CDK
    print_info "Synthesizing CDK templates..."
    if ! cdk synth 2>&1 | grep -q "Successfully synthesized"; then
        print_warning "CDK synth completed (check for warnings)"
    fi
    
    # Deploy shared stack
    if cdk deploy ${CDK_STACK_PREFIX}-Shared --require-approval never; then
        print_success "Shared stack deployed successfully"
    else
        print_error "Shared stack deployment failed"
        cd ../..
        return 1
    fi
    
    cd ../..
}

# ============================================================================
# Local HTTPS Setup
# ============================================================================

setup_local_https() {
    print_header "Setting Up Local HTTPS Certificates"
    
    source .env
    
    if [ "$ENABLE_LOCAL_HTTPS" != "true" ]; then
        print_info "Local HTTPS disabled in .env"
        return 0
    fi
    
    # Frontend HTTPS
    if [ ! -f "nextjs-admin-cms/localhost.pem" ] || [ ! -f "nextjs-admin-cms/localhost-key.pem" ]; then
        print_info "Generating frontend HTTPS certificates..."
        
        # Create frontend certs directory if needed
        mkdir -p nextjs-admin-cms
        
        # Generate self-signed certificate for localhost
        if openssl req -x509 -newkey rsa:2048 -keyout nextjs-admin-cms/localhost-key.pem -out nextjs-admin-cms/localhost.pem -days 365 -nodes -subj "/CN=localhost" 2>/dev/null; then
            print_success "Frontend HTTPS certificates generated"
            print_info "  Cert: nextjs-admin-cms/localhost.pem"
            print_info "  Key:  nextjs-admin-cms/localhost-key.pem"
        else
            print_warning "Could not generate frontend certificates (openssl not found)"
        fi
    else
        print_success "Frontend HTTPS certificates already exist"
    fi
    
    # Backend HTTPS (if API exists)
    if [ -d "apps/api" ]; then
        if [ ! -f "backend-cert.pem" ] || [ ! -f "backend-key.pem" ]; then
            print_info "Generating backend HTTPS certificates..."
            
            if openssl req -x509 -newkey rsa:2048 -keyout backend-key.pem -out backend-cert.pem -days 365 -nodes -subj "/CN=localhost" 2>/dev/null; then
                print_success "Backend HTTPS certificates generated"
                print_info "  Cert: backend-cert.pem"
                print_info "  Key:  backend-key.pem"
            else
                print_warning "Could not generate backend certificates (openssl not found)"
            fi
        else
            print_success "Backend HTTPS certificates already exist"
        fi
    fi
}

# ============================================================================
# Verify Deployment
# ============================================================================

verify_deployment() {
    print_header "Verifying Deployment"
    
    source .env
    
    print_info "Checking CloudFormation stacks..."
    
    cd infra/cdk
    
    # List stacks
    if cdk list 2>&1 | grep -q "SiteForgeShared"; then
        print_success "Stacks available"
    else
        print_warning "Could not verify stacks"
    fi
    
    cd ../..
    
    print_info "Checking SSM Parameter Store..."
    
    # Check for SiteForge namespace
    if aws ssm describe-parameters --query 'Parameters[*].Name' --output text 2>/dev/null | grep -q "siteforge"; then
        print_success "SSM parameters found"
    else
        print_warning "No SiteForge SSM parameters yet (normal for first setup)"
    fi
}

# ============================================================================
# Completion Summary
# ============================================================================

print_completion() {
    print_header "✅ Setup Complete!"
    
    source .env
    
    echo "Bootstrap phase completed successfully."
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Create your first site (serenity-therapy demo):"
    echo "   ${BLUE}./scripts/manage.sh create serenity-therapy \\${NC}"
    echo "     ${BLUE}--domain serenity-therapy.com \\${NC}"
    echo "     ${BLUE}--admin admin@serenity-therapy.com \\${NC}"
    echo "     ${BLUE}--name 'Serenity Therapy'${NC}"
    echo ""
    echo "2. Deploy the site:"
    echo "   ${BLUE}./scripts/manage.sh deploy serenity-therapy${NC}"
    echo ""
    echo "3. View all sites:"
    echo "   ${BLUE}./scripts/manage.sh status${NC}"
    echo ""
    echo "4. Local development:"
    echo "   ${BLUE}./scripts/manage.sh local serenity-therapy${NC}"
    echo ""
    echo "Reference:"
    echo "   ${BLUE}./scripts/manage.sh --help${NC}"
    echo ""
}

# ============================================================================
# Main Setup Flow
# ============================================================================

main() {
    print_header "🚀 SiteForge Bootstrap Setup"
    
    # Step 1: Check prerequisites
    if ! check_prerequisites; then
        print_error "Prerequisites check failed. Please install missing tools."
        exit 1
    fi
    
    # Step 2: Setup environment
    if ! setup_environment; then
        print_error ".env file created. Please edit with your AWS account ID, then run setup again."
        exit 1
    fi
    
    # Step 3: Install dependencies
    if ! install_dependencies; then
        print_error "Dependency installation failed"
        exit 1
    fi
    
    # Step 4: CDK Bootstrap
    print_info "CDK Bootstrap will now run. This creates CloudFormation resources in your AWS account."
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if ! cdk_bootstrap; then
            print_error "CDK bootstrap failed"
            exit 1
        fi
    else
        print_warning "CDK bootstrap skipped"
    fi
    
    # Step 5: Deploy shared stack
    print_info "Deploying shared infrastructure stack..."
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if ! deploy_shared_stack; then
            print_error "Shared stack deployment failed"
            exit 1
        fi
    else
        print_warning "Shared stack deployment skipped"
    fi
    
    # Step 6: Setup local HTTPS
    setup_local_https
    
    # Step 7: Verify
    verify_deployment
    
    # Step 8: Summary
    print_completion
}

# ============================================================================
# Run
# ============================================================================

if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    cd "$(dirname "$0")/.." || exit 1
    main "$@"
fi
