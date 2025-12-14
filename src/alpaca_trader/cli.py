import argparse
import sys
from typing import Optional

def main(args: Optional[list[str]] = None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Alpaca Trader CLI")
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    
    subparsers = parser.add_subparsers(dest="command")
    run_parser = subparsers.add_parser("run", help="Start the trading bot")
    
    parsed_args = parser.parse_args(args)
    
    if parsed_args.command == "run":
        from alpaca_trader.core.bot import AlpacaBot
        bot = AlpacaBot()
        try:
            bot.start()
        except KeyboardInterrupt:
            print("\nShutting down...")
        return 0
    
    print("Welcome to Alpaca Trader! Use 'run' to start the bot.")
    parser.print_help()
    return 0

if __name__ == "__main__":
    sys.exit(main())
