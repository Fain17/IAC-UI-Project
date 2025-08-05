import asyncio
import logging
from fastapi import WebSocket
from datetime import datetime, timezone
from app.auth.service import auth_service

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self.websocket: WebSocket = None
        self.monitoring_task: asyncio.Task = None
        self.warning_sent: bool = False
        self._disconnecting: bool = False
    
    async def connect(self, websocket: WebSocket, token: str):
        """Connect to WebSocket and start monitoring."""
        # Disconnect any existing connection first
        if self.websocket:
            await self.disconnect()
        
        self.websocket = websocket
        self.warning_sent = False
        self._disconnecting = False
        
        # Start monitoring task
        self.monitoring_task = asyncio.create_task(
            self.monitor_token(token)
        )
    
    async def disconnect(self):
        """Disconnect from WebSocket."""
        if self._disconnecting:
            return  # Already disconnecting
        
        self._disconnecting = True
        
        # Cancel monitoring task first
        if self.monitoring_task and not self.monitoring_task.done():
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
        
        # Close WebSocket connection
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.debug(f"Error closing WebSocket: {e}")
            finally:
                self.websocket = None
        
        self.warning_sent = False
        self._disconnecting = False
    
    def calculate_sleep_time(self, time_remaining: int) -> int:
        """Calculate smart sleep time based on token expiration."""
        if time_remaining <= 0:
            return 1  # Check immediately if expired
        
        # Smart timing strategy:
        # - If > 10 minutes: check every 5 minutes
        # - If 5-10 minutes: check every 2 minutes  
        # - If 2-5 minutes: check every 1 minute
        # - If 1-2 minutes: check every 30 seconds
        # - If < 1 minute: check every 10 seconds
        # - If < 60 seconds: check every 5 seconds
        
        if time_remaining > 600:  # > 10 minutes
            return 300  # 5 minutes
        elif time_remaining > 300:  # 5-10 minutes
            return 120  # 2 minutes
        elif time_remaining > 120:  # 2-5 minutes
            return 60   # 1 minute
        elif time_remaining > 60:   # 1-2 minutes
            return 30   # 30 seconds
        elif time_remaining > 10:   # 10 seconds - 1 minute
            return 10   # 10 seconds
        else:  # < 10 seconds
            return 5    # 5 seconds
    
    async def monitor_token(self, token: str):
        """Monitor token and send warning when below 60 seconds."""
        try:
            while True:
                # Check if connection is still active
                if not self.websocket or self._disconnecting:
                    break
                
                # Get session info
                session_info = await auth_service.get_session_info_for_token(token)
                
                if not session_info:
                    break
                
                time_remaining = session_info.get("time_remaining_seconds", 0)
                
                # Check if token is below 60 seconds and warning not sent yet
                if time_remaining <= 60 and not self.warning_sent:
                    # Send single warning message
                    message = {
                        "call_refresh": True,
                        "time_remaining_seconds": time_remaining,
                        "message": "Token expires soon, please refresh"
                    }
                    
                    await self.send_message(message)
                    self.warning_sent = True  # Mark warning as sent
                    break  # Stop monitoring after sending warning
                
                # Calculate smart sleep time based on remaining time
                sleep_time = self.calculate_sleep_time(time_remaining)
                
                # Log monitoring info for debugging (optional)
                if time_remaining > 0:
                    logger.debug(f"Token: {time_remaining}s remaining, checking again in {sleep_time}s")
                
                # Sleep with smart timing
                await asyncio.sleep(sleep_time)
                
        except asyncio.CancelledError:
            logger.debug("Token monitoring task cancelled")
        except Exception as e:
            logger.error(f"Error monitoring token: {e}")
        finally:
            # Clean up if not already done
            if self.websocket and not self._disconnecting:
                await self.disconnect()
    
    async def send_message(self, message: dict):
        """Send message to WebSocket."""
        if self.websocket and not self._disconnecting:
            try:
                await self.websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                await self.disconnect()
    
    def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self.websocket is not None and not self._disconnecting

# Global WebSocket manager instance
websocket_manager = WebSocketManager() 