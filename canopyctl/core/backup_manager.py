"""
Backup management for safe rebase operations.
"""

import time
from typing import Dict, Optional
from pathlib import Path

from .git_ops import GitOperations
from ..exceptions import RebaseError, GitError


class BackupManager:
    """Manages backup creation and restoration for safe rebasing."""
    
    def __init__(self):
        self.git_ops = GitOperations()
    
    def _generate_backup_name(self) -> str:
        """Generate a timestamped backup branch name."""
        timestamp = int(time.time())
        return f"canopy-backup-{timestamp}"
    
    def create_backup(self, commit_hash: str) -> str:
        """
        Create backup branch for safe rebase recovery.
        Returns backup branch name.
        """
        backup_name = self._generate_backup_name()
        
        try:
            # Create backup branch pointing to current commit
            self.git_ops.create_branch(backup_name, commit_hash)
            
            print(f"   ✓ Backup branch created: {backup_name}")
            return backup_name
            
        except GitError as e:
            raise RebaseError(f"Failed to create backup: {e}")
    
    def restore_backup(self, backup_name: str, expected_commit: str) -> None:
        """Restore from backup branch."""
        try:
            # Verify backup exists and points to expected commit
            if not self._verify_backup(backup_name, expected_commit):
                raise RebaseError(f"Backup {backup_name} is invalid or corrupted")
            
            # Reset current branch to backup
            self.git_ops.reset_hard(backup_name)
            
            print(f"   ✓ Restored from backup: {backup_name}")
            
        except GitError as e:
            raise RebaseError(f"Failed to restore backup: {e}")
    
    def cleanup_backup(self, backup_name: str) -> None:
        """Clean up backup branch after successful rebase."""
        try:
            # Phase 1: Keep backups for safety, cleanup in later phases
            # TODO: Implement in Phase 2 with retention policy
            pass
        except Exception:
            # Non-critical error, don't fail rebase
            pass
    
    def list_backups(self) -> Dict[str, Dict]:
        """List available backup branches."""
        # Phase 1: Simple implementation, enhance in Phase 2
        try:
            # Get list of backup branches
            all_branches = self.git_ops._run_git(['branch', '--list']).strip()
            backups = {}
            
            for line in all_branches.split('\n'):
                branch_name = line.strip().lstrip('* ')
                if branch_name.startswith('canopy-backup-'):
                    # Extract timestamp from branch name
                    try:
                        timestamp_str = branch_name.replace('canopy-backup-', '')
                        timestamp = int(timestamp_str)
                        backups[branch_name] = {
                            'timestamp': timestamp,
                            'created': time.ctime(timestamp)
                        }
                    except ValueError:
                        # Invalid backup name format, skip
                        continue
            
            return backups
            
        except GitError:
            return {}
    
    def _verify_backup(self, backup_name: str, expected_commit: str) -> bool:
        """Verify backup branch exists and points to expected commit."""
        try:
            # Check if backup branch exists and get its commit
            backup_commit = self.git_ops.rev_parse(backup_name)
            
            # Verify it points to the expected commit
            return backup_commit == expected_commit
            
        except GitError:
            return False