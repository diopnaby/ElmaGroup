#!/bin/bash

# ELMA Group - Professional EC2 Deployment Script
# This script automates the complete deployment of ELMA Group Flask application on AWS EC2
# Run this script on your EC2 Ubuntu 22.04 LTS instance after connecting via SSH

set -e  # Exit on any error

echo "🏢 ELMA Group - Professional EC2 Deployment Starting..."
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root. Please run as ubuntu user."
   exit 1
fi

print_info "Starting ELMA Group EC2 deployment..."

# Step 1: System Update and Basic Packages
print_info "Step 1: Updating system and installing basic packages..."
sudo apt update -y
sudo apt upgrade -y
sudo apt install -y curl wget git unzip software-properties-common
print_status "System updated successfully"

# Step 2: Install Python and Development Tools
print_info "Step 2: Installing Python and development tools..."
sudo apt install -y python3 python3-pip python3-venv python3-dev
sudo apt install -y build-essential libssl-dev libffi-dev
sudo apt install -y libpq-dev  # PostgreSQL development headers
print_status "Python environment ready"

# Step 3: Install PostgreSQL
print_info "Step 3: Installing and configuring PostgreSQL..."
sudo apt install -y postgresql postgresql-contrib
sudo systemctl enable postgresql
sudo systemctl start postgresql
print_status "PostgreSQL installed and running"

# Step 4: Install Nginx
print_info "Step 4: Installing Nginx web server..."
sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
print_status "Nginx installed and running"

# Step 5: Install Redis (for caching)
print_info "Step 5: Installing Redis for caching..."
sudo apt install -y redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
print_status "Redis installed and running"

# Step 6: Install Supervisor (process management)
print_info "Step 6: Installing Supervisor for process management..."
sudo apt install -y supervisor
sudo systemctl enable supervisor
sudo systemctl start supervisor
print_status "Supervisor installed and running"

# Step 7: Clone ELMA Group Application
print_info "Step 7: Cloning ELMA Group application..."
cd /home/ubuntu
if [ -d "ElmaGroup" ]; then
    print_warning "ElmaGroup directory exists, updating..."
    cd ElmaGroup
    git pull origin main
else
    git clone https://github.com/diopnaby/ElmaGroup.git
    cd ElmaGroup
fi
print_status "Application code ready"

# Step 8: Create Python Virtual Environment
print_info "Step 8: Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements-production.txt
print_status "Python dependencies installed"

# Step 9: Configure PostgreSQL Database
print_info "Step 9: Configuring PostgreSQL database..."

# Generate a secure random password
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
echo "ELMA_DB_PASSWORD=$DB_PASSWORD" > /home/ubuntu/ElmaGroup/.env

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE elmagroup_db;
CREATE USER elmagroup WITH PASSWORD '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE elmagroup_db TO elmagroup;
ALTER USER elmagroup CREATEDB;
\q
EOF

# Configure PostgreSQL for application access
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = 'localhost'/" /etc/postgresql/14/main/postgresql.conf

# Add application user to pg_hba.conf
echo "local   elmagroup_db    elmagroup                               md5" | sudo tee -a /etc/postgresql/14/main/pg_hba.conf

sudo systemctl restart postgresql
print_status "PostgreSQL database configured"

# Step 10: Set Environment Variables
print_info "Step 10: Configuring environment variables..."
cat << EOF > /home/ubuntu/ElmaGroup/.env
# ELMA Group Production Environment
FLASK_ENV=production
DATABASE_URL=postgresql://elmagroup:$DB_PASSWORD@localhost:5432/elmagroup_db
SECRET_KEY=$(openssl rand -base64 32)
REDIS_URL=redis://localhost:6379/0
UPLOAD_FOLDER=/home/ubuntu/ElmaGroup/app/static/uploads
MAX_CONTENT_LENGTH=16777216
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
EOF
print_status "Environment variables configured"

# Step 11: Migrate Database
print_info "Step 11: Migrating database from SQLite to PostgreSQL..."
source venv/bin/activate
export $(cat .env | xargs)
python migrate_database.py
print_status "Database migration completed"

# Step 12: Create Gunicorn Service
print_info "Step 12: Setting up Gunicorn service..."
sudo tee /etc/systemd/system/elmagroup.service > /dev/null << EOF
[Unit]
Description=ELMA Group Gunicorn daemon
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/ElmaGroup
Environment="PATH=/home/ubuntu/ElmaGroup/venv/bin"
EnvironmentFile=/home/ubuntu/ElmaGroup/.env
ExecStart=/home/ubuntu/ElmaGroup/venv/bin/gunicorn --workers 3 --bind unix:/home/ubuntu/ElmaGroup/elmagroup.sock application:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable elmagroup
sudo systemctl start elmagroup
print_status "Gunicorn service configured and started"

# Step 13: Configure Nginx
print_info "Step 13: Configuring Nginx web server..."
sudo tee /etc/nginx/sites-available/elmagroup > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";

    # Favicon
    location = /favicon.ico { 
        access_log off; 
        log_not_found off; 
    }

    # Static files with caching
    location /static/ {
        root /home/ubuntu/ElmaGroup/app;
        expires 30d;
        add_header Cache-Control "public, immutable";
        
        # Gzip compression
        gzip on;
        gzip_vary on;
        gzip_min_length 1000;
        gzip_types text/css application/javascript image/svg+xml;
    }

    # Upload files
    location /uploads/ {
        alias /home/ubuntu/ElmaGroup/app/static/uploads/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Main application
    location / {
        include proxy_params;
        proxy_pass http://unix:/home/ubuntu/ElmaGroup/elmagroup.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Rate limiting for admin panel
    location /admin/ {
        limit_req zone=admin burst=5 nodelay;
        include proxy_params;
        proxy_pass http://unix:/home/ubuntu/ElmaGroup/elmagroup.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Create rate limiting configuration
sudo tee /etc/nginx/conf.d/rate_limit.conf > /dev/null << 'EOF'
# Rate limiting zones
limit_req_zone $binary_remote_addr zone=admin:10m rate=1r/s;
limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;
EOF

# Enable site and test configuration
sudo ln -sf /etc/nginx/sites-available/elmagroup /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
print_status "Nginx configured and reloaded"

# Step 14: Configure Firewall
print_info "Step 14: Configuring UFW firewall..."
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
print_status "Firewall configured"

# Step 15: Set up automated backups
print_info "Step 15: Setting up automated database backups..."
sudo mkdir -p /opt/elmagroup/backups
sudo chown ubuntu:ubuntu /opt/elmagroup/backups

# Create backup script
sudo tee /opt/elmagroup/backup_database.sh > /dev/null << EOF
#!/bin/bash
# ELMA Group Database Backup Script

BACKUP_DIR="/opt/elmagroup/backups"
DATE=\$(date +%Y%m%d_%H%M%S)
DB_NAME="elmagroup_db"
DB_USER="elmagroup"

# Create backup
pg_dump -h localhost -U \$DB_USER -d \$DB_NAME > \$BACKUP_DIR/elmagroup_backup_\$DATE.sql

# Keep only last 7 days of backups
find \$BACKUP_DIR -name "elmagroup_backup_*.sql" -mtime +7 -delete

# Log backup
echo "\$DATE: Database backup completed" >> \$BACKUP_DIR/backup.log
EOF

sudo chmod +x /opt/elmagroup/backup_database.sh
sudo chown ubuntu:ubuntu /opt/elmagroup/backup_database.sh

# Add to crontab for daily backups at 2 AM
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/elmagroup/backup_database.sh") | crontab -
print_status "Automated backups configured"

# Step 16: Install monitoring tools
print_info "Step 16: Installing monitoring and maintenance tools..."

# Install htop for system monitoring
sudo apt install -y htop

# Install fail2ban for security
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Configure fail2ban for nginx
sudo tee /etc/fail2ban/jail.local > /dev/null << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
EOF

sudo systemctl restart fail2ban
print_status "Security monitoring configured"

# Step 17: Install SSL certificate tools
print_info "Step 17: Installing SSL certificate tools..."
sudo apt install -y certbot python3-certbot-nginx
print_status "SSL tools installed"

# Step 18: Create maintenance scripts
print_info "Step 18: Creating maintenance scripts..."

# System update script
sudo tee /opt/elmagroup/update_system.sh > /dev/null << 'EOF'
#!/bin/bash
# ELMA Group System Update Script

echo "$(date): Starting system update" >> /var/log/elmagroup_maintenance.log

# Update system packages
apt update && apt upgrade -y

# Restart services if needed
systemctl restart elmagroup
systemctl reload nginx

echo "$(date): System update completed" >> /var/log/elmagroup_maintenance.log
EOF

sudo chmod +x /opt/elmagroup/update_system.sh

# Log rotation for application
sudo tee /etc/logrotate.d/elmagroup > /dev/null << 'EOF'
/var/log/elmagroup_maintenance.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
}
EOF

print_status "Maintenance scripts created"

# Step 19: Test deployment
print_info "Step 19: Testing deployment..."

# Test PostgreSQL connection
source /home/ubuntu/ElmaGroup/venv/bin/activate
export $(cat /home/ubuntu/ElmaGroup/.env | xargs)
cd /home/ubuntu/ElmaGroup
python test_postgresql.py

# Check service status
sudo systemctl status elmagroup --no-pager
sudo systemctl status nginx --no-pager
sudo systemctl status postgresql --no-pager

print_status "Deployment testing completed"

# Final setup summary
echo ""
echo "🎉 ELMA Group EC2 Deployment Completed Successfully!"
echo "=================================================="
echo ""
print_info "Services Status:"
echo "✅ PostgreSQL Database: Running"
echo "✅ Gunicorn Application Server: Running"
echo "✅ Nginx Web Server: Running"
echo "✅ Redis Cache: Running"
echo "✅ UFW Firewall: Active"
echo "✅ Fail2ban Security: Running"
echo "✅ Daily Backups: Configured"
echo ""
print_info "Next Steps:"
echo "1. Point your domain to this server's IP address"
echo "2. Run: sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com"
echo "3. Test your website at http://$(curl -s ifconfig.me)"
echo "4. Access admin panel at http://$(curl -s ifconfig.me)/admin"
echo ""
print_info "Important Files:"
echo "📄 Environment: /home/ubuntu/ElmaGroup/.env"
echo "📄 Nginx Config: /etc/nginx/sites-available/elmagroup"
echo "📄 Service Config: /etc/systemd/system/elmagroup.service"
echo "📄 Backup Script: /opt/elmagroup/backup_database.sh"
echo ""
print_info "Useful Commands:"
echo "🔧 Restart App: sudo systemctl restart elmagroup"
echo "🔧 Check Logs: sudo journalctl -u elmagroup -f"
echo "🔧 Nginx Reload: sudo systemctl reload nginx"
echo "🔧 View Backups: ls -la /opt/elmagroup/backups/"
echo ""
print_warning "Remember to:"
echo "- Change default passwords in .env file"
echo "- Set up your domain DNS"
echo "- Configure SSL certificate"
echo "- Test all application features"
echo ""
print_status "ELMA Group is now professionally deployed on AWS EC2! 🚀"
