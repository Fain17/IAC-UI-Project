import asyncio
import logging
from fastapi import WebSocket
from datetime import datetime, timezone
from app.auth.service import auth_service

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        # Support multiple connections per user
        self.user_connections: dict = {}  # user_id -> list of WebSocket connections
        self.connection_tasks: dict = {}  # connection_id -> monitoring task
        self.warning_sent: dict = {}  # connection_id -> warning status
        self._disconnecting: set = set()  # Set of disconnecting connection IDs
    
    async def connect(self, websocket: WebSocket, token: str):
        """Connect to WebSocket and start monitoring."""
        try:
            # Verify token to get user_id
            from jose import jwt
            from app.config import SECRET_KEY, ALGORITHM
            
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            
            if not user_id:
                logger.error("WebSocket manager: Invalid token, no user_id")
                await websocket.close(code=4001, reason="Invalid token")
                return
            
            # Generate unique connection ID
            import uuid
            connection_id = str(uuid.uuid4())
            
            logger.info(f"WebSocket manager: Connecting new WebSocket for user {user_id}, connection {connection_id}")
            
            # Initialize user connections list if needed
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            
            # Add connection to user's connection list
            connection_info = {
                "websocket": websocket,
                "connection_id": connection_id,
                "user_id": user_id,
                "token": token
            }
            self.user_connections[user_id].append(connection_info)
            
            # Initialize warning status for this connection
            self.warning_sent[connection_id] = False
            
            # Start monitoring task for this specific connection
            monitoring_task = asyncio.create_task(
                self.monitor_token(connection_id, token)
            )
            self.connection_tasks[connection_id] = monitoring_task
            
            logger.info(f"WebSocket manager: Connection {connection_id} established for user {user_id}")
            
        except Exception as e:
            logger.error(f"WebSocket manager: Connection error: {e}")
            try:
                await websocket.close(code=4000, reason="Connection error")
            except Exception:
                pass
    
    async def disconnect(self, connection_id: str = None):
        """Disconnect a specific WebSocket connection."""
        if connection_id and connection_id in self._disconnecting:
            logger.debug(f"WebSocket manager: Connection {connection_id} already disconnecting, skipping")
            return
        
        if connection_id:
            await self._disconnect_connection(connection_id)
        else:
            # Disconnect all connections (for backward compatibility)
            logger.warning("WebSocket manager: Disconnect called without connection_id, disconnecting all")
            for user_id in list(self.user_connections.keys()):
                for conn_info in list(self.user_connections[user_id]):
                    await self._disconnect_connection(conn_info["connection_id"])
    
    async def _disconnect_connection(self, connection_id: str):
        """Disconnect a specific connection."""
        logger.info(f"WebSocket manager: Starting disconnection for connection {connection_id}")
        self._disconnecting.add(connection_id)
        
        try:
            # Cancel monitoring task
            if connection_id in self.connection_tasks:
                task = self.connection_tasks[connection_id]
                if not task.done():
                    logger.debug(f"WebSocket manager: Cancelling monitoring task for {connection_id}")
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                del self.connection_tasks[connection_id]
            
            # Find and remove connection from user_connections
            for user_id in list(self.user_connections.keys()):
                self.user_connections[user_id] = [
                    conn for conn in self.user_connections[user_id] 
                    if conn["connection_id"] != connection_id
                ]
                
                # Remove user if no more connections
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            # Clean up connection-specific data
            if connection_id in self.warning_sent:
                del self.warning_sent[connection_id]
            
            logger.info(f"WebSocket manager: Disconnection completed for {connection_id}")
            
        except Exception as e:
            logger.error(f"WebSocket manager: Error during disconnection of {connection_id}: {e}")
        finally:
            self._disconnecting.discard(connection_id)
    
    async def disconnect_user(self, user_id: str):
        """Disconnect all connections for a specific user."""
        logger.info(f"WebSocket manager: Disconnecting all connections for user {user_id}")
        if user_id in self.user_connections:
            for conn_info in list(self.user_connections[user_id]):
                await self._disconnect_connection(conn_info["connection_id"])
    
    async def disconnect_by_websocket(self, websocket: WebSocket):
        """Disconnect a specific connection by WebSocket object."""
        # Find the connection that matches this websocket
        for user_id in list(self.user_connections.keys()):
            for conn_info in list(self.user_connections[user_id]):
                if conn_info["websocket"] == websocket:
                    logger.info(f"WebSocket manager: Found connection {conn_info['connection_id']} for websocket, disconnecting")
                    await self._disconnect_connection(conn_info["connection_id"])
                    return
        logger.warning("WebSocket manager: Could not find connection for websocket")
    
    def get_connection_count(self, user_id: str = None) -> int:
        """Get connection count for a user or total connections."""
        if user_id:
            return len(self.user_connections.get(user_id, []))
        else:
            total = 0
            for user_connections in self.user_connections.values():
                total += len(user_connections)
            return total
    
    def is_connected(self, user_id: str = None) -> bool:
        """Check if user is connected or if any connections exist."""
        if user_id:
            return user_id in self.user_connections and len(self.user_connections[user_id]) > 0
        else:
            return len(self.user_connections) > 0
    
    def get_connection_stats(self) -> dict:
        """Get detailed connection statistics for debugging."""
        stats = {
            "total_users": len(self.user_connections),
            "total_connections": 0,
            "users": {}
        }
        
        for user_id, connections in self.user_connections.items():
            stats["total_connections"] += len(connections)
            stats["users"][user_id] = {
                "connection_count": len(connections),
                "connection_ids": [conn["connection_id"] for conn in connections]
            }
        
        return stats
    
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
    
    async def monitor_token(self, connection_id: str, token: str):
        """Monitor JWT token and send warning when below 60 seconds."""
        try:
            logger.info(f"Starting token monitoring for connection {connection_id}")
            while True:
                # Check if connection is still active
                if connection_id not in self.connection_tasks or connection_id in self._disconnecting:
                    logger.info(f"Connection {connection_id} lost or disconnecting, stopping monitoring")
                    break
                
                # Decode JWT token to get expiration time
                try:
                    from jose import jwt
                    from app.config import SECRET_KEY, ALGORITHM
                    
                    # Decode JWT token without verification (we already verified it in the route)
                    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                    exp_timestamp = payload.get("exp")
                    
                    if not exp_timestamp:
                        logger.warning(f"JWT token for connection {connection_id} has no expiration time, stopping monitoring")
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