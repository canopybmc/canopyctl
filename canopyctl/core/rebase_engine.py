"""
Core rebase orchestration logic.
"""

import time
from typing import Dict, List
from pathlib import Path

from .git_ops import GitOperations
from .backup_manager import BackupManager
from ..exceptions import RebaseError, GitError


class RebaseEngine:
    """Core rebase orchestration logic."""
    
    def __init__(self):
        self.git_ops = GitOperations()
        self.backup_manager = BackupManager()
        self.state_file = Path('.canopyctl-rebase-state')
    
    def execute_rebase(self, rebase_state: Dict) -> int:
        """Execute the rebase operation."""
        try:
            print("⚙️ Starting rebase operation...")
            
            # 1. Reset to upstream target
            print(f"   🔄 Resetting to upstream: {rebase_state['upstream_target'][:8]}...")
            self.git_ops.reset_hard(rebase_state['upstream_target'])
            print("   ✓ Reset completed")
            
            # 2. Cherry-pick patches
            return self._cherry_pick_patches(rebase_state)
            
        except GitError as e:
            print(f"❌ Rebase failed: {e}")
            return 1
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return 1
    
    def continue_rebase(self, rebase_state: Dict) -> int:
        """Continue rebase after user resolves conflicts."""
        try:
            # Verify user has resolved conflicts
            if self.git_ops.is_cherry_pick_in_progress():
                conflicted_files = self.git_ops.get_conflicted_files()
                if conflicted_files:
                    print("❌ Conflicts still exist in:")
                    for file in conflicted_files:
                        print(f"   - {file}")
                    print("Please resolve conflicts and try again.")
                    print()
                    print("💡 To resolve conflicts:")
                    print("   1. Edit the files to resolve conflicts")
                    print("   2. Add resolved files: git add <file>")
                    print("   3. Continue: canopyctl rebase --continue")
                    return 1
                
                # Continue cherry-pick
                if not self.git_ops.cherry_pick_continue():
                    print("❌ Failed to continue cherry-pick")
                    return 1
                
                print("   ✓ Conflict resolved, continuing...")
                
                # Update state and continue with remaining patches
                rebase_state['current_patch_index'] += 1
                self._save_rebase_state(rebase_state)
            
            return self._cherry_pick_patches(rebase_state)
            
        except Exception as e:
            print(f"❌ Continue failed: {e}")
            return 1
    
    def _cherry_pick_patches(self, rebase_state: Dict) -> int:
        """Cherry-pick remaining patches."""
        patches = rebase_state['patches']
        current_index = rebase_state['current_patch_index']
        
        if not patches:
            print("   ✓ No patches to rebase")
            return self._complete_rebase(rebase_state)
        
        print(f"   🍒 Cherry-picking patches ({current_index + 1}/{len(patches)})...")
        
        for i in range(current_index, len(patches)):
            patch = patches[i]
            print(f"   [{i+1}/{len(patches)}] {patch['hash']} - \"{patch['subject']}\"")
            
            # Attempt cherry-pick
            try:
                success = self.git_ops.cherry_pick(patch['full_hash'])
            except GitError as e:
                print(f"   ❌ Cherry-pick failed: {e}")
                # Update state and exit
                rebase_state['current_patch_index'] = i
                self._save_rebase_state(rebase_state)
                return 1
            
            if success:
                print(f"   ✓ Applied cleanly")
            else:
                # Conflict occurred
                conflicted_files = self.git_ops.get_conflicted_files()
                print(f"   ❌ CONFLICT in {len(conflicted_files)} file(s)")
                
                # Show conflicted files (limit to first 5)
                for file in conflicted_files[:5]:
                    print(f"      - {file}")
                if len(conflicted_files) > 5:
                    print(f"      ... and {len(conflicted_files) - 5} more")
                
                print()
                print("💡 To resolve conflicts:")
                print("   1. Edit the conflicted files to resolve conflicts")
                print("   2. Add resolved files: git add <file>")
                print("   3. Continue rebase: canopyctl rebase --continue")
                print("   4. Or abort: canopyctl rebase --abort")
                print()
                print("💡 To see conflicts:")
                print("   git status")
                print("   git diff")
                
                # Update state to current position
                rebase_state['current_patch_index'] = i
                self._save_rebase_state(rebase_state)
                return 1
        
        # All patches applied successfully
        return self._complete_rebase(rebase_state)
    
    def _complete_rebase(self, rebase_state: Dict) -> int:
        """Complete successful rebase."""
        print()
        print("✅ Rebase completed successfully!")
        
        # Show summary
        patches_count = len(rebase_state['patches'])
        print(f"   • Rebased {patches_count} patches")
        print(f"   • New base: {rebase_state['upstream_target'][:8]}")
        print(f"   • Backup available: {rebase_state['backup_name']}")
        
        # Clean up state file
        if self.state_file.exists():
            self.state_file.unlink()
        
        print()
        print("💡 Next steps:")
        print("   • Test your changes: run build/tests as appropriate")
        print("   • Push when ready: git push --force-with-lease origin <branch>")
        print(f"   • Backup kept for safety: {rebase_state['backup_name']}")
        
        return 0
    
    def _save_rebase_state(self, state: Dict) -> None:
        """Save rebase state to file."""
        import json
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            # Non-critical error for Phase 1
            print(f"Warning: Could not save rebase state: {e}")