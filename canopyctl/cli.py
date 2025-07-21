"""
Command line interface for canopyctl.
"""

import argparse
import sys

from .core import CanopyCtl
from .commands import ConfigShowCommand


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
    
    parser.print_help()
    return 1


if __name__ == '__main__':
    sys.exit(main())