"""
Git operations wrapper for safe rebase functionality.
"""

import subprocess
from pathlib import Path
from typing import List, Optional

from ..exceptions import GitError


class GitOperations:
    """Safe wrapper around Git operations."""
    
    def __init__(self, repo_root: Optional[Path] = None):
        if repo_root:
            self.repo_root = repo_root
        else:
            self.repo_root = self._find_repo_root()
    
    def create_branch(self, branch_name: str, start_point: Optional[str] = None) -> None:
        """Create a new branch."""
        cmd = ['branch', branch_name]
        if start_point:
            cmd.append(start_point)
        self._run_git(cmd)
    
    def checkout(self, branch_or_commit: str) -> None:
        """Checkout branch or commit."""
        self._run_git(['checkout', branch_or_commit])
    
    def reset_hard(self, commit: str) -> None:
        """Hard reset to specified commit."""
        self._run_git(['reset', '--hard', commit])
    
    def cherry_pick(self, commit: str) -> bool:
        """
        Cherry-pick a commit.
        Returns True if successful, False if conflicts.
        """
        try:
            self._run_git(['cherry-pick', commit])
            return True
        except GitError as e:
            # Check if it's a conflict (exit code 1) vs other error
            if 'conflict' in str(e).lower() or 'merge conflict' in str(e).lower():
                return False
            else:
                raise
    
    def cherry_pick_continue(self) -> bool:
        """Continue cherry-pick after resolving conflicts."""
        try:
            self._run_git(['cherry-pick', '--continue'])
            return True
        except GitError:
            return False
    
    def cherry_pick_abort(self) -> None:
        """Abort current cherry-pick."""
        self._run_git(['cherry-pick', '--abort'])
    
    def get_conflicted_files(self) -> List[str]:
        """Get list of files with conflicts."""
        try:
            output = self._run_git(['diff', '--name-only', '--diff-filter=U'])
            return [f.strip() for f in output.split('\n') if f.strip()]
        except GitError:
            return []
    
    def is_cherry_pick_in_progress(self) -> bool:
        """Check if cherry-pick is in progress."""
        cherry_pick_head = self.repo_root / '.git' / 'CHERRY_PICK_HEAD'
        return cherry_pick_head.exists()
    
    def get_current_commit(self) -> str:
        """Get current commit hash."""
        return self._run_git(['rev-parse', 'HEAD']).strip()
    
    def commit_exists(self, commit_hash: str) -> bool:
        """Check if commit exists."""
        try:
            self._run_git(['cat-file', '-e', commit_hash])
            return True
        except GitError:
            return False
    
    def fetch(self, remote: str) -> None:
        """Fetch from remote."""
        self._run_git(['fetch', remote])
    
    def get_merge_base(self, commit1: str, commit2: str) -> str:
        """Get merge base between two commits."""
        return self._run_git(['merge-base', commit1, commit2]).strip()
    
    def get_commit_list(self, from_commit: str, to_commit: str, reverse: bool = False) -> List[str]:
        """Get list of commits between two points."""
        cmd = ['log', '--oneline']
        if reverse:
            cmd.append('--reverse')
        cmd.append(f"{from_commit}..{to_commit}")
        
        output = self._run_git(cmd).strip()
        if not output:
            return []
        
        return output.split('\n')
    
    def get_remote_list(self) -> List[str]:
        """Get list of configured remotes."""
        try:
            output = self._run_git(['remote']).strip()
            return [r.strip() for r in output.split('\n') if r.strip()]
        except GitError:
            return []
    
    def get_remote_url(self, remote: str) -> str:
        """Get URL for remote."""
        return self._run_git(['remote', 'get-url', remote]).strip()
    
    def get_status_porcelain(self) -> str:
        """Get git status in porcelain format."""
        return self._run_git(['status', '--porcelain']).strip()
    
    def get_current_branch(self) -> str:
        """Get current branch name."""
        return self._run_git(['branch', '--show-current']).strip()
    
    def rev_parse(self, ref: str) -> str:
        """Resolve reference to commit hash."""
        return self._run_git(['rev-parse', ref]).strip()
    
    def get_remote_branches(self, remote: str) -> List[str]:
        """Get list of branches on remote."""
        try:
            output = self._run_git(['branch', '-r', '--list', f'{remote}/*']).strip()
            if not output:
                return []
            
            branches = []
            for line in output.split('\n'):
                line = line.strip()
                if line and not line.endswith('/HEAD'):
                    # Remove leading '* ' if present and extract branch name
                    branch = line.lstrip('* ').strip()
                    branches.append(branch)
            return branches
        except GitError:
            return []
    
    def count_commits(self, from_commit: str, to_commit: str) -> int:
        """Count commits between two points."""
        try:
            output = self._run_git(['rev-list', '--count', f'{from_commit}..{to_commit}']).strip()
            return int(output) if output.isdigit() else 0
        except (GitError, ValueError):
            return 0
    
    def rebase(self, onto: str) -> None:
        """Rebase current branch onto specified commit/branch."""
        try:
            self._run_git(['rebase', onto])
        except GitError as e:
            # Re-raise with more context for rebase conflicts
            if 'conflict' in str(e).lower() or 'merge conflict' in str(e).lower():
                raise GitError(f"Rebase conflicts detected. Resolve conflicts and use 'canopyctl rebase --continue'")
            else:
                raise
    
    def _find_repo_root(self) -> Path:
        """Find Git repository root."""
        try:
            root = subprocess.run(
                ['git', 'rev-parse', '--show-toplevel'],
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()
            return Path(root)
        except subprocess.CalledProcessError:
            raise GitError("Not in a Git repository")
    
    def _run_git(self, args: List[str]) -> str:
        """Run git command and return output."""
        try:
            cmd = ['git'] + args
            result = subprocess.run(
                cmd,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise GitError(f"Git command failed: {' '.join(cmd)}\n{e.stderr}")