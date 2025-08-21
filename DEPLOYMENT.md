# Printer SaaS Deployment Guide

Complete deployment guide for the Printer SaaS application with Etsy and Shopify integrations.

## 🏗️ Architecture Overview

The Printer SaaS platform is a multi-tenant SaaS application with the following components:

- **Backend API**: FastAPI application with OAuth integrations
- **Database**: PostgreSQL with multi-tenant schema isolation
- **Cache**: Redis for caching and background job queue
- **Background Workers**: Celery for asynchronous tasks
- **Monitoring**: Prometheus and Grafana for observability
- **Integrations**: Native Etsy and Shopify API integrations

## 📋 Prerequisites

### Required Software
- Docker (version 20.10+)
- Docker Compose (version 2.0+)
- Git
- curl (for health checks)

### Required Accounts & API Access
- **Etsy Developer Account**: [Etsy Developers](https://developers.etsy.com/)
- **Shopify Partner Account**: [Shopify Partners](https://partners.shopify.com/)

### System Requirements
- **Minimum**: 4 GB RAM, 2 CPU cores, 20 GB disk space
- **Recommended**: 8 GB RAM, 4 CPU cores, 50 GB disk space
- **Production**: 16 GB RAM, 8 CPU cores, 100 GB disk space

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd "Printer Saas"

# Create environment file
cp backend/.env.example .env.development

# Setup monitoring (optional)
./scripts/setup-monitoring.sh
```

### 2. Configure Environment

Edit `.env.development` with your configuration:

```bash
# Database
DATABASE_PASSWORD=your_secure_password

# Security Keys (generate random strings)
JWT_SECRET_KEY=your_jwt_secret_key_here
SESSION_SECRET_KEY=your_session_secret_key_here

# Etsy API (from Etsy Developers Console)
ETSY_CLIENT_ID=your_etsy_client_id
ETSY_CLIENT_SECRET=your_etsy_client_secret

# Shopify API (from Shopify Partner Dashboard)
SHOPIFY_CLIENT_ID=your_shopify_client_id
SHOPIFY_CLIENT_SECRET=your_shopify_client_secret
```

### 3. Deploy

```bash
# Development deployment
./deploy.sh development

# With monitoring
./deploy.sh development --monitoring

# With development tools
./deploy.sh development --development-tools
```

### 4. Access Applications

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000
- **Prometheus**: http://localhost:9090 (if monitoring enabled)
- **Grafana**: http://localhost:3001 (if monitoring enabled)

## 🔧 Configuration

### Environment Files

Create environment-specific configuration files:

```bash
# Development
.env.development

# Staging  
.env.staging

# Production
.env.production
```

### Key Configuration Options

#### Database Configuration
```bash
DATABASE_URL=postgresql://user:password@host:port/database
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
```

#### Security Configuration
```bash
JWT_SECRET_KEY=your-256-bit-secret-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
PASSWORD_BCRYPT_ROUNDS=12
```

#### Integration Configuration
```bash
# Etsy API
ETSY_CLIENT_ID=your_etsy_client_id
ETSY_CLIENT_SECRET=your_etsy_client_secret
ETSY_OAUTH_SCOPES=shops_r,shops_w,listings_r,listings_w,transactions_r

# Shopify API  
SHOPIFY_CLIENT_ID=your_shopify_client_id
SHOPIFY_CLIENT_SECRET=your_shopify_client_secret
SHOPIFY_OAUTH_SCOPES=read_products,write_products,read_orders,write_orders
```

#### Feature Flags
```bash
FEATURE_ETSY_INTEGRATION=true
FEATURE_SHOPIFY_INTEGRATION=true
FEATURE_BATCH_OPERATIONS=true
FEATURE_WEBHOOK_PROCESSING=true
```

## 📊 Database Management

### Running Migrations

```bash
# Run all pending migrations
./scripts/db-migrate.sh development migrate

# Migrate to specific version
./scripts/db-migrate.sh development migrate 003

# Check migration status
./scripts/db-migrate.sh development status

# Rollback to version
./scripts/db-migrate.sh development rollback 002
```

### Creating Tenants

```bash
# Create new tenant
./scripts/db-migrate.sh development create-tenant acme_corp

# This creates:
# - Tenant record in core.tenants
# - Dedicated schema: tenant_acme_corp
# - All tenant-specific tables
```

### Database Backup

```bash
# Backup database (production only, automatic in deploy script)
docker-compose exec postgres pg_dump -U postgres printer_saas > backup.sql

# Restore database
docker-compose exec -T postgres psql -U postgres printer_saas < backup.sql
```

## 🔌 API Integrations

### Etsy Integration Setup

1. **Create Etsy App**:
   - Go to [Etsy Developers](https://developers.etsy.com/)
   - Create new app
   - Note Client ID and Client Secret

2. **Configure OAuth Redirect**:
   ```bash
   ETSY_OAUTH_REDIRECT_URI=http://your-domain.com/api/v1/etsy/oauth/callback
   ```

3. **Test Integration**:
   ```bash
   curl -X GET "http://localhost:8000/api/v1/etsy/health"
   ```

### Shopify Integration Setup

1. **Create Shopify App**:
   - Go to [Shopify Partners](https://partners.shopify.com/)
   - Create new app
   - Note API Key and Secret Key

2. **Configure OAuth Redirect**:
   ```bash
   SHOPIFY_OAUTH_REDIRECT_URI=http://your-domain.com/api/v1/shopify/oauth/callback
   ```

3. **Test Integration**:
   ```bash
   curl -X GET "http://localhost:8000/api/v1/shopify/health"
   ```

## 📈 Monitoring

### Setup Monitoring Stack

```bash
# Setup monitoring configuration
./scripts/setup-monitoring.sh

# Deploy with monitoring
./deploy.sh development --monitoring
```

### Access Monitoring

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)

### Key Metrics

#### Application Metrics
- HTTP request rate and response times
- Error rates and status codes
- Active user sessions
- Integration API call rates

#### Business Metrics
- Connected Etsy/Shopify shops
- Order sync success/failure rates
- Template usage statistics
- Webhook processing metrics

#### Infrastructure Metrics
- Database connection pool usage
- Redis memory usage
- Celery queue lengths
- Container resource usage

### Alerts

Pre-configured alerts for:
- Service health issues
- High error rates
- Database performance problems
- Integration API failures
- Business logic failures

## 🛠️ Development Tools

### Enable Development Tools

```bash
./deploy.sh development --development-tools
```

### Available Tools

- **PgAdmin**: http://localhost:5050 (admin@printersaas.com/admin)
- **Redis Commander**: http://localhost:8081

### Useful Commands

```bash
# View logs
docker-compose logs -f backend

# Access backend container
docker-compose exec backend bash

# Run tests
docker-compose exec backend pytest

# Database shell
docker-compose exec postgres psql -U postgres printer_saas

# Redis CLI
docker-compose exec redis redis-cli
```

## 🚢 Production Deployment

### Production Environment Setup

1. **Create Production Environment File**:
   ```bash
   cp .env.example .env.production
   ```

2. **Configure Production Settings**:
   ```bash
   ENVIRONMENT=production
   DEBUG=false
   DATABASE_PASSWORD=secure_random_password
   JWT_SECRET_KEY=secure_random_jwt_key
   SESSION_SECRET_KEY=secure_random_session_key
   ```

3. **Deploy to Production**:
   ```bash
   ./deploy.sh production --monitoring
   ```

### Security Considerations

#### Secrets Management
- Use environment variables for all secrets
- Never commit secrets to version control
- Rotate secrets regularly
- Use dedicated secret management tools in production

#### Network Security
- Configure firewall rules
- Use HTTPS/TLS for all communication
- Implement rate limiting
- Monitor for suspicious activity

#### Database Security
- Use strong passwords
- Enable connection encryption
- Regular backups
- Monitor access logs

### Scaling Considerations

#### Horizontal Scaling
```bash
# Scale backend workers
docker-compose up -d --scale celery-worker=4

# Scale backend API
docker-compose up -d --scale backend=3
```

#### Performance Optimization
- Database connection pooling
- Redis caching strategy
- CDN for static assets
- Load balancing

## 🔍 Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check database logs
docker-compose logs postgres

# Test database connectivity
docker-compose exec backend python -c "from database.core import test_connection; test_connection()"
```

#### Integration API Issues
```bash
# Check API credentials
curl -X GET "http://localhost:8000/api/v1/etsy/integration/status"
curl -X GET "http://localhost:8000/api/v1/shopify/integration/status"

# View integration logs
docker-compose logs backend | grep -i "etsy\|shopify"
```

#### Performance Issues
```bash
# Check resource usage
docker stats

# Check database performance
docker-compose exec postgres psql -U postgres -c "\
SELECT pid, now() - pg_stat_activity.query_start AS duration, query \
FROM pg_stat_activity \
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';"
```

### Health Checks

```bash
# Overall health
curl http://localhost:8000/health

# API status
curl http://localhost:8000/api/v1/status

# Integration health
curl http://localhost:8000/api/v1/etsy/health
curl http://localhost:8000/api/v1/shopify/health
```

### Log Analysis

```bash
# Application logs
docker-compose logs backend

# Database logs
docker-compose logs postgres

# Worker logs
docker-compose logs celery-worker

# Search for errors
docker-compose logs backend | grep -i error

# Monitor real-time logs
docker-compose logs -f backend
```

## 📚 Additional Resources

### API Documentation
- Interactive docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Integration Documentation
- [Etsy API Documentation](https://developers.etsy.com/documentation/)
- [Shopify API Documentation](https://shopify.dev/api)

### Database Schema
- View schema: Connect to PgAdmin and explore `core` schema
- Entity relationships: See `/backend/database/entities/` directory

### Support
- Check logs for error messages
- Review monitoring dashboards
- Consult API documentation
- Check integration status endpoints

## 🔄 Maintenance

### Regular Tasks

#### Daily
- Monitor application health
- Check error rates and alerts
- Review integration sync status

#### Weekly
- Database backup verification
- Security update checks
- Performance review

#### Monthly
- Log rotation and cleanup
- Security audit
- Capacity planning review

### Updates and Upgrades

```bash
# Update application
git pull origin main
./deploy.sh production --force-recreate

# Update dependencies
# (Update requirements.txt and rebuild)
docker-compose build --no-cache backend
./deploy.sh production
```

This deployment guide provides comprehensive instructions for setting up, configuring, and maintaining the Printer SaaS application with full Etsy and Shopify integration support.