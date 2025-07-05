# ELMA Group - Professional Deployment Checklist

## 🚀 Pre-Deployment Checklist

### AWS EC2 Setup
- [ ] Launch EC2 instance (Ubuntu 22.04 LTS, t3.medium or larger)
- [ ] Configure security group (ports 22, 80, 443)
- [ ] Associate Elastic IP (optional but recommended)
- [ ] Create key pair and download private key
- [ ] Test SSH connection to instance

### Domain Configuration
- [ ] Purchase domain name
- [ ] Point A records to EC2 IP address
  - [ ] `yourdomain.com` → EC2_IP
  - [ ] `www.yourdomain.com` → EC2_IP
- [ ] Verify DNS propagation: `dig yourdomain.com`

### Local Preparation
- [ ] Commit all code changes to Git
- [ ] Update requirements-production.txt
- [ ] Test application locally
- [ ] Prepare environment variables

## 🔧 Deployment Process

### Step 1: Upload Code to EC2
```bash
# Method 1: Git (Recommended)
ssh -i your-key.pem ubuntu@your-ec2-ip
git clone https://github.com/your-username/ElmaGroup.git
cd ElmaGroup

# Method 2: SCP
scp -i your-key.pem -r ./ElmaGroup ubuntu@your-ec2-ip:/home/ubuntu/
```

### Step 2: Run Deployment Script
```bash
# On EC2 instance
chmod +x deploy_ec2.sh
./deploy_ec2.sh
```

### Step 3: Configure Environment
```bash
# Edit environment variables
nano /home/ubuntu/ElmaGroup/.env

# Update these critical settings:
MAIL_SERVER=your-smtp-server
MAIL_USERNAME=your-email
MAIL_PASSWORD=your-app-password
ADMIN_EMAIL=admin@yourdomain.com
```

### Step 4: SSL Certificate
```bash
# After DNS is pointed to your server
./ssl_setup.sh yourdomain.com
```

### Step 5: Performance Optimization
```bash
# Optional but recommended
./optimize_performance.sh
```

## ✅ Post-Deployment Verification

### Service Status Check
```bash
# Check all services are running
sudo systemctl status elmagroup nginx postgresql redis-server

# Check service logs
sudo journalctl -u elmagroup -f
sudo tail -f /var/log/nginx/access.log
```

### Application Testing
- [ ] Visit website: `https://yourdomain.com`
- [ ] Test homepage loads correctly
- [ ] Test navigation menu
- [ ] Test blog posts page
- [ ] Test library/books page
- [ ] Test contact forms
- [ ] Test file uploads
- [ ] Test search functionality

### Admin Panel Testing
- [ ] Access admin panel: `https://yourdomain.com/admin`
- [ ] Login with admin credentials
- [ ] Test CRUD operations:
  - [ ] Create/edit blog post
  - [ ] Upload book/document
  - [ ] Manage authors
  - [ ] View analytics
- [ ] Test file upload functionality
- [ ] Test image resizing/optimization

### Database Testing
```bash
# Connect to database
sudo -u postgres psql elmagroup_db

# Check tables exist
\dt

# Check data migration
SELECT COUNT(*) FROM posts;
SELECT COUNT(*) FROM books;
SELECT COUNT(*) FROM users;
```

### Security Testing
- [ ] SSL certificate working: `https://yourdomain.com`
- [ ] HTTP redirects to HTTPS
- [ ] Security headers present
- [ ] Admin panel requires authentication
- [ ] File upload restrictions working
- [ ] Rate limiting functional

### Performance Testing
```bash
# Test response time
curl -w "@curl-format.txt" -o /dev/null -s "https://yourdomain.com"

# Test with load
ab -n 100 -c 10 https://yourdomain.com/

# Monitor system resources
htop
```

## 🔧 Maintenance Setup

### Monitoring
- [ ] Performance monitoring active: `tail -f /var/log/elmagroup-performance.log`
- [ ] System monitoring: `./monitor_system.sh`
- [ ] Log rotation configured
- [ ] Backup system tested: `./backup_system.sh`

### Security
- [ ] Firewall configured (UFW)
- [ ] Fail2ban active
- [ ] SSH key-only authentication
- [ ] Regular security updates enabled
- [ ] SSL auto-renewal tested: `sudo certbot renew --dry-run`

### Backups
```bash
# Test backup creation
./backup_system.sh

# Verify backups exist
ls -la /var/backups/elmagroup/

# Test backup restoration (in staging environment)
./backup_system.sh restore-db /path/to/backup.sql.gz
```

## 📊 Performance Optimization

### Optional Enhancements
- [ ] CDN setup (CloudFlare)
- [ ] Image optimization
- [ ] Database query optimization
- [ ] Caching implementation
- [ ] Search engine optimization

### Monitoring Tools
- [ ] Google Analytics setup
- [ ] Google Search Console
- [ ] Uptime monitoring (UptimeRobot)
- [ ] Error tracking (Sentry - optional)

## 🚨 Troubleshooting Guide

### Common Issues

#### Application Won't Start
```bash
# Check service status
sudo systemctl status elmagroup

# Check logs
sudo journalctl -u elmagroup -n 50

# Restart service
sudo systemctl restart elmagroup
```

#### Database Connection Issues
```bash
# Test database connection
cd /home/ubuntu/ElmaGroup
source venv/bin/activate
python test_postgresql.py

# Check PostgreSQL status
sudo systemctl status postgresql
```

#### Nginx 502 Bad Gateway
```bash
# Check application socket
ls -la /home/ubuntu/ElmaGroup/elmagroup.sock

# Restart services
sudo systemctl restart elmagroup nginx
```

#### SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Renew manually
sudo certbot renew --force-renewal
```

## 📞 Emergency Procedures

### Service Recovery
```bash
# Full service restart
sudo systemctl restart elmagroup nginx postgresql redis-server

# Check all services
sudo systemctl status elmagroup nginx postgresql redis-server
```

### Database Recovery
```bash
# Restore from latest backup
./backup_system.sh restore-db /var/backups/elmagroup/database/latest_backup.sql.gz
```

### Complete System Recovery
```bash
# If complete failure, launch new EC2 instance and:
1. Install dependencies
2. Restore application from backup
3. Restore database from backup
4. Reconfigure services
5. Update DNS if IP changed
```

## 📋 Maintenance Schedule

### Daily
- [ ] Monitor application logs
- [ ] Check system resources
- [ ] Verify backup completion
- [ ] Review security alerts

### Weekly
- [ ] Review performance metrics
- [ ] Update system packages: `sudo apt update && sudo apt upgrade`
- [ ] Clean up old log files
- [ ] Review database performance

### Monthly
- [ ] Full backup verification
- [ ] Security audit
- [ ] Performance optimization review
- [ ] SSL certificate check
- [ ] Infrastructure cost review

### Quarterly
- [ ] Disaster recovery test
- [ ] Security penetration test
- [ ] Performance benchmarking
- [ ] Infrastructure scaling review

## 📄 Important Information

### System Credentials
- Database Password: [Save in secure location]
- Admin Password: [Save in secure location]
- SSL Certificate: Auto-renewed by Let's Encrypt
- SSH Key: [Keep secure backup]

### File Locations
- Application: `/home/ubuntu/ElmaGroup/`
- Environment: `/home/ubuntu/ElmaGroup/.env`
- Logs: `/var/log/nginx/`, `/var/log/gunicorn/`
- Backups: `/var/backups/elmagroup/`
- SSL Certificates: `/etc/letsencrypt/`

### Service Commands
```bash
# Application
sudo systemctl restart elmagroup
sudo systemctl status elmagroup
sudo journalctl -u elmagroup -f

# Web Server
sudo systemctl reload nginx
sudo nginx -t

# Database
sudo systemctl restart postgresql
sudo -u postgres psql elmagroup_db

# Monitoring
./monitor_system.sh
./backup_system.sh verify
tail -f /var/log/elmagroup-performance.log
```

### Support Contacts
- System Administrator: [Your contact]
- Database Administrator: [Your contact]
- Security Team: [Your contact]
- AWS Support: [Your support level]

---

## ✅ Final Deployment Verification

Once all items are checked, your ELMA Group application is professionally deployed and ready for production use!

**Key Success Metrics:**
- Website loads in < 3 seconds
- All admin functions working
- Automated backups running
- SSL certificate active
- Security measures enabled
- Performance monitoring active

Your professional ELMA Group website is now live and secure! 🚀
