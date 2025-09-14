#!/bin/bash

# HelloStockBuy Deployment Script
# This script handles deployment to different environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-development}
COMPOSE_FILE="docker-compose.yml"
BACKUP_DIR="./backups"
LOG_FILE="./deploy.log"

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a $LOG_FILE
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a $LOG_FILE
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a $LOG_FILE
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a $LOG_FILE
    exit 1
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        error "Docker is not running. Please start Docker and try again."
    fi
}

# Check if Docker Compose is available
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed. Please install Docker Compose and try again."
    fi
}

# Check environment file
check_env_file() {
    if [ ! -f ".env" ]; then
        error ".env file not found. Please copy .env.example to .env and configure it."
    fi
}

# Backup database
backup_database() {
    if [ "$ENVIRONMENT" = "production" ]; then
        log "Creating database backup..."
        mkdir -p $BACKUP_DIR
        BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"
        
        if docker-compose exec -T db pg_dump -U $POSTGRES_USER $POSTGRES_DB > $BACKUP_FILE; then
            success "Database backup created: $BACKUP_FILE"
        else
            warning "Failed to create database backup"
        fi
    fi
}

# Pull latest images
pull_images() {
    log "Pulling latest Docker images..."
    docker-compose pull
}

# Build images
build_images() {
    log "Building Docker images..."
    docker-compose build --no-cache
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    docker-compose exec backend alembic upgrade head
}

# Start services
start_services() {
    log "Starting services..."
    docker-compose up -d
    
    # Wait for services to be healthy
    log "Waiting for services to be healthy..."
    sleep 30
    
    # Check if services are running
    if docker-compose ps | grep -q "Up"; then
        success "Services started successfully"
    else
        error "Failed to start services"
    fi
}

# Stop services
stop_services() {
    log "Stopping services..."
    docker-compose down
}

# Clean up old images
cleanup() {
    log "Cleaning up old Docker images..."
    docker image prune -f
    docker volume prune -f
}

# Health check
health_check() {
    log "Performing health check..."
    
    # Check backend
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        success "Backend is healthy"
    else
        error "Backend health check failed"
    fi
    
    # Check frontend
    if curl -f http://localhost:3001 > /dev/null 2>&1; then
        success "Frontend is healthy"
    else
        error "Frontend health check failed"
    fi
}

# Show logs
show_logs() {
    log "Showing recent logs..."
    docker-compose logs --tail=50
}

# Main deployment function
deploy() {
    log "Starting deployment to $ENVIRONMENT environment..."
    
    # Pre-deployment checks
    check_docker
    check_docker_compose
    check_env_file
    
    # Set compose file based on environment
    if [ "$ENVIRONMENT" = "production" ]; then
        COMPOSE_FILE="docker-compose.prod.yml"
        backup_database
    fi
    
    # Stop existing services
    stop_services
    
    # Pull and build images
    pull_images
    build_images
    
    # Start services
    start_services
    
    # Run migrations
    run_migrations
    
    # Health check
    health_check
    
    # Cleanup
    cleanup
    
    success "Deployment completed successfully!"
    
    # Show service status
    log "Service status:"
    docker-compose ps
    
    # Show logs
    show_logs
}

# Rollback function
rollback() {
    log "Rolling back to previous version..."
    
    # Stop current services
    stop_services
    
    # Restore from backup if available
    LATEST_BACKUP=$(ls -t $BACKUP_DIR/*.sql 2>/dev/null | head -n1)
    if [ -n "$LATEST_BACKUP" ]; then
        log "Restoring database from backup: $LATEST_BACKUP"
        docker-compose up -d db
        sleep 10
        docker-compose exec -T db psql -U $POSTGRES_USER -d $POSTGRES_DB < $LATEST_BACKUP
    fi
    
    # Start services
    start_services
    
    success "Rollback completed!"
}

# Show help
show_help() {
    echo "HelloStockBuy Deployment Script"
    echo ""
    echo "Usage: $0 [ENVIRONMENT] [COMMAND]"
    echo ""
    echo "Environments:"
    echo "  development  - Deploy to development environment (default)"
    echo "  production   - Deploy to production environment"
    echo ""
    echo "Commands:"
    echo "  deploy       - Deploy the application (default)"
    echo "  rollback     - Rollback to previous version"
    echo "  stop         - Stop all services"
    echo "  start        - Start all services"
    echo "  restart      - Restart all services"
    echo "  logs         - Show service logs"
    echo "  status       - Show service status"
    echo "  health       - Perform health check"
    echo "  help         - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Deploy to development"
    echo "  $0 production         # Deploy to production"
    echo "  $0 production rollback # Rollback production"
    echo "  $0 logs               # Show logs"
}

# Main script logic
case "${2:-deploy}" in
    deploy)
        deploy
        ;;
    rollback)
        rollback
        ;;
    stop)
        stop_services
        ;;
    start)
        start_services
        ;;
    restart)
        stop_services
        start_services
        ;;
    logs)
        show_logs
        ;;
    status)
        docker-compose ps
        ;;
    health)
        health_check
        ;;
    help)
        show_help
        ;;
    *)
        error "Unknown command: $2. Use '$0 help' for usage information."
        ;;
esac
