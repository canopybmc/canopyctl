"""
Command line interface for canopyctl.
"""

import argparse
import sys

# Import CanopyCtl with fallback to direct file import
try:
    from .core import CanopyCtl
    if CanopyCtl is None:
        raise ImportError("CanopyCtl resolved to None")
except (ImportError, AttributeError):
    # Direct import from core.py as fallback
    from pathlib import Path
    import importlib.util
    
    core_path = Path(__file__).parent / "core.py"
    spec = importlib.util.spec_from_file_location("core", core_path)
    core_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(core_module)
    CanopyCtl = core_module.CanopyCtl
from .commands import ConfigShowCommand, ConfigListCommand, RebaseCommand


def create_parser() -> argparse.ArgumentParser:
    """Create the command line argument parser."""
    parser = argparse.ArgumentParser(description='Canopy control tool')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # config command
    config_parser = subparsers.add_parser('config', help='Configuration management')
    config_subparsers = config_parser.add_subparsers(dest='config_command', help='Config commands')
    
    # config show command
    show_parser = config_subparsers.add_parser('show', help='Show configuration')
    show_parser.add_argument('recipe', nargs='?', help='Recipe name to analyze')
    
    # config list command
    list_parser = config_subparsers.add_parser('list', help='List all available recipes')
    list_parser.add_argument('pattern', nargs='?', help='Filter pattern - supports glob patterns like phosphor* or *network* (optional)')

    # rebase command
    rebase_parser = subparsers.add_parser('rebase', help='Smart rebase against Canopy repository')
    
    # rebase --continue
    rebase_parser.add_argument('--continue', action='store_true', help='Continue rebase after resolving conflicts')
    
    # rebase --abort  
    rebase_parser.add_argument('--abort', action='store_true', help='Abort rebase and restore original state')

    return parser


def main() -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == 'config':
        if not args.config_command:
            # Get the config subparser to print help
            config_parser = create_parser().parse_args(['config', '--help'])
            return 1
        
        if args.config_command == 'show':
            canopyctl = CanopyCtl()
            config_show = ConfigShowCommand(canopyctl)
            return config_show.execute(getattr(args, 'recipe', None))
        
        if args.config_command == 'list':
            canopyctl = CanopyCtl()
            config_list = ConfigListCommand(canopyctl)
            return config_list.execute(getattr(args, 'pattern', None))

    if args.command == 'rebase':
        rebase_command = RebaseCommand()
        
        # Handle continue/abort flags
        if getattr(args, 'abort', False):
            return rebase_command.abort_rebase()
        elif getattr(args, 'continue', False):
            return rebase_command.continue_rebase()
        else:
            # Execute rebase (new workflow - no parameters needed)
            return rebase_command.execute_rebase()

    parser.print_help()
    return 1


if __name__ == '__main__':
    sys.exit(main())