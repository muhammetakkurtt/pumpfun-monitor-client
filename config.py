"""
Pump Monitor Configuration Module

This module contains configuration classes and validation logic for the Pump Monitor client.
"""

from dataclasses import dataclass
from typing import Optional, List
import logging

@dataclass
class PumpMonitorConfig:
    """Configuration class for Pump Monitor client.
    
    Contains all configuration parameters required for connecting to and monitoring
    the Pump.fun real-time data stream via Server-Sent Events.
    """
    
    # Server Configuration
    server_url: str = "https://muhammetakkurtt--pump-fun-real-time-monitor.apify.actor"
    api_token: str = "YOUR_API_TOKEN"
    endpoint: str = "all"
    
    # Connection Configuration
    connection_timeout: int = 15          # Initial connection timeout in seconds
    read_timeout: Optional[int] = None    # SSE read timeout (None = unlimited)
    stream_timeout: int = 180             # Data stream timeout in seconds
    reconnect_delay: int = 3              # Delay between reconnection attempts in seconds
    max_retries: int = 10                 # Maximum number of connection retry attempts
    health_check_interval: int = 240      # Health check interval in seconds
    
    # Display Configuration
    show_detailed_logs: bool = True       # Display detailed event information
    show_stats_interval: int = 60         # Statistics display interval in seconds
    quiet_mode: bool = False              # Quiet mode - only errors and statistics
    show_raw_data: bool = False           # Display raw JSON data for debugging
    
    # Data Persistence Configuration
    save_to_file: bool = True             # Enable data persistence to JSON file
    output_file: Optional[str] = None     # Output filename (auto-generated if None)
    
    # Logging Configuration
    enable_debug_logging: bool = False    # Enable detailed debug logging
    
    def __post_init__(self):
        """Post-initialization configuration setup.
        
        Automatically generates output filename if not specified.
        """
        if self.output_file is None:
            endpoint_safe = self.endpoint.replace('/', '_')
            self.output_file = f"pump_data_{endpoint_safe}.jsonl"
    
    def validate(self) -> List[str]:
        """Validate configuration parameters.
        
        Returns:
            List of validation error messages. Empty list indicates valid configuration.
        """
        issues = []
        
        if not self.api_token.strip():
            issues.append("ERROR: API_TOKEN is empty. Please configure your Apify API token.")
        
        if not self.server_url.strip():
            issues.append("ERROR: SERVER_URL is empty. Please configure the Standby server URL.")
        
        if not self.server_url.startswith(('http://', 'https://')):
            issues.append("WARNING: SERVER_URL should start with http:// or https://")
        
        valid_endpoints = ["all", "tokens/new", "tokens/new/detailed", 
                          "tokens/graduated", "trades/pump", "trades/pumpswap"]
        if self.endpoint not in valid_endpoints:
            issues.append(f"ERROR: Invalid endpoint. Valid values: {valid_endpoints}")
        
        if self.connection_timeout < 5:
            issues.append("WARNING: CONNECTION_TIMEOUT is too low. Minimum recommended: 5 seconds")
        
        return issues
    
    def is_valid(self) -> bool:
        """Check if configuration is valid.
        
        Returns:
            True if configuration is valid, False otherwise.
        """
        return len(self.validate()) == 0
    
    def setup_logging(self):
        """Configure logging based on debug settings."""
        level = logging.DEBUG if self.enable_debug_logging else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
    
    def print_summary(self):
        """Print configuration summary."""
        print("📋 Configuration Summary:")
        print(f"   📡 Server: {self.server_url}")
        print(f"   🔐 API Token: {'✓ Configured' if self.api_token else '❌ Missing'}")
        print(f"   🎯 Endpoint: /{self.endpoint}")
        print(f"   ⏱️ Timeout: {self.connection_timeout}s")
        print("   🌊 Mode: Server-Sent Events (SSE)")
        
        if self.save_to_file:
            print(f"   📁 Data logging: {self.output_file}")
        else:
            print("   📁 Data logging: Disabled")
        
        if self.quiet_mode:
            print("   🔇 Quiet mode: Enabled")
        
        if self.show_raw_data:
            print("   📄 Raw data display: Enabled")
        
        print("-" * 70)


# Available endpoint configurations
ENDPOINT_DESCRIPTIONS = {
    "all": "Retrieve all event types",
    "tokens/new": "New token events only",
    "tokens/new/detailed": "Detailed new token information",
    "tokens/graduated": "Graduated token events",
    "trades/pump": "Pump trading events",
    "trades/pumpswap": "PumpSwap trading events"
}

def print_available_endpoints():
    """Print available endpoint configurations."""
    print("🎯 Available Endpoints:")
    for endpoint, description in ENDPOINT_DESCRIPTIONS.items():
        print(f"   • {endpoint} - {description}")
    print()
