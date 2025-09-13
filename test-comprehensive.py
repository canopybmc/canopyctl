#!/usr/bin/env python3
"""
Comprehensive integration test suite for canopyctl rebase functionality.
Tests various scenarios and edge cases to ensure robust operation.
"""

import subprocess
import sys
import tempfile
import shutil
import os
from pathlib import Path
import time

class TestRunner:
    """Test runner with setup and teardown capabilities."""
    
    def __init__(self):
        self.test_dir = None
        self.original_cwd = Path.cwd()
        self.passed = 0
        self.failed = 0
        
    def setup_test_repo(self, with_upstream=True, with_patches=True, clean=True):
        """Create a test git repository."""
        self.test_dir = tempfile.mkdtemp(prefix="canopyctl_test_")
        os.chdir(self.test_dir)
        
        # Initialize git repo
        self.run_cmd("git init")
        self.run_cmd("git config user.name 'Test User'")
        self.run_cmd("git config user.email 'test@example.com'")
        
        # Create initial commit
        Path("README.md").write_text("Initial commit\n")
        self.run_cmd("git add README.md")
        self.run_cmd("git commit -m 'Initial commit'")
        
        if with_upstream:
            # Add upstream remote (we'll use the same repo as a mock)
            self.run_cmd("git remote add upstream .")
        
        if with_patches:
            # Create some "Canopy" patches
            for i in range(3):
                Path(f"canopy_patch_{i}.txt").write_text(f"Canopy patch {i}\n")
                self.run_cmd(f"git add canopy_patch_{i}.txt")
                self.run_cmd(f"git commit -m 'feat: Canopy patch {i}'")
        
        if not clean:
            # Create uncommitted changes
            Path("dirty.txt").write_text("Uncommitted change\n")
        
        return self.test_dir
    
    def cleanup_test_repo(self):
        """Clean up test repository."""
        if self.test_dir:
            os.chdir(self.original_cwd)
            shutil.rmtree(self.test_dir, ignore_errors=True)
            self.test_dir = None
    
    def run_cmd(self, cmd, check=True):
        """Run a command and return result."""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, 
                                  text=True, check=check)
            return result.returncode, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return e.returncode, e.stdout, e.stderr
    
    def run_canopyctl(self, args, check=False):
        """Run canopyctl command."""
        canopyctl_path = self.original_cwd / "canopyctl.py"
        cmd = f"python {canopyctl_path} {args}"
        return self.run_cmd(cmd, check=check)
    
    def assert_contains(self, text, substring, description):
        """Assert that text contains substring."""
        if substring in text:
            print(f"    ✓ {description}")
            return True
        else:
            print(f"    ❌ {description}")
            print(f"    Expected to find: '{substring}'")
            print(f"    In text: '{text[:200]}...'")
            return False
    
    def run_test(self, test_func, test_name):
        """Run a single test."""
        print(f"\n=== {test_name} ===")
        try:
            if test_func():
                self.passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                self.failed += 1
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            self.failed += 1
            print(f"💥 {test_name} ERROR: {e}")
        finally:
            self.cleanup_test_repo()

def test_basic_cli_functionality(runner):
    """Test 1: Basic CLI Functionality"""
    # Test help commands
    returncode, stdout, stderr = runner.run_canopyctl("--help")
    if returncode != 0:
        return False
    
    if not runner.assert_contains(stdout, "rebase", "Help shows rebase command"):
        return False
    
    # Test rebase help
    returncode, stdout, stderr = runner.run_canopyctl("rebase --help")
    if returncode != 0:
        return False
    
    if not runner.assert_contains(stdout, "upstream", "Rebase help shows upstream option"):
        return False
    
    return True

def test_dirty_working_directory(runner):
    """Test 2: Dirty Working Directory Handling"""
    runner.setup_test_repo(clean=False)
    
    returncode, stdout, stderr = runner.run_canopyctl("rebase upstream")
    
    if returncode == 0:
        print("    ❌ Should have failed with dirty working directory")
        return False
    
    return runner.assert_contains((stderr + stdout).lower(), "uncommitted changes", 
                                "Error message mentions uncommitted changes")

def test_missing_upstream_remote(runner):
    """Test 3: Missing Upstream Remote"""
    runner.setup_test_repo(with_upstream=False)
    
    returncode, stdout, stderr = runner.run_canopyctl("rebase upstream")
    
    if returncode == 0:
        print("    ❌ Should have failed without upstream remote")
        return False
    
    return runner.assert_contains((stderr + stdout).lower(), "upstream", 
                                "Error message mentions upstream remote")

def test_not_git_repository(runner):
    """Test 4: Not in Git Repository"""
    runner.test_dir = tempfile.mkdtemp(prefix="canopyctl_test_nogit_")
    os.chdir(runner.test_dir)
    
    returncode, stdout, stderr = runner.run_canopyctl("rebase upstream")
    
    if returncode == 0:
        print("    ❌ Should have failed outside git repository")
        return False
    
    return runner.assert_contains((stderr + stdout).lower(), "git", 
                                "Error message mentions git")

def test_no_rebase_in_progress(runner):
    """Test 5: Continue/Abort Without Active Rebase"""
    runner.setup_test_repo()
    
    # Test continue
    returncode, stdout, stderr = runner.run_canopyctl("rebase --continue")
    if returncode == 0:
        print("    ❌ Continue should fail when no rebase in progress")
        return False
    
    if not runner.assert_contains(stderr + stdout, "No rebase in progress", 
                                "Continue shows appropriate message"):
        return False
    
    # Test abort
    returncode, stdout, stderr = runner.run_canopyctl("rebase --abort")
    if returncode == 0:
        print("    ❌ Abort should fail when no rebase in progress")
        return False
    
    return runner.assert_contains(stderr + stdout, "No rebase in progress", 
                                "Abort shows appropriate message")

def test_already_up_to_date(runner):
    """Test 6: Repository Already Up-to-Date"""
    runner.setup_test_repo(with_patches=False)
    
    returncode, stdout, stderr = runner.run_canopyctl("rebase upstream")
    
    # For a repo with no patches, it should either succeed gracefully or give a reasonable error
    # The key is it shouldn't crash
    if returncode not in [0, 1]:
        print(f"    ❌ Unexpected return code: {returncode}")
        return False
    
    combined = (stdout + stderr).lower()
    if "traceback" in combined or "exception" in combined:
        print(f"    ❌ Unexpected exception in output: {combined[:200]}...")
        return False
    
    print("    ✓ Handled repository with no patches gracefully")
    return True

def test_invalid_subcommand(runner):
    """Test 7: Invalid Subcommand"""
    returncode, stdout, stderr = runner.run_canopyctl("rebase invalid_subcommand")
    
    if returncode == 0:
        print("    ❌ Should have failed with invalid subcommand")
        return False
    
    return runner.assert_contains((stderr + stdout).lower(), "invalid choice", 
                                "Error mentions invalid choice")

def test_config_commands(runner):
    """Test 8: Config Commands Work"""
    returncode, stdout, stderr = runner.run_canopyctl("config --help")
    
    if returncode != 0:
        print(f"    ❌ Config help failed: {stderr}")
        return False
    
    return runner.assert_contains(stdout, "show", 
                                "Config help shows show command")

def test_backup_branch_naming(runner):
    """Test 9: Backup Branch Naming Convention"""
    runner.setup_test_repo()
    
    # Create a mock scenario where we can check backup naming
    # This is a basic test - in a real scenario we'd need to simulate
    # the actual rebase process
    from canopyctl.core.backup_manager import BackupManager
    
    os.chdir(runner.test_dir)
    backup_manager = BackupManager()
    
    # Test timestamp format
    backup_name = backup_manager._generate_backup_name()
    if not backup_name.startswith("canopy-backup-"):
        print(f"    ❌ Backup name format incorrect: {backup_name}")
        return False
    
    # Check timestamp is numeric
    timestamp = backup_name.replace("canopy-backup-", "")
    try:
        int(timestamp)
        print(f"    ✓ Backup name format correct: {backup_name}")
        return True
    except ValueError:
        print(f"    ❌ Backup timestamp not numeric: {timestamp}")
        return False

def test_error_message_quality(runner):
    """Test 10: Error Messages Are Helpful"""
    tests = [
        ("rebase upstream", "uncommitted changes", False),
        ("rebase --continue", "no rebase in progress", True),
        ("rebase --abort", "no rebase in progress", True),
    ]
    
    for cmd, expected_phrase, should_work_clean in tests:
        if should_work_clean:
            runner.setup_test_repo()
        else:
            runner.setup_test_repo(clean=False)
        
        returncode, stdout, stderr = runner.run_canopyctl(cmd)
        combined_output = (stdout + stderr).lower()
        
        if expected_phrase not in combined_output:
            print(f"    ❌ Command '{cmd}' doesn't contain expected phrase '{expected_phrase}'")
            print(f"    Output: {combined_output[:200]}...")
            return False
        
        runner.cleanup_test_repo()
    
    print("    ✓ All error messages contain helpful information")
    return True

def main():
    """Run comprehensive test suite."""
    print("🧪 canopyctl Comprehensive Test Suite")
    print("=" * 50)
    
    runner = TestRunner()
    
    # Define all tests
    tests = [
        (test_basic_cli_functionality, "Basic CLI Functionality"),
        (test_dirty_working_directory, "Dirty Working Directory Handling"),
        (test_missing_upstream_remote, "Missing Upstream Remote"),
        (test_not_git_repository, "Not in Git Repository"),
        (test_no_rebase_in_progress, "Continue/Abort Without Active Rebase"),
        (test_already_up_to_date, "Repository Already Up-to-Date"),
        (test_invalid_subcommand, "Invalid Subcommand"),
        (test_config_commands, "Config Commands Work"),
        (test_backup_branch_naming, "Backup Branch Naming Convention"),
        (test_error_message_quality, "Error Message Quality"),
    ]
    
    # Run all tests
    for test_func, test_name in tests:
        runner.run_test(lambda: test_func(runner), test_name)
    
    # Summary
    total = runner.passed + runner.failed
    print(f"\n🏁 Test Summary")
    print("=" * 30)
    print(f"✅ Passed: {runner.passed}/{total}")
    print(f"❌ Failed: {runner.failed}/{total}")
    
    if runner.failed == 0:
        print(f"\n🎉 All tests passed! Phase 1 implementation is robust and ready.")
        return 0
    else:
        print(f"\n💥 {runner.failed} test(s) failed. Please review the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())