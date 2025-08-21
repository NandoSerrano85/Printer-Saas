#!/usr/bin/env python3
"""
Database Migration Manager
Manages database migrations for the multi-tenant Etsy Seller Automater SaaS
"""

import os
import sys
import importlib.util
from pathlib import Path
from typing import List, Dict, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MigrationManager:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.migrations_dir = Path(__file__).parent
        self.conn = None
        
    def connect(self):
        """Connect to the database"""
        try:
            self.conn = psycopg2.connect(self.database_url)
            self.conn.autocommit = False
            logger.info("Connected to database successfully")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from the database"""
        if self.conn:
            self.conn.close()
            logger.info("Disconnected from database")
    
    def create_migration_table(self):
        """Create the migrations tracking table"""
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE SCHEMA IF NOT EXISTS core;
                
                CREATE TABLE IF NOT EXISTS core.schema_migrations (
                    version VARCHAR(50) PRIMARY KEY,
                    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    execution_time_seconds DECIMAL(10,3),
                    checksum VARCHAR(64),
                    description TEXT
                );
                
                CREATE INDEX IF NOT EXISTS idx_schema_migrations_applied_at 
                ON core.schema_migrations(applied_at);
            """)
            self.conn.commit()
            logger.info("Migration tracking table created/verified")
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration versions"""
        with self.conn.cursor() as cur:
            cur.execute("SELECT version FROM core.schema_migrations ORDER BY version")
            return [row[0] for row in cur.fetchall()]
    
    def get_available_migrations(self) -> List[Dict]:
        """Get list of available migration files"""
        migrations = []
        
        for file_path in sorted(self.migrations_dir.glob('[0-9]*.py')):
            if file_path.name.startswith('__'):
                continue
                
            # Extract version from filename (e.g., '001' from '001_create_core_schema.py')
            version = file_path.stem.split('_')[0]
            
            # Load migration module to get metadata
            spec = importlib.util.spec_from_file_location(f"migration_{version}", file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            migrations.append({
                'version': version,
                'file_path': file_path,
                'module': module,
                'description': getattr(module, '__doc__', '').strip().split('\n')[0] if getattr(module, '__doc__', None) else '',
                'down_revision': getattr(module, 'down_revision', None),
                'depends_on': getattr(module, 'depends_on', None)
            })
        
        return migrations
    
    def get_pending_migrations(self) -> List[Dict]:
        """Get list of pending (unapplied) migrations"""
        applied = set(self.get_applied_migrations())
        available = self.get_available_migrations()
        
        pending = [m for m in available if m['version'] not in applied]
        return sorted(pending, key=lambda x: x['version'])
    
    def calculate_checksum(self, file_path: Path) -> str:
        """Calculate checksum of migration file"""
        import hashlib
        with open(file_path, 'rb') as f:
            content = f.read()
            return hashlib.sha256(content).hexdigest()[:16]
    
    def apply_migration(self, migration: Dict) -> bool:
        """Apply a single migration"""
        start_time = datetime.now()
        version = migration['version']
        
        logger.info(f"Applying migration {version}: {migration['description']}")
        
        try:
            with self.conn.cursor() as cur:
                # Execute the upgrade function
                migration['module'].upgrade()
                
                # Record the migration
                end_time = datetime.now()
                execution_time = (end_time - start_time).total_seconds()
                checksum = self.calculate_checksum(migration['file_path'])
                
                cur.execute("""
                    INSERT INTO core.schema_migrations 
                    (version, applied_at, execution_time_seconds, checksum, description)
                    VALUES (%s, %s, %s, %s, %s)
                """, (version, end_time, execution_time, checksum, migration['description']))
                
                self.conn.commit()
                logger.info(f"Migration {version} applied successfully in {execution_time:.3f}s")
                return True
                
        except Exception as e:
            logger.error(f"Failed to apply migration {version}: {e}")
            self.conn.rollback()
            return False
    
    def rollback_migration(self, migration: Dict) -> bool:
        """Rollback a single migration"""
        start_time = datetime.now()
        version = migration['version']
        
        logger.info(f"Rolling back migration {version}: {migration['description']}")
        
        try:
            with self.conn.cursor() as cur:
                # Execute the downgrade function
                migration['module'].downgrade()
                
                # Remove the migration record
                cur.execute("DELETE FROM core.schema_migrations WHERE version = %s", (version,))
                
                self.conn.commit()
                end_time = datetime.now()
                execution_time = (end_time - start_time).total_seconds()
                logger.info(f"Migration {version} rolled back successfully in {execution_time:.3f}s")
                return True
                
        except Exception as e:
            logger.error(f"Failed to rollback migration {version}: {e}")
            self.conn.rollback()
            return False
    
    def migrate_up(self, target_version: Optional[str] = None) -> bool:
        """Apply all pending migrations or up to target version"""
        pending = self.get_pending_migrations()
        
        if not pending:
            logger.info("No pending migrations to apply")
            return True
        
        if target_version:
            pending = [m for m in pending if m['version'] <= target_version]
        
        success_count = 0
        for migration in pending:
            if self.apply_migration(migration):
                success_count += 1
            else:
                break
        
        logger.info(f"Applied {success_count}/{len(pending)} migrations")
        return success_count == len(pending)
    
    def migrate_down(self, target_version: str) -> bool:
        """Rollback migrations down to target version"""
        applied = self.get_applied_migrations()
        available = {m['version']: m for m in self.get_available_migrations()}
        
        # Find migrations to rollback (in reverse order)
        to_rollback = []
        for version in reversed(applied):
            if version > target_version and version in available:
                to_rollback.append(available[version])
        
        if not to_rollback:
            logger.info(f"Already at or below target version {target_version}")
            return True
        
        success_count = 0
        for migration in to_rollback:
            if self.rollback_migration(migration):
                success_count += 1
            else:
                break
        
        logger.info(f"Rolled back {success_count}/{len(to_rollback)} migrations")
        return success_count == len(to_rollback)
    
    def create_tenant_schema(self, tenant_id: str, schema_name: str) -> bool:
        """Create schema and tables for a new tenant"""
        logger.info(f"Creating tenant schema: {schema_name}")
        
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT create_tenant_schema(%s, %s)", (tenant_id, schema_name))
                self.conn.commit()
                logger.info(f"Tenant schema {schema_name} created successfully")
                return True
        except Exception as e:
            logger.error(f"Failed to create tenant schema {schema_name}: {e}")
            self.conn.rollback()
            return False
    
    def list_migrations(self) -> None:
        """List all migrations and their status"""
        applied = set(self.get_applied_migrations())
        available = self.get_available_migrations()
        
        print("\nMigration Status:")
        print("=" * 80)
        print(f"{'Version':<10} {'Status':<10} {'Description'}")
        print("-" * 80)
        
        for migration in available:
            version = migration['version']
            status = "Applied" if version in applied else "Pending"
            description = migration['description'][:50] + "..." if len(migration['description']) > 50 else migration['description']
            print(f"{version:<10} {status:<10} {description}")
    
    def get_migration_info(self) -> Dict:
        """Get information about migration status"""
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()
        
        return {
            'applied_count': len(applied),
            'pending_count': len(pending),
            'latest_applied': applied[-1] if applied else None,
            'next_pending': pending[0]['version'] if pending else None,
            'applied_migrations': applied,
            'pending_migrations': [m['version'] for m in pending]
        }

def main():
    """Command line interface for migration manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Database Migration Manager')
    parser.add_argument('--database-url', required=True, help='Database connection URL')
    parser.add_argument('command', choices=['list', 'migrate', 'rollback', 'create-tenant', 'info'], 
                       help='Command to execute')
    parser.add_argument('--target', help='Target version for migrate/rollback')
    parser.add_argument('--tenant-id', help='Tenant ID for create-tenant command')
    parser.add_argument('--schema-name', help='Schema name for create-tenant command')
    
    args = parser.parse_args()
    
    manager = MigrationManager(args.database_url)
    
    try:
        manager.connect()
        manager.create_migration_table()
        
        if args.command == 'list':
            manager.list_migrations()
            
        elif args.command == 'migrate':
            success = manager.migrate_up(args.target)
            sys.exit(0 if success else 1)
            
        elif args.command == 'rollback':
            if not args.target:
                logger.error("Target version required for rollback")
                sys.exit(1)
            success = manager.migrate_down(args.target)
            sys.exit(0 if success else 1)
            
        elif args.command == 'create-tenant':
            if not args.tenant_id or not args.schema_name:
                logger.error("Both --tenant-id and --schema-name required")
                sys.exit(1)
            success = manager.create_tenant_schema(args.tenant_id, args.schema_name)
            sys.exit(0 if success else 1)
            
        elif args.command == 'info':
            info = manager.get_migration_info()
            print(f"\nMigration Info:")
            print(f"Applied migrations: {info['applied_count']}")
            print(f"Pending migrations: {info['pending_count']}")
            print(f"Latest applied: {info['latest_applied']}")
            print(f"Next pending: {info['next_pending']}")
            
    finally:
        manager.disconnect()

if __name__ == '__main__':
    main()