"""
Core modules for canopyctl rebase functionality.
"""

# Import the main CanopyCtl class from the sibling core module
# This maintains backward compatibility
try:
    from ..core import CanopyCtl
except ImportError:
    try:
        # Alternative path if the above fails
        import sys
        from pathlib import Path
        parent_path = Path(__file__).parent.parent
        sys.path.insert(0, str(parent_path))
        from core import CanopyCtl
    except ImportError:
        CanopyCtl = None

from .git_ops import GitOperations
from .repo_analyzer import RepoAnalyzer
from .backup_manager import BackupManager
from .rebase_engine import RebaseEngine

__all__ = ["GitOperations", "RepoAnalyzer", "BackupManager", "RebaseEngine"]
if CanopyCtl is not None:
    __all__.append("CanopyCtl")