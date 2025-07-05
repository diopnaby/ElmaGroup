# ELMA Group - Professional EC2 Deployment Guide

This guide provides step-by-step instructions for deploying the ELMA Group Flask application on AWS EC2 with PostgreSQL, Nginx, and professional security configurations.

## 🏗️ Infrastructure Overview

### Architecture Components
- **Web Server**: Nginx with SSL/TLS termination
- **Application Server**: Gunicorn with multiple workers
- **Database**: Self-managed PostgreSQL 14
- **Cache**: Redis for session storage and caching
- **Security**: UFW firewall, Fail2ban, SSL certificates
- **Monitoring**: Automated service monitoring and alerting
- **Backup**: Daily automated database and application backups

### Cost Structure
- **EC2 Instance**: $10-50/month (depending on instance type)
- **Storage**: $3-10/month (20-100GB EBS)
- **Data Transfer**: $1-5/month (typical usage)
- **Domain**: $12/year
- **SSL Certificate**: Free (Let's Encrypt)
- **Total Monthly**: ~$15-70/month

## 🚀 Quick Deployment

### Prerequisites
1. AWS EC2 instance (Ubuntu 22.04 LTS, t3.medium or larger)
2. Security group allowing ports 22, 80, 443
3. Domain name pointed to your EC2 instance
4. SSH access to your instance

### One-Command Deployment
```bash
# On your EC2 instance
cd /home/ubuntu
git clone <your-repository-url> ElmaGroup
cd ElmaGroup
chmod +x deploy_ec2.sh
./deploy_ec2.sh
```

## 📋 Detailed Deployment Steps

### Step 1: EC2 Instance Setup

#### 1.1 Launch EC2 Instance
```bash
# Recommended instance types:
# - t3.medium (2 vCPU, 4 GB RAM) - $30/month
# - t3.large (2 vCPU, 8 GB RAM) - $60/month
# - c5.large (2 vCPU, 4 GB RAM) - $72/month (compute optimized)

# Operating System: Ubuntu 22.04 LTS
# Storage: 20-50 GB GP3 SSD
```

#### 1.2 Security Group Configuration
```bash
# Inbound Rules:
# SSH (22) - Your IP only
# HTTP (80) - 0.0.0.0/0
# HTTPS (443) - 0.0.0.0/0
# PostgreSQL (5432) - ONLY if external access needed
```

#### 1.3 Connect to Instance
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### Step 2: Domain Configuration

#### 2.1 DNS Setup
```bash
# Point your domain to EC2 instance:
# A record: yourdomain.com -> EC2_IP_ADDRESS
# A record: www.yourdomain.com -> EC2_IP_ADDRESS
```

#### 2.2 Verify DNS Propagation
```bash
dig yourdomain.com
nslookup yourdomain.com
```

### Step 3: Application Deployment

#### 3.1 Upload Application Code
```bash
# Method 1: Git (Recommended)
git clone https://github.com/your-username/ElmaGroup.git
cd ElmaGroup

# Method 2: SCP
scp -i your-key.pem -r ./ElmaGroup ubuntu@your-ec2-ip:/home/ubuntu/
```

#### 3.2 Run Deployment Script
```bash
chmod +x deploy_ec2.sh
./deploy_ec2.sh
```

### Step 4: SSL Certificate Setup

#### 4.1 Install SSL Certificate
```bash
# After domain is pointed to your server
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com --non-interactive --agree-tos --email admin@yourdomain.com
```

#### 4.2 Test SSL Auto-Renewal
```bash
sudo certbot renew --dry-run
```

### Step 5: Application Configuration

#### 5.1 Environment Variables
```bash
# Edit /home/ubuntu/ElmaGroup/.env
nano /home/ubuntu/ElmaGroup/.env

# Update these settings:
MAIL_SERVER=smtp.gmail.com
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
ADMIN_EMAIL=admin@yourdomain.com
```

#### 5.2 Admin Account Setup
```bash
# Create admin user via Python shell
cd /home/ubuntu/ElmaGroup
source venv/bin/activate
python -c "
from application import application
from app.models import User
from app.extensions import db, bcrypt

with application.app_context():
    # Create admin user
    admin = User(
        username='admin',
        email='admin@yourdomain.com',
        password_hash=bcrypt.generate_password_hash('your-secure-password').decode('utf-8'),
        is_admin=True
    )
    db.session.add(admin)
    db.session.commit()
    print('Admin user created successfully')
"
```

## 🔧 Post-Deployment Configuration

### Database Management

#### Access PostgreSQL
```bash
# Connect to PostgreSQL
sudo -u postgres psql elmagroup_db

# Basic database commands
\dt  # List tables
\d+ table_name  # Describe table
SELECT * FROM users LIMIT 5;  # Query data
```

#### Manual Backup
```bash
# Create manual backup
sudo -u postgres pg_dump elmagroup_db > backup_$(date +%Y%m%d).sql

# Restore from backup
sudo -u postgres psql elmagroup_db < backup_file.sql
```

### Service Management

#### Application Services
```bash
# Restart application
sudo systemctl restart elmagroup

# Check application logs
sudo journalctl -u elmagroup -f

# Check service status
sudo systemctl status elmagroup nginx postgresql
```

#### Nginx Configuration
```bash
# Test nginx configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

# View nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Performance Optimization

#### 1. Database Optimization
```sql
-- Connect to PostgreSQL and run:
-- Create indexes for better performance
CREATE INDEX idx_posts_created_at ON posts(created_at);
CREATE INDEX idx_posts_author_id ON posts(author_id);
CREATE INDEX idx_books_category ON books(category);

-- Analyze tables for optimization
ANALYZE;
```

#### 2. Nginx Caching
```nginx
# Add to nginx configuration for static file caching
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    add_header Vary Accept-Encoding;
    access_log off;
}
```

#### 3. Application Performance
```bash
# Increase Gunicorn workers based on CPU cores
# Edit /etc/systemd/system/elmagroup.service
# Change --workers 3 to --workers $((2 * CPU_CORES + 1))

# Restart service
sudo systemctl daemon-reload
sudo systemctl restart elmagroup
```

## 🛡️ Security Hardening

### SSH Security
```bash
# Disable password authentication
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config
sudo systemctl restart ssh
```

### Additional Security Measures
```bash
# Install additional security tools
sudo apt install -y unattended-upgrades aide lynis

# Configure automatic security updates
sudo dpkg-reconfigure -plow unattended-upgrades

# Run security audit
sudo lynis audit system
```

### Database Security
```bash
# Secure PostgreSQL installation
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'very-secure-password';"

# Restrict database access
sudo nano /etc/postgresql/14/main/pg_hba.conf
# Ensure only local connections are allowed for application
```

## 📊 Monitoring and Maintenance

### Log Monitoring
```bash
# Monitor application logs
sudo journalctl -u elmagroup -f --since "1 hour ago"

# Monitor nginx access logs
sudo tail -f /var/log/nginx/access.log | grep -E "(40[0-9]|50[0-9])"

# Monitor system resources
htop
df -h
free -m
```

### Automated Monitoring Script
```bash
# Check monitoring script status
sudo systemctl status elmagroup-monitor.timer

# View monitoring logs
sudo journalctl -u elmagroup-monitor.service -f
```

### Performance Monitoring
```bash
# Database performance
sudo -u postgres psql elmagroup_db -c "
SELECT schemaname,tablename,attname,n_distinct,correlation
FROM pg_stats WHERE tablename='posts';
"

# Application response times
curl -w "@curl-format.txt" -o /dev/null -s "http://yourdomain.com"
```

## 🔄 Backup and Recovery

### Automated Backups
```bash
# View backup status
ls -la /opt/elmagroup/backups/

# Test backup restoration
sudo /opt/elmagroup/restore_database.sh backup_file.sql
```

### Manual Backup Procedures
```bash
# Full system backup
sudo tar -czf /tmp/elmagroup_full_backup_$(date +%Y%m%d).tar.gz \
  /home/ubuntu/ElmaGroup \
  /etc/nginx/sites-available/elmagroup \
  /etc/systemd/system/elmagroup.service \
  --exclude=/home/ubuntu/ElmaGroup/venv

# Database backup with compression
sudo -u postgres pg_dump elmagroup_db | gzip > elmagroup_db_$(date +%Y%m%d).sql.gz
```

### Disaster Recovery
```bash
# Complete system restoration procedure
# 1. Launch new EC2 instance
# 2. Install dependencies: sudo apt update && sudo apt install -y postgresql nginx python3-pip
# 3. Restore application files from backup
# 4. Restore database: gunzip -c backup.sql.gz | sudo -u postgres psql elmagroup_db
# 5. Configure services and restart
```

## 🚀 Scaling Considerations

### Vertical Scaling (Single Server)
```bash
# Upgrade EC2 instance type
# Stop instance -> Change instance type -> Start instance

# Increase storage
# Create snapshot -> Modify volume -> Extend filesystem
sudo resize2fs /dev/xvda1
```

### Horizontal Scaling Preparation
```bash
# Separate database server
# 1. Launch RDS PostgreSQL instance
# 2. Update DATABASE_URL in .env
# 3. Migrate data to RDS

# Load balancer setup
# 1. Launch Application Load Balancer
# 2. Launch multiple EC2 instances
# 3. Configure shared storage for uploads
```

### Performance Monitoring
```bash
# Install performance monitoring
sudo apt install -y netdata

# Access monitoring dashboard
# http://yourdomain.com:19999
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Application Won't Start
```bash
# Check service status
sudo systemctl status elmagroup

# Check logs
sudo journalctl -u elmagroup -n 50

# Common fixes:
sudo systemctl restart elmagroup
sudo chown -R ubuntu:ubuntu /home/ubuntu/ElmaGroup
```

#### 2. Database Connection Issues
```bash
# Test database connection
cd /home/ubuntu/ElmaGroup
source venv/bin/activate
python test_postgresql.py

# Check PostgreSQL status
sudo systemctl status postgresql

# Check database logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

#### 3. Nginx 502 Bad Gateway
```bash
# Check if application is running
sudo systemctl status elmagroup

# Check socket file
ls -la /home/ubuntu/ElmaGroup/elmagroup.sock

# Restart services
sudo systemctl restart elmagroup nginx
```

#### 4. SSL Certificate Issues
```bash
# Renew certificate manually
sudo certbot renew --force-renewal

# Check certificate status
sudo certbot certificates

# Test HTTPS
curl -I https://yourdomain.com
```

### Performance Issues
```bash
# Check system resources
htop
df -h
free -m

# Check database performance
sudo -u postgres psql elmagroup_db -c "
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC LIMIT 10;
"

# Optimize database
sudo -u postgres psql elmagroup_db -c "VACUUM ANALYZE;"
```

## 📞 Support and Maintenance

### Regular Maintenance Tasks

#### Weekly
- Review application and system logs
- Check backup integrity
- Monitor disk space and performance
- Review security alerts

#### Monthly
- Update system packages
- Review and rotate log files
- Check SSL certificate expiration
- Performance optimization review

#### Quarterly
- Security audit and penetration testing
- Database performance optimization
- Backup and recovery testing
- Infrastructure cost optimization

### Emergency Contacts
- **System Administrator**: [Your contact]
- **Database Administrator**: [Your contact]
- **Security Team**: [Your contact]
- **AWS Support**: [Your AWS support tier]

---

## 📄 Quick Reference

### Essential Commands
```bash
# Service management
sudo systemctl restart elmagroup nginx postgresql
sudo systemctl status elmagroup
sudo journalctl -u elmagroup -f

# Database access
sudo -u postgres psql elmagroup_db

# Log monitoring
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# SSL certificate
sudo certbot renew
sudo certbot certificates

# Backup
sudo /opt/elmagroup/backup_database.sh
```

### Important File Locations
- Application: `/home/ubuntu/ElmaGroup/`
- Environment: `/home/ubuntu/ElmaGroup/.env`
- Nginx Config: `/etc/nginx/sites-available/elmagroup`
- Service Config: `/etc/systemd/system/elmagroup.service`
- Logs: `/var/log/nginx/` and `journalctl -u elmagroup`
- Backups: `/opt/elmagroup/backups/`

This professional deployment guide ensures your ELMA Group application runs securely and efficiently on AWS EC2 with enterprise-grade reliability.
