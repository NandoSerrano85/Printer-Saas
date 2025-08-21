# Multi-Tenant Database Architecture

This directory contains the complete database architecture for the multi-tenant Etsy Seller Automater SaaS platform.

## Architecture Overview

The database follows a **schema-per-tenant** multi-tenancy model:

- **Core Schema (`core`)**: Contains tenant management tables, subscriptions, and global configuration
- **Tenant Schemas (`tenant_*`)**: Each tenant gets their own schema with isolated data

## Directory Structure

```
database/
├── core.py                 # Database connection and core functions
├── init.sql               # Database initialization script
├── seed_data.sql          # Sample data for development/testing
├── README.md              # This documentation
├── entities/              # SQLAlchemy entity definitions
│   ├── __init__.py        # Entity exports
│   ├── base.py            # Base classes and mixins
│   ├── tenant.py          # Core tenant management entities
│   ├── user.py            # User-related entities
│   ├── template.py        # Product template entities
│   ├── design.py          # Design and image entities
│   ├── mockup.py          # Mockup generation entities
│   ├── order.py           # Order management entities
│   └── canvas.py          # Canvas and size configuration entities
├── migrations/            # Database migrations
│   ├── migration_manager.py    # Migration management tool
│   ├── 001_create_core_schema.py
│   └── 002_create_tenant_tables.py
└── schemas/               # Schema definitions and documentation
```

## Entity Relationship Overview

### Core Multi-Tenant Entities

- **Tenant**: Core tenant information (company, subdomain, subscription)
- **TenantUser**: Admin users who can manage the tenant
- **TenantSubscription**: Billing and subscription management
- **TenantApiKey**: API keys for service integration
- **TenantUsage**: Usage metrics and billing data

### Tenant-Scoped Entities

Each tenant schema contains:

- **User**: Application users (shop owners, designers)
- **EtsyProductTemplate**: Product templates for Etsy listings
- **DesignImage**: Uploaded design files and assets
- **CanvasConfig**: Canvas configurations for different product types
- **SizeConfig**: Size variations within canvases
- **Mockup**: Mockup generation jobs and results
- **Order**: Orders from various platforms (Etsy, Shopify, etc.)

## Key Features

### Multi-Tenant Security
- **Schema Isolation**: Each tenant's data is in a separate schema
- **Row-Level Security**: Additional tenant_id validation where needed
- **API Key Authentication**: Service-to-service authentication
- **User Session Management**: Secure user authentication and sessions

### Soft Deletes
- **SoftDeleteMixin**: Entities can be soft-deleted instead of hard-deleted
- **Audit Trail**: Track who created/modified records and when

### Flexible Metadata
- **JSON Columns**: Settings, preferences, and metadata stored as JSON
- **Tag Support**: Many entities support tagging for organization
- **Custom Fields**: Extensible through JSON metadata columns

### Performance Optimizations
- **Strategic Indexing**: Indexes on tenant_id, user_id, and frequently queried fields
- **Connection Pooling**: Efficient database connection management
- **Query Optimization**: Designed for efficient multi-tenant queries

## Database Setup

### 1. Initialize the Database

Run the initialization script to create the core schema and functions:

```bash
psql -d etsy_saas -f backend/database/init.sql
```

### 2. Run Migrations

Use the migration manager to apply all migrations:

```bash
cd backend/database/migrations
python migration_manager.py --database-url "postgresql://user:pass@localhost/etsy_saas" migrate
```

### 3. Create Tenant Schemas

Create a new tenant schema:

```bash
python migration_manager.py --database-url "postgresql://user:pass@localhost/etsy_saas" create-tenant --tenant-id "uuid-here" --schema-name "tenant_example"
```

### 4. Seed Sample Data (Optional)

For development/testing, load sample data:

```bash
psql -d etsy_saas -f backend/database/seed_data.sql
```

## Working with Tenants

### Creating a New Tenant

1. Insert into `core.tenants` table
2. Create tenant schema using `create_tenant_schema()` function
3. Set up initial user and subscription

```sql
-- Create tenant record
INSERT INTO core.tenants (subdomain, company_name, database_schema) 
VALUES ('newcompany', 'New Company Inc', 'tenant_newcompany');

-- Create tenant schema and tables
SELECT create_tenant_schema(
    (SELECT id FROM core.tenants WHERE subdomain = 'newcompany'),
    'tenant_newcompany'
);
```

### Querying Tenant Data

Always set the search path when working with tenant data:

```python
# Python example
db.execute(text("SET search_path TO tenant_example, core, public"))
users = db.query(User).all()  # Queries tenant_example.users
```

### Tenant Context Middleware

Services should use tenant context middleware to:
1. Extract tenant information from request (subdomain, API key)
2. Set appropriate database search path
3. Validate tenant permissions and limits

## Migration Management

The migration system supports:

- **Forward Migrations**: `migrate` command applies pending migrations
- **Rollback Migrations**: `rollback` command reverts to target version
- **Tenant Schema Creation**: Automated tenant schema and table creation
- **Migration Tracking**: All applied migrations are tracked with checksums

### Creating New Migrations

1. Create new file: `003_description.py`
2. Implement `upgrade()` and `downgrade()` functions
3. Set revision metadata (version, down_revision, etc.)
4. Test thoroughly before applying to production

## Performance Considerations

### Connection Pooling
- Use connection pooling for high-traffic applications
- Configure appropriate pool sizes per service
- Monitor connection usage and adjust as needed

### Query Optimization
- Always filter by `tenant_id` first in multi-tenant queries
- Use appropriate indexes on frequently queried columns
- Consider partitioning for very large datasets

### Caching Strategy
- Cache tenant configuration and subscription data
- Use Redis for session storage and temporary data
- Implement query result caching for expensive operations

## Security Best Practices

### Data Isolation
- Never mix tenant data in queries
- Always validate tenant context before data operations
- Use parameterized queries to prevent SQL injection

### Access Control
- Implement proper authentication and authorization
- Use API keys for service-to-service communication
- Regular security audits and penetration testing

### Audit Logging
- Track all data modifications with user context
- Log authentication and authorization events
- Monitor for suspicious activity patterns

## Monitoring and Maintenance

### Health Checks
- Monitor database connection health
- Track query performance and slow queries
- Alert on unusual tenant usage patterns

### Backup Strategy
- Regular automated backups of all tenant data
- Point-in-time recovery capability
- Test restore procedures regularly

### Tenant Usage Monitoring
- Track resource usage per tenant
- Implement usage limits and throttling
- Generate billing reports from usage metrics

## Development Workflow

### Local Development
1. Set up local PostgreSQL database
2. Run initialization and migration scripts
3. Load seed data for testing
4. Use `migration_manager.py` for schema changes

### Testing
- Use separate test database with isolated tenant schemas
- Implement automated tests for all entity relationships
- Test migration rollback scenarios

### Production Deployment
- Use migration manager for zero-downtime deployments
- Monitor migration execution time and impact
- Have rollback plan for failed migrations

## Troubleshooting

### Common Issues

**Connection Issues**
- Check database connection string format
- Verify network connectivity and firewall settings
- Confirm database user permissions

**Migration Failures**
- Review migration logs for specific errors
- Check for conflicting schema changes
- Verify migration dependencies and order

**Performance Issues**
- Analyze slow query logs
- Check index usage with EXPLAIN ANALYZE
- Monitor connection pool utilization

**Data Isolation Issues**
- Verify search_path is set correctly
- Check tenant_id filtering in queries
- Review multi-tenant middleware configuration

For additional help, check the logs and monitoring dashboards, or consult the development team.