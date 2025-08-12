from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from app.services.websocket_manager import websocket_manager
from app.auth.service import auth_service
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["WebSocket"])

def verify_websocket_token(token: str) -> dict:
    """Verify token for WebSocket connection."""
    try:
        # Decode JWT token without checking expiration
        from jose import jwt
        from app.config import SECRET_KEY, ALGORITHM
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # user_id is now a UUID string, don't convert to int
        return {"user_id": user_id, "token": token}
    except Exception as e:
        logger.error(f"WebSocket token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

@router.websocket("/ws/token-monitor")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    """WebSocket endpoint for token monitoring."""
    connection_closed = False
    
    try:
        await websocket.accept()
        logger.info("WebSocket connection accepted")
        
        # Verify token
        token_info = verify_websocket_token(token)
        logger.info(f"Token verified for user: {token_info['user_id']}")
        
        # Connect to WebSocket manager
        await websocket_manager.connect(websocket, token)
        logger.info("Connected to WebSocket manager")
        
        # Keep connection alive and monitor for disconnection
        try:
            while True:
                # Wait for client disconnect or message
                try:
                    # Use a timeout to prevent blocking indefinitely
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                    logger.debug(f"Received message: {data}")
                except asyncio.TimeoutError:
                    # No message received, continue monitoring
                    continue
                except WebSocketDisconnect:
                    logger.info("WebSocket disconnected by client")
                    connection_closed = True
                    break
                except Exception as e:
                    logger.error(f"WebSocket receive error: {e}")
                    connection_closed = True
                    break
                    
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected by client")
            connection_closed = True
        except Exception as e:
            logger.error(f"WebSocket receive error: {e}")
            connection_closed = True
        finally:
            # Only disconnect if not already closed
            if not connection_closed:
                await websocket_manager.disconnect()
            
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        if not connection_closed:
            try:
                await websocket.close()
            except Exception as close_error:
                logger.debug(f"WebSocket already closed: {close_error}")

@router.get("/ws/status")
async def get_websocket_status():
    """Get WebSocket connection status."""
    return {
        "connected": websocket_manager.is_connected()
    } 