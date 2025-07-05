#!/bin/bash

# ELMA Group - Professional Backup and Recovery Script
# This script handles automated backups, monitoring, and recovery procedures
# Author: GitHub Copilot for ELMA Group
# Version: 1.0

set -e

# Configuration
BACKUP_BASE_DIR="/var/backups/elmagroup"
APP_DIR="/home/ubuntu/ElmaGroup"
DB_NAME="elmagroup_db"
DB_USER="elmagroup"
RETENTION_DAYS=30
EMAIL_NOTIFICATIONS="admin@elmagroup.com"
S3_BUCKET=""  # Optional: Set for S3 backup storage

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging function
log_message() {
    echo -e "${GREEN}$(date '+%Y-%m-%d %H:%M:%S')${NC} - $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$BACKUP_BASE_DIR/backup.log"
}

error_message() {
    echo -e "${RED}$(date '+%Y-%m-%d %H:%M:%S')${NC} - ERROR: $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: $1" >> "$BACKUP_BASE_DIR/backup.log"
}

# Create backup directories
create_backup_dirs() {
    log_message "Creating backup directory structure"
    sudo mkdir -p "$BACKUP_BASE_DIR"/{database,application,config,logs}
    sudo chown -R ubuntu:ubuntu "$BACKUP_BASE_DIR"
}

# Database backup function
backup_database() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_BASE_DIR/database/db_backup_$timestamp.sql"
    local compressed_file="$backup_file.gz"
    
    log_message "Starting database backup"
    
    # Create database dump
    if sudo -u postgres pg_dump "$DB_NAME" > "$backup_file"; then
        # Compress the backup
        gzip "$backup_file"
        
        local file_size=$(du -h "$compressed_file" | cut -f1)
        log_message "Database backup completed: $compressed_file ($file_size)"
        
        # Verify backup integrity
        if gunzip -t "$compressed_file"; then
            log_message "Database backup integrity verified"
        else
            error_message "Database backup integrity check failed"
            return 1
        fi
        
        echo "$compressed_file"
        return 0
    else
        error_message "Database backup failed"
        return 1
    fi
}

# Application backup function
backup_application() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_BASE_DIR/application/app_backup_$timestamp.tar.gz"
    
    log_message "Starting application backup"
    
    # Create application backup excluding virtual environment and cache
    if tar -czf "$backup_file" \
        -C "$(dirname "$APP_DIR")" \
        --exclude="ElmaGroup/venv" \
        --exclude="ElmaGroup/__pycache__" \
        --exclude="ElmaGroup/.git" \
        --exclude="ElmaGroup/node_modules" \
        --exclude="ElmaGroup/*.pyc" \
        --exclude="ElmaGroup/.pytest_cache" \
        ElmaGroup; then
        
        local file_size=$(du -h "$backup_file" | cut -f1)
        log_message "Application backup completed: $backup_file ($file_size)"
        
        echo "$backup_file"
        return 0
    else
        error_message "Application backup failed"
        return 1
    fi
}

# Configuration backup function
backup_configuration() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_BASE_DIR/config/config_backup_$timestamp.tar.gz"
    
    log_message "Starting configuration backup"
    
    # Create temporary directory for config files
    local temp_dir=$(mktemp -d)
    
    # Copy configuration files
    sudo cp -r /etc/nginx/sites-available "$temp_dir/"
    sudo cp -r /etc/systemd/system/elmagroup.service "$temp_dir/" 2>/dev/null || true
    sudo cp -r /etc/postgresql/*/main/postgresql.conf "$temp_dir/" 2>/dev/null || true
    sudo cp -r /etc/postgresql/*/main/pg_hba.conf "$temp_dir/" 2>/dev/null || true
    sudo cp -r /etc/fail2ban/jail.local "$temp_dir/" 2>/dev/null || true
    sudo cp -r /etc/ufw/user.rules "$temp_dir/" 2>/dev/null || true
    
    # Change ownership
    sudo chown -R ubuntu:ubuntu "$temp_dir"
    
    # Create archive
    if tar -czf "$backup_file" -C "$temp_dir" .; then
        local file_size=$(du -h "$backup_file" | cut -f1)
        log_message "Configuration backup completed: $backup_file ($file_size)"
        
        # Cleanup
        rm -rf "$temp_dir"
        
        echo "$backup_file"
        return 0
    else
        error_message "Configuration backup failed"
        rm -rf "$temp_dir"
        return 1
    fi
}

# Upload to S3 (optional)
upload_to_s3() {
    local file="$1"
    
    if [ -z "$S3_BUCKET" ]; then
        return 0
    fi
    
    if command -v aws >/dev/null 2>&1; then
        log_message "Uploading to S3: $(basename "$file")"
        
        if aws s3 cp "$file" "s3://$S3_BUCKET/elmagroup-backups/$(date +%Y/%m/)/"; then
            log_message "S3 upload completed: $(basename "$file")"
        else
            error_message "S3 upload failed: $(basename "$file")"
        fi
    else
        log_message "AWS CLI not installed, skipping S3 upload"
    fi
}

# Cleanup old backups
cleanup_old_backups() {
    log_message "Cleaning up backups older than $RETENTION_DAYS days"
    
    # Count files before cleanup
    local before_count=$(find "$BACKUP_BASE_DIR" -type f -name "*.gz" -o -name "*.tar.gz" | wc -l)
    
    # Remove old database backups
    find "$BACKUP_BASE_DIR/database" -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
    
    # Remove old application backups
    find "$BACKUP_BASE_DIR/application" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
    
    # Remove old configuration backups
    find "$BACKUP_BASE_DIR/config" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
    
    # Count files after cleanup
    local after_count=$(find "$BACKUP_BASE_DIR" -type f -name "*.gz" -o -name "*.tar.gz" | wc -l)
    local removed_count=$((before_count - after_count))
    
    log_message "Cleanup completed: $removed_count old backup files removed"
}

# Send email notification
send_notification() {
    local subject="$1"
    local message="$2"
    
    if command -v mail >/dev/null 2>&1 && [ -n "$EMAIL_NOTIFICATIONS" ]; then
        echo "$message" | mail -s "$subject" "$EMAIL_NOTIFICATIONS"
        log_message "Email notification sent: $subject"
    fi
}

# Database restore function
restore_database() {
    local backup_file="$1"
    
    if [ -z "$backup_file" ] || [ ! -f "$backup_file" ]; then
        error_message "Backup file not found or not specified"
        echo "Usage: $0 restore-db /path/to/backup.sql.gz"
        return 1
    fi
    
    log_message "Starting database restore from: $backup_file"
    
    # Confirm restore operation
    echo -e "${YELLOW}WARNING: This will replace the current database!${NC}"
    echo -e "${YELLOW}Current database will be backed up before restore.${NC}"
    read -p "Continue with restore? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log_message "Database restore cancelled by user"
        return 1
    fi
    
    # Create backup of current database
    local current_backup="$BACKUP_BASE_DIR/database/pre_restore_backup_$(date +%Y%m%d_%H%M%S).sql.gz"
    log_message "Creating backup of current database"
    
    if ! backup_database > /dev/null; then
        error_message "Failed to backup current database"
        return 1
    fi
    
    # Restore database
    log_message "Restoring database from backup"
    
    if gunzip -c "$backup_file" | sudo -u postgres psql "$DB_NAME"; then
        log_message "Database restore completed successfully"
        
        # Restart application
        sudo systemctl restart elmagroup
        log_message "Application restarted"
        
        return 0
    else
        error_message "Database restore failed"
        return 1
    fi
}

# Application restore function
restore_application() {
    local backup_file="$1"
    
    if [ -z "$backup_file" ] || [ ! -f "$backup_file" ]; then
        error_message "Backup file not found or not specified"
        echo "Usage: $0 restore-app /path/to/backup.tar.gz"
        return 1
    fi
    
    log_message "Starting application restore from: $backup_file"
    
    # Confirm restore operation
    echo -e "${YELLOW}WARNING: This will replace the current application files!${NC}"
    read -p "Continue with restore? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log_message "Application restore cancelled by user"
        return 1
    fi
    
    # Stop application
    sudo systemctl stop elmagroup
    
    # Backup current application
    local current_backup="$BACKUP_BASE_DIR/application/pre_restore_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    log_message "Creating backup of current application"
    backup_application > /dev/null
    
    # Restore application
    log_message "Restoring application from backup"
    
    if tar -xzf "$backup_file" -C "$(dirname "$APP_DIR")"; then
        log_message "Application restore completed"
        
        # Restart services
        sudo systemctl start elmagroup
        sudo systemctl restart nginx
        
        log_message "Services restarted"
        return 0
    else
        error_message "Application restore failed"
        sudo systemctl start elmagroup  # Try to start the old version
        return 1
    fi
}

# List available backups
list_backups() {
    echo -e "${BLUE}Available Database Backups:${NC}"
    find "$BACKUP_BASE_DIR/database" -name "*.sql.gz" -printf "%T@ %Tc %p\n" 2>/dev/null | sort -nr | head -10 | cut -d' ' -f2-
    
    echo -e "\n${BLUE}Available Application Backups:${NC}"
    find "$BACKUP_BASE_DIR/application" -name "*.tar.gz" -printf "%T@ %Tc %p\n" 2>/dev/null | sort -nr | head -10 | cut -d' ' -f2-
    
    echo -e "\n${BLUE}Available Configuration Backups:${NC}"
    find "$BACKUP_BASE_DIR/config" -name "*.tar.gz" -printf "%T@ %Tc %p\n" 2>/dev/null | sort -nr | head -10 | cut -d' ' -f2-
}

# Backup verification
verify_backups() {
    log_message "Starting backup verification"
    
    # Check database backups
    local db_backup_count=$(find "$BACKUP_BASE_DIR/database" -name "*.sql.gz" -mtime -1 | wc -l)
    if [ "$db_backup_count" -eq 0 ]; then
        error_message "No recent database backups found"
    else
        log_message "Found $db_backup_count recent database backup(s)"
    fi
    
    # Check application backups
    local app_backup_count=$(find "$BACKUP_BASE_DIR/application" -name "*.tar.gz" -mtime -1 | wc -l)
    if [ "$app_backup_count" -eq 0 ]; then
        error_message "No recent application backups found"
    else
        log_message "Found $app_backup_count recent application backup(s)"
    fi
    
    # Test backup integrity
    local latest_db_backup=$(find "$BACKUP_BASE_DIR/database" -name "*.sql.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
    if [ -n "$latest_db_backup" ]; then
        if gunzip -t "$latest_db_backup"; then
            log_message "Latest database backup integrity: OK"
        else
            error_message "Latest database backup integrity: FAILED"
        fi
    fi
}

# Main backup function
main_backup() {
    log_message "Starting ELMA Group backup process"
    
    create_backup_dirs
    
    local success_count=0
    local total_backups=0
    
    # Database backup
    ((total_backups++))
    if db_backup=$(backup_database); then
        ((success_count++))
        upload_to_s3 "$db_backup"
    fi
    
    # Application backup
    ((total_backups++))
    if app_backup=$(backup_application); then
        ((success_count++))
        upload_to_s3 "$app_backup"
    fi
    
    # Configuration backup
    ((total_backups++))
    if config_backup=$(backup_configuration); then
        ((success_count++))
        upload_to_s3 "$config_backup"
    fi
    
    # Cleanup old backups
    cleanup_old_backups
    
    # Summary
    log_message "Backup process completed: $success_count/$total_backups successful"
    
    # Send notification
    if [ "$success_count" -eq "$total_backups" ]; then
        send_notification "ELMA Group Backup Success" "All backups completed successfully on $(hostname) at $(date)"
    else
        send_notification "ELMA Group Backup Warning" "Some backups failed on $(hostname) at $(date). Check logs for details."
    fi
    
    # Verify backups
    verify_backups
}

# Display usage information
usage() {
    echo "ELMA Group Backup and Recovery Script"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  backup                 - Run full backup (default)"
    echo "  restore-db <file>      - Restore database from backup file"
    echo "  restore-app <file>     - Restore application from backup file"
    echo "  list                   - List available backups"
    echo "  verify                 - Verify backup integrity"
    echo "  cleanup                - Remove old backups"
    echo ""
    echo "Examples:"
    echo "  $0 backup"
    echo "  $0 restore-db /var/backups/elmagroup/database/db_backup_20231201_120000.sql.gz"
    echo "  $0 restore-app /var/backups/elmagroup/application/app_backup_20231201_120000.tar.gz"
    echo "  $0 list"
}

# Main script logic
case "${1:-backup}" in
    "backup")
        main_backup
        ;;
    "restore-db")
        restore_database "$2"
        ;;
    "restore-app")
        restore_application "$2"
        ;;
    "list")
        list_backups
        ;;
    "verify")
        verify_backups
        ;;
    "cleanup")
        cleanup_old_backups
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
