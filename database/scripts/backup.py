#!/usr/bin/env python3
"""
Backup and restore utilities for the Energy Certificate database
"""

import os
import pyodbc
import datetime
from pathlib import Path
import logging
import subprocess
from config import get_config

class DatabaseBackup:
    def __init__(self, connection_string: str, backup_path: str = "./backups"):
        self.connection_string = connection_string
        self.backup_path = Path(backup_path)
        self.backup_path.mkdir(exist_ok=True)
        self.setup_logging()
    
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def create_backup(self, database_name: str = None) -> str:
        """Create a full database backup"""
        try:
            if not database_name:
                database_name = self.extract_database_name()
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{database_name}_{timestamp}.bak"
            backup_path = self.backup_path / backup_filename
            
            conn = pyodbc.connect(self.connection_string)
            cursor = conn.cursor()
            
            backup_sql = f"""
                BACKUP DATABASE [{database_name}] 
                TO DISK = '{backup_path}' 
                WITH FORMAT, INIT, COMPRESSION,
                NAME = 'Full Backup of {database_name}',
                DESCRIPTION = 'Automated backup created by Python script'
            """
            
            self.logger.info(f"Creating backup: {backup_filename}")
            cursor.execute(backup_sql)
            
            while cursor.nextset():
                pass
            
            cursor.close()
            conn.close()
            
            self.logger.info(f"✅ Backup created successfully: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"❌ Backup failed: {e}")
            raise
    
    def list_backups(self) -> list:
        """List available backup files"""
        backup_files = list(self.backup_path.glob("*.bak"))
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        backups = []
        for file in backup_files:
            stat = file.stat()
            backups.append({
                'filename': file.name,
                'path': str(file),
                'size_mb': round(stat.st_size / 1024 / 1024, 2),
                'created': datetime.datetime.fromtimestamp(stat.st_mtime)
            })
        
        return backups
    
    def restore_backup(self, backup_file: str, target_database: str = None):
        """Restore database from backup file"""
        try:
            backup_path = Path(backup_file)
            if not backup_path.exists():
                backup_path = self.backup_path / backup_file
            
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_file}")
            
            if not target_database:
                target_database = self.extract_database_name() + "_restored"
            
            conn = pyodbc.connect(self.connection_string)
            cursor = conn.cursor()
            
            # Get logical file names from backup
            cursor.execute(f"RESTORE FILELISTONLY FROM DISK = '{backup_path}'")
            files = cursor.fetchall()
            
            if not files:
                raise Exception("Could not read backup file structure")
            
            data_file = None
            log_file = None
            for file in files:
                if file[2] == 'D':  # Data file
                    data_file = file[0]
                elif file[2] == 'L':  # Log file
                    log_file = file[0]
            
            # Restore database
            restore_sql = f"""
                RESTORE DATABASE [{target_database}] 
                FROM DISK = '{backup_path}'
                WITH MOVE '{data_file}' TO '{target_database}.mdf',
                MOVE '{log_file}' TO '{target_database}.ldf',
                REPLACE
            """
            
            self.logger.info(f"Restoring backup to database: {target_database}")
            cursor.execute(restore_sql)
            
            cursor.close()
            conn.close()
            
            self.logger.info(f"✅ Database restored successfully: {target_database}")
            
        except Exception as e:
            self.logger.error(f"❌ Restore failed: {e}")
            raise
    
    def extract_database_name(self) -> str:
        """Extract database name from connection string"""
        import re
        match = re.search(r'Database=([^;]+)', self.connection_string, re.IGNORECASE)
        if match:
            return match.group(1)
        raise ValueError("Could not extract database name from connection string")
    
    def cleanup_old_backups(self, keep_days: int = 30):
        """Remove backup files older than specified days"""
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=keep_days)
        
        removed_count = 0
        for backup_file in self.backup_path.glob("*.bak"):
            if datetime.datetime.fromtimestamp(backup_file.stat().st_mtime) < cutoff_date:
                backup_file.unlink()
                removed_count += 1
                self.logger.info(f"Removed old backup: {backup_file.name}")
        
        self.logger.info(f"Cleanup completed. Removed {removed_count} old backup files.")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Database backup and restore utilities')
    parser.add_argument('action', choices=['backup', 'restore', 'list', 'cleanup'], help='Action to perform')
    parser.add_argument('--environment', default='development', help='Target environment')
    parser.add_argument('--backup-file', help='Backup file for restore operation')
    parser.add_argument('--target-db', help='Target database name for restore')
    parser.add_argument('--keep-days', type=int, default=30, help='Days to keep backups (for cleanup)')
    
    args = parser.parse_args()
    
    config = get_config(args.environment)
    if not config['connection_string']:
        print(f"❌ No connection string configured for {args.environment}")
        return
    
    backup_util = DatabaseBackup(config['connection_string'])
    
    if args.action == 'backup':
        backup_file = backup_util.create_backup()
        print(f"Backup created: {backup_file}")
    
    elif args.action == 'list':
        backups = backup_util.list_backups()
        print(f"\nAvailable backups ({len(backups)}):")
        for backup in backups:
            print(f"  {backup['filename']} - {backup['size_mb']}MB - {backup['created']}")
    
    elif args.action == 'restore':
        if not args.backup_file:
            print("❌ --backup-file required for restore operation")
            return
        backup_util.restore_backup(args.backup_file, args.target_db)
    
    elif args.action == 'cleanup':
        backup_util.cleanup_old_backups(args.keep_days)

if __name__ == "__main__":
    main()
