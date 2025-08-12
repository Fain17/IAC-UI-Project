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
        logger.info("WebSocket manager: Connecting new WebSocket")
        # Disconnect any existing connection first
        if self.websocket:
            logger.info("WebSocket manager: Disconnecting existing connection")
            await self.disconnect()
        
        self.websocket = websocket
        self.warning_sent = False
        self._disconnecting = False
        
        # Start monitoring task
        self.monitoring_task = asyncio.create_task(
            self.monitor_token(token)
        )
        logger.info("WebSocket manager: Connection established and monitoring started")
    
    async def disconnect(self):
        """Disconnect from WebSocket."""
        if self._disconnecting:
            logger.debug("WebSocket manager: Already disconnecting, skipping")
            return  # Already disconnecting
        
        logger.info("WebSocket manager: Starting disconnection")
        self._disconnecting = True
        
        # Cancel monitoring task first
        if self.monitoring_task and not self.monitoring_task.done():
            logger.debug("WebSocket manager: Cancelling monitoring task")
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
        
        # Close WebSocket connection
        if self.websocket:
            try:
                logger.debug("WebSocket manager: Closing WebSocket connection")
                await self.websocket.close()
            except Exception as e:
                logger.debug(f"Error closing WebSocket: {e}")
            finally:
                self.websocket = None
        
        self.warning_sent = False
        self._disconnecting = False
        logger.info("WebSocket manager: Disconnection completed")
    
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
        """Monitor JWT token and send warning when below 60 seconds."""
        try:
            logger.info(f"Starting token monitoring for token: {token[:20]}...")
            while True:
                # Check if connection is still active
                if not self.websocket or self._disconnecting:
                    logger.info("WebSocket connection lost or disconnecting, stopping monitoring")
                    break
                
                # Decode JWT token to get expiration time
                try:
                    from jose import jwt
                    from app.config import SECRET_KEY, ALGORITHM
                    
                    # Decode JWT token without verification (we already verified it in the route)
                    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                    exp_timestamp = payload.get("exp")
                    
                    if not exp_timestamp:
                        logger.warning("JWT token has no expiration time, stopping monitoring")
                        break
                    
                    # Calculate time remaining
                    current_time = datetime.now().timestamp()
                    time_remaining = int(exp_timestamp - current_time)
                    
                    logger.debug(f"Token monitoring: {time_remaining}s remaining")
                    
                    # Check if token is below 60 seconds and warning not sent yet
                    if time_remaining <= 60 and not self.warning_sent:
                        # Send single warning message
                        message = {
                            "call_refresh": True,
                            "time_remaining_seconds": time_remaining,
                            "message": "Token expires soon, please refresh"
                        }
                        
                        logger.info(f"Sending token expiration warning: {time_remaining}s remaining")
                        await self.send_message(message)
                        self.warning_sent = True  # Mark warning as sent
                        break  # Stop monitoring after sending warning
                    
                    # If token is expired, stop monitoring
                    if time_remaining <= 0:
                        logger.info("Token has expired, stopping monitoring")
                        break
                    
                    # Calculate smart sleep time based on remaining time
                    sleep_time = self.calculate_sleep_time(time_remaining)
                    
                    # Log monitoring info for debugging (optional)
                    if time_remaining > 0:
                        logger.debug(f"Token: {time_remaining}s remaining, checking again in {sleep_time}s")
                    
                    # Sleep with smart timing
                    await asyncio.sleep(sleep_time)
                    
                except Exception as jwt_error:
                    logger.error(f"Error decoding JWT token: {jwt_error}")
                    break
                
        except asyncio.CancelledError:
            logger.debug("Token monitoring task cancelled")
        except Exception as e:
            logger.error(f"Error monitoring token: {e}")
        finally:
            logger.info("Token monitoring task ended")
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