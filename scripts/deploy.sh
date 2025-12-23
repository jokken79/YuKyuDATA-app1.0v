#!/bin/bash

# deploy.sh
# Script de deployment seguro para YuKyuDATA
# Uso: ./scripts/deploy.sh [environment] [version]

set -euo pipefail

# ============================================
# CONFIGURACIÓN
# ============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

ENVIRONMENT="${1:-staging}"
VERSION="${2:-latest}"
LOG_FILE="/var/log/yukyu-deploy.log"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================
# FUNCIONES
# ============================================

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "$LOG_FILE"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*" | tee -a "$LOG_FILE"
}

# ============================================
# PRE-DEPLOYMENT CHECKS
# ============================================

check_requirements() {
    log "Checking requirements..."

    # Verificar Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
    fi

    # Verificar Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
    fi

    # Verificar git
    if ! command -v git &> /dev/null; then
        error "Git is not installed"
    fi

    # Verificar que estamos en un repo git
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        error "Not in a git repository"
    fi

    log "All requirements met"
}

check_environment() {
    log "Checking environment configuration..."

    # Verificar archivo .env
    if [ ! -f ".env.$ENVIRONMENT" ]; then
        error "Environment file .env.$ENVIRONMENT not found"
    fi

    # Verificar que no hay secrets en git
    if git log -p | grep -i "password\|secret\|api_key" > /dev/null; then
        error "Secrets detected in git history!"
    fi

    log "Environment configuration OK"
}

build_image() {
    log "Building Docker image..."

    docker build \
        -f Dockerfile.secure \
        -t yukyu-app:$VERSION \
        -t yukyu-app:$ENVIRONMENT \
        --label "com.yukyu.version=$VERSION" \
        --label "com.yukyu.environment=$ENVIRONMENT" \
        --label "com.yukyu.build-date=$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        . || error "Docker build failed"

    log "Image built successfully: yukyu-app:$VERSION"
}

scan_image() {
    log "Scanning Docker image for vulnerabilities..."

    if command -v trivy &> /dev/null; then
        trivy image \
            --severity HIGH,CRITICAL \
            --exit-code 1 \
            --no-progress \
            yukyu-app:$VERSION || error "Critical vulnerabilities found in image"

        log "Image scan passed"
    else
        warning "Trivy not installed, skipping vulnerability scan"
    fi
}

push_image() {
    log "Pushing image to registry..."

    REGISTRY="${REGISTRY:-ghcr.io}"
    REPO="${REPO:-myorg/yukyu-app}"

    docker tag yukyu-app:$VERSION $REGISTRY/$REPO:$VERSION
    docker tag yukyu-app:$VERSION $REGISTRY/$REPO:$ENVIRONMENT

    docker push $REGISTRY/$REPO:$VERSION || error "Failed to push image"
    docker push $REGISTRY/$REPO:$ENVIRONMENT || error "Failed to push image"

    log "Image pushed to registry"
}

backup_database() {
    log "Creating database backup..."

    BACKUP_DIR="/backups"
    BACKUP_FILE="$BACKUP_DIR/yukyu-backup-$(date +%Y%m%d-%H%M%S).sql"

    mkdir -p "$BACKUP_DIR"

    # Usar el container de PostgreSQL existente
    docker-compose \
        -f docker-compose.secure.yml \
        exec -T db \
        pg_dump -U ${DB_USER} -d ${DB_NAME} \
        > "$BACKUP_FILE" || error "Database backup failed"

    # Comprimir backup
    gzip "$BACKUP_FILE"

    log "Database backup created: ${BACKUP_FILE}.gz"
}

run_migrations() {
    log "Running database migrations..."

    docker-compose \
        -f docker-compose.secure.yml \
        exec -T app \
        python scripts/run_migrations.py || error "Database migrations failed"

    log "Database migrations completed"
}

deploy_staging() {
    log "Deploying to staging..."

    check_environment
    build_image
    scan_image

    # Deploy to Docker Compose
    docker-compose \
        -f docker-compose.secure.yml \
        --env-file .env.$ENVIRONMENT \
        pull || warning "Failed to pull images"

    docker-compose \
        -f docker-compose.secure.yml \
        --env-file .env.$ENVIRONMENT \
        up -d || error "Docker Compose up failed"

    log "Staging deployment completed"
}

deploy_production() {
    log "Deploying to production..."

    # Extra checks para producción
    check_environment
    build_image
    scan_image

    # Backup
    backup_database

    # Usar ArgoCD para deployment
    if ! command -v argocd &> /dev/null; then
        error "ArgoCD is not installed"
    fi

    # Sync aplicación
    argocd app sync yukyu-app \
        --grpc-web \
        --server $ARGOCD_SERVER \
        --auth-token $ARGOCD_AUTH_TOKEN || error "ArgoCD sync failed"

    # Wait para que la app esté lista
    log "Waiting for application to be ready..."
    argocd app wait yukyu-app \
        --grpc-web \
        --server $ARGOCD_SERVER \
        --auth-token $ARGOCD_AUTH_TOKEN \
        --health \
        --timeout 5m || error "Application failed to become ready"

    log "Production deployment completed"
}

health_check() {
    log "Running health checks..."

    local url="$1"
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -f -s "$url/health" > /dev/null; then
            log "Health check passed"
            return 0
        fi

        attempt=$((attempt + 1))
        sleep 2
    done

    error "Health check failed after $max_attempts attempts"
}

smoke_tests() {
    log "Running smoke tests..."

    docker-compose \
        -f docker-compose.secure.yml \
        run --rm app \
        pytest smoke_tests/ -v || error "Smoke tests failed"

    log "Smoke tests passed"
}

rollback() {
    log "Rolling back deployment..."

    if [ "$ENVIRONMENT" = "production" ]; then
        argocd app rollout undo yukyu-app \
            --grpc-web \
            --server $ARGOCD_SERVER \
            --auth-token $ARGOCD_AUTH_TOKEN || error "Rollback failed"
    else
        docker-compose \
            -f docker-compose.secure.yml \
            down || warning "Failed to stop containers"
    fi

    log "Rollback completed"
}

create_incident() {
    log "Creating incident ticket..."

    if command -v curl &> /dev/null; then
        curl -X POST \
            -H "Authorization: Bearer $INCIDENT_API_TOKEN" \
            -H "Content-Type: application/json" \
            -d "{
                \"title\": \"Deployment failed for $ENVIRONMENT\",
                \"severity\": \"high\",
                \"description\": \"Deployment of version $VERSION to $ENVIRONMENT failed. Check logs: tail -f $LOG_FILE\"
            }" \
            "$INCIDENT_API_URL/incidents" || warning "Failed to create incident"
    fi
}

# ============================================
# MAIN FLOW
# ============================================

main() {
    log "========================================"
    log "YuKyuDATA Deployment Script"
    log "Environment: $ENVIRONMENT"
    log "Version: $VERSION"
    log "========================================"

    # Pre-flight checks
    check_requirements

    # Crear directorio de logs
    mkdir -p "$(dirname "$LOG_FILE")"

    case "$ENVIRONMENT" in
        staging)
            deploy_staging
            health_check "http://localhost:8000"
            smoke_tests
            ;;

        production)
            # Confirmation check
            echo -e "${YELLOW}WARNING: You are about to deploy to PRODUCTION${NC}"
            echo "Version: $VERSION"
            read -p "Type 'yes' to continue: " confirm

            if [ "$confirm" != "yes" ]; then
                log "Deployment cancelled"
                exit 0
            fi

            deploy_production
            health_check "https://yukyu-data.example.com"
            smoke_tests
            ;;

        *)
            error "Unknown environment: $ENVIRONMENT"
            ;;
    esac

    log "========================================"
    log "Deployment completed successfully!"
    log "========================================"
}

# ============================================
# ERROR HANDLING
# ============================================

trap 'error "Deployment failed"; create_incident' ERR

# ============================================
# EXECUTE
# ============================================

main "$@"
