# deploy-frontend.sh
#!/bin/bash

# QNAP Container Station deployment script
echo "Deploying Etsy Seller Automater Frontend to QNAP NAS..."

# Build production image
docker build -t etsy-frontend:latest \
  --build-arg REACT_APP_API_BASE_URL=http://your-qnap-ip:3003 \
  --build-arg REACT_APP_TENANT_MODE=multi \
  -f Dockerfile.frontend .

# Create tenant-specific volumes
docker volume create etsy_tenant_assets
docker volume create etsy_nginx_config

# Deploy with Container Station
docker run -d \
  --name etsy-frontend-prod \
  --restart unless-stopped \
  -p 80:80 \
  -p 443:443 \
  -v etsy_tenant_assets:/usr/share/nginx/html/tenant-assets \
  -v etsy_nginx_config:/etc/nginx/conf.d \
  --network etsy-network \
  etsy-frontend:latest

echo "Frontend deployed successfully!"
echo "Access at: http://tenant1.your-qnap-ip or http://your-qnap-ip"