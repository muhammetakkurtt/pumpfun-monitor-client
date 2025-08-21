# Pump.fun Monitor - Python Client

**Python client for real-time Pump.fun trading data**

A comprehensive Python SSE (Server-Sent Events) client for connecting to the [Pump.fun Real-Time Monitor Apify Actor](https://apify.com/muhammetakkurtt/pump-fun-real-time-monitor). Monitor live Solana meme token events, new launches, graduations, and trading activity in real-time with minimal latency.

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![SSE](https://img.shields.io/badge/protocol-SSE-orange.svg)
![Real-time](https://img.shields.io/badge/streaming-real--time-red.svg)

## 🎯 Overview

This Python client provides a clean, interface to consume real-time Pump.fun events from the **Pump.fun Real-Time Monitor Apify Standby Actor**. The client handles connection management, automatic reconnection, event parsing, data formatting, and persistence - so you can focus on building your trading strategies.

### What is the Pump.fun Real-Time Monitor?

The [Pump.fun Real-Time Monitor](https://apify.com/muhammetakkurtt/pump-fun-real-time-monitor) is a high-performance Apify Standby Actor that streams live Solana meme token events from Pump.fun in real-time via Server-Sent Events. It provides sub-second event delivery for:

- 🪙 New token launches with complete metadata
- 🎓 Token graduations to Raydium
- 📈 Live trading activity (buy/sell transactions)
- 🔄 PumpSwap trades (Pump.fun's native DEX)

## ✨ Key Features

### 🚀 **Production Ready**
- **Automatic Reconnection**: Robust connection management with configurable retry logic
- **Health Monitoring**: Periodic health checks to ensure connection stability
- **Error Handling**: Comprehensive error handling and graceful degradation
- **Thread-Safe**: Safe for multi-threaded applications

### 📊 **Data Management**
- **Event Formatting**: Human-readable console output with emojis and colors
- **JSON Persistence**: Save events to JSON Lines files for analysis
- **Statistics Tracking**: Real-time performance metrics and connection stats
- **Raw Data Access**: Optional raw JSON data display for debugging

### ⚙️ **Flexible Configuration**
- **Multiple Endpoints**: Connect to specific event types or monitor everything
- **CLI Interface**: Full command-line interface with help and validation
- **Programmatic API**: Easy integration into Python applications
- **Environment Configs**: Externalized configuration for different environments

### 🎨 **User Experience**
- **Real-time Display**: Live formatted output with timestamps and market data
- **Quiet Mode**: Minimal output for production environments
- **Debug Mode**: Detailed logging for development and troubleshooting
- **Statistics Dashboard**: Regular performance and connection summaries

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- Apify API Token
- Access to Pump.fun Real-Time Monitor Standby Actor

### Quick Install

```bash
# Clone the repository
git clone https://github.com/muhammetakkurtt/pumpfun-monitor-client.git
cd pumpfun-monitor-client

# Install dependencies (only requests is required)
pip install requests

# Configure your API token
# Edit config.py and set your API_TOKEN
```

## 🔧 Configuration

### Basic Configuration

Edit `config.py` to configure your client:

```python
@dataclass
class PumpMonitorConfig:
    # Required: Your Apify API Token
    api_token: str = "apify_api_YOUR_TOKEN_HERE"
    
    # Standby Actor URL
    server_url: str = "https://muhammetakkurtt--pump-fun-real-time-monitor.apify.actor"
    
    # Endpoint selection (see Available Endpoints below)
    endpoint: str = "all"  # Monitor all events
    
    # Optional: Customize behavior
    save_to_file: bool = True          # Save events to JSON file
    quiet_mode: bool = False           # Minimal console output
    show_raw_data: bool = False        # Display raw JSON data
```

### Available Endpoints

Connect to different event streams based on your needs:

| Endpoint | Description | Events | Best For |
|----------|-------------|---------|----------|
| `all` | **All platform events** | All event types | Complete monitoring |
| `tokens/new` | **Basic new tokens** | `new_coin` | Fast new token detection |
| `tokens/new/detailed` | **Detailed new tokens** | `new_coin_detailed` | Complete token metadata |
| `tokens/graduated` | **Graduated tokens** | `graduated` | Raydium graduation tracking |
| `trades/pump` | **Pump trades** | `trade` | Bonding curve trading |
| `trades/pumpswap` | **PumpSwap trades** | `pump_trade` | DEX trading activity |

## 🚀 Quick Start

### 1. Command Line Usage

```bash
# Start monitoring with default settings
python main.py

# Monitor only new token launches
python main.py --endpoint tokens/new

# Quiet mode for production
python main.py --quiet

# Enable debug logging
python main.py --debug

# Check configuration
python main.py --config-check

# List all available endpoints
python main.py --list-endpoints
```

### 2. Programmatic Usage

```python
from pump_monitor import PumpMonitorConfig, PumpMonitorClient, GracefulShutdown

# Create configuration
config = PumpMonitorConfig(
    api_token="apify_api_YOUR_TOKEN_HERE",
    server_url="https://muhammetakkurtt--pump-fun-real-time-monitor.apify.actor",
    endpoint="all",
    quiet_mode=False
)

# Start monitoring
shutdown_handler = GracefulShutdown()
monitor = PumpMonitorClient(config)
monitor.run_monitor(shutdown_handler=shutdown_handler)
```

### 3. Quick Start Function

```python
from pump_monitor import quick_start

# Simplest usage
quick_start(api_token="apify_api_YOUR_TOKEN_HERE")

# With specific endpoint
quick_start(
    api_token="apify_api_YOUR_TOKEN_HERE",
    endpoint="tokens/new",
    quiet=False
)
```

## 📊 Event Examples

### New Token Launch
```
🪙 [19:28:15] New Token: DOGE (Moon Doge Token) | 💎 $5,432.10 | 🏠 EnXAsNu...
```

### Trading Activity
```
🟢 BUY [19:27:43] Cycle (The Cycle Never Stops) | 💰 0.535084 SOL | 💎 $11,765.88
🔴 SELL [19:27:44] ELDENDOG (ELDEN DOG) | 💰 0.089087 SOL | 💎 $24,844.01
```

### Token Graduation
```
🎓 [19:29:01] GRADUATED: DOGE (Doge Coin 2.0) | 💎 $85,432.10 | 🏆 ATH: $120,000.00 | 👥 156 | 📊 2,450.25 SOL
```

### PumpSwap Trading
```
🟢 BUY [19:27:43] 🔄 GARRY (The Internet's AI Punc...) | 💰 0.023149 SOL | 💎 $147,859.55 | 📊 81,757.79 VOL
```

### Statistics Summary
```
📊 Statistics:
   🕐 Uptime: 0:05:23
   📨 Total Events: 147
   ⚡ Average events/min: 27.2
   🔗 Active connections: 3
   📋 Event Types:
      trade: 89
      new_coin: 32
      graduated: 8
   📁 File size: 45,672 bytes
```

## 🛠️ Advanced Usage

### Custom Event Processing

```python
from pump_monitor import PumpMonitorClient, PumpMonitorConfig

class CustomMonitorClient(PumpMonitorClient):
    def handle_sse_event(self, event_name: str, data: dict):
        # Custom event processing
        if event_name == "new_coin":
            token_name = data.get('data', {}).get('name', 'Unknown')
            market_cap = data.get('data', {}).get('marketCap', 0)
            
            if market_cap > 10000:  # Only process high-value tokens
                print(f"🚨 High-value token detected: {token_name} (${market_cap:,.2f})")
                # Your custom logic here
        
        # Call parent handler for standard processing
        super().handle_sse_event(event_name, data)

# Use custom client
config = PumpMonitorConfig(api_token="your_token")
custom_monitor = CustomMonitorClient(config)
custom_monitor.run_monitor()
```

## 🔍 Data Structure

### Event Wrapper Format
All events follow this structure:
```json
{
  "data": { /* Event-specific data */ },
  "event_type": "new_coin|trade|graduated|pump_trade|new_coin_detailed"
}
```

## 📋 Command Line Options

```bash
Usage: python main.py [options]

Options:
  -h, --help              Show help message
  -e, --endpoint ENDPOINT Endpoint to monitor (default: all)
  -t, --api-token TOKEN   Apify API token
  -s, --server-url URL    Standby server URL
  -q, --quiet             Quiet mode (errors and stats only)
  --debug                 Enable debug logging
  --no-save               Disable file logging
  -o, --output-file FILE  Output filename
  --show-raw              Show raw JSON data
  --list-endpoints        List available endpoints
  --config-check          Validate configuration
```

### Health Monitoring

The client automatically performs health checks every 4 minutes. Monitor the output for:

```
🟢 Server Status: Connected=true, Total Connections=23, Messages Processed=125847
```

If health checks fail:
```
⚠️ Health check failed - retrying connection
```
