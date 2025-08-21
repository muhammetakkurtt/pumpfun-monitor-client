"""
SSE Client and Monitor Logic

Core client classes for connecting to and monitoring the Pump.fun real-time data stream.
Provides SSE connection management, event handling, statistics tracking, and file operations.
"""

import json
import time
import requests
import threading
import signal
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from urllib.parse import urljoin

from config import PumpMonitorConfig
from formatters import EventFormatter, format_raw_data

logger = logging.getLogger(__name__)


class FileManager:
    """File operations manager for event data persistence.
    
    Handles saving events to JSON Lines format files with thread-safe operations.
    """
    
    def __init__(self, output_file: str):
        """Initialize file manager.
        
        Args:
            output_file: Path to the output file for event storage
        """
        self.output_file = output_file
        self.lock = threading.Lock()
        
    def save_event(self, event_type: str, event_data: Dict) -> bool:
        """Save event to file in JSON Lines format.
        
        Args:
            event_type: Type of event to save
            event_data: Event data dictionary
            
        Returns:
            True if save was successful, False otherwise
        """
        if not event_data:
            return True
            
        try:
            with self.lock:
                record = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "event_type": event_type,
                    "data": event_data
                }
                
                with open(self.output_file, 'a', encoding='utf-8') as f:
                    json.dump(record, f, ensure_ascii=False)
                    f.write('\n')
            return True
        except Exception as e:
            logger.error(f"File save error: {e}")
            return False
    
    def get_file_size(self) -> int:
        """Get output file size in bytes.
        
        Returns:
            File size in bytes, or 0 if file doesn't exist
        """
        try:
            import os
            return os.path.getsize(self.output_file) if os.path.exists(self.output_file) else 0
        except:
            return 0


class StatsManager:
    """Statistics tracking and reporting manager.
    
    Tracks event counts, connection statistics, and performance metrics.
    """
    
    def __init__(self):
        """Initialize statistics manager."""
        self.total_events = 0
        self.event_counts = {}  # event_type -> count
        self.connections = 0
        self.start_time = datetime.now()
        self.lock = threading.Lock()
        
    def add_event(self, event_type: str):
        """Add event to statistics.
        
        Args:
            event_type: Type of event to record
        """
        with self.lock:
            self.total_events += 1
            self.event_counts[event_type] = self.event_counts.get(event_type, 0) + 1
            
    def update_connection_count(self, count: int):
        """Update connection count from server data.
        
        Args:
            count: Current number of connections
        """
        with self.lock:
            self.connections = count
    
    def get_uptime(self) -> datetime:
        """Get monitoring uptime duration.
        
        Returns:
            Timedelta representing uptime
        """
        return datetime.now() - self.start_time
    
    def get_avg_per_minute(self) -> float:
        """Calculate average events per minute.
        
        Returns:
            Average events per minute
        """
        uptime_minutes = max(self.get_uptime().total_seconds() / 60, 1)
        return self.total_events / uptime_minutes
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics summary.
        
        Returns:
            Dictionary containing current statistics
        """
        with self.lock:
            uptime = self.get_uptime()
            events_per_min = self.get_avg_per_minute()
            
            return {
                "uptime": str(uptime).split('.')[0],  # Remove microseconds
                "total_events": self.total_events,
                "events_per_min": round(events_per_min, 1),
                "connections": self.connections,
                "event_breakdown": dict(self.event_counts)
            }


class SSEClient:
    """Server-Sent Events client for real-time data streaming.
    
    Manages connection to the Pump.fun Standby server via SSE protocol,
    handles authentication, health checks, and stream parsing.
    """
    
    def __init__(self, config: PumpMonitorConfig):
        """Initialize SSE client.
        
        Args:
            config: Configuration object containing connection parameters
        """
        self.config = config
        self.server_url = config.server_url.rstrip('/')
        self.endpoint = config.endpoint
        self.api_token = config.api_token
        
        # Build URLs
        self.events_url = urljoin(f"{self.server_url}/", f"events/{self.endpoint}")
        self.health_url = urljoin(f"{self.server_url}/", "health")
        
        # Connection state
        self.connection_id: Optional[str] = None
        self.last_data_time = time.time()
        self.last_health_check = None
        self.connected = False
        
        # HTTP session setup
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_token}',
            'Accept': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        })
        
    def check_server_health(self) -> bool:
        """Perform server health check.
        
        Returns:
            True if server is healthy, False otherwise
        """
        try:
            response = self.session.get(self.health_url, timeout=10)
            response.raise_for_status()
            
            health_data = response.json()
            if not self.config.quiet_mode:
                connected = health_data.get('connected', False)
                total_conns = health_data.get('connections', {}).get('total', 0)
                processed = health_data.get('messages_processed', 0)
                
                status = "🟢" if connected else "🟡"
                print(f"{status} Server Status: Connected={connected}, Total Connections={total_conns}, Messages Processed={processed}")
            
            return True
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return False
    
    def needs_health_check(self) -> bool:
        """Check if periodic health check is due.
        
        Returns:
            True if health check should be performed
        """
        if not self.last_health_check:
            return True
        
        time_since_health_check = time.time() - self.last_health_check
        return time_since_health_check > self.config.health_check_interval
    
    def perform_health_check(self) -> bool:
        """Perform background health check without blocking main stream.
        
        Returns:
            True if health check successful, False otherwise
        """
        try:
            # Use separate session to avoid interfering with main SSE session
            health_session = requests.Session()
            health_session.headers.update({
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json'
            })
            
            response = health_session.get(self.health_url, timeout=5)
            response.raise_for_status()
            
            self.last_health_check = time.time()
            logger.debug("Health check successful")
            return True
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False
    
    def connect_stream(self) -> Optional[requests.Response]:
        """Establish SSE stream connection.
        
        Returns:
            Response object for streaming, or None if connection failed
        """
        try:
            response = self.session.get(
                self.events_url,
                stream=True,
                timeout=(self.config.connection_timeout, self.config.read_timeout)
            )
            response.raise_for_status()
            
            self.connected = True
            current_time = time.time()
            self.last_data_time = current_time
            self.last_health_check = current_time  # Set initial health check timer
            return response
            
        except requests.RequestException as e:
            self.connected = False
            logger.error(f"SSE connection error: {e}")
            return None
    
    def is_connection_stale(self) -> bool:
        """Check if connection appears to be stale or dead.
        
        Returns:
            True if connection is stale and should be reconnected
        """
        current_time = time.time()
        
        if (current_time - self.last_data_time) > self.config.stream_timeout:
            logger.warning(f"Stream timeout: {current_time - self.last_data_time:.1f}s without data")
            return True
        
        return False
    
    def update_data_time(self):
        """Update timestamp of last received data."""
        self.last_data_time = time.time()
    
    def parse_sse_line(self, line: str) -> Optional[Dict]:
        """Parse a single SSE protocol line.
        
        Args:
            line: Raw SSE line to parse
            
        Returns:
            Parsed line data dictionary, or None if invalid
        """
        if not line or line.startswith(':'):
            return None
            
        try:
            if line.startswith('event: '):
                return {'type': 'event', 'event': line[7:].strip()}
            elif line.startswith('data: '):
                data_str = line[6:].strip()
                
                try:
                    data = json.loads(data_str)
                    return {'type': 'data', 'data': data}
                except json.JSONDecodeError:
                    return {'type': 'data', 'data': {'message': data_str, 'is_text': True}}
            elif line.startswith('id: '):
                return {'type': 'id', 'id': line[4:].strip()}
                
        except Exception as e:
            logger.error(f"SSE line parsing error: {e}")
            return None
        
        return None
    
    def listen_stream(self, response: requests.Response):
        """Listen to SSE stream and yield parsed events.
        
        Args:
            response: SSE stream response object
            
        Yields:
            Parsed event dictionaries
        """
        current_event = None
        
        try:
            for line in response.iter_lines(decode_unicode=True):
                if line is None:
                    continue
                
                parsed = self.parse_sse_line(line)
                if parsed is None:
                    # Empty line indicates end of event
                    if current_event:
                        yield current_event
                        current_event = None
                    continue
                
                if parsed['type'] == 'event':
                    current_event = {'event': parsed['event']}
                elif parsed['type'] == 'data' and current_event:
                    current_event['data'] = parsed['data']
                elif parsed['type'] == 'id' and current_event:
                    current_event['id'] = parsed['id']
                    
        except Exception as e:
            logger.error(f"SSE stream error: {e}")
            self.connected = False


class PumpMonitorClient:
    """Main monitoring client orchestrator.
    
    Coordinates SSE connection, event formatting, statistics tracking,
    and file operations to provide complete monitoring functionality.
    """
    
    def __init__(self, config: PumpMonitorConfig):
        """Initialize monitoring client.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.sse_client = SSEClient(config)
        self.formatter = EventFormatter()
        self.stats_manager = StatsManager()
        
        # File manager (optional)
        self.file_manager = FileManager(config.output_file) if config.save_to_file else None
        
        self.running = True
        
        if config.save_to_file:
            print(f"📁 Data will be saved to '{config.output_file}'")
    
    def handle_sse_event(self, event_name: str, data: Dict[str, Any]):
        """Process received SSE event.
        
        Args:
            event_name: Name/type of the event
            data: Event data dictionary
        """
        try:
            # Update data timing
            self.sse_client.update_data_time()
            
            if event_name == "connected":
                self.sse_client.connection_id = data.get("connection_id")
                endpoint = data.get("endpoint", "unknown")
                
                if not self.config.quiet_mode:
                    print(f"✅ Connected: {endpoint} endpoint (ID: {self.sse_client.connection_id})")
            
            elif event_name == "ping":
                if self.config.enable_debug_logging:
                    logger.debug("Keepalive ping received")
                return  # Don't add pings to statistics
            
            else:
                # Add event to statistics
                self.stats_manager.add_event(event_name)
                
                # Display raw data for debugging
                if self.config.show_raw_data and not self.config.quiet_mode:
                    print(format_raw_data(event_name, data))
                
                # Display formatted event
                if self.config.show_detailed_logs and not self.config.quiet_mode:
                    formatted_event = self.formatter.format_event(event_name, data)
                    print(formatted_event)
                
                # Save to file
                if self.file_manager:
                    self.file_manager.save_event(event_name, data)
            
        except Exception as e:
            logger.error(f"Event processing error: {e}", exc_info=True)
    
    def print_stats(self):
        """Print current statistics summary."""
        stats = self.stats_manager.get_stats()
        
        print(f"\n📊 Statistics:")
        print(f"   🕐 Uptime: {stats['uptime']}")
        print(f"   📨 Total Events: {stats['total_events']}")
        print(f"   ⚡ Average events/min: {stats['events_per_min']}")
        print(f"   🔗 Active connections: {stats['connections']}")
        
        # Event type breakdown
        if stats['event_breakdown']:
            print(f"   📋 Event Types:")
            for event_type, count in stats['event_breakdown'].items():
                print(f"      {event_type}: {count}")
        
        if self.file_manager:
            file_size = self.file_manager.get_file_size()
            if file_size > 0:
                print(f"   📁 File size: {file_size:,} bytes")
        
        print("-" * 80)
    
    def run_monitor(self, shutdown_handler=None):
        """Start monitoring process.
        
        Args:
            shutdown_handler: Optional graceful shutdown handler
        """
        print("🚀 Starting Pump Monitor Client...")
        print(f"🎯 Target endpoint: /{self.config.endpoint}")
        print(f"📡 Server URL: {self.sse_client.server_url}")
        
        # Initial health check
        if not self.sse_client.check_server_health():
            print("❌ Cannot connect to server or server is not responding")
            return
        
        print("🌊 Establishing SSE stream connection...")
        print("=" * 80)
        
        self._run_sse_monitor(shutdown_handler)
    
    def _run_sse_monitor(self, shutdown_handler=None):
        """Execute SSE monitoring loop.
        
        Args:
            shutdown_handler: Optional graceful shutdown handler
        """
        connection_attempts = 0
        last_stats_time = time.time()
        
        try:
            while self.running:
                # Check for shutdown request
                if shutdown_handler and shutdown_handler.should_shutdown():
                    print("🛑 Shutdown requested - stopping monitor")
                    break
                
                # Connect to SSE stream
                response = self.sse_client.connect_stream()
                if not response:
                    connection_attempts += 1
                    if connection_attempts >= self.config.max_retries:
                        print(f"❌ Failed to connect after {self.config.max_retries} attempts")
                        break
                    
                    if not self.config.quiet_mode:
                        print(f"🔄 Retrying in {self.config.reconnect_delay} seconds... ({connection_attempts}/{self.config.max_retries})")
                    time.sleep(self.config.reconnect_delay)
                    continue
                
                # Successful connection
                connection_attempts = 0
                
                if not self.config.quiet_mode:
                    print("🌊 SSE stream connected! Listening for real-time data...")
                
                try:
                    # Listen to SSE stream
                    for event in self.sse_client.listen_stream(response):
                        # Check for shutdown request
                        if shutdown_handler and shutdown_handler.should_shutdown():
                            print("🛑 Shutdown requested during streaming")
                            return
                        
                        # Check connection staleness
                        if self.sse_client.is_connection_stale():
                            if not self.config.quiet_mode:
                                print("⚠️ Connection appears stale - reconnecting")
                            break
                        
                        # Perform periodic health check
                        if self.sse_client.needs_health_check():
                            if not self.sse_client.perform_health_check():
                                logger.warning("Health check failed - connection may be stale")
                                if not self.config.quiet_mode:
                                    print("⚠️ Health check failed - retrying connection")
                                break
                        
                        # Process event
                        event_name = event.get('event')
                        event_data = event.get('data', {})
                        
                        if event_name:
                            self.handle_sse_event(event_name, event_data)
                        
                        # Display statistics periodically
                        current_time = time.time()
                        if current_time - last_stats_time >= self.config.show_stats_interval:
                            self.print_stats()
                            last_stats_time = current_time
                            
                except Exception as stream_error:
                    logger.warning(f"Stream error: {stream_error}")
                    if not self.config.quiet_mode:
                        print(f"⚠️ Stream error: {stream_error}")
                        print(f"🔄 Reconnecting in {self.config.reconnect_delay} seconds...")
                    time.sleep(self.config.reconnect_delay)
                    continue
                    
        except KeyboardInterrupt:
            print(f"\n\n⏹️ Stopped by user...")
            self.print_stats()
        except Exception as e:
            logger.error(f"Monitor error: {e}")
            print(f"\n❌ Unexpected error: {e}")


class GracefulShutdown:
    """Graceful shutdown signal handler.
    
    Handles SIGINT and SIGTERM signals to allow clean application shutdown.
    """
    
    def __init__(self):
        """Initialize signal handlers."""
        self.shutdown_requested = False
        signal.signal(signal.SIGINT, self._signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        print(f"\n🛑 Shutdown requested (signal {signum})")
        self.shutdown_requested = True
    
    def should_shutdown(self) -> bool:
        """Check if shutdown was requested.
        
        Returns:
            True if shutdown was requested
        """
        return self.shutdown_requested