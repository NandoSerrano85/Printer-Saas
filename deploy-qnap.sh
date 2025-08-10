#!/bin/bash
# deploy-qnap.sh

# Install Container Station if not already installed
# Access QNAP Web UI -> App Center -> Container Station

# Create project directory
ssh admin@qnap-ip "mkdir -p /share/Container/etsy-saas"

# Copy docker-compose files
scp docker-compose.yml admin@qnap-ip:/share/Container/etsy-saas/
scp docker-compose.override.yml admin@qnap-ip:/share/Container/etsy-saas/

# Create persistent volumes on QNAP
ssh admin@qnap-ip "mkdir -p /share/Container/volumes/{postgres,redis,minio}"

# Set proper permissions
ssh admin@qnap-ip "chmod -R 755 /share/Container/etsy-saas"

# Start services
ssh admin@qnap-ip "cd /share/Container/etsy-saas && docker-compose up -d"