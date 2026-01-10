#!/bin/bash
# docker-dev.sh - Start YuKyuDATA Development Environment
#
# Usage:
#   ./scripts/docker-dev.sh          # Start with build
#   ./scripts/docker-dev.sh --no-build   # Start without build
#   ./scripts/docker-dev.sh --rebuild    # Force rebuild
#   ./scripts/docker-dev.sh --stop       # Stop containers
#   ./scripts/docker-dev.sh --logs       # View logs
#   ./scripts/docker-dev.sh --test       # Run tests in container
#   ./scripts/docker-dev.sh --shell      # Open shell in container

set -e

# ============================================
# CONFIGURATION
# ============================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.dev.yml"
CONTAINER_NAME="yukyu-dev"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================
# FUNCTIONS
# ============================================

print_header() {
    echo ""
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}  YuKyuDATA Docker Development Environment${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi

    print_success "Docker is available"
}

check_compose() {
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    elif command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        print_error "Docker Compose is not installed."
        exit 1
    fi
    print_success "Docker Compose is available"
}

check_env_file() {
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        if [ -f "$PROJECT_DIR/.env.example" ]; then
            print_warning ".env file not found. Creating from .env.example..."
            cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
            print_success "Created .env file. Please review and update secrets."
        else
            print_warning ".env file not found. Using default environment variables."
        fi
    else
        print_success ".env file found"
    fi
}

start_dev() {
    local build_flag="$1"

    print_header
    check_docker
    check_compose
    check_env_file

    echo ""
    print_info "Starting development environment..."
    echo ""

    cd "$PROJECT_DIR"

    if [ "$build_flag" == "--rebuild" ]; then
        print_info "Forcing rebuild..."
        $COMPOSE_CMD -f "$COMPOSE_FILE" build --no-cache
    fi

    if [ "$build_flag" == "--no-build" ]; then
        $COMPOSE_CMD -f "$COMPOSE_FILE" up
    else
        $COMPOSE_CMD -f "$COMPOSE_FILE" up --build
    fi
}

stop_dev() {
    print_header
    check_compose

    print_info "Stopping development environment..."
    cd "$PROJECT_DIR"
    $COMPOSE_CMD -f "$COMPOSE_FILE" down

    print_success "Development environment stopped"
}

show_logs() {
    check_compose

    cd "$PROJECT_DIR"
    $COMPOSE_CMD -f "$COMPOSE_FILE" logs -f
}

run_tests() {
    print_header
    check_compose

    print_info "Running tests inside container..."
    cd "$PROJECT_DIR"

    if docker ps --format '{{.Names}}' | grep -q "$CONTAINER_NAME"; then
        $COMPOSE_CMD -f "$COMPOSE_FILE" exec app pytest tests/ -v
    else
        print_error "Container is not running. Start it first with: $0"
        exit 1
    fi
}

open_shell() {
    check_compose

    print_info "Opening shell in container..."
    cd "$PROJECT_DIR"

    if docker ps --format '{{.Names}}' | grep -q "$CONTAINER_NAME"; then
        $COMPOSE_CMD -f "$COMPOSE_FILE" exec app /bin/bash
    else
        print_error "Container is not running. Start it first with: $0"
        exit 1
    fi
}

show_status() {
    check_compose

    cd "$PROJECT_DIR"
    echo ""
    print_info "Container status:"
    $COMPOSE_CMD -f "$COMPOSE_FILE" ps
    echo ""
}

show_help() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  (none)       Start development environment with build"
    echo "  --no-build   Start without rebuilding the image"
    echo "  --rebuild    Force rebuild the image (no cache)"
    echo "  --stop       Stop the development environment"
    echo "  --logs       View container logs"
    echo "  --test       Run pytest inside the container"
    echo "  --shell      Open bash shell in the container"
    echo "  --status     Show container status"
    echo "  --help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Start with build"
    echo "  $0 --no-build         # Start without build"
    echo "  $0 --stop             # Stop containers"
    echo ""
    echo "Access the application at: http://localhost:8000"
}

# ============================================
# MAIN
# ============================================

case "${1:-}" in
    --no-build)
        start_dev "--no-build"
        ;;
    --rebuild)
        start_dev "--rebuild"
        ;;
    --stop)
        stop_dev
        ;;
    --logs)
        show_logs
        ;;
    --test)
        run_tests
        ;;
    --shell)
        open_shell
        ;;
    --status)
        show_status
        ;;
    --help|-h)
        show_help
        ;;
    "")
        start_dev "--build"
        ;;
    *)
        print_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac
