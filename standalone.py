#!/usr/bin/env python3
"""
Standalone entry point for canopyctl - simplified for PyInstaller.
"""

import sys
from pathlib import Path

# Add the canopyctl directory to the path
sys.path.insert(0, str(Path(__file__).parent))

# Import directly from the modules to avoid dynamic import issues
from canopyctl.core import CanopyCtl
from canopyctl.commands.config import ConfigShowCommand, ConfigListCommand
from canopyctl.commands.rebase import RebaseCommand
from canopyctl.cli import create_parser

def main() -> int:
    """Main entry point for the standalone CLI."""
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
            # Execute rebase with remote and branch parameters
            remote = getattr(args, 'remote', 'upstream')
            branch = getattr(args, 'branch', None)
            return rebase_command.execute_rebase(remote, branch)

    parser.print_help()
    return 1

if __name__ == '__main__':
    sys.exit(main())