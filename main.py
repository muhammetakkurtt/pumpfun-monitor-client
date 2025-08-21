#!/usr/bin/env python3
"""
Pump Monitor - Entry Point

Main executable for the Pump.fun real-time monitoring client.
Provides command-line interface and application entry point.
"""

import sys
import argparse
from typing import Optional

from config import PumpMonitorConfig, print_available_endpoints
from client import PumpMonitorClient, GracefulShutdown


def print_banner():
    """Print application banner."""
    print("=" * 70)
    print("🔥 Pump.fun Real-Time Monitor Client")
    print("📈 Python SSE Client for Standby Server")
    print("=" * 70)


def parse_arguments() -> Optional[argparse.Namespace]:
    """Parse command-line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Pump.fun Real-Time Monitor Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                              # Run with default settings
  python main.py --endpoint trades/pump       # Monitor pump trades only
  python main.py --quiet                      # Quiet mode
  python main.py --no-save                    # Disable file logging
  python main.py --debug                      # Enable debug logging

Endpoint Options:
  all                 - Retrieve all event types
  tokens/new          - New token events only
  tokens/new/detailed - Detailed new token information
  tokens/graduated    - Graduated token events
  trades/pump         - Pump trading events
  trades/pumpswap     - PumpSwap trading events
        """
    )
    
    parser.add_argument(
        '--endpoint', '-e',
        type=str,
        help='Endpoint selection (default: all)'
    )
    
    parser.add_argument(
        '--api-token', '-t',
        type=str,
        help='Apify API Token'
    )
    
    parser.add_argument(
        '--server-url', '-s',
        type=str,
        help='Standby server URL'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Quiet mode (errors and statistics only)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Disable file logging'
    )
    
    parser.add_argument(
        '--output-file', '-o',
        type=str,
        help='Output filename'
    )
    
    parser.add_argument(
        '--show-raw',
        action='store_true',
        help='Enable raw data display'
    )
    
    parser.add_argument(
        '--list-endpoints',
        action='store_true',
        help='List available endpoints and exit'
    )
    
    parser.add_argument(
        '--config-check',
        action='store_true',
        help='Check configuration and exit'
    )
    
    return parser.parse_args()


def create_config_from_args(args: argparse.Namespace) -> PumpMonitorConfig:
    """Create configuration from command-line arguments.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Configuration object with applied command-line overrides
    """
    config = PumpMonitorConfig()
    
    # Override config values from command line arguments
    if args.endpoint:
        config.endpoint = args.endpoint
    if args.api_token:
        config.api_token = args.api_token
    if args.server_url:
        config.server_url = args.server_url
    if args.quiet:
        config.quiet_mode = True
    if args.debug:
        config.enable_debug_logging = True
    if args.no_save:
        config.save_to_file = False
    if args.output_file:
        config.output_file = args.output_file
    if args.show_raw:
        config.show_raw_data = True
    
    return config


def validate_and_setup_config(config: PumpMonitorConfig) -> bool:
    """Validate and setup configuration.
    
    Args:
        config: Configuration object to validate
        
    Returns:
        True if configuration is valid, False otherwise
    """
    # Setup logging
    config.setup_logging()
    
    # Validate configuration
    issues = config.validate()
    if issues:
        print("🔧 Configuration Issues:")
        for issue in issues:
            print(f"   {issue}")
        print()
        print("📝 Solutions:")
        print("   • Edit config.py file")
        print("   • Or use command-line arguments:")
        print("     python main.py --api-token your_token_here")
        print()
        return False
    
    return True


def main():
    """Main function and application entry point."""
    try:
        # Display banner
        print_banner()
        
        # Parse command-line arguments
        args = parse_arguments()
        
        # Handle endpoint listing
        if args.list_endpoints:
            print_available_endpoints()
            return 0
        
        # Create configuration
        config = create_config_from_args(args)
        
        # Handle configuration check
        if args.config_check:
            print("🔍 Configuration Check:")
            config.print_summary()
            
            issues = config.validate()
            if issues:
                print("❌ Configuration Issues:")
                for issue in issues:
                    print(f"   {issue}")
                return 1
            else:
                print("✅ Configuration is valid!")
                return 0
        
        # Validate and setup configuration
        if not validate_and_setup_config(config):
            return 1
        
        # Print configuration summary
        config.print_summary()
        
        # Setup graceful shutdown
        shutdown_handler = GracefulShutdown()
        
        # Start monitor
        monitor = PumpMonitorClient(config)
        monitor.run_monitor(shutdown_handler=shutdown_handler)
        
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1
    
    print("✅ Monitor stopped gracefully")
    return 0


if __name__ == "__main__":
    sys.exit(main())