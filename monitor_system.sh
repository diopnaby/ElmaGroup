#!/bin/bash

# ELMA Group - Professional Monitoring and Alerting Script
# This script monitors system health, application status, and sends alerts
# Author: GitHub Copilot for ELMA Group
# Version: 1.0

set -e

# Configuration
LOG_FILE="/var/log/elmagroup-monitor.log"
EMAIL_ALERT="admin@elmagroup.com"
SLACK_WEBHOOK=""  # Add your Slack webhook URL if needed
SERVICE_NAME="elmagroup"
DB_NAME="elmagroup_db"
THRESHOLD_CPU=80
THRESHOLD_MEMORY=85
THRESHOLD_DISK=90

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging function
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Alert function
send_alert() {
    local message="$1"
    local severity="$2"
    
    log_message "$severity: $message"
    
    # Send email alert if configured
    if command -v mail >/dev/null 2>&1 && [ -n "$EMAIL_ALERT" ]; then
        echo "$message" | mail -s "ELMA Group Alert - $severity" "$EMAIL_ALERT"
    fi
    
    # Send Slack alert if configured
    if [ -n "$SLACK_WEBHOOK" ]; then
        curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"🚨 ELMA Group Alert\\n*$severity*: $message\"}" \
        "$SLACK_WEBHOOK" >/dev/null 2>&1
    fi
}

# Check service status
check_service() {
    local service="$1"
    local display_name="$2"
    
    if systemctl is-active --quiet "$service"; then
        log_message "✅ $display_name is running"
        return 0
    else
        send_alert "$display_name service is down. Attempting restart..." "CRITICAL"
        
        # Attempt to restart the service
        if systemctl restart "$service" >/dev/null 2>&1; then
            sleep 5
            if systemctl is-active --quiet "$service"; then
                send_alert "$display_name service restarted successfully" "WARNING"
                return 0
            else
                send_alert "$display_name service failed to restart" "CRITICAL"
                return 1
            fi
        else
            send_alert "Failed to restart $display_name service" "CRITICAL"
            return 1
        fi
    fi
}

# Check system resources
check_system_resources() {
    # CPU Usage
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
    CPU_USAGE=${CPU_USAGE%.*}  # Remove decimal part
    
    if [ "$CPU_USAGE" -gt "$THRESHOLD_CPU" ]; then
        send_alert "High CPU usage detected: ${CPU_USAGE}%" "WARNING"
    else
        log_message "✅ CPU usage: ${CPU_USAGE}%"
    fi
    
    # Memory Usage
    MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100)}')
    
    if [ "$MEMORY_USAGE" -gt "$THRESHOLD_MEMORY" ]; then
        send_alert "High memory usage detected: ${MEMORY_USAGE}%" "WARNING"
    else
        log_message "✅ Memory usage: ${MEMORY_USAGE}%"
    fi
    
    # Disk Usage
    DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$DISK_USAGE" -gt "$THRESHOLD_DISK" ]; then
        send_alert "High disk usage detected: ${DISK_USAGE}%" "CRITICAL"
    else
        log_message "✅ Disk usage: ${DISK_USAGE}%"
    fi
}

# Check database connectivity
check_database() {
    if sudo -u postgres psql -d "$DB_NAME" -c "SELECT 1;" >/dev/null 2>&1; then
        log_message "✅ Database connectivity OK"
        
        # Check database size
        DB_SIZE=$(sudo -u postgres psql -d "$DB_NAME" -t -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));" | xargs)
        log_message "ℹ️  Database size: $DB_SIZE"
        
        # Check active connections
        ACTIVE_CONNECTIONS=$(sudo -u postgres psql -d "$DB_NAME" -t -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';" | xargs)
        log_message "ℹ️  Active database connections: $ACTIVE_CONNECTIONS"
        
        return 0
    else
        send_alert "Database connectivity failed" "CRITICAL"
        return 1
    fi
}

# Check web server response
check_web_response() {
    local response_code
    local response_time
    
    # Get response code and time
    response_data=$(curl -o /dev/null -s -w "%{http_code} %{time_total}" http://localhost/ 2>/dev/null || echo "000 0")
    response_code=$(echo $response_data | cut -d' ' -f1)
    response_time=$(echo $response_data | cut -d' ' -f2)
    
    if [ "$response_code" = "200" ]; then
        log_message "✅ Web server responding (${response_time}s)"
        
        # Check if response time is too slow
        if (( $(echo "$response_time > 5" | bc -l) )); then
            send_alert "Slow web server response time: ${response_time}s" "WARNING"
        fi
        
        return 0
    else
        send_alert "Web server not responding (HTTP $response_code)" "CRITICAL"
        return 1
    fi
}

# Check SSL certificate expiration
check_ssl_certificate() {
    local domain="$1"
    
    if [ -z "$domain" ]; then
        log_message "⚠️  No domain specified for SSL check"
        return 0
    fi
    
    # Get certificate expiration date
    expiry_date=$(echo | openssl s_client -servername "$domain" -connect "$domain:443" 2>/dev/null | openssl x509 -noout -dates | grep notAfter | cut -d= -f2)
    
    if [ -n "$expiry_date" ]; then
        expiry_timestamp=$(date -d "$expiry_date" +%s)
        current_timestamp=$(date +%s)
        days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
        
        if [ "$days_until_expiry" -lt 7 ]; then
            send_alert "SSL certificate expires in $days_until_expiry days" "CRITICAL"
        elif [ "$days_until_expiry" -lt 30 ]; then
            send_alert "SSL certificate expires in $days_until_expiry days" "WARNING"
        else
            log_message "✅ SSL certificate valid for $days_until_expiry days"
        fi
    else
        log_message "⚠️  Could not check SSL certificate for $domain"
    fi
}

# Check log file sizes
check_log_sizes() {
    local max_size_mb=100
    
    # Check application logs
    if [ -f "/var/log/gunicorn/error.log" ]; then
        log_size=$(du -m /var/log/gunicorn/error.log | cut -f1)
        if [ "$log_size" -gt "$max_size_mb" ]; then
            send_alert "Large log file detected: /var/log/gunicorn/error.log (${log_size}MB)" "WARNING"
        fi
    fi
    
    # Check nginx logs
    if [ -f "/var/log/nginx/error.log" ]; then
        log_size=$(du -m /var/log/nginx/error.log | cut -f1)
        if [ "$log_size" -gt "$max_size_mb" ]; then
            send_alert "Large log file detected: /var/log/nginx/error.log (${log_size}MB)" "WARNING"
        fi
    fi
}

# Check backup status
check_backup_status() {
    local backup_dir="/var/backups/elmagroup"
    local max_age_days=2
    
    if [ -d "$backup_dir" ]; then
        # Find the most recent backup
        latest_backup=$(find "$backup_dir" -name "*.sql" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
        
        if [ -n "$latest_backup" ]; then
            backup_age=$(find "$latest_backup" -mtime +$max_age_days)
            if [ -n "$backup_age" ]; then
                send_alert "Database backup is older than $max_age_days days" "WARNING"
            else
                log_message "✅ Recent database backup found"
            fi
        else
            send_alert "No database backups found" "CRITICAL"
        fi
    else
        send_alert "Backup directory not found: $backup_dir" "CRITICAL"
    fi
}

# Check for security updates
check_security_updates() {
    updates=$(apt list --upgradable 2>/dev/null | grep -c security || echo 0)
    
    if [ "$updates" -gt 0 ]; then
        send_alert "$updates security updates available" "WARNING"
    else
        log_message "✅ No security updates pending"
    fi
}

# Check fail2ban status
check_fail2ban() {
    if systemctl is-active --quiet fail2ban; then
        banned_count=$(fail2ban-client status 2>/dev/null | grep "Currently banned" | awk '{print $4}' || echo 0)
        log_message "✅ Fail2ban active with $banned_count banned IPs"
    else
        send_alert "Fail2ban service is not running" "WARNING"
    fi
}

# Main monitoring function
main() {
    log_message "🔍 Starting ELMA Group system monitoring"
    
    # Initialize error counter
    error_count=0
    
    # Check all services
    check_service "nginx" "Nginx Web Server" || ((error_count++))
    check_service "$SERVICE_NAME" "ELMA Group Application" || ((error_count++))
    check_service "postgresql" "PostgreSQL Database" || ((error_count++))
    check_service "redis-server" "Redis Cache" || ((error_count++))
    
    # Check system resources
    check_system_resources
    
    # Check database
    check_database || ((error_count++))
    
    # Check web response
    check_web_response || ((error_count++))
    
    # Check SSL certificate (uncomment and set domain)
    # check_ssl_certificate "yourdomain.com"
    
    # Check log sizes
    check_log_sizes
    
    # Check backup status
    check_backup_status
    
    # Check security updates
    check_security_updates
    
    # Check fail2ban
    check_fail2ban
    
    # Summary
    if [ "$error_count" -eq 0 ]; then
        log_message "✅ All systems operational"
    else
        send_alert "$error_count critical issues detected. Check logs for details." "CRITICAL"
    fi
    
    log_message "🔍 System monitoring completed"
}

# Performance monitoring function
performance_check() {
    log_message "📊 Starting performance monitoring"
    
    # Load average
    load_avg=$(uptime | awk -F'load average:' '{print $2}' | tr -d ' ')
    log_message "ℹ️  Load average: $load_avg"
    
    # Network connections
    connections=$(netstat -an | wc -l)
    log_message "ℹ️  Active network connections: $connections"
    
    # Process count
    processes=$(ps aux | wc -l)
    log_message "ℹ️  Running processes: $processes"
    
    # Top memory consumers
    log_message "ℹ️  Top memory consumers:"
    ps aux --sort=-%mem | head -5 | awk '{print $11 " - " $4 "%"}' | tail -4 | while read line; do
        log_message "   $line"
    done
}

# Check command line arguments
case "${1:-}" in
    "performance")
        performance_check
        ;;
    "quick")
        check_service "nginx" "Nginx"
        check_service "$SERVICE_NAME" "Application"
        check_web_response
        ;;
    *)
        main
        ;;
esac

exit 0
