#!/bin/bash
# Professional EC2 Server Setup Script for ELMA Group
# Run this script on a fresh Ubuntu 22.04 LTS EC2 instance

set -e

echo "🏢 ELMA Group Professional Server Setup"
echo "==========================================="

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install professional server stack
echo "🔧 Installing professional server components..."
sudo apt install -y \
    nginx \
    postgresql postgresql-contrib \
    redis-server \
    supervisor \
    python3-pip \
    python3-venv \
    python3-dev \
    libpq-dev \
    build-essential \
    curl \
    wget \
    unzip \
    git \
    htop \
    fail2ban \
    ufw

# Configure firewall (professional security)
echo "🔒 Configuring professional firewall..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# Configure fail2ban (brute force protection)
echo "🛡️ Setting up brute force protection..."
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Create application user
echo "👤 Creating application user..."
sudo adduser --system --group --home /home/elmagroup elmagroup

# Create application directory
echo "📁 Setting up application directory..."
sudo mkdir -p /var/www/elmagroup
sudo chown elmagroup:elmagroup /var/www/elmagroup

# Clone ELMA Group application
echo "📥 Cloning ELMA Group application..."
cd /var/www/elmagroup
sudo -u elmagroup git clone https://github.com/diopnaby/ElmaGroup.git .

# Set up Python virtual environment
echo "🐍 Setting up Python environment..."
sudo -u elmagroup python3 -m venv venv
sudo -u elmagroup /var/www/elmagroup/venv/bin/pip install --upgrade pip
sudo -u elmagroup /var/www/elmagroup/venv/bin/pip install -r requirements-production.txt

# Configure PostgreSQL
echo "🗄️ Setting up PostgreSQL database..."
sudo -u postgres createuser elmagroup
sudo -u postgres createdb elmagroup_db -O elmagroup
sudo -u postgres psql -c "ALTER USER elmagroup PASSWORD 'elma_secure_password_2024';"

# Configure Gunicorn service
echo "⚙️ Setting up Gunicorn service..."
sudo tee /etc/systemd/system/elmagroup.service > /dev/null <<EOF
[Unit]
Description=ELMA Group Gunicorn daemon
After=network.target

[Service]
User=elmagroup
Group=elmagroup
WorkingDirectory=/var/www/elmagroup
Environment="PATH=/var/www/elmagroup/venv/bin"
ExecStart=/var/www/elmagroup/venv/bin/gunicorn --workers 3 --bind unix:/var/www/elmagroup/elmagroup.sock application:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
echo "🌐 Setting up Nginx configuration..."
sudo tee /etc/nginx/sites-available/elmagroup > /dev/null <<EOF
server {
    listen 80;
    server_name elmagroup.com www.elmagroup.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /var/www/elmagroup/app;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/elmagroup/elmagroup.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}
EOF

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/elmagroup /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Enable and start services
echo "🚀 Starting professional services..."
sudo systemctl daemon-reload
sudo systemctl enable elmagroup
sudo systemctl start elmagroup
sudo systemctl enable nginx
sudo systemctl restart nginx
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Install SSL certificate (Let's Encrypt)
echo "🔐 Setting up SSL certificate..."
sudo apt install -y certbot python3-certbot-nginx
# Note: Run manually after domain is pointed to server:
# sudo certbot --nginx -d elmagroup.com -d www.elmagroup.com

# Set up database tables
echo "🗄️ Initializing database..."
cd /var/www/elmagroup
sudo -u elmagroup /var/www/elmagroup/venv/bin/python -c "
from application import application
with application.app_context():
    from app.extensions import db
    db.create_all()
    print('✅ Database tables created')
"

# Set up log rotation
echo "📝 Setting up log rotation..."
sudo tee /etc/logrotate.d/elmagroup > /dev/null <<EOF
/var/log/elmagroup/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 elmagroup elmagroup
    postrotate
        systemctl reload elmagroup
    endscript
}
EOF

# Create log directory
sudo mkdir -p /var/log/elmagroup
sudo chown elmagroup:elmagroup /var/log/elmagroup

echo ""
echo "🎉 ELMA Group Professional Server Setup Complete!"
echo "=================================================="
echo ""
echo "✅ Professional server stack installed"
echo "✅ Application deployed and running"
echo "✅ Database configured"
echo "✅ Security hardening applied"
echo "✅ SSL ready (run certbot after domain setup)"
echo ""
echo "🌐 Your application is running on:"
echo "   - HTTP: http://your-server-ip"
echo "   - Admin: http://your-server-ip/admin"
echo ""
echo "🔧 Next steps:"
echo "1. Point your domain (elmagroup.com) to this server IP"
echo "2. Run: sudo certbot --nginx -d elmagroup.com -d www.elmagroup.com"
echo "3. Configure professional email service"
echo "4. Set up monitoring and backups"
echo ""
echo "📊 Service status:"
sudo systemctl status elmagroup --no-pager -l
sudo systemctl status nginx --no-pager -l
