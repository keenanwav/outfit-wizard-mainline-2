import os
from backup_manager import BackupManager
import logging

def test_backup_system():
    # Initialize backup manager
    backup_mgr = BackupManager()
    
    # Test database backup
    print("Testing database backup...")
    success_db, db_file = backup_mgr.backup_database()
    if success_db:
        print(f"Database backup created successfully at: {db_file}")
        # Verify the backup
        verify_success, verify_msg = backup_mgr.verify_backup('database', db_file)
        print(f"Database backup verification: {verify_msg}")
    else:
        print(f"Database backup failed: {db_file}")
    
    # Test files backup
    print("\nTesting files backup...")
    success_files, files_backup = backup_mgr.backup_files()
    if success_files:
        print(f"Files backup created successfully at: {files_backup}")
        # Verify the backup
        verify_success, verify_msg = backup_mgr.verify_backup('files', files_backup)
        print(f"Files backup verification: {verify_msg}")
    else:
        print(f"Files backup failed: {files_backup}")
    
    # List all backups
    print("\nListing all backups:")
    backups = backup_mgr.list_backups()
    for backup_type, backup_list in backups.items():
        print(f"\n{backup_type.upper()} backups:")
        for backup in backup_list:
            print(f"- {backup['filepath']} (Created: {backup['timestamp']})")

if __name__ == "__main__":
    test_backup_system()
