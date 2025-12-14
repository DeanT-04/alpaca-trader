import argparse
import sys
from typing import Optional

def main(args: Optional[list[str]] = None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Alpaca Trader CLI")
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    
    # Add commands here
    # subparsers = parser.add_subparsers(dest="command")
    
    parsed_args = parser.parse_args(args)
    
    print("Welcome to Alpaca Trader!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
