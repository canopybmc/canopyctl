#!/usr/bin/env python3
"""
Integration test script for canopyctl rebase functionality.
Tests the core functionality without requiring a full OpenBMC environment.
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, check=True):
    """Run a command and return the result."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
        return result.returncode, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout, e.stderr

def test_help_commands():
    """Test help commands work correctly."""
    print("Testing help commands...")
    
    commands = [
        "python canopyctl.py --help",
        "python canopyctl.py rebase --help",
        "python canopyctl.py rebase upstream --help",
        "python canopyctl.py config --help"
    ]
    
    for cmd in commands:
        print(f"  Testing: {cmd}")
        returncode, stdout, stderr = run_command(cmd)
        if returncode != 0:
            print(f"    ❌ FAILED: {stderr}")
            return False
        print(f"    ✓ OK")
    
    return True

def test_error_handling():
    """Test error handling for invalid scenarios."""
    print("Testing error handling...")
    
    # Test rebase continue/abort without active rebase
    commands = [
        "python canopyctl.py rebase --continue",
        "python canopyctl.py rebase --abort"
    ]
    
    for cmd in commands:
        print(f"  Testing: {cmd}")
        returncode, stdout, stderr = run_command(cmd, check=False)
        if returncode == 0:
            print(f"    ❌ FAILED: Should have returned non-zero exit code")
            return False
        if "No rebase in progress" not in stderr and "No rebase in progress" not in stdout:
            print(f"    ❌ FAILED: Expected 'No rebase in progress' message")
            print(f"    stdout: {stdout}")
            print(f"    stderr: {stderr}")
            return False
        print(f"    ✓ OK: Correctly detected no rebase in progress")
    
    return True

def test_imports():
    """Test that all modules can be imported."""
    print("Testing module imports...")
    
    try:
        from canopyctl.commands.rebase import RebaseCommand
        from canopyctl.core.git_ops import GitOperations
        from canopyctl.core.repo_analyzer import RepoAnalyzer
        from canopyctl.core.backup_manager import BackupManager
        from canopyctl.core.rebase_engine import RebaseEngine
        from canopyctl.exceptions import RebaseError, GitError
        print("  ✓ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        return False

def main():
    """Run integration tests."""
    print("=== canopyctl Phase 1 Integration Tests ===\n")
    
    # Change to the canopyctl directory
    original_cwd = Path.cwd()
    canopyctl_dir = Path(__file__).parent
    import os
    os.chdir(canopyctl_dir)
    
    try:
        tests = [
            test_imports,
            test_help_commands,
            test_error_handling
        ]
        
        passed = 0
        for test in tests:
            if test():
                passed += 1
                print()
            else:
                print("❌ Test failed!\n")
        
        print(f"=== Test Results: {passed}/{len(tests)} passed ===")
        
        if passed == len(tests):
            print("🎉 All tests passed! Phase 1 implementation is ready.")
            return 0
        else:
            print("💥 Some tests failed. Please review the implementation.")
            return 1
            
    finally:
        os.chdir(original_cwd)

if __name__ == "__main__":
    sys.exit(main())