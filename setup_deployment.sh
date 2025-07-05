#!/bin/bash

# ELMA Group - Final Setup and Verification Script
# This script ensures all deployment files are properly configured
# Author: GitHub Copilot for ELMA Group
# Version: 1.0

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🏢 ELMA Group - Final Setup Verification${NC}"
echo -e "${BLUE}=======================================${NC}"

# Check if we're in the right directory
if [ ! -f "application.py" ]; then
    echo -e "${RED}❌ Error: Please run this script from the ElmaGroup directory${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Verifying deployment files and permissions...${NC}"

# Make all scripts executable
chmod +x *.sh

# Verify all required files exist
required_files=(
    "deploy_ec2.sh"
    "monitor_system.sh"
    "backup_system.sh"
    "optimize_performance.sh"
    "migrate_database.py"
    "test_postgresql.py"
    "requirements-production.txt"
    "config_production.py"
    "DEPLOYMENT_GUIDE.md"
    "DEPLOYMENT_CHECKLIST.md"
    "README_DEPLOYMENT.md"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ All required deployment files are present${NC}"
else
    echo -e "${RED}❌ Missing files:${NC}"
    printf '%s\n' "${missing_files[@]}"
    exit 1
fi

# Check script permissions
echo -e "${GREEN}✅ Checking script permissions...${NC}"
for script in *.sh; do
    if [ -x "$script" ]; then
        echo -e "  ✅ $script is executable"
    else
        echo -e "${RED}  ❌ $script is not executable${NC}"
        chmod +x "$script"
        echo -e "${GREEN}  ✅ Fixed permissions for $script${NC}"
    fi
done

# Verify Python requirements
echo -e "${GREEN}✅ Verifying requirements files...${NC}"
if [ -f "requirements-production.txt" ]; then
    echo -e "  ✅ Production requirements file exists"
    
    # Check for essential packages
    essential_packages=("Flask" "psycopg2-binary" "gunicorn" "redis")
    for package in "${essential_packages[@]}"; do
        if grep -q "$package" requirements-production.txt; then
            echo -e "  ✅ $package found in requirements"
        else
            echo -e "${YELLOW}  ⚠️  $package not found in requirements${NC}"
        fi
    done
else
    echo -e "${RED}  ❌ requirements-production.txt not found${NC}"
fi

# Create necessary directories
echo -e "${GREEN}✅ Creating necessary directories...${NC}"
mkdir -p app/static/uploads/{avatars,books,collections,posts}
echo -e "  ✅ Upload directories created"

# Verify application structure
echo -e "${GREEN}✅ Verifying application structure...${NC}"
required_dirs=(
    "app"
    "app/templates"
    "app/static"
    "app/static/css"
    "app/static/js"
    "app/static/images"
)

for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "  ✅ $dir exists"
    else
        echo -e "${RED}  ❌ $dir missing${NC}"
    fi
done

# Check for .gitignore
if [ ! -f ".gitignore" ]; then
    echo -e "${YELLOW}⚠️  Creating .gitignore file...${NC}"
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# Environment Variables
.env
.env.local
.env.production

# Database
*.db
*.sqlite3

# Logs
*.log
logs/

# OS Files
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo

# Uploads (keep directory structure)
app/static/uploads/*/*
!app/static/uploads/*/.gitkeep

# Backup files
*.backup
*.bak
EOF
    echo -e "${GREEN}  ✅ .gitignore created${NC}"
fi

# Create .gitkeep files for upload directories
for dir in app/static/uploads/{avatars,books,collections,posts}; do
    if [ ! -f "$dir/.gitkeep" ]; then
        touch "$dir/.gitkeep"
    fi
done

# Display deployment summary
echo -e "\n${BLUE}📋 Deployment Summary${NC}"
echo -e "${BLUE}=====================${NC}"

echo -e "\n${GREEN}✅ Ready for deployment!${NC}"
echo -e "\n${YELLOW}📁 Key Files:${NC}"
echo -e "  🚀 Main deployment: ${BLUE}deploy_ec2.sh${NC}"
echo -e "  🔧 Performance optimization: ${BLUE}optimize_performance.sh${NC}"
echo -e "  📊 System monitoring: ${BLUE}monitor_system.sh${NC}"
echo -e "  💾 Backup management: ${BLUE}backup_system.sh${NC}"
echo -e "  📖 Documentation: ${BLUE}DEPLOYMENT_GUIDE.md${NC}"
echo -e "  ✅ Checklist: ${BLUE}DEPLOYMENT_CHECKLIST.md${NC}"

echo -e "\n${YELLOW}🚀 Next Steps:${NC}"
echo -e "1. ${BLUE}git add . && git commit -m 'Professional deployment setup'${NC}"
echo -e "2. ${BLUE}git push origin main${NC}"
echo -e "3. Launch AWS EC2 instance (Ubuntu 22.04 LTS)"
echo -e "4. Upload code to EC2: ${BLUE}git clone <repo-url> ElmaGroup${NC}"
echo -e "5. Run deployment: ${BLUE}cd ElmaGroup && ./deploy_ec2.sh${NC}"
echo -e "6. Configure domain and SSL: ${BLUE}./ssl_setup.sh yourdomain.com${NC}"

echo -e "\n${YELLOW}📊 Expected Costs (Monthly):${NC}"
echo -e "  💰 EC2 t3.medium: ~$30"
echo -e "  💰 EBS Storage (20GB): ~$3"
echo -e "  💰 Data Transfer: ~$1-5"
echo -e "  💰 Domain (yearly): ~$12"
echo -e "  💰 SSL Certificate: Free (Let's Encrypt)"
echo -e "  ${GREEN}Total: ~$35-40/month${NC}"

echo -e "\n${GREEN}🎉 ELMA Group is ready for professional deployment!${NC}"
echo -e "${GREEN}All scripts, documentation, and configurations are in place.${NC}"

echo -e "\n${BLUE}📞 Support:${NC}"
echo -e "  📖 Full guide: ${BLUE}DEPLOYMENT_GUIDE.md${NC}"
echo -e "  ✅ Checklist: ${BLUE}DEPLOYMENT_CHECKLIST.md${NC}"
echo -e "  📄 README: ${BLUE}README_DEPLOYMENT.md${NC}"

echo -e "\n${YELLOW}⚠️  Remember to:${NC}"
echo -e "  - Keep your .env file secure and backed up"
echo -e "  - Update DNS records to point to your EC2 IP"
echo -e "  - Test all functionality after deployment"
echo -e "  - Set up monitoring and backup verification"

exit 0
