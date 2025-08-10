#!/bin/bash
# deploy-production.sh

set -e

QNAP_HOST="your-qnap-ip"
QNAP_USER="admin"
PROJECT_PATH="/share/Container/etsy-saas-prod"
BACKUP_PATH="/share/Container/backups"

echo "🚀 Starting production deployment to QNAP NAS..."

# Create deployment directory
ssh $QNAP_USER@$QNAP_HOST "mkdir -p $PROJECT_PATH"

# Backup current deployment if exists
ssh $QNAP_USER@$QNAP_HOST "
if [ -d $PROJECT_PATH/current ]; then
    echo '📦 Creating backup of current deployment...'
    mkdir -p $BACKUP_PATH
    tar -czf $BACKUP_PATH/backup-$(date +%Y%m%d-%H%M%S).tar.gz -C $PROJECT_PATH current
fi
"

# Upload new deployment files
echo "📤 Uploading deployment files..."
rsync -avz --exclude='.git' --exclude='node_modules' --exclude='__pycache__' \
    ./ $QNAP_USER@$QNAP_HOST:$PROJECT_PATH/new/

# Switch to new deployment
ssh $QNAP_USER@$QNAP_HOST "
cd $PROJECT_PATH
if [ -d current ]; then
    mv current previous
fi
mv new current
"

# Start services
echo "🔄 Starting production services..."
ssh $QNAP_USER@$QNAP_HOST "
cd $PROJECT_PATH/current
docker-compose -f docker-compose.prod.yml down || true
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
"

# Health check
echo "🏥 Running health checks..."
sleep 30
ssh $QNAP_USER@$QNAP_HOST "
cd $PROJECT_PATH/current
./scripts/health-check.sh
"

# Cleanup old images
ssh $QNAP_USER@$QNAP_HOST "
echo '🧹 Cleaning up old Docker images...'
docker system prune -f
docker image prune -f
"

echo "✅ Production deployment completed successfully!"
echo "🌐 Services available at: https://your-domain.com"
echo "📊 Monitor logs with: ssh $QNAP_USER@$QNAP_HOST 'cd $PROJECT_PATH/current && docker-compose logs -f'"