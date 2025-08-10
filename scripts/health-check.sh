#!/bin/bash
# scripts/health-check.sh

set -e

echo "🔍 Running comprehensive health checks..."

# Check if all services are running
echo "📋 Checking service status..."
services=("api-gateway" "auth-service" "etsy-service" "design-service" "analytics-service" "postgres" "redis" "minio")

for service in "${services[@]}"; do
    if docker-compose ps | grep -q "$service.*Up"; then
        echo "✅ $service is running"
    else
        echo "❌ $service is not running"
        exit 1
    fi
done

# Check service endpoints
echo "🌐 Testing service endpoints..."

# API Gateway health check
if curl -f http://localhost:8080/health &>/dev/null; then
    echo "✅ API Gateway health check passed"
else
    echo "❌ API Gateway health check failed"
    exit 1
fi

# Database connectivity
if docker-compose exec -T postgres pg_isready -U postgres &>/dev/null; then
    echo "✅ Database connectivity check passed"
else
    echo "❌ Database connectivity check failed"
    exit 1
fi

# Redis connectivity
if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
    echo "✅ Redis connectivity check passed"
else
    echo "❌ Redis connectivity check failed"
    exit 1
fi

# MinIO health check
if curl -f http://localhost:9000/minio/health/live &>/dev/null; then
    echo "✅ MinIO health check passed"
else
    echo "❌ MinIO health check failed"
    exit 1
fi

echo "🎉 All health checks passed!"