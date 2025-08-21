"""
Event Formatters Module

Provides formatting functionality for different event types received from the Pump.fun
real-time data stream. Converts raw JSON event data into human-readable formatted strings.
"""

import json
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class EventFormatter:
    """Event data formatting class.
    
    Provides static methods to format various event types (trades, new coins, 
    graduated tokens, etc.) into human-readable strings for console output.
    """
    
    @staticmethod
    def format_event(event_type: str, event_data: Dict[str, Any]) -> str:
        """Format event data for human-readable display.
        
        Args:
            event_type: Type of event to format
            event_data: Raw event data dictionary
            
        Returns:
            Formatted string representation of the event
        """
        try:
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            if event_type == "connected":
                conn_id = event_data.get("connection_id", "unknown")
                endpoint = event_data.get("endpoint", "unknown")
                return f"✅ [{timestamp}] Connected: {endpoint} (ID: {conn_id})"
            
            elif event_type == "ping":
                if isinstance(event_data, dict) and 'connections' in event_data:
                    return f"💗 [{timestamp}] Keepalive ping (connections: {event_data.get('connections', 0)})"
                return f"💗 [{timestamp}] Keepalive ping"
            
            elif event_type == "trade":
                return EventFormatter._format_trade(timestamp, event_data)
            
            elif event_type == "new_coin":
                return EventFormatter._format_new_coin(timestamp, event_data)
            
            elif event_type == "new_coin_detailed":
                return EventFormatter._format_new_coin_detailed(timestamp, event_data)
            
            elif event_type == "graduated":
                return EventFormatter._format_graduated(timestamp, event_data)
            
            elif event_type == "pump_trade":
                return EventFormatter._format_pump_trade(timestamp, event_data)
            
            else:
                return f"📨 [{timestamp}] {event_type}: {str(event_data)[:100]}..."
        
        except Exception as e:
            logger.error(f"Event formatting error: {e}")
            return f"❌ [{timestamp}] Format error: {str(e)[:50]}..."
    
    @staticmethod
    def _format_trade(timestamp: str, data: Dict) -> str:
        """Format trade event data.
        
        Args:
            timestamp: Event timestamp string
            data: Trade event data dictionary
            
        Returns:
            Formatted trade event string
        """
        try:
            # Expected format: {"data": [...], "event_type": "trade"}
            # Extract the data array
            if isinstance(data, dict) and 'data' in data:
                trade_array = data['data']
                if isinstance(trade_array, list) and len(trade_array) > 0:
                    trade = trade_array[0]  # Use first trade data
                else:
                    return f"📈 [{timestamp}] Trade: Empty data array"
            else:
                return f"📈 [{timestamp}] Trade: Invalid data format"
            
            # Extract trade information
            is_buy = trade.get('isBuy', True)
            sol_amount = trade.get('solAmount', '0')
            market_cap = trade.get('marketCap', '0')
            
            # Get ticker and name from updatedData
            updated_data = trade.get('updatedData', {})
            ticker = updated_data.get('ticker', 'UNKNOWN')
            name = updated_data.get('name', 'Unknown')
            
            # Format values
            try:
                sol_amount_num = abs(float(sol_amount)) if sol_amount else 0.0
                sol_amount = f"{sol_amount_num:.6f}"
            except (ValueError, TypeError):
                sol_amount = "0.000000"
            
            try:
                market_cap_num = float(market_cap) if market_cap else 0.0
                market_cap = f"${market_cap_num:,.2f}"
            except (ValueError, TypeError):
                market_cap = "$0.00"
            
            action = "🟢 BUY" if is_buy else "🔴 SELL"
            name_short = name[:20] + "..." if len(name) > 20 else name
            
            return f"{action} [{timestamp}] {ticker} ({name_short}) | 💰 {sol_amount} SOL | 💎 {market_cap}"
        except Exception as e:
            logger.error(f"Trade format error: {e}")
            return f"📈 [{timestamp}] Trade: Error - {str(e)[:50]}..."
    
    @staticmethod
    def _format_new_coin(timestamp: str, data: Dict) -> str:
        """Format new coin event data.
        
        Args:
            timestamp: Event timestamp string
            data: New coin event data dictionary
            
        Returns:
            Formatted new coin event string
        """
        try:
            # Handle wrapper format if present
            if isinstance(data, dict) and 'data' in data:
                coin_data = data['data']
            else:
                coin_data = data
            
            if not isinstance(coin_data, dict):
                return f"🪙 [{timestamp}] New Coin: Invalid data format"
            
            # Extract coin information
            name = coin_data.get('name', 'Unknown Token')
            ticker = coin_data.get('ticker', 'UNKNOWN')
            market_cap = coin_data.get('marketCap', 0)
            mint = coin_data.get('mint', 'N/A')
            
            # Format values
            try:
                market_cap_num = float(market_cap) if market_cap else 0.0
                market_cap_formatted = f"${market_cap_num:,.2f}"
            except (ValueError, TypeError):
                market_cap_formatted = "$0.00"
            
            # Truncate long strings
            mint_short = mint[:8] + "..." if len(mint) > 8 else mint
            name_short = name[:25] + "..." if len(name) > 25 else name
            
            return f"🪙 [{timestamp}] New Token: {ticker} ({name_short}) | 💎 {market_cap_formatted} | 🏠 {mint_short}"
        except Exception as e:
            logger.error(f"New coin format error: {e}")
            return f"🪙 [{timestamp}] New Coin: Error - {str(e)[:50]}..."
    
    @staticmethod
    def _format_new_coin_detailed(timestamp: str, data: Dict) -> str:
        """Format detailed new coin event data.
        
        Args:
            timestamp: Event timestamp string
            data: Detailed new coin event data dictionary
            
        Returns:
            Formatted detailed new coin event string
        """
        try:
            # Handle wrapper format if present
            if isinstance(data, dict) and 'data' in data:
                coin_data = data['data']
            else:
                coin_data = data
            
            if not isinstance(coin_data, dict):
                return f"🪙✨ [{timestamp}] Detailed New Coin: Invalid data format"
            
            # Extract basic information
            symbol = coin_data.get('symbol', 'UNKNOWN')
            name = coin_data.get('name', 'Unknown Token')
            market_cap = coin_data.get('usd_market_cap', coin_data.get('market_cap', 0))
            creator = coin_data.get('creator', 'N/A')
            
            # Extract social media information
            twitter = coin_data.get('twitter', '')
            website = coin_data.get('website', '')
            telegram = coin_data.get('telegram', '')
            
            # Extract supply information
            total_supply = coin_data.get('total_supply', 0)
            
            # Format values
            try:
                market_cap_num = float(market_cap) if market_cap else 0.0
                market_cap_formatted = f"${market_cap_num:,.2f}"
            except (ValueError, TypeError):
                market_cap_formatted = "$0.00"
            
            try:
                supply_formatted = f"{int(total_supply):,}" if total_supply else "N/A"
            except (ValueError, TypeError):
                supply_formatted = str(total_supply)
            
            # Truncate long strings
            creator_short = creator[:8] + "..." if len(creator) > 8 else creator
            name_short = name[:20] + "..." if len(name) > 20 else name
            
            # Social media icons
            socials = []
            if twitter: socials.append("🐦")
            if website: socials.append("🌐")
            if telegram: socials.append("💬")
            social_icons = "".join(socials) if socials else ""
            
            return f"🪙✨ [{timestamp}] {symbol} ({name_short}) | 💎 {market_cap_formatted} | 👤 {creator_short} | 📊 {supply_formatted} {social_icons}"
        except Exception as e:
            logger.error(f"Detailed new coin format error: {e}")
            return f"🪙✨ [{timestamp}] Detailed New Coin: Error - {str(e)[:50]}..."
    
    @staticmethod
    def _format_graduated(timestamp: str, data: Dict) -> str:
        """Format graduated coin event data.
        
        Args:
            timestamp: Event timestamp string
            data: Graduated coin event data dictionary
            
        Returns:
            Formatted graduated coin event string
        """
        try:
            # Handle wrapper format if present
            if isinstance(data, dict) and 'data' in data:
                coin_data = data['data']
            else:
                coin_data = data
            
            if not isinstance(coin_data, dict):
                return f"🎓 [{timestamp}] Graduated Coin: Invalid data format"
            
            # Extract basic information
            name = coin_data.get('name', 'Unknown Token')
            ticker = coin_data.get('ticker', 'UNKNOWN')
            market_cap = coin_data.get('marketCap', 0)
            ath_market_cap = coin_data.get('allTimeHighMarketCap', 0)
            num_holders = coin_data.get('numHolders', 0)
            sniper_count = coin_data.get('sniperCount', 0)
            volume = coin_data.get('volume', 0)
            
            # Format values
            try:
                market_cap_num = float(market_cap) if market_cap else 0.0
                market_cap_formatted = f"${market_cap_num:,.2f}"
                ath_num = float(ath_market_cap) if ath_market_cap else 0.0
                ath_formatted = f"${ath_num:,.2f}"
                volume_num = float(volume) if volume else 0.0
                volume_formatted = f"{volume_num:,.2f}"
            except (ValueError, TypeError):
                market_cap_formatted = "$0.00"
                ath_formatted = "$0.00"
                volume_formatted = "0.00"
            
            # Truncate long strings
            name_short = name[:20] + "..." if len(name) > 20 else name
            
            # Sniper warning
            sniper_warning = f"⚠️ {sniper_count} sniper" if sniper_count > 0 else ""
            
            return f"🎓 [{timestamp}] GRADUATED: {ticker} ({name_short}) | 💎 {market_cap_formatted} | 🏆 ATH: {ath_formatted} | 👥 {num_holders} | 📊 {volume_formatted} SOL {sniper_warning}"
        except Exception as e:
            logger.error(f"Graduated format error: {e}")
            return f"🎓 [{timestamp}] Graduated Coin: Error - {str(e)[:50]}..."
    
    @staticmethod
    def _format_pump_trade(timestamp: str, data: Dict) -> str:
        """Format PumpSwap trade event data.
        
        Args:
            timestamp: Event timestamp string
            data: PumpSwap trade event data dictionary
            
        Returns:
            Formatted PumpSwap trade event string
        """
        try:
            # Expected format: {"data": [...], "event_type": "pump_trade"}
            # Extract the data array
            if isinstance(data, dict) and 'data' in data:
                trade_array = data['data']
                if isinstance(trade_array, list) and len(trade_array) > 0:
                    trade = trade_array[0]  # Use first trade data
                else:
                    return f"🔄 [{timestamp}] PumpSwap: Empty data array"
            else:
                return f"🔄 [{timestamp}] PumpSwap: Invalid data format"
            
            # Extract trade information
            is_buy = trade.get('isBuy', True)
            sol_amount = trade.get('solAmount', '0')
            market_cap = trade.get('marketCap', '0')
            
            # Get ticker and name from updatedData
            updated_data = trade.get('updatedData', {})
            ticker = updated_data.get('ticker', 'UNKNOWN')
            name = updated_data.get('name', 'Unknown')
            volume = updated_data.get('volume', '0')
            
            # Format values
            try:
                sol_amount_num = abs(float(sol_amount)) if sol_amount else 0.0
                sol_amount = f"{sol_amount_num:.6f}"
            except (ValueError, TypeError):
                sol_amount = "0.000000"
            
            try:
                market_cap_num = float(market_cap) if market_cap else 0.0
                market_cap = f"${market_cap_num:,.2f}"
            except (ValueError, TypeError):
                market_cap = "$0.00"
            
            try:
                volume_num = float(volume) if volume else 0.0
                volume_formatted = f"{volume_num:,.2f}"
            except (ValueError, TypeError):
                volume_formatted = "0.00"
            
            action = "🟢 BUY" if is_buy else "🔴 SELL"
            name_short = name[:18] + "..." if len(name) > 18 else name
            
            return f"{action} [{timestamp}] 🔄 {ticker} ({name_short}) | 💰 {sol_amount} SOL | 💎 {market_cap} | 📊 {volume_formatted} VOL"
        except Exception as e:
            logger.error(f"Pump trade format error: {e}")
            return f"🔄 [{timestamp}] PumpSwap: Error - {str(e)[:50]}..."


def format_raw_data(event_name: str, data: Dict[str, Any], indent: int = 2) -> str:
    """Format raw event data for debug display.
    
    Args:
        event_name: Name of the event
        data: Raw event data dictionary
        indent: JSON indentation level
        
    Returns:
        Formatted raw data string
    """
    return f"📄 Raw Data ({event_name}): {json.dumps(data, ensure_ascii=False, indent=indent)}"