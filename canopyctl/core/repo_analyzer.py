"""
Repository analysis for rebase functionality.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional

from .git_ops import GitOperations
from ..exceptions import GitError, RebaseError


class RepoAnalyzer:
    """Analyzes repository state and identifies rebase requirements."""
    
    def __init__(self):
        try:
            self.git_ops = GitOperations()
            self.repo_root = self.git_ops.repo_root
        except GitError as e:
            raise RebaseError(f"Repository analysis failed: {e}")
    
    def analyze_current_state(self) -> Dict:
        """Analyze current repository state."""
        return {
            'repo_root': self.repo_root,
            'current_head': self.git_ops.get_current_commit(),
            'current_branch': self.git_ops.get_current_branch(),
            'working_tree_clean': self._is_working_tree_clean(),
            'upstream_remote': self._find_upstream_remote(),
            'upstream_base': self._find_upstream_base()
        }
    
    def analyze_upstream(self, target: str) -> Dict:
        """Analyze upstream target for rebase."""
        upstream_remote = self._find_upstream_remote()
        if not upstream_remote:
            raise RebaseError("No upstream remote configured")
        
        # Fetch latest from upstream
        print("📥 Fetching latest upstream...")
        self.git_ops.fetch(upstream_remote)
        
        # Parse target (could be "upstream/main" or just "main")
        if '/' in target:
            remote_part, branch_part = target.split('/', 1)
            upstream_branch = target
        else:
            upstream_branch = f"{upstream_remote}/{target}"
        
        try:
            new_head = self.git_ops.rev_parse(upstream_branch)
        except GitError:
            raise RebaseError(f"Cannot find branch {upstream_branch}")
        
        current_base = self._find_upstream_base()
        
        # Count new commits
        if current_base and new_head != current_base:
            try:
                commit_list = self.git_ops.get_commit_list(current_base, new_head)
                new_commits_count = len([c for c in commit_list if c.strip()])
            except GitError:
                new_commits_count = 0
        else:
            new_commits_count = 0
        
        return {
            'remote': upstream_remote,
            'branch': upstream_branch,
            'old_head': current_base,
            'new_head': new_head,
            'new_commits_count': new_commits_count
        }
    
    def find_canopy_patches(self, base_commit: str, head_commit: str) -> List[Dict]:
        """Find Canopy patches between base and head."""
        if not base_commit or base_commit == head_commit:
            return []
        
        try:
            # Get list of commits between base and head (oldest first for cherry-picking)
            commit_list = self.git_ops.get_commit_list(base_commit, head_commit, reverse=True)
        except GitError:
            return []
        
        if not commit_list or not commit_list[0].strip():
            return []
        
        patches = []
        for line in commit_list:
            line = line.strip()
            if line:
                # Parse commit line: "abc1234 commit subject"
                parts = line.split(' ', 1)
                if len(parts) >= 2:
                    commit_hash = parts[0]
                    subject = parts[1]
                else:
                    commit_hash = parts[0]
                    subject = ""
                
                try:
                    full_hash = self.git_ops.rev_parse(commit_hash)
                    patches.append({
                        'hash': commit_hash,
                        'subject': subject,
                        'full_hash': full_hash
                    })
                except GitError:
                    # Skip invalid commits
                    continue
        
        return patches
    
    def detect_target_branch(self) -> str:
        """
        Detect which branch to rebase against based on current branch or fork point.
        
        Logic:
        1. Try to find exact match: if on "LTS/2025.08", look for "upstream/LTS/2025.08"
        2. If no exact match, walk back through git history to find the branch we forked from
        3. Check if that historical branch exists on upstream
        4. Fallback to main/master
        """
        try:
            current_branch = self.git_ops.get_current_branch()
            upstream_remote = self._find_upstream_remote()
            canopy_remote = self._find_canopy_remote()
            
            if not upstream_remote:
                return "main"  # Fallback when no upstream
            
            print(f"   🔍 Using upstream remote: {upstream_remote}")
            if canopy_remote:
                print(f"   🏠 Using Canopy remote: {canopy_remote}")
            
            # Step 1: Try exact match with current branch on upstream
            if current_branch and current_branch not in ['HEAD']:
                upstream_branch = f"{upstream_remote}/{current_branch}"
                try:
                    self.git_ops.rev_parse(upstream_branch)
                    print(f"   ✓ Found exact upstream match: {current_branch}")
                    return current_branch
                except GitError:
                    print(f"   ℹ No exact upstream match for {current_branch}")
                    
                # Step 1.5: Check if branch exists on Canopy remote (indicates it's a Canopy-maintained branch)
                if canopy_remote:
                    canopy_branch = f"{canopy_remote}/{current_branch}"
                    try:
                        self.git_ops.rev_parse(canopy_branch)
                        print(f"   📋 {current_branch} exists on Canopy remote, analyzing origin...")
                        # This is a Canopy-maintained branch, find what upstream branch it should track
                    except GitError:
                        print(f"   ℹ Branch {current_branch} not found on Canopy remote either")
            
            # Step 2: Walk back through history to find origin branch
            target_branch = self._find_origin_branch(current_branch, upstream_remote)
            if target_branch:
                return target_branch
            
            # Step 3: Fallback to main/master (whichever exists on upstream)
            for fallback in ['main', 'master']:
                try:
                    upstream_branch = f"{upstream_remote}/{fallback}"
                    self.git_ops.rev_parse(upstream_branch)
                    print(f"   ⚠ Falling back to {fallback} branch")
                    return fallback
                except GitError:
                    continue
            
            # Ultimate fallback
            print("   ⚠ No upstream branches found, using 'main'")
            return "main"
            
        except GitError as e:
            print(f"   ⚠ Error detecting branch: {e}, using 'main'")
            return "main"
    
    def _find_origin_branch(self, current_branch: str, upstream_remote: str) -> Optional[str]:
        """
        Find the branch this current branch was originally forked from by examining history.
        Enhanced to consider Canopy branch patterns.
        """
        try:
            canopy_remote = self._find_canopy_remote()
            
            # Special handling for known Canopy patterns
            if current_branch.startswith('LTS/'):
                # LTS branches typically track master, but let's verify by checking merge-base
                print(f"   📋 {current_branch} is an LTS branch")
                
                # Check if there's a Canopy LTS branch and analyze its relationship
                if canopy_remote:
                    canopy_lts = f"{canopy_remote}/{current_branch}"
                    try:
                        self.git_ops.rev_parse(canopy_lts)
                        # Find what upstream branch this Canopy LTS tracks
                        return self._analyze_canopy_branch_origin(canopy_lts, upstream_remote)
                    except GitError:
                        pass
            
            # Get the list of all upstream branches
            remote_branches = self.git_ops.get_remote_branches(upstream_remote)
            
            # For each remote branch, check if we have a merge-base
            best_match = None
            best_distance = float('inf')
            best_commit_count = float('inf')
            
            for remote_branch in remote_branches:
                # Extract just the branch name (remove remote prefix)
                branch_name = remote_branch.replace(f"{upstream_remote}/", "")
                
                try:
                    # Find merge base between HEAD and this upstream branch
                    merge_base = self.git_ops.get_merge_base('HEAD', remote_branch)
                    if merge_base:
                        # Count commits since merge base (measure "distance") 
                        distance = self.git_ops.count_commits(merge_base, 'HEAD')
                        
                        # Also get the commit count on the upstream branch since merge base
                        upstream_commits = self.git_ops.count_commits(merge_base, remote_branch)
                        
                        # Prefer branches with fewer commits on our side (closer to upstream)
                        # and more commits on upstream (more "active" branch)
                        score = distance - (upstream_commits * 0.1)  # Slight preference for active upstream branches
                        
                        if score < best_distance:
                            best_distance = score
                            best_match = branch_name
                            best_commit_count = distance
                            
                except GitError:
                    continue
            
            if best_match:
                print(f"   🔍 Detected origin branch from history: {best_match} (distance: {int(best_commit_count)} commits)")
                return best_match
            
            return None
            
        except GitError:
            return None
    
    def _analyze_canopy_branch_origin(self, canopy_branch: str, upstream_remote: str) -> Optional[str]:
        """Analyze which upstream branch a Canopy branch should track."""
        try:
            # Get list of upstream branches and find the best merge-base
            remote_branches = self.git_ops.get_remote_branches(upstream_remote)
            
            best_match = None
            best_score = float('inf')
            
            for remote_branch in remote_branches:
                branch_name = remote_branch.replace(f"{upstream_remote}/", "")
                
                try:
                    merge_base = self.git_ops.get_merge_base(canopy_branch, remote_branch)
                    if merge_base:
                        # Distance from Canopy branch to upstream
                        distance = self.git_ops.count_commits(merge_base, canopy_branch)
                        
                        if distance < best_score:
                            best_score = distance
                            best_match = branch_name
                            
                except GitError:
                    continue
            
            if best_match:
                print(f"   🎯 Canopy branch origin analysis suggests: {best_match}")
                return best_match
            
            return None
            
        except GitError:
            return None
    
    def _is_working_tree_clean(self) -> bool:
        """Check if working tree is clean (no uncommitted changes)."""
        try:
            status = self.git_ops.get_status_porcelain()
            return len(status) == 0
        except GitError:
            return False
    
    def _find_upstream_remote(self) -> Optional[str]:
        """Find upstream remote (prefer 'upstream', fall back to others)."""
        try:
            remotes = self.git_ops.get_remote_list()
            
            # Prefer 'upstream' if it exists
            if 'upstream' in remotes:
                return 'upstream'
            
            # Look for remote with openbmc/openbmc URL
            for remote in remotes:
                if remote.strip():
                    try:
                        url = self.git_ops.get_remote_url(remote.strip())
                        if 'openbmc/openbmc' in url:
                            return remote.strip()
                    except GitError:
                        continue
            
            return None
            
        except GitError:
            return None
    
    def _find_canopy_remote(self) -> Optional[str]:
        """
        Find Canopy remote (canopybmc/openbmc).
        Checks for both HTTPS and SSH URLs.
        """
        try:
            remotes = self.git_ops.get_remote_list()
            
            # Look for remote with canopybmc/openbmc URL (both HTTPS and SSH)
            for remote in remotes:
                if remote.strip():
                    try:
                        url = self.git_ops.get_remote_url(remote.strip())
                        # Check for both HTTPS and SSH patterns
                        if ('canopybmc/openbmc' in url or 
                            'github.com:canopybmc/openbmc' in url):
                            return remote.strip()
                    except GitError:
                        continue
            
            # Fallback to 'origin' if no explicit canopybmc remote found
            if 'origin' in remotes:
                try:
                    url = self.git_ops.get_remote_url('origin')
                    if ('canopybmc' in url or 
                        'github.com:canopybmc/openbmc' in url):
                        return 'origin'
                except GitError:
                    pass
            
            return None
            
        except GitError:
            return None
    
    def _find_upstream_base(self) -> Optional[str]:
        """Find the upstream commit this branch is based on."""
        upstream_remote = self._find_upstream_remote()
        if not upstream_remote:
            return None
        
        try:
            # Try main branch first
            upstream_branch = f"{upstream_remote}/main"
            try:
                base = self.git_ops.get_merge_base('HEAD', upstream_branch)
                return base
            except GitError:
                # Try master branch
                upstream_branch = f"{upstream_remote}/master"
                base = self.git_ops.get_merge_base('HEAD', upstream_branch)
                return base
                
        except GitError:
            return None