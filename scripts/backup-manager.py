# scripts/backup_manager.py
#!/usr/bin/env python3

import os
import sys
import subprocess
import datetime
import boto3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackupManager:
    def __init__(self, qnap_path: str = "/share/Container/etsy-saas-prod"):
        self.qnap_path = qnap_path
        self.backup_path = "/share/Container/backups"
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def backup_database(self):
        """Create PostgreSQL database backup"""
        logger.info("🗄️ Starting database backup...")
        
        backup_file = f"{self.backup_path}/postgres_backup_{self.timestamp}.sql"
        
        cmd = [
            "docker-compose", "-f", f"{self.qnap_path}/docker-compose.prod.yml",
            "exec", "-T", "postgres",
            "pg_dumpall", "-U", "postgres"
        ]
        
        try:
            with open(backup_file, 'w') as f:
                subprocess.run(cmd, stdout=f, check=True)
            
            logger.info(f"✅ Database backup completed: {backup_file}")
            
            # Compress backup
            subprocess.run(["gzip", backup_file], check=True)
            logger.info(f"✅ Database backup compressed: {backup_file}.gz")
            
            return f"{backup_file}.gz"
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Database backup failed: {e}")
            sys.exit(1)
    
    def backup_file_storage(self):
        """Backup MinIO file storage"""
        logger.info("📁 Starting file storage backup...")
        
        backup_file = f"{self.backup_path}/minio_backup_{self.timestamp}.tar.gz"
        minio_data_path = f"{self.qnap_path}/volumes/minio_data"
        
        try:
            cmd = ["tar", "-czf", backup_file, "-C", minio_data_path, "."]
            subprocess.run(cmd, check=True)
            
            logger.info(f"✅ File storage backup completed: {backup_file}")
            return backup_file
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ File storage backup failed: {e}")
            sys.exit(1)
    
    def backup_application_config(self):
        """Backup application configuration and docker-compose files"""
        logger.info("⚙️ Starting configuration backup...")
        
        backup_file = f"{self.backup_path}/config_backup_{self.timestamp}.tar.gz"
        
        files_to_backup = [
            "docker-compose.prod.yml",
            "docker-compose.yml",
            ".env.production",
            "traefik",
            "nginx"
        ]
        
        try:
            cmd = ["tar", "-czf", backup_file, "-C", self.qnap_path]
            cmd.extend(files_to_backup)
            subprocess.run(cmd, check=True)
            
            logger.info(f"✅ Configuration backup completed: {backup_file}")
            return backup_file
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Configuration backup failed: {e}")
            sys.exit(1)
    
    def cleanup_old_backups(self, retention_days: int = 30):
        """Remove backups older than retention period"""
        logger.info(f"🧹 Cleaning up backups older than {retention_days} days...")
        
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=retention_days)
        
        for backup_file in Path(self.backup_path).glob("*_backup_*"):
            if backup_file.stat().st_mtime < cutoff_date.timestamp():
                backup_file.unlink()
                logger.info(f"🗑️ Removed old backup: {backup_file}")
    
    def run_full_backup(self):
        """Run complete backup procedure"""
        logger.info("🚀 Starting full backup procedure...")
        
        # Create backup directory
        os.makedirs(self.backup_path, exist_ok=True)
        
        # Run all backup procedures
        db_backup = self.backup_database()
        file_backup = self.backup_file_storage()
        config_backup = self.backup_application_config()
        
        # Cleanup old backups
        self.cleanup_old_backups()
        
        logger.info("✅ Full backup completed successfully!")
        
        return {
            "database_backup": db_backup,
            "file_backup": file_backup,
            "config_backup": config_backup,
            "timestamp": self.timestamp
        }

if __name__ == "__main__":
    backup_manager = BackupManager()
    backup_manager.run_full_backup()