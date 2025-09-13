#!/usr/bin/env python3
"""
Simplified canopyctl entry point for standalone distribution.
This version avoids complex import structures that can cause issues with PyInstaller.
"""

import argparse
import sys
import subprocess
from pathlib import Path
from typing import List, Optional

def run_git(args: List[str], check: bool = True) -> str:
    """Run git command and return output."""
    try:
        cmd = ['git'] + args
        result = subprocess.run(cmd, capture_output=True, text=True, check=check)
        return result.stdout
    except subprocess.CalledProcessError as e:
        if check:
            print(f"❌ Git command failed: {' '.join(cmd)}")
            print(f"Error: {e.stderr}")
            sys.exit(1)
        return ""

def get_current_branch() -> str:
    """Get current branch name."""
    return run_git(['branch', '--show-current']).strip()

def get_remote_list() -> List[str]:
    """Get list of configured remotes."""
    output = run_git(['remote']).strip()
    return [r.strip() for r in output.split('\n') if r.strip()]

def get_remote_url(remote: str) -> str:
    """Get URL for remote.""" 
    return run_git(['remote', 'get-url', remote]).strip()

def find_upstream_remote() -> Optional[str]:
    """Find upstream remote."""
    remotes = get_remote_list()
    
    # Prefer 'upstream' if it exists
    if 'upstream' in remotes:
        return 'upstream'
    
    # Look for remote with openbmc URL
    for remote in remotes:
        if remote.strip():
            try:
                url = get_remote_url(remote.strip())
                if 'openbmc/openbmc' in url:
                    return remote.strip()
            except:
                continue
    
    return None

def find_canopy_remote() -> Optional[str]:
    """Find Canopy remote."""
    remotes = get_remote_list()
    
    # Look for remote with canopybmc/openbmc URL
    for remote in remotes:
        if remote.strip():
            try:
                url = get_remote_url(remote.strip())
                if 'canopybmc/openbmc' in url:
                    return remote.strip()
            except:
                continue
    
    # Fallback to 'origin' if it contains canopybmc
    if 'origin' in remotes:
        try:
            url = get_remote_url('origin')
            if 'canopybmc' in url:
                return 'origin'
        except:
            pass
    
    return None

def simple_rebase(remote: str = 'upstream', branch: str = None):
    """Simplified rebase implementation."""
    print("🔍 Analyzing repository state...")
    
    # Check working directory is clean
    status = run_git(['status', '--porcelain']).strip()
    if status:
        print("❌ Rebase failed: Working directory has uncommitted changes.")
        print("Please commit or stash your changes first:")
        print("  git add .")
        print('  git commit -m "Work in progress"')
        print("  # Or: git stash push -m \"Before rebase\"")
        return 1
    
    current_branch = get_current_branch()
    upstream_remote = find_upstream_remote()
    canopy_remote = find_canopy_remote()
    
    if not upstream_remote:
        print("❌ No upstream remote found.")
        print("Please add upstream remote:")
        print("  git remote add upstream https://github.com/openbmc/openbmc.git")
        return 1
    
    print(f"   🔍 Using upstream remote: {upstream_remote}")
    if canopy_remote:
        print(f"   🏠 Using Canopy remote: {canopy_remote}")
    
    # Auto-detect branch if not specified
    if branch is None:
        # Try exact match first
        try:
            run_git(['rev-parse', f'{upstream_remote}/{current_branch}'])
            branch = current_branch
            print(f"   ✓ Found exact upstream match: {branch}")
        except:
            # Default to master
            branch = 'master'
            print(f"   🎯 Auto-detected target branch: {branch}")
    
    target = f"{remote}/{branch}"
    print(f"   📍 Rebasing against: {target}")
    
    # Fetch upstream
    print("📥 Fetching latest upstream...")
    run_git(['fetch', upstream_remote])
    
    # Create backup
    import time
    backup_name = f"canopy-backup-{int(time.time())}"
    print("🛡️ Creating safety backup...")
    run_git(['branch', backup_name])
    print(f"   ✓ Backup branch created: {backup_name}")
    
    # Perform rebase
    print("⚙️ Starting rebase operation...")
    try:
        run_git(['rebase', target])
        print("✅ Rebase completed successfully!")
        print(f"   • Backup available: {backup_name}")
        print("💡 Next steps:")
        print("   • Test your changes: run build/tests as appropriate")
        print("   • Push when ready: git push --force-with-lease origin <branch>")
        print(f"   • Backup kept for safety: {backup_name}")
        return 0
    except:
        print("❌ Rebase failed with conflicts.")
        print("💡 To resolve conflicts:")
        print("   1. Edit the conflicted files to resolve conflicts")
        print("   2. Add resolved files: git add <file>")
        print("   3. Continue rebase: git rebase --continue")
        print("   4. Or abort: git rebase --abort")
        return 1

def create_parser() -> argparse.ArgumentParser:
    """Create the command line argument parser."""
    parser = argparse.ArgumentParser(description='Canopy control tool (simplified)')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # rebase command
    rebase_parser = subparsers.add_parser('rebase', help='Smart rebase against upstream OpenBMC')
    rebase_parser.add_argument('--remote', default='upstream', help='Remote to rebase against (default: upstream)')
    rebase_parser.add_argument('--branch', help='Branch to rebase against (default: auto-detect)')

    return parser

def main() -> int:
    """Main entry point for the simplified CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        print("\nNote: This is a simplified standalone version of canopyctl.")
        print("For full functionality, install the Python package: pip install canopyctl")
        return 1
    
    if args.command == 'rebase':
        remote = getattr(args, 'remote', 'upstream')
        branch = getattr(args, 'branch', None)
        return simple_rebase(remote, branch)
    
    parser.print_help()
    return 1

if __name__ == '__main__':
    sys.exit(main())