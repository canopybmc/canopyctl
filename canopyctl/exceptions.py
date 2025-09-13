"""
Custom exceptions for canopyctl.
"""


class RebaseError(Exception):
    """Base exception for rebase operations."""
    pass


class GitError(Exception):
    """Exception for Git operation failures."""
    pass


class ConfigError(Exception):
    """Exception for configuration issues."""
    pass