# migrations/migration_manager.py
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
import os

class TenantMigrationManager:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url)
    
    def run_core_migrations(self):
        """Run migrations for core (non-tenant) tables"""
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", self.database_url)
        command.upgrade(alembic_cfg, "head")
    
    def create_tenant_schema(self, tenant_id: str, schema_name: str):
        """Create schema and tables for new tenant"""
        
        with self.engine.begin() as conn:
            # Create schema
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
            
            # Create tenant-specific tables
            tenant_tables = [
                f"""
                CREATE TABLE {schema_name}.orders (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    etsy_receipt_id BIGINT UNIQUE,
                    buyer_email VARCHAR(255),
                    total_amount DECIMAL(10,2),
                    currency VARCHAR(3) DEFAULT 'USD',
                    order_date TIMESTAMP,
                    status VARCHAR(50) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                f"""
                CREATE TABLE {schema_name}.products (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    etsy_listing_id BIGINT UNIQUE,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    price DECIMAL(10,2),
                    quantity INTEGER DEFAULT 0,
                    sku VARCHAR(100),
                    tags TEXT[],
                    images JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                f"""
                CREATE TABLE {schema_name}.designs (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(255) NOT NULL,
                    file_path VARCHAR(500),
                    file_size BIGINT,
                    content_type VARCHAR(100),
                    tags TEXT[],
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                f"""
                CREATE TABLE {schema_name}.mockups (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    design_id UUID REFERENCES {schema_name}.designs(id),
                    template_name VARCHAR(100),
                    mockup_url VARCHAR(500),
                    settings JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                f"""
                CREATE TABLE {schema_name}.jobs (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    job_type VARCHAR(100) NOT NULL,
                    status VARCHAR(50) DEFAULT 'queued',
                    payload JSONB,
                    result JSONB,
                    error_message TEXT,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            ]
            
            for table_sql in tenant_tables:
                conn.execute(text(table_sql))
            
            # Create indexes for performance
            indexes = [
                f"CREATE INDEX IF NOT EXISTS idx_{schema_name}_orders_date ON {schema_name}.orders(order_date)",
                f"CREATE INDEX IF NOT EXISTS idx_{schema_name}_orders_status ON {schema_name}.orders(status)",
                f"CREATE INDEX IF NOT EXISTS idx_{schema_name}_products_etsy_id ON {schema_name}.products(etsy_listing_id)",
                f"CREATE INDEX IF NOT EXISTS idx_{schema_name}_designs_created ON {schema_name}.designs(created_at)",
                f"CREATE INDEX IF NOT EXISTS idx_{schema_name}_jobs_status ON {schema_name}.jobs(status, created_at)",
            ]
            
            for index_sql in indexes:
                conn.execute(text(index_sql))
        
        print(f"✅ Created schema and tables for tenant: {tenant_id}")
    
    def migrate_tenant_data(self, from_schema: str, to_schema: str):
        """Migrate data between tenant schemas"""
        
        tables = ["orders", "products", "designs", "mockups", "jobs"]
        
        with self.engine.begin() as conn:
            for table in tables:
                # Copy data from old schema to new schema
                copy_sql = f"""
                INSERT INTO {to_schema}.{table}
                SELECT * FROM {from_schema}.{table}
                ON CONFLICT DO NOTHING
                """
                conn.execute(text(copy_sql))
        
        print(f"✅ Migrated data from {from_schema} to {to_schema}")
    
    def get_tenant_schema_size(self, schema_name: str) -> dict:
        """Get storage usage statistics for tenant schema"""
        
        with self.engine.connect() as conn:
            result = conn.execute(text(f"""
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
            FROM pg_tables 
            WHERE schemaname = '{schema_name}'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            """))
            
            tables = []
            total_size = 0
            
            for row in result:
                table_info = {
                    "table_name": row.tablename,
                    "size_pretty": row.size,
                    "size_bytes": row.size_bytes
                }
                tables.append(table_info)
                total_size += row.size_bytes
            
            return {
                "schema": schema_name,
                "tables": tables,
                "total_size_bytes": total_size,
                "total_size_pretty": self._format_bytes(total_size)
            }
    
    def _format_bytes(self, bytes_size: int) -> str:
        """Format bytes to human readable size"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} PB"

# Migration CLI tool
if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Tenant Migration Manager')
    parser.add_argument('command', choices=['create', 'migrate', 'stats'])
    parser.add_argument('--tenant-id', required=True)
    parser.add_argument('--from-schema', help='Source schema for migration')
    parser.add_argument('--to-schema', help='Target schema for migration')
    
    args = parser.parse_args()
    
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/etsy_saas')
    manager = TenantMigrationManager(database_url)
    
    if args.command == 'create':
        schema_name = f"tenant_{args.tenant_id}"
        manager.create_tenant_schema(args.tenant_id, schema_name)
    
    elif args.command == 'migrate':
        if not args.from_schema or not args.to_schema:
            print("Error: --from-schema and --to-schema required for migration")
            sys.exit(1)
        manager.migrate_tenant_data(args.from_schema, args.to_schema)
    
    elif args.command == 'stats':
        schema_name = f"tenant_{args.tenant_id}"
        stats = manager.get_tenant_schema_size(schema_name)
        
        print(f"\n📊 Storage statistics for {stats['schema']}:")
        print(f"Total size: {stats['total_size_pretty']}")
        print("\nTable breakdown:")
        for table in stats['tables']:
            print(f"  {table['table_name']}: {table['size_pretty']}")