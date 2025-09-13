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
    
    def execute_rebase(self, remote: str = None, branch: str = None) -> int:
        """Execute rebase with new Canopy-aware workflow."""
        try:
            # Initialize components
            self._initialize_components()
            
            print("🔍 Analyzing repository state...")
            
            # 1. Pre-flight checks
            repo_state = self.repo_analyzer.analyze_current_state()
            self._validate_repo_state(repo_state)
            
            # 2. Find Canopy remote - this is required!
            canopy_remote = self.repo_analyzer._find_canopy_remote()
            if not canopy_remote:
                print("❌ No Canopy remote found!")
                print("   Please add the Canopy remote:")
                print("   git remote add canopy https://github.com/canopybmc/openbmc.git")
                print("   # Or if you prefer SSH:")
                print("   git remote add canopy git@github.com:canopybmc/openbmc.git")
                return 1
            
            current_branch = repo_state['current_branch']
            print(f"   📍 Current local branch: {current_branch}")
            
            # 3. Determine rebase strategy based on current branch
            if current_branch == 'main':
                return self._handle_main_branch_rebase(canopy_remote, repo_state)
            else:
                return self._handle_feature_branch_rebase(canopy_remote, current_branch, repo_state)
            
        except RebaseError as e:
            print(f"❌ Rebase failed: {e}")
            return 1
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return 1
    
    def continue_rebase(self) -> int:
        """Continue rebase after user resolves conflicts."""
        try:
            self._initialize_components()
            
            # Check if we're in a git rebase state
            rebase_dir = self.repo_analyzer.repo_root / '.git' / 'rebase-apply'
            rebase_merge_dir = self.repo_analyzer.repo_root / '.git' / 'rebase-merge'
            
            if not (rebase_dir.exists() or rebase_merge_dir.exists()):
                print("❌ No rebase in progress")
                return 1
            
            print("🔄 Continuing rebase...")
            
            # Check for unresolved conflicts
            conflicted_files = self.git_ops.get_conflicted_files()
            if conflicted_files:
                print("❌ There are still unresolved conflicts in:")
                for file in conflicted_files:
                    print(f"   - {file}")
                print("Please resolve all conflicts and run 'git add <files>' before continuing")
                return 1
            
            # Continue the rebase
            try:
                self.git_ops._run_git(['rebase', '--continue'])
                print("✅ Rebase continued successfully!")
                return 0
            except Exception as e:
                if 'conflict' in str(e).lower():
                    print("❌ More conflicts detected, please resolve and continue again")
                    return 1
                else:
                    print(f"❌ Continue failed: {e}")
                    return 1
                    
        except Exception as e:
            print(f"❌ Continue failed: {e}")
            return 1
    
    def abort_rebase(self) -> int:
        """Abort rebase and restore original state."""
        try:
            self._initialize_components()
            
            print("🔄 Aborting rebase...")
            
            # Check if we're in a git rebase state
            rebase_dir = self.repo_analyzer.repo_root / '.git' / 'rebase-apply'
            rebase_merge_dir = self.repo_analyzer.repo_root / '.git' / 'rebase-merge'
            
            if rebase_dir.exists() or rebase_merge_dir.exists():
                # Use git rebase --abort
                try:
                    self.git_ops._run_git(['rebase', '--abort'])
                    print("✅ Git rebase aborted successfully")
                    return 0
                except Exception as e:
                    print(f"❌ Git rebase abort failed: {e}")
                    print("💡 You may need to manually reset your branch")
                    return 1
            else:
                print("❌ No rebase in progress")
                return 1
                
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
    
    def _handle_main_branch_rebase(self, canopy_remote: str, repo_state: dict) -> int:
        """Handle rebase when on main branch."""
        print(f"   📋 On main branch, checking for changes from {canopy_remote}/main...")
        
        # Fetch latest from Canopy remote
        print(f"📥 Fetching latest from {canopy_remote}...")
        try:
            self.git_ops.fetch(canopy_remote)
        except Exception as e:
            print(f"❌ Failed to fetch from {canopy_remote}: {e}")
            return 1
        
        # Check for new commits on remote main
        try:
            remote_main = f"{canopy_remote}/main"
            remote_head = self.git_ops.rev_parse(remote_main)
            local_head = repo_state['current_head']
            
            if remote_head == local_head:
                print("✅ Already up to date with remote main - no changes!")
                return 0
            
            # Count new commits (only commits that are on remote but not on local)
            try:
                # Find merge base between local and remote
                merge_base = self.git_ops.get_merge_base(local_head, remote_head)
                
                # Count commits from merge_base to remote_head (new commits)
                remote_commits = self.git_ops.count_commits(merge_base, remote_head)
                
                # Count commits from merge_base to local_head (our commits that will be reapplied)
                local_commits = self.git_ops.count_commits(merge_base, local_head)
                
                # New commits = commits on remote that we don't have
                new_commits = remote_commits
                
            except Exception as e:
                print(f"   ⚠ Warning: Could not calculate commit counts: {e}")
                new_commits = "unknown"
                local_commits = 0
            
            # Display stats
            print(f"\📊 Rebase Statistics:")
            print(f"   Current local branch: main")
            print(f"   Matching remote branch: {canopy_remote}/main")
            print(f"   Number of new remote commits: {new_commits + 1 - local_commits}")
            if local_commits > 0:
                print(f"   Number of local commits to reapply: {local_commits}")
            
            # Ask user confirmation
            if not self._get_user_confirmation():
                print("❌ Rebase cancelled by user")
                return 0
            
            # Create backup before rebase
            print("🛡️ Creating safety backup...")
            backup_name = self.backup_manager.create_backup(local_head)
            
            # Perform rebase
            print(f"🔄 Rebasing main against {canopy_remote}/main...")
            try:
                self.git_ops.rebase(remote_main)
                print("✅ Rebase completed successfully!")
                return 0
            except Exception as e:
                print(f"❌ Rebase failed: {e}")
                print(f"💡 You can restore from backup: git reset --hard {backup_name}")
                return 1
                
        except Exception as e:
            print(f"❌ Error checking remote main: {e}")
            return 1
    
    def _handle_feature_branch_rebase(self, canopy_remote: str, current_branch: str, repo_state: dict) -> int:
        """Handle rebase when on feature/topic branch."""
        print(f"   🌿 On feature branch '{current_branch}', determining origin...")
        
        # Fetch from Canopy remote
        print(f"📥 Fetching latest from {canopy_remote}...")
        try:
            self.git_ops.fetch(canopy_remote)
        except Exception as e:
            print(f"❌ Failed to fetch from {canopy_remote}: {e}")
            return 1
        
        # Check if remote branch with same name exists
        try:
            remote_branch = f"{canopy_remote}/{current_branch}"
            self.git_ops.rev_parse(remote_branch)
            target_branch = current_branch
            origin_info = f"(matches remote branch {remote_branch})"
            print(f"   ✓ Found matching remote branch: {remote_branch}")
        except:
            # No matching remote branch, find origin
            print(f"   ℹ No remote branch '{current_branch}' found, analyzing origin...")
            target_branch = self._find_branch_origin(canopy_remote, current_branch)
            if target_branch:
                origin_info = f"(branched from {target_branch})"
                print(f"   🎯 Detected origin: {target_branch}")
            else:
                print(f"   ⚠ Cannot determine origin, defaulting to main")
                target_branch = "main"
                origin_info = "(defaulting to main - could not detect origin)"
        
        # Get target info
        target_ref = f"{canopy_remote}/{target_branch}"
        try:
            target_head = self.git_ops.rev_parse(target_ref)
            local_head = repo_state['current_head']
            
            # Find merge base to count new commits correctly
            try:
                merge_base = self.git_ops.get_merge_base(local_head, target_ref)
                
                # Count commits from merge_base to target (new commits on remote)
                remote_commits = self.git_ops.count_commits(merge_base, target_ref)
                
                # Count commits from merge_base to local_head (our commits that will be reapplied)
                local_commits = self.git_ops.count_commits(merge_base, local_head)
                
                # New commits = commits on remote branch that we don't have
                new_commits = remote_commits
                
                
                if new_commits == 0:
                    print("✅ Already up to date - no new commits to rebase!")
                    return 0
            except Exception as e:
                print(f"   ⚠ Warning: Could not calculate commit counts: {e}")
                new_commits = "unknown"
                local_commits = 0
            
            # Display stats
            print(f"📊 Rebase Statistics:")
            print(f"   Current local branch: {current_branch}")
            print(f"   Matching remote branch: {canopy_remote}/{target_branch} {origin_info}")
            print(f"   Number of new remote commits: {new_commits + 1 - local_commits}")
            if local_commits > 0:
                print(f"   Number of local commits to reapply: {local_commits}")
            
            # Ask user confirmation
            if not self._get_user_confirmation():
                print("❌ Rebase cancelled by user")
                return 0
            
            # Create backup before rebase
            print("🛡️ Creating safety backup...")
            backup_name = self.backup_manager.create_backup(local_head)
            
            # Perform rebase
            print(f"🔄 Rebasing {current_branch} against {canopy_remote}/{target_branch}...")
            try:
                self.git_ops.rebase(target_ref)
                print("✅ Rebase completed successfully!")
                return 0
            except Exception as e:
                print(f"❌ Rebase failed with conflicts")
                print(f"💡 Resolve conflicts and run: canopyctl rebase --continue")
                print(f"💡 Or abort with: canopyctl rebase --abort")
                print(f"💡 Manual restore: git reset --hard {backup_name}")
                return 1
                
        except Exception as e:
            print(f"❌ Error accessing target branch {target_ref}: {e}")
            return 1
    
    def _find_branch_origin(self, canopy_remote: str, current_branch: str) -> str:
        """Find which branch this feature branch originated from."""
        try:
            # Get available remote branches
            remote_branches = self.git_ops.get_remote_branches(canopy_remote)
            
            # Look for main and LTS branches
            candidates = []
            for remote_branch in remote_branches:
                branch_name = remote_branch.replace(f"{canopy_remote}/", "")
                if branch_name == 'main' or branch_name.startswith('LTS/'):
                    candidates.append(branch_name)
            
            # Find the best match using merge-base
            best_match = None
            best_distance = float('inf')
            
            for candidate in candidates:
                try:
                    candidate_ref = f"{canopy_remote}/{candidate}"
                    merge_base = self.git_ops.get_merge_base('HEAD', candidate_ref)
                    if merge_base:
                        # Count commits from merge-base to HEAD (our commits)
                        distance = self.git_ops.count_commits(merge_base, 'HEAD')
                        if distance < best_distance:
                            best_distance = distance
                            best_match = candidate
                except:
                    continue
            
            return best_match or 'main'
            
        except Exception:
            return 'main'  # Safe fallback
    
    def _get_user_confirmation(self) -> bool:
        """Get user confirmation to proceed with rebase."""
        try:
            response = input("❓ Proceed with rebase? (y/N): ").lower().strip()
            return response in ['y', 'yes']
        except (EOFError, KeyboardInterrupt):
            print("\\n❌ Cancelled by user")
            return False
