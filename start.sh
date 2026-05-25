#!/usr/bin/env bash
# =============================================================================
# NutriMind – Quick Start Script
# Starts the full system (Backend + AI Models + Web + DB + Redis + Nginx)
# Usage: bash start.sh [dev|prod]
# =============================================================================

set -e
MODE="${1:-dev}"
BLUE='\033[0;34m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_err()   { echo -e "${RED}[ERR]${NC} $1"; }

check_deps() {
    for dep in docker docker-compose; do
        command -v "$dep" &>/dev/null || { log_err "Missing: $dep"; exit 1; }
    done
}

check_env() {
    if [ ! -f ".env" ]; then
        log_warn ".env not found. Copying .env.example → .env"
        cp .env.example .env
        log_warn "⚠️  Please edit .env and set GEMINI_API_KEY, then rerun."
        exit 1
    fi
    if grep -q "YOUR_GEMINI_API_KEY_HERE" .env; then
        log_err "GEMINI_API_KEY not set in .env"
        exit 1
    fi
}

start_dev() {
    log_info "Starting NutriMind in DEVELOPMENT mode..."
    docker-compose -f docker-compose.yml up -d --build
    log_ok "All services starting..."
    echo ""
    echo "  🌐 Web App:    http://localhost:3000"
    echo "  🔌 API:        http://localhost:8000/docs"
    echo "  🤖 AI Models:  http://localhost:8001/docs"
    echo "  📊 Grafana:    http://localhost:3001 (admin/admin)"
    echo ""
    log_info "Tailing logs (Ctrl+C to stop)..."
    docker-compose logs -f --tail=50
}

start_prod() {
    log_info "Starting NutriMind in PRODUCTION mode..."
    docker-compose -f docker-compose.prod.yml up -d --build
    log_ok "All services started!"
    echo ""
    echo "  🌐 Web App:    https://nutrimind.app"
    echo "  🔌 API:        https://nutrimind.app/api/v1/docs"
    echo ""
}

stop() {
    log_info "Stopping all services..."
    docker-compose down
    log_ok "Done."
}

status() {
    docker-compose ps
}

logs() {
    docker-compose logs -f "${@:2}"
}

check_deps
check_env

case "$MODE" in
    dev)    start_dev ;;
    prod)   start_prod ;;
    stop)   stop ;;
    status) status ;;
    logs)   logs "$@" ;;
    *)
        echo "Usage: bash start.sh [dev|prod|stop|status|logs]"
        exit 1
        ;;
esac
