#!/bin/bash

# ELMA Group - Performance Optimization Script
# This script optimizes the application and system for better performance
# Author: GitHub Copilot for ELMA Group
# Version: 1.0

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
APP_DIR="/home/ubuntu/ElmaGroup"
SERVICE_NAME="elmagroup"
DB_NAME="elmagroup_db"

# Logging function
log_message() {
    echo -e "${GREEN}$(date '+%Y-%m-%d %H:%M:%S')${NC} - $1"
}

warning_message() {
    echo -e "${YELLOW}$(date '+%Y-%m-%d %H:%M:%S')${NC} - WARNING: $1"
}

error_message() {
    echo -e "${RED}$(date '+%Y-%m-%d %H:%M:%S')${NC} - ERROR: $1"
}

info_message() {
    echo -e "${BLUE}$(date '+%Y-%m-%d %H:%M:%S')${NC} - INFO: $1"
}

# Check system resources
check_system_resources() {
    log_message "Checking system resources"
    
    # CPU cores
    cpu_cores=$(nproc)
    log_message "CPU cores: $cpu_cores"
    
    # Memory
    total_memory=$(free -m | awk 'NR==2{printf "%.1f", $2/1024}')
    log_message "Total memory: ${total_memory}GB"
    
    # Disk space
    disk_space=$(df -h / | awk 'NR==2 {print $4}')
    log_message "Available disk space: $disk_space"
    
    echo "$cpu_cores"
}

# Optimize Gunicorn configuration
optimize_gunicorn() {
    local cpu_cores="$1"
    local workers=$((2 * cpu_cores + 1))
    
    log_message "Optimizing Gunicorn configuration for $cpu_cores CPU cores"
    log_message "Setting workers to: $workers"
    
    # Update Gunicorn service configuration
    sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << EOF
[Unit]
Description=ELMA Group Gunicorn daemon
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn \\
    --workers $workers \\
    --worker-class sync \\
    --worker-connections 1000 \\
    --max-requests 1000 \\
    --max-requests-jitter 100 \\
    --timeout 30 \\
    --keep-alive 5 \\
    --bind unix:$APP_DIR/$SERVICE_NAME.sock \\
    --access-logfile /var/log/gunicorn/access.log \\
    --error-logfile /var/log/gunicorn/error.log \\
    --log-level info \\
    application:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=5
KillMode=mixed
TimeoutStopSec=5

[Install]
WantedBy=multi-user.target
EOF

    # Reload and restart service
    sudo systemctl daemon-reload
    sudo systemctl restart $SERVICE_NAME
    
    log_message "Gunicorn configuration optimized"
}

# Optimize Nginx configuration
optimize_nginx() {
    local cpu_cores="$1"
    
    log_message "Optimizing Nginx configuration"
    
    # Update main nginx configuration
    sudo tee /etc/nginx/nginx.conf > /dev/null << EOF
user www-data;
worker_processes $cpu_cores;
worker_rlimit_nofile 65535;
pid /run/nginx.pid;
include /etc/nginx/modules-enabled/*.conf;

events {
    worker_connections 2048;
    use epoll;
    multi_accept on;
}

http {
    # Basic Settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 30;
    keepalive_requests 100;
    types_hash_max_size 2048;
    server_tokens off;
    client_max_body_size 16M;
    client_body_timeout 30;
    client_header_timeout 30;
    send_timeout 30;

    # MIME
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '\$remote_addr - \$remote_user [\$time_local] "\$request" '
                    '\$status \$body_bytes_sent "\$http_referer" '
                    '"\$http_user_agent" "\$http_x_forwarded_for" '
                    'rt=\$request_time uct="\$upstream_connect_time" '
                    'uht="\$upstream_header_time" urt="\$upstream_response_time"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;

    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1000;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        application/atom+xml
        application/geo+json
        application/javascript
        application/x-javascript
        application/json
        application/ld+json
        application/manifest+json
        application/rdf+xml
        application/rss+xml
        application/xhtml+xml
        application/xml
        font/eot
        font/otf
        font/ttf
        image/svg+xml
        text/css
        text/javascript
        text/plain
        text/xml;

    # Rate Limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone \$binary_remote_addr zone=login:10m rate=1r/s;

    # Include virtual host configs
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
EOF

    # Update site-specific configuration
    sudo tee /etc/nginx/sites-available/$SERVICE_NAME > /dev/null << 'EOF'
upstream gunicorn_backend {
    server unix:/home/ubuntu/ElmaGroup/elmagroup.sock fail_timeout=0;
}

# Rate limiting for admin panel
limit_req_zone $binary_remote_addr zone=admin:10m rate=5r/m;

server {
    listen 80;
    server_name _;

    # Security headers
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self'; media-src 'self'; object-src 'none'; child-src 'none'; frame-ancestors 'none'; form-action 'self'; base-uri 'self';" always;

    # Root and index
    root /home/ubuntu/ElmaGroup;
    index index.html;

    # Favicon with long cache
    location = /favicon.ico {
        access_log off;
        log_not_found off;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Robots.txt
    location = /robots.txt {
        access_log off;
        log_not_found off;
        expires 7d;
    }

    # Static files with aggressive caching
    location /static/ {
        alias /home/ubuntu/ElmaGroup/app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header Vary "Accept-Encoding";
        
        # Security for uploaded files
        location ~* \.(php|php5|phtml|pl|py|jsp|asp|sh|cgi)$ {
            deny all;
        }
        
        # Optimize file serving
        try_files $uri $uri/ =404;
        
        # Enable Brotli compression if available
        location ~* \.(js|css|svg|woff|woff2)$ {
            add_header Cache-Control "public, immutable";
            expires 1y;
        }
    }

    # Admin panel with rate limiting
    location /admin {
        limit_req zone=admin burst=10 nodelay;
        
        include proxy_params;
        proxy_pass http://gunicorn_backend;
        proxy_redirect off;
        proxy_buffering on;
        proxy_buffer_size 8k;
        proxy_buffers 8 8k;
        proxy_busy_buffers_size 16k;
    }

    # API endpoints with rate limiting
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        
        include proxy_params;
        proxy_pass http://gunicorn_backend;
        proxy_buffering on;
    }

    # Main application
    location / {
        # Basic rate limiting
        limit_req zone=api burst=50 nodelay;
        
        include proxy_params;
        proxy_pass http://gunicorn_backend;
        proxy_redirect off;
        proxy_buffering on;
        proxy_buffer_size 8k;
        proxy_buffers 16 8k;
        proxy_busy_buffers_size 16k;
        
        # Connection settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;
    }

    # Deny access to sensitive files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }

    location ~ ~$ {
        deny all;
        access_log off;
        log_not_found off;
    }

    # Error pages
    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;

    # Logging
    access_log /var/log/nginx/elmagroup_access.log main;
    error_log /var/log/nginx/elmagroup_error.log;
}
EOF

    # Test configuration and reload
    if sudo nginx -t; then
        sudo systemctl reload nginx
        log_message "Nginx configuration optimized and reloaded"
    else
        error_message "Nginx configuration test failed"
        return 1
    fi
}

# Optimize PostgreSQL configuration
optimize_postgresql() {
    local memory_gb="$1"
    
    log_message "Optimizing PostgreSQL configuration"
    
    # Calculate memory-based settings
    local shared_buffers=$(echo "scale=0; $memory_gb * 256 / 1" | bc)  # 25% of RAM in MB
    local effective_cache_size=$(echo "scale=0; $memory_gb * 768 / 1" | bc)  # 75% of RAM in MB
    local work_mem=$(echo "scale=0; $memory_gb * 4 / 1" | bc)  # 4MB per GB of RAM
    
    # Ensure minimum values
    [ $shared_buffers -lt 128 ] && shared_buffers=128
    [ $effective_cache_size -lt 512 ] && effective_cache_size=512
    [ $work_mem -lt 4 ] && work_mem=4
    
    log_message "Setting shared_buffers to ${shared_buffers}MB"
    log_message "Setting effective_cache_size to ${effective_cache_size}MB"
    log_message "Setting work_mem to ${work_mem}MB"
    
    # Find PostgreSQL version and config file
    local pg_version=$(sudo -u postgres psql -t -c "SELECT version();" | grep -oP "\d+\.\d+" | head -1)
    local pg_config="/etc/postgresql/$pg_version/main/postgresql.conf"
    
    if [ ! -f "$pg_config" ]; then
        # Fallback to find config file
        pg_config=$(sudo find /etc/postgresql -name "postgresql.conf" | head -1)
    fi
    
    if [ -f "$pg_config" ]; then
        log_message "Updating PostgreSQL configuration: $pg_config"
        
        # Backup original configuration
        sudo cp "$pg_config" "${pg_config}.backup.$(date +%Y%m%d)"
        
        # Update configuration
        sudo tee -a "$pg_config" > /dev/null << EOF

# ELMA Group Performance Optimizations
# Added on $(date)

# Memory Settings
shared_buffers = ${shared_buffers}MB
effective_cache_size = ${effective_cache_size}MB
work_mem = ${work_mem}MB
maintenance_work_mem = 64MB

# Checkpoint Settings
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100

# Connection Settings
max_connections = 100

# Query Planning
random_page_cost = 1.1
effective_io_concurrency = 200

# Logging
log_statement = 'none'
log_min_duration_statement = 1000
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on

# Autovacuum
autovacuum_max_workers = 3
autovacuum_naptime = 20s
EOF

        # Restart PostgreSQL
        sudo systemctl restart postgresql
        
        if sudo systemctl is-active --quiet postgresql; then
            log_message "PostgreSQL configuration optimized and restarted"
        else
            error_message "PostgreSQL failed to restart with new configuration"
            # Restore backup
            sudo cp "${pg_config}.backup.$(date +%Y%m%d)" "$pg_config"
            sudo systemctl restart postgresql
            return 1
        fi
    else
        error_message "PostgreSQL configuration file not found"
        return 1
    fi
}

# Optimize database with indexes and maintenance
optimize_database() {
    log_message "Optimizing database with indexes and maintenance"
    
    # Create performance indexes
    sudo -u postgres psql "$DB_NAME" << 'EOF'
-- Performance indexes for ELMA Group

-- Posts table optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_posts_created_at ON posts(created_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_posts_author_id ON posts(author_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_posts_published ON posts(created_at DESC) WHERE published = true;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_posts_category ON posts(category);

-- Books table optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_books_category ON books(category);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_books_author_id ON books(author_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_books_featured ON books(id) WHERE featured = true;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_books_created_at ON books(created_at DESC);

-- Users table optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_username ON users(username);

-- Comments table optimization (if exists)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_comments_post_id ON comments(post_id) WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'comments');
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_comments_created_at ON comments(created_at DESC) WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'comments');

-- Update table statistics
ANALYZE;

-- Run maintenance
VACUUM ANALYZE;

-- Show index usage statistics
SELECT schemaname, tablename, attname, n_distinct, correlation 
FROM pg_stats 
WHERE tablename IN ('posts', 'books', 'users') 
ORDER BY tablename, attname;
EOF

    log_message "Database optimization completed"
}

# System-level optimizations
optimize_system() {
    log_message "Applying system-level optimizations"
    
    # Optimize kernel parameters
    sudo tee /etc/sysctl.d/99-elmagroup.conf > /dev/null << EOF
# ELMA Group System Optimizations

# Network optimizations
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 12582912 16777216
net.ipv4.tcp_wmem = 4096 12582912 16777216
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_congestion_control = bbr

# File descriptor limits
fs.file-max = 100000

# Virtual memory optimizations
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5

# Security
kernel.dmesg_restrict = 1
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1
EOF

    # Apply sysctl settings
    sudo sysctl -p /etc/sysctl.d/99-elmagroup.conf
    
    # Optimize file descriptor limits
    sudo tee /etc/security/limits.d/elmagroup.conf > /dev/null << EOF
ubuntu soft nofile 10000
ubuntu hard nofile 10000
www-data soft nofile 10000
www-data hard nofile 10000
postgres soft nofile 10000
postgres hard nofile 10000
EOF

    log_message "System optimizations applied"
}

# Redis optimization
optimize_redis() {
    log_message "Optimizing Redis configuration"
    
    # Create Redis configuration for session storage
    sudo tee /etc/redis/redis-elmagroup.conf > /dev/null << EOF
# ELMA Group Redis Configuration

port 6379
bind 127.0.0.1
protected-mode yes
timeout 300
keepalive 60

# Memory management
maxmemory 256mb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# Performance
tcp-backlog 511
databases 16
EOF

    # Restart Redis
    sudo systemctl restart redis-server
    
    if sudo systemctl is-active --quiet redis-server; then
        log_message "Redis optimized and restarted"
    else
        error_message "Redis failed to restart"
        return 1
    fi
}

# Application-level optimizations
optimize_application() {
    log_message "Applying application-level optimizations"
    
    # Create Flask cache configuration
    if [ ! -f "$APP_DIR/config_cache.py" ]; then
        cat > "$APP_DIR/config_cache.py" << 'EOF'
# ELMA Group Cache Configuration

import os

class CacheConfig:
    # Redis cache configuration
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/1')
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Session configuration
    SESSION_TYPE = 'redis'
    SESSION_REDIS = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Static file optimization
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 year
EOF
    fi
    
    # Install performance monitoring dependencies
    cd "$APP_DIR"
    source venv/bin/activate
    pip install redis flask-caching flask-session
    
    log_message "Application optimizations applied"
}

# Performance monitoring setup
setup_monitoring() {
    log_message "Setting up performance monitoring"
    
    # Create performance monitoring script
    sudo tee /usr/local/bin/elmagroup-performance.sh > /dev/null << 'EOF'
#!/bin/bash
# ELMA Group Performance Monitoring

LOG_FILE="/var/log/elmagroup-performance.log"

# Function to log performance metrics
log_metrics() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# System metrics
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.1f", $3/$2 * 100)}')
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
LOAD_AVG=$(uptime | awk -F'load average:' '{print $2}' | tr -d ' ')

# Database metrics
DB_CONNECTIONS=$(sudo -u postgres psql elmagroup_db -t -c "SELECT count(*) FROM pg_stat_activity;" | xargs)
DB_SIZE=$(sudo -u postgres psql elmagroup_db -t -c "SELECT pg_size_pretty(pg_database_size('elmagroup_db'));" | xargs)

# Web server metrics
NGINX_CONNECTIONS=$(ss -tuln | grep :80 | wc -l)
RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' http://localhost/ || echo "0")

# Log all metrics
log_metrics "CPU: ${CPU_USAGE}%, Memory: ${MEMORY_USAGE}%, Disk: ${DISK_USAGE}%, Load: ${LOAD_AVG}"
log_metrics "DB Connections: ${DB_CONNECTIONS}, DB Size: ${DB_SIZE}, Response Time: ${RESPONSE_TIME}s"
log_metrics "Nginx Connections: ${NGINX_CONNECTIONS}"

# Alert on high resource usage
if (( $(echo "$MEMORY_USAGE > 90" | bc -l) )); then
    echo "HIGH MEMORY USAGE: ${MEMORY_USAGE}%" | logger -t elmagroup-alert
fi

if [ "$CPU_USAGE" -gt 90 ]; then
    echo "HIGH CPU USAGE: ${CPU_USAGE}%" | logger -t elmagroup-alert
fi
EOF

    sudo chmod +x /usr/local/bin/elmagroup-performance.sh
    
    # Add to crontab for regular monitoring
    (sudo crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/elmagroup-performance.sh") | sudo crontab -
    
    log_message "Performance monitoring setup completed"
}

# Log rotation optimization
optimize_log_rotation() {
    log_message "Setting up optimized log rotation"
    
    # Configure logrotate for application logs
    sudo tee /etc/logrotate.d/elmagroup > /dev/null << EOF
/var/log/gunicorn/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    sharedscripts
    postrotate
        systemctl reload elmagroup
    endscript
}

/var/log/nginx/elmagroup_*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    sharedscripts
    postrotate
        systemctl reload nginx
    endscript
}

/var/log/elmagroup-*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
}
EOF

    log_message "Log rotation optimized"
}

# Main optimization function
main() {
    log_message "Starting ELMA Group performance optimization"
    
    # Check if running as correct user
    if [ "$USER" != "ubuntu" ]; then
        error_message "This script must be run as the ubuntu user"
        exit 1
    fi
    
    # Get system information
    cpu_cores=$(check_system_resources)
    memory_gb=$(free -m | awk 'NR==2{printf "%.1f", $2/1024}')
    
    log_message "System specs: ${cpu_cores} CPU cores, ${memory_gb}GB RAM"
    
    # Run optimizations
    optimize_gunicorn "$cpu_cores"
    optimize_nginx "$cpu_cores"
    optimize_postgresql "$memory_gb"
    optimize_database
    optimize_system
    optimize_redis
    optimize_application
    setup_monitoring
    optimize_log_rotation
    
    log_message "Performance optimization completed"
    
    # Show optimization summary
    echo -e "\n${GREEN}🚀 ELMA Group Performance Optimization Complete!${NC}"
    echo -e "${BLUE}=================================================${NC}"
    echo -e "${GREEN}✅ Gunicorn optimized for $cpu_cores CPU cores${NC}"
    echo -e "${GREEN}✅ Nginx optimized with caching and compression${NC}"
    echo -e "${GREEN}✅ PostgreSQL tuned for ${memory_gb}GB RAM${NC}"
    echo -e "${GREEN}✅ Database indexes created${NC}"
    echo -e "${GREEN}✅ System kernel parameters optimized${NC}"
    echo -e "${GREEN}✅ Redis configured for caching${NC}"
    echo -e "${GREEN}✅ Performance monitoring enabled${NC}"
    echo -e "${GREEN}✅ Log rotation optimized${NC}"
    
    echo -e "\n${YELLOW}📊 Recommended next steps:${NC}"
    echo -e "1. Test website performance: ${BLUE}curl -w '@curl-format.txt' -o /dev/null -s http://your-domain.com${NC}"
    echo -e "2. Monitor performance logs: ${BLUE}tail -f /var/log/elmagroup-performance.log${NC}"
    echo -e "3. Check service status: ${BLUE}sudo systemctl status elmagroup nginx postgresql${NC}"
    echo -e "4. Run database ANALYZE: ${BLUE}sudo -u postgres psql $DB_NAME -c 'ANALYZE;'${NC}"
    
    warning_message "Please test all application functionality after optimization"
}

# Usage information
usage() {
    echo "ELMA Group Performance Optimization Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  optimize     - Run all optimizations (default)"
    echo "  gunicorn     - Optimize Gunicorn only"
    echo "  nginx        - Optimize Nginx only"
    echo "  database     - Optimize PostgreSQL and database only"
    echo "  system       - Optimize system settings only"
    echo "  monitoring   - Setup performance monitoring only"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run all optimizations"
    echo "  $0 optimize          # Run all optimizations"
    echo "  $0 database          # Optimize database only"
}

# Command handling
case "${1:-optimize}" in
    "optimize")
        main
        ;;
    "gunicorn")
        cpu_cores=$(check_system_resources)
        optimize_gunicorn "$cpu_cores"
        ;;
    "nginx")
        cpu_cores=$(check_system_resources)
        optimize_nginx "$cpu_cores"
        ;;
    "database")
        memory_gb=$(free -m | awk 'NR==2{printf "%.1f", $2/1024}')
        optimize_postgresql "$memory_gb"
        optimize_database
        ;;
    "system")
        optimize_system
        ;;
    "monitoring")
        setup_monitoring
        ;;
    "help"|"-h"|"--help")
        usage
        ;;
    *)
        echo "Unknown command: $1"
        usage
        exit 1
        ;;
esac

exit 0
