"""
CKSEARCH - CLI Argument Parser
================================
Command line interface untuk CKSEARCH.
"""

import argparse
import sys
from typing import Optional, Tuple

import config


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog="cksearch",
        description=f"CKSEARCH - Professional OSINT Tool v{config.VERSION}",
        epilog=f"By {config.AUTHOR} | https://github.com/CimenkDev/CKSEARCH",
    )
    
    # Version
    parser.add_argument(
        "-V", "--version",
        action="version",
        version=f"CKSEARCH v{config.VERSION}",
    )
    
    # Scan targets (mutually exclusive)
    target_group = parser.add_mutually_exclusive_group()
    
    target_group.add_argument(
        "-p", "--phone",
        metavar="NUMBER",
        help="Scan phone number (e.g., +62812345678)",
    )
    
    target_group.add_argument(
        "-e", "--email",
        metavar="EMAIL",
        help="Scan email address",
    )
    
    target_group.add_argument(
        "-u", "--username",
        metavar="USERNAME",
        help="Search username across platforms",
    )
    
    target_group.add_argument(
        "-d", "--domain",
        metavar="DOMAIN",
        help="Scan domain (e.g., example.com)",
    )
    
    target_group.add_argument(
        "-i", "--ip",
        metavar="IP",
        help="Scan IP address",
    )
    
    target_group.add_argument(
        "-n", "--name",
        metavar="NAME",
        help="Search person by name",
    )
    
    target_group.add_argument(
        "--image",
        metavar="PATH",
        help="Analyze image EXIF data",
    )
    
    target_group.add_argument(
        "--social",
        metavar="URL",
        help="Deep scan social media profile",
    )
    
    target_group.add_argument(
        "--geo",
        metavar="COORDS",
        help="Geolocation OSINT (lat,lon)",
    )
    
    # Scan mode
    parser.add_argument(
        "--deep",
        action="store_true",
        help="Use deep scan mode (more thorough, slower)",
    )
    
    # Output options
    parser.add_argument(
        "-o", "--output",
        choices=["console", "json", "txt", "html", "all"],
        default="console",
        help="Output format (default: console)",
    )
    
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Export results to PDF report",
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Quiet mode (less output)",
    )
    
    # License options
    license_group = parser.add_argument_group("License")
    
    license_group.add_argument(
        "--activate",
        metavar="KEY",
        help="Activate license key (e.g., XXXX-XXXX-XXXX-XXXX)",
    )
    
    license_group.add_argument(
        "--status",
        action="store_true",
        help="Show license status",
    )
    
    license_group.add_argument(
        "--referral",
        metavar="CODE",
        help="Use referral code for bonus requests",
    )
    
    return parser


def parse_args(args=None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = create_parser()
    return parser.parse_args(args)


def get_scan_target(args: argparse.Namespace) -> Tuple[Optional[str], Optional[str]]:
    """
    Get scan type and target from args.
    Returns: (scan_type, target) or (None, None) if no target specified.
    """
    if args.phone:
        return "phone", args.phone
    elif args.email:
        return "email", args.email
    elif args.username:
        return "username", args.username
    elif args.domain:
        return "domain", args.domain
    elif args.ip:
        return "ip", args.ip
    elif args.name:
        return "name", args.name
    elif args.image:
        return "image", args.image
    elif args.social:
        return "social", args.social
    elif args.geo:
        return "geo", args.geo
    
    return None, None


def has_cli_target(args: argparse.Namespace) -> bool:
    """Check if any scan target was provided via CLI."""
    scan_type, _ = get_scan_target(args)
    return scan_type is not None


def is_interactive_mode(args: argparse.Namespace) -> bool:
    """Check if we should run in interactive mode."""
    # Interactive if no target and no special commands
    if has_cli_target(args):
        return False
    if args.status or args.activate or args.referral:
        return False
    return True


if __name__ == "__main__":
    # Test CLI
    args = parse_args()
    print(f"Args: {args}")
    print(f"Interactive: {is_interactive_mode(args)}")
    print(f"Target: {get_scan_target(args)}")
