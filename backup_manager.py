import os
import shutil
import datetime
import logging
import psycopg2
from typing import Tuple, Optional
import subprocess
import json
from pathlib import Path
import hashlib

class BackupManager:
    def __init__(self):
        self.backup_dir = "backups"
        self.db_backup_dir = os.path.join(self.backup_dir, "database")
        self.files_backup_dir = os.path.join(self.backup_dir, "files")
        self.manifest_file = os.path.join(self.backup_dir, "backup_manifest.json")
        self._setup_directories()
        self._setup_logging()

    def _setup_directories(self):
        """Create necessary backup directories if they don't exist"""
        os.makedirs(self.db_backup_dir, exist_ok=True)
        os.makedirs(self.files_backup_dir, exist_ok=True)

    def _setup_logging(self):
        """Configure logging for backup operations"""
        logging.basicConfig(
            filename=os.path.join(self.backup_dir, 'backup.log'),
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def _get_backup_filename(self, prefix: str) -> str:
        """Generate a timestamp-based backup filename"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}"

    def backup_database(self) -> Tuple[bool, str]:
        """Create a backup of the PostgreSQL database"""
        try:
            backup_file = os.path.join(
                self.db_backup_dir,
                f"{self._get_backup_filename('db')}.sql"
            )
            
            # Use environment variables for database connection
            db_url = os.environ.get('DATABASE_URL')
            if not db_url:
                return False, "DATABASE_URL environment variable not found"

            # Execute pg_dump using subprocess
            result = subprocess.run(
                ['pg_dump', db_url, '-f', backup_file],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return False, f"Database backup failed: {result.stderr}"

            # Calculate checksum for verification
            with open(backup_file, 'rb') as f:
                checksum = hashlib.md5(f.read()).hexdigest()

            self._update_manifest('database', backup_file, checksum)
            logging.info(f"Database backup created successfully: {backup_file}")
            return True, backup_file

        except Exception as e:
            error_msg = f"Database backup failed: {str(e)}"
            logging.error(error_msg)
            return False, error_msg

    def backup_files(self) -> Tuple[bool, str]:
        """Backup user-uploaded files and images"""
        try:
            backup_file = os.path.join(
                self.files_backup_dir,
                f"{self._get_backup_filename('files')}.zip"
            )

            # Directories to backup
            dirs_to_backup = ['user_images', 'wardrobe', 'merged_outfits']
            
            # Create a temporary directory for organizing files
            temp_dir = os.path.join(self.files_backup_dir, 'temp')
            os.makedirs(temp_dir, exist_ok=True)

            try:
                # Copy directories to temp location
                for dir_name in dirs_to_backup:
                    if os.path.exists(dir_name):
                        shutil.copytree(
                            dir_name,
                            os.path.join(temp_dir, dir_name),
                            dirs_exist_ok=True
                        )

                # Create zip archive
                shutil.make_archive(
                    backup_file[:-4],  # Remove .zip extension
                    'zip',
                    temp_dir
                )

                # Calculate checksum
                with open(backup_file, 'rb') as f:
                    checksum = hashlib.md5(f.read()).hexdigest()

                self._update_manifest('files', backup_file, checksum)
                logging.info(f"Files backup created successfully: {backup_file}")
                return True, backup_file

            finally:
                # Clean up temp directory
                shutil.rmtree(temp_dir, ignore_errors=True)

        except Exception as e:
            error_msg = f"Files backup failed: {str(e)}"
            logging.error(error_msg)
            return False, error_msg

    def _update_manifest(self, backup_type: str, filepath: str, checksum: str):
        """Update the backup manifest file"""
        manifest = self._load_manifest()
        
        backup_entry = {
            'filepath': filepath,
            'timestamp': datetime.datetime.now().isoformat(),
            'checksum': checksum,
            'type': backup_type
        }

        if backup_type not in manifest:
            manifest[backup_type] = []
        
        manifest[backup_type].append(backup_entry)
        
        # Keep only last 5 backups in manifest
        manifest[backup_type] = manifest[backup_type][-5:]

        with open(self.manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)

    def _load_manifest(self) -> dict:
        """Load the backup manifest file"""
        if os.path.exists(self.manifest_file):
            with open(self.manifest_file, 'r') as f:
                return json.load(f)
        return {}

    def verify_backup(self, backup_type: str, backup_file: str) -> Tuple[bool, str]:
        """Verify the integrity of a backup file"""
        try:
            manifest = self._load_manifest()
            
            # Find backup entry in manifest
            backup_entry = None
            for entry in manifest.get(backup_type, []):
                if entry['filepath'] == backup_file:
                    backup_entry = entry
                    break

            if not backup_entry:
                return False, "Backup not found in manifest"

            # Calculate current checksum
            with open(backup_file, 'rb') as f:
                current_checksum = hashlib.md5(f.read()).hexdigest()

            # Compare with stored checksum
            if current_checksum != backup_entry['checksum']:
                return False, "Backup file integrity check failed"

            return True, "Backup verified successfully"

        except Exception as e:
            error_msg = f"Backup verification failed: {str(e)}"
            logging.error(error_msg)
            return False, error_msg

    def restore_database(self, backup_file: str) -> Tuple[bool, str]:
        """Restore database from backup"""
        try:
            # Verify backup first
            verified, msg = self.verify_backup('database', backup_file)
            if not verified:
                return False, f"Backup verification failed: {msg}"

            db_url = os.environ.get('DATABASE_URL')
            if not db_url:
                return False, "DATABASE_URL environment variable not found"

            # Execute psql to restore
            result = subprocess.run(
                ['psql', db_url, '-f', backup_file],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return False, f"Database restore failed: {result.stderr}"

            logging.info(f"Database restored successfully from {backup_file}")
            return True, "Database restored successfully"

        except Exception as e:
            error_msg = f"Database restore failed: {str(e)}"
            logging.error(error_msg)
            return False, error_msg

    def restore_files(self, backup_file: str) -> Tuple[bool, str]:
        """Restore files from backup"""
        try:
            # Verify backup first
            verified, msg = self.verify_backup('files', backup_file)
            if not verified:
                return False, f"Backup verification failed: {msg}"

            # Create temporary extraction directory
            temp_dir = os.path.join(self.files_backup_dir, 'temp_restore')
            os.makedirs(temp_dir, exist_ok=True)

            try:
                # Extract backup
                shutil.unpack_archive(backup_file, temp_dir)

                # Restore directories
                for dir_name in ['user_images', 'wardrobe', 'merged_outfits']:
                    source_dir = os.path.join(temp_dir, dir_name)
                    if os.path.exists(source_dir):
                        # Remove existing directory if it exists
                        if os.path.exists(dir_name):
                            shutil.rmtree(dir_name)
                        # Restore from backup
                        shutil.copytree(source_dir, dir_name)

                logging.info(f"Files restored successfully from {backup_file}")
                return True, "Files restored successfully"

            finally:
                # Clean up temp directory
                shutil.rmtree(temp_dir, ignore_errors=True)

        except Exception as e:
            error_msg = f"Files restore failed: {str(e)}"
            logging.error(error_msg)
            return False, error_msg

    def list_backups(self) -> dict:
        """List all available backups"""
        return self._load_manifest()

    def cleanup_old_backups(self, days_to_keep: int = 30) -> Tuple[bool, str]:
        """Remove backups older than specified days"""
        try:
            manifest = self._load_manifest()
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_to_keep)
            
            for backup_type in manifest:
                manifest[backup_type] = [
                    entry for entry in manifest[backup_type]
                    if datetime.datetime.fromisoformat(entry['timestamp']) > cutoff_date
                ]
                
                # Remove files not in manifest
                backup_dir = self.db_backup_dir if backup_type == 'database' else self.files_backup_dir
                for file in os.listdir(backup_dir):
                    file_path = os.path.join(backup_dir, file)
                    if not any(entry['filepath'] == file_path for entry in manifest[backup_type]):
                        os.remove(file_path)

            # Update manifest
            with open(self.manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2)

            return True, f"Cleaned up backups older than {days_to_keep} days"

        except Exception as e:
            error_msg = f"Backup cleanup failed: {str(e)}"
            logging.error(error_msg)
            return False, error_msg
