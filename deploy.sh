#!/bin/bash

# Deals89.store Deployment Script
# This script helps deploy the application with Docker and SSL certificates

set -e

echo "🚀 Starting Deals89.store deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p ssl logs backups instance

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        print_warning "Please edit .env file with your actual configuration before continuing."
        read -p "Press Enter to continue after editing .env file..."
    else
        print_error ".env.example file not found. Please create .env file manually."
        exit 1
    fi
fi

# Function to setup SSL certificates
setup_ssl() {
    print_status "Setting up SSL certificates..."
    
    read -p "Enter your domain name (e.g., deals89.store): " DOMAIN
    read -p "Enter your email for Let's Encrypt: " EMAIL
    
    if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
        print_error "Domain and email are required for SSL setup."
        return 1
    fi
    
    # Create temporary nginx config for certificate generation
    cat > nginx-temp.conf << EOF
events {
    worker_connections 1024;
}

http {
    server {
        listen 80;
        server_name $DOMAIN www.$DOMAIN;
        
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }
        
        location / {
            return 200 'OK';
            add_header Content-Type text/plain;
        }
    }
}
EOF

    # Start temporary nginx for certificate generation
    docker run -d --name nginx-temp \
        -p 80:80 \
        -v $(pwd)/nginx-temp.conf:/etc/nginx/nginx.conf:ro \
        -v certbot-www:/var/www/certbot \
        nginx:alpine

    # Generate SSL certificate
    docker run --rm \
        -v certbot-certs:/etc/letsencrypt \
        -v certbot-www:/var/www/certbot \
        certbot/certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        -d $DOMAIN -d www.$DOMAIN

    # Stop temporary nginx
    docker stop nginx-temp
    docker rm nginx-temp

    # Copy certificates to ssl directory
    docker run --rm \
        -v certbot-certs:/etc/letsencrypt \
        -v $(pwd)/ssl:/ssl \
        alpine:latest sh -c "
            cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem /ssl/
            cp /etc/letsencrypt/live/$DOMAIN/privkey.pem /ssl/
            chmod 644 /ssl/fullchain.pem
            chmod 600 /ssl/privkey.pem
        "

    # Clean up
    rm nginx-temp.conf
    docker volume rm certbot-www certbot-certs

    print_status "SSL certificates generated successfully!"
}

# Function to deploy application
deploy_app() {
    print_status "Building and starting the application..."
    
    # Build the application
    docker-compose build
    
    # Start the services
    docker-compose up -d
    
    # Wait for services to be ready
    print_status "Waiting for services to start..."
    sleep 10
    
    # Check if services are running
    if docker-compose ps | grep -q "Up"; then
        print_status "Application deployed successfully!"
        print_status "Your application should be available at:"
        if [ -f ssl/fullchain.pem ]; then
            echo "  https://your-domain.com"
        else
            echo "  http://localhost:5000"
        fi
    else
        print_error "Some services failed to start. Check logs with: docker-compose logs"
        exit 1
    fi
}

# Function to show logs
show_logs() {
    print_status "Showing application logs..."
    docker-compose logs -f
}

# Function to stop application
stop_app() {
    print_status "Stopping application..."
    docker-compose down
    print_status "Application stopped."
}

# Function to update application
update_app() {
    print_status "Updating application..."
    
    # Pull latest changes (if using git)
    if [ -d .git ]; then
        git pull
    fi
    
    # Rebuild and restart
    docker-compose down
    docker-compose build --no-cache
    docker-compose up -d
    
    print_status "Application updated successfully!"
}

# Function to backup database
backup_db() {
    print_status "Creating database backup..."
    docker-compose exec web python scheduler.py backup
    print_status "Database backup completed!"
}

# Main menu
case "${1:-}" in
    "ssl")
        setup_ssl
        ;;
    "deploy")
        deploy_app
        ;;
    "logs")
        show_logs
        ;;
    "stop")
        stop_app
        ;;
    "update")
        update_app
        ;;
    "backup")
        backup_db
        ;;
    "full")
        setup_ssl
        deploy_app
        ;;
    *)
        echo "Deals89.store Deployment Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  ssl     - Setup SSL certificates with Let's Encrypt"
        echo "  deploy  - Deploy the application"
        echo "  full    - Setup SSL and deploy (recommended for first time)"
        echo "  logs    - Show application logs"
        echo "  stop    - Stop the application"
        echo "  update  - Update and restart the application"
        echo "  backup  - Create database backup"
        echo ""
        echo "Examples:"
        echo "  $0 full     # First time deployment with SSL"
        echo "  $0 deploy   # Deploy without SSL setup"
        echo "  $0 logs     # View logs"
        ;;
esac