"""
Pump.fun Monitor Package

Python SSE Client for Pump.fun Real-time Trading Data Monitoring

This package provides a comprehensive solution for monitoring real-time trading data
from Pump.fun via Server-Sent Events (SSE) protocol. Features include automatic
reconnection, event formatting, statistics tracking, and data persistence.
"""

__version__ = "1.0.0"
__author__ = "Muhammet Akkurt"
__description__ = "Real-time Pump.fun trading data monitor via SSE"

# Export main classes for public API
from .config import PumpMonitorConfig, print_available_endpoints
from .client import PumpMonitorClient, SSEClient, GracefulShutdown
from .formatters import EventFormatter, format_raw_data

# Convenience imports
from .main import main

__all__ = [
    'PumpMonitorConfig',
    'PumpMonitorClient', 
    'SSEClient',
    'EventFormatter',
    'GracefulShutdown',
    'main',
    'print_available_endpoints',
    'format_raw_data'
]


def quick_start(api_token: str, endpoint: str = "all", quiet: bool = False):
    """Quick start function for programmatic usage.
    
    Provides a simple way to start monitoring without manual configuration setup.
    
    Args:
        api_token: Apify API token for authentication
        endpoint: Endpoint to monitor (default: "all")
        quiet: Enable quiet mode (default: False)
        
    Example:
        >>> from pump_monitor import quick_start
        >>> quick_start(api_token="your_token_here")
    """
    config = PumpMonitorConfig(
        api_token=api_token,
        endpoint=endpoint,
        quiet_mode=quiet
    )
    
    if not config.is_valid():
        issues = config.validate()
        print("❌ Configuration issues:")
        for issue in issues:
            print(f"   {issue}")
        return
    
    config.setup_logging()
    
    shutdown_handler = GracefulShutdown()
    monitor = PumpMonitorClient(config)
    monitor.run_monitor(shutdown_handler=shutdown_handler)