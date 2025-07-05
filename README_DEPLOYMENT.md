# ELMA Group - Professional Flask Application

A modern, professional Flask web application for the ELMA Group organization, featuring a blog, digital library, admin panel, and comprehensive content management system.

## 🚀 Quick Start

### Local Development
```bash
git clone <repository-url>
cd ElmaGroup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python application.py
```

### Professional Production Deployment
```bash
# On AWS EC2 Ubuntu 22.04 LTS
git clone <repository-url> ElmaGroup
cd ElmaGroup
chmod +x deploy_ec2.sh
./deploy_ec2.sh
```

## 📋 Features

### Public Features
- **Modern Homepage** with hero section and featured content
- **Blog System** with categories, tags, and search
- **Digital Library** with book downloads and collections
- **Author Profiles** and testimonials
- **Contact Forms** with email notifications
- **Responsive Design** optimized for all devices
- **SEO Optimized** with meta tags and structured data

### Admin Features
- **Comprehensive Admin Panel** with dashboard analytics
- **Content Management** for posts, books, and pages
- **File Upload System** with image optimization
- **User Management** with role-based permissions
- **Comment Moderation** and spam protection
- **Analytics Dashboard** with visitor statistics
- **Backup Management** with automated backups

### Technical Features
- **Flask Framework** with Blueprint architecture
- **PostgreSQL Database** with optimized queries
- **Redis Caching** for improved performance
- **Nginx Reverse Proxy** with SSL termination
- **Gunicorn WSGI Server** with multiple workers
- **Security Headers** and CSRF protection
- **Automated Backups** with retention policies
- **Performance Monitoring** and alerting

## 🏗️ Architecture

### Technology Stack
- **Backend**: Python 3.11 + Flask 2.3
- **Database**: PostgreSQL 14
- **Cache**: Redis 6
- **Web Server**: Nginx 1.18
- **Application Server**: Gunicorn 20
- **Frontend**: HTML5, CSS3, JavaScript
- **Infrastructure**: AWS EC2, Ubuntu 22.04 LTS

### Security Features
- **SSL/TLS Encryption** with Let's Encrypt
- **Security Headers** (CSP, HSTS, XSS Protection)
- **Rate Limiting** and DDoS protection
- **Input Validation** and SQL injection prevention
- **File Upload Security** with type/size restrictions
- **Session Management** with secure cookies
- **Firewall Protection** with UFW and Fail2ban

## 📁 Project Structure

```
ElmaGroup/
├── app/                          # Application package
│   ├── __init__.py              # App factory
│   ├── models.py                # Database models
│   ├── extensions.py            # Flask extensions
│   ├── config.py                # Configuration
│   ├── admin.py                 # Admin interface
│   ├── auth/                    # Authentication blueprint
│   ├── main/                    # Main blueprint
│   ├── blog/                    # Blog blueprint
│   ├── library/                 # Library blueprint
│   ├── admin_panel/             # Admin panel blueprint
│   ├── testimonials/            # Testimonials blueprint
│   ├── static/                  # Static files
│   │   ├── css/                # Stylesheets
│   │   ├── js/                 # JavaScript
│   │   ├── images/             # Images
│   │   └── uploads/            # User uploads
│   └── templates/               # Jinja2 templates
├── deployment/                   # Deployment scripts
│   ├── deploy_ec2.sh           # Main deployment script
│   ├── optimize_performance.sh  # Performance optimization
│   ├── backup_system.sh        # Backup management
│   ├── monitor_system.sh       # System monitoring
│   └── ssl_setup.sh            # SSL configuration
├── docs/                        # Documentation
│   ├── DEPLOYMENT_GUIDE.md     # Deployment guide
│   ├── DEPLOYMENT_CHECKLIST.md # Deployment checklist
│   └── API_DOCUMENTATION.md    # API documentation
├── tests/                       # Test suite
├── requirements.txt             # Development dependencies
├── requirements-production.txt  # Production dependencies
├── application.py               # Application entry point
├── config_production.py         # Production configuration
└── migrate_database.py          # Database migration script
```

## 🚀 Deployment

### Production Requirements
- **Server**: AWS EC2 t3.medium or larger (2 vCPU, 4GB RAM)
- **Operating System**: Ubuntu 22.04 LTS
- **Storage**: 20GB+ SSD storage
- **Network**: Security group with ports 22, 80, 443 open
- **Domain**: Registered domain name with DNS access

### Deployment Process

1. **Launch EC2 Instance**
   ```bash
   # Launch Ubuntu 22.04 LTS instance
   # Configure security group (SSH, HTTP, HTTPS)
   # Create or use existing key pair
   ```

2. **Upload Application Code**
   ```bash
   # Method 1: Git (Recommended)
   git clone <your-repository> ElmaGroup
   
   # Method 2: SCP Upload
   scp -i key.pem -r ElmaGroup ubuntu@ec2-ip:/home/ubuntu/
   ```

3. **Run Deployment Script**
   ```bash
   cd ElmaGroup
   chmod +x deploy_ec2.sh
   ./deploy_ec2.sh
   ```

4. **Configure Domain and SSL**
   ```bash
   # Point domain to EC2 IP address
   # Run SSL setup
   ./ssl_setup.sh yourdomain.com
   ```

5. **Performance Optimization** (Optional)
   ```bash
   ./optimize_performance.sh
   ```

### Environment Configuration

Create and configure `.env` file:
```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/database

# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-secret-key

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Admin Configuration
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=secure-admin-password
```

## 🔧 Management

### Service Management
```bash
# Check service status
sudo systemctl status elmagroup nginx postgresql

# Restart services
sudo systemctl restart elmagroup
sudo systemctl reload nginx

# View logs
sudo journalctl -u elmagroup -f
sudo tail -f /var/log/nginx/access.log
```

### Database Management
```bash
# Connect to database
sudo -u postgres psql elmagroup_db

# Create backup
./backup_system.sh

# Restore from backup
./backup_system.sh restore-db backup_file.sql.gz
```

### Performance Monitoring
```bash
# System monitoring
./monitor_system.sh

# Performance metrics
tail -f /var/log/elmagroup-performance.log

# Resource usage
htop
df -h
```

## 🛡️ Security

### Implemented Security Measures
- **SSL/TLS encryption** for all traffic
- **Security headers** (CSP, HSTS, XSS protection)
- **Rate limiting** on API endpoints and admin panel
- **Input validation** and sanitization
- **File upload restrictions** and scanning
- **Session security** with secure cookies
- **Database security** with parameterized queries
- **Firewall protection** with UFW and Fail2ban

### Security Best Practices
- Regular security updates with `apt upgrade`
- Strong passwords and key-based SSH authentication
- Regular backup verification and testing
- Log monitoring and intrusion detection
- SSL certificate auto-renewal

## 📊 Performance

### Optimization Features
- **Nginx caching** with gzip compression
- **Database indexing** for improved query performance
- **Redis caching** for sessions and frequently accessed data
- **Image optimization** and lazy loading
- **CDN integration** ready (CloudFlare compatible)
- **Database connection pooling**
- **Static file optimization** with long-term caching

### Performance Metrics
- **Page load time**: < 2 seconds
- **Time to first byte**: < 500ms
- **Database queries**: Optimized with indexes
- **Concurrent users**: 100+ supported
- **Uptime**: 99.9% target

## 🔄 Backup and Recovery

### Automated Backups
- **Daily database backups** with compression
- **Weekly full application backups**
- **30-day retention policy**
- **Backup integrity verification**
- **Optional S3 storage integration**

### Recovery Procedures
```bash
# List available backups
./backup_system.sh list

# Restore database
./backup_system.sh restore-db backup_file.sql.gz

# Restore application
./backup_system.sh restore-app backup_file.tar.gz
```

## 📈 Monitoring and Analytics

### System Monitoring
- **Real-time performance monitoring**
- **Resource usage tracking** (CPU, memory, disk)
- **Service health checks**
- **Automated alerting** via email/Slack
- **Log aggregation and analysis**

### Application Analytics
- **User activity tracking**
- **Content performance metrics**
- **Search analytics**
- **Admin panel usage statistics**
- **Error tracking and reporting**

## 🛠️ Development

### Local Development Setup
```bash
# Clone repository
git clone <repository-url>
cd ElmaGroup

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up local database
python migrate_database.py

# Run development server
python application.py
```

### Testing
```bash
# Run tests
python -m pytest tests/

# Coverage report
python -m pytest --cov=app tests/

# Linting
flake8 app/
black app/
```

### Contributing
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Submit a pull request

## 📞 Support

### Technical Support
- **Documentation**: See `/docs` directory
- **Issues**: Submit via GitHub issues
- **Email**: admin@elmagroup.com

### Maintenance
- **Updates**: Monthly security and feature updates
- **Backups**: Daily automated backups
- **Monitoring**: 24/7 system monitoring
- **Support**: Business hours support available

## 📜 License

This project is proprietary software developed for ELMA Group. All rights reserved.

---

## 🎯 Quick Commands Reference

```bash
# Deployment
./deploy_ec2.sh                    # Deploy application
./ssl_setup.sh domain.com          # Setup SSL
./optimize_performance.sh          # Optimize performance

# Management
sudo systemctl restart elmagroup   # Restart app
sudo systemctl reload nginx        # Reload web server
./backup_system.sh                 # Create backup
./monitor_system.sh                # Check system health

# Database
sudo -u postgres psql elmagroup_db # Access database
./backup_system.sh restore-db file # Restore backup

# Logs
sudo journalctl -u elmagroup -f    # App logs
sudo tail -f /var/log/nginx/access.log # Web logs
tail -f /var/log/elmagroup-monitor.log # Monitor logs
```

Your ELMA Group application is now ready for professional deployment! 🚀
