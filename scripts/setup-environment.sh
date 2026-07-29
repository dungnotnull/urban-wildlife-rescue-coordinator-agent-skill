#!/usr/bin/env bash
# =============================================================================
# setup-environment.sh
#
# Environment setup script for urban-wildlife-rescue-coordinator
#
# This script automates the initial setup of the development environment
# including dependency installation, log directory creation, and validation.
#
# Usage:
#   ./scripts/setup-environment.sh [--skip-deps] [--dry-run]
#
# Options:
#   --skip-deps   Skip Python dependency installation
#   --dry-run     Show what would be done without making changes
# =============================================================================

set -euo pipefail

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SKIP_DEPS=false
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-deps)
            SKIP_DEPS=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

run_cmd() {
    local cmd="$1"
    if [ "$DRY_RUN" = true ]; then
        echo "DRY RUN: $cmd"
    else
        eval "$cmd"
    fi
}

# =============================================================================
# VALIDATION
# =============================================================================

validate_environment() {
    log_info "Validating environment..."

    # Check Python version
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | awk '{print $2}')
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
            log_info "Python version: $PYTHON_VERSION (OK)"
        else
            log_error "Python 3.11+ required, found $PYTHON_VERSION"
            exit 1
        fi
    else
        log_error "Python 3 not found"
        exit 1
    fi

    # Check project structure
    REQUIRED_DIRS=("config" "skills" "tools" "references" "assets")
    for dir in "${REQUIRED_DIRS[@]}"; do
        if [ -d "$PROJECT_ROOT/$dir" ]; then
            log_info "Directory exists: $dir/"
        else
            log_error "Required directory missing: $dir/"
            exit 1
        fi
    done

    log_info "Environment validation complete"
}

# =============================================================================
# DIRECTORY SETUP
# =============================================================================

setup_directories() {
    log_info "Setting up directories..."

    # Create log directory
    run_cmd "mkdir -p $PROJECT_ROOT/logs"
    log_info "Created logs/ directory"

    # Create scripts directory
    run_cmd "mkdir -p $PROJECT_ROOT/scripts"
    log_info "Created scripts/ directory"
}

# =============================================================================
# DEPENDENCY INSTALLATION
# =============================================================================

install_dependencies() {
    if [ "$SKIP_DEPS" = true ]; then
        log_warn "Skipping dependency installation (--skip-deps)"
        return
    fi

    log_info "Installing Python dependencies..."

    if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
        run_cmd "pip install -r $PROJECT_ROOT/requirements.txt"
        log_info "Dependencies installed"
    else
        log_warn "requirements.txt not found, skipping"
    fi
}

# =============================================================================
# VALIDATION
# =============================================================================

validate_project() {
    log_info "Validating project structure..."

    # Run project validator if available
    if [ -f "$PROJECT_ROOT/tools/validate_project.py" ]; then
        run_cmd "python3 $PROJECT_ROOT/tools/validate_project.py"
        log_info "Project validation complete"
    else
        log_warn "validate_project.py not found, skipping validation"
    fi
}

# =============================================================================
# KNOWLEDGE BASE SETUP
# =============================================================================

setup_knowledge_base() {
    log_info "Setting up knowledge base..."

    if [ ! -f "$PROJECT_ROOT/SECOND-KNOWLEDGE-BRAIN.md" ]; then
        log_error "SECOND-KNOWLEDGE-BRAIN.md not found"
        exit 1
    fi

    log_info "Knowledge base found at SECOND-KNOWLEDGE-BRAIN.md"
}

# =============================================================================
# SUMMARY
# =============================================================================

print_summary() {
    log_info "Environment setup complete!"
    echo ""
    echo "Project: urban-wildlife-rescue-coordinator"
    echo "Root: $PROJECT_ROOT"
    echo "Python: $(python3 --version)"
    echo ""
    echo "Next steps:"
    echo "  1. Review CLAUDE.md for project overview"
    echo "  2. Run tests: python3 tools/test_knowledge_updater.py"
    echo "  3. Run scenarios: python3 tools/run_test_scenarios.py"
    echo "  4. Start development: see CONTRIBUTING.md"
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

main() {
    echo "============================================================================"
    echo "Urban Wildlife Rescue Coordinator - Environment Setup"
    echo "============================================================================"
    echo ""

    validate_environment
    setup_directories
    install_dependencies
    setup_knowledge_base
    validate_project
    print_summary
}

main "$@"
