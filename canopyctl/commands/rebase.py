"""
Rebase command implementation for canopyctl.
"""

import sys
import os
import json
from pathlib import Path

from ..core.repo_analyzer import RepoAnalyzer
from ..core.backup_manager import BackupManager
from ..core.rebase_engine import RebaseEngine
from ..core.git_ops import GitOperations
from ..exceptions import RebaseError, GitError


class RebaseCommand:
    """Main rebase command handler for Phase 1 MVP."""
    
    def __init__(self):
        self.repo_analyzer = None
        self.backup_manager = None
        self.rebase_engine = None
        self.git_ops = None
        
        # Phase 1: Simple state file for continue/abort
        self.state_file = Path('.canopyctl-rebase-state')
    
    def execute_rebase(self, remote: str = 'upstream', branch: str = None) -> int:
        """Execute rebase against remote/branch (defaults to upstream and auto-detected branch)."""
        try:
            # Initialize components
            self._initialize_components()
            
            print("🔍 Analyzing repository state...")
            
            # 1. Pre-flight checks
            repo_state = self.repo_analyzer.analyze_current_state()
            self._validate_repo_state(repo_state)
            
            # 2. Auto-detect target branch if not specified
            if branch is None:
                branch = self.repo_analyzer.detect_target_branch()
                print(f"   🎯 Auto-detected target branch: {branch}")
            
            target = f"{remote}/{branch}"
            print(f"   📍 Rebasing against: {target}")
            
            # 3. Analyze what needs to be rebased
            upstream_info = self.repo_analyzer.analyze_upstream(target)
            patches = self.repo_analyzer.find_canopy_patches(
                repo_state['upstream_base'], 
                repo_state['current_head']
            )
            
            print(f"   ✓ Found {len(patches)} Canopy patches to rebase")
            print(f"   ✓ Upstream has {upstream_info['new_commits_count']} new commits")
            
            if len(patches) == 0:
                print("   ✓ No patches to rebase - you're up to date!")
                return 0
            
            if upstream_info['new_commits_count'] == 0:
                print("   ✓ Already up to date with upstream")
                return 0
            
            # 3. Create safety backup
            print("🛡️ Creating safety backup...")
            backup_name = self.backup_manager.create_backup(repo_state['current_head'])
            
            # 4. Save rebase state for continue/abort
            rebase_state = {
                'backup_name': backup_name,
                'original_head': repo_state['current_head'],
                'upstream_target': upstream_info['new_head'],
                'patches': patches,
                'current_patch_index': 0,
                'status': 'in_progress'
            }
            self._save_rebase_state(rebase_state)
            
            # 5. Execute rebase
            return self.rebase_engine.execute_rebase(rebase_state)
            
        except RebaseError as e:
            print(f"❌ Rebase failed: {e}")
            return 1
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return 1
    
    def continue_rebase(self) -> int:
        """Continue rebase after user resolves conflicts."""
        if not self.state_file.exists():
            print("❌ No rebase in progress")
            return 1
        
        try:
            self._initialize_components()
            rebase_state = self._load_rebase_state()
            return self.rebase_engine.continue_rebase(rebase_state)
        except Exception as e:
            print(f"❌ Continue failed: {e}")
            return 1
    
    def abort_rebase(self) -> int:
        """Abort rebase and restore original state."""
        if not self.state_file.exists():
            print("❌ No rebase in progress")
            return 1
        
        try:
            print("🔄 Aborting rebase...")
            
            self._initialize_components()
            rebase_state = self._load_rebase_state()
            
            # Abort any ongoing cherry-pick
            try:
                if self.git_ops.is_cherry_pick_in_progress():
                    self.git_ops.cherry_pick_abort()
            except GitError:
                # Ignore errors in cherry-pick abort
                pass
            
            # Restore from backup
            self.backup_manager.restore_backup(
                rebase_state['backup_name'],
                rebase_state['original_head']
            )
            
            # Clean up state
            self.state_file.unlink()
            
            print("✅ Rebase aborted successfully")
            print(f"   ✓ Restored to original state: {rebase_state['original_head'][:8]}")
            return 0
            
        except Exception as e:
            print(f"❌ Abort failed: {e}")
            return 1
    
    def _initialize_components(self):
        """Initialize rebase components (lazy initialization)."""
        if not self.repo_analyzer:
            self.repo_analyzer = RepoAnalyzer()
            self.backup_manager = BackupManager()
            self.rebase_engine = RebaseEngine()
            self.git_ops = GitOperations()
    
    def _validate_repo_state(self, repo_state: dict) -> None:
        """Validate repository is ready for rebase."""
        if not repo_state['working_tree_clean']:
            raise RebaseError(
                "Working directory has uncommitted changes.\n"
                "Please commit or stash your changes first:\n"
                "  git add .\n"
                "  git commit -m \"Work in progress\"\n"
                "  # Or: git stash push -m \"Before rebase\""
            )
        
        if not repo_state['upstream_remote']:
            raise RebaseError(
                "No upstream remote found. Please add upstream remote:\n"
                "  git remote add upstream https://github.com/openbmc/openbmc.git\n"
                "  git fetch upstream"
            )
        
        if not repo_state['upstream_base']:
            raise RebaseError(
                "Cannot determine upstream base commit.\n"
                "Make sure your branch is based on upstream."
            )
    
    def _save_rebase_state(self, state: dict) -> None:
        """Save rebase state to file for continue/abort."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            # Non-critical in Phase 1
            print(f"Warning: Could not save rebase state: {e}")
    
    def _load_rebase_state(self) -> dict:
        """Load rebase state from file."""
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise RebaseError(f"Could not load rebase state: {e}")