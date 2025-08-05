from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import home_router, workflow_router, settings_router
from app.auth import auth_router, auth_service
from app.routes.admin_routes import router as admin_router
from app.routes.websocket_routes import router as websocket_router
from app.config import APP_NAME, APP_VERSION, CLEANUP_INTERVAL_SECONDS
from app.db.database import db_service
import logging
import ssl
import os

logger = logging.getLogger(__name__)

async def periodic_cleanup():
    """Run periodic cleanup every hour."""
    while True:
        try:
            await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)  # Wait 1 hour
            logger.info("Running scheduled cleanup...")
            await auth_service.run_periodic_cleanup()
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db_service.initialize()
    
    # Start periodic cleanup task
    cleanup_task = asyncio.create_task(periodic_cleanup())
    logger.info("Periodic cleanup task started (runs every hour)")
    
    yield
    
    # Cancel cleanup task on shutdown
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    
    await db_service.close()

def create_app() -> FastAPI:
    app = FastAPI(
        title=APP_NAME,
        version=APP_VERSION,
        description="IAC UI Agent for managing EC2 instances and launch templates",
        lifespan=lifespan
    )
    app.include_router(home_router)
    app.include_router(workflow_router)
    app.include_router(settings_router)
    app.include_router(auth_router)
    app.include_router(admin_router)
    app.include_router(websocket_router)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "https://localhost:3000"],
        allow_methods=["*"],
        allow_headers=["*"]
    )
    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    
    # SSL Configuration for WSS
    ssl_keyfile = os.getenv("SSL_KEYFILE", "certs/key.pem")
    ssl_certfile = os.getenv("SSL_CERTFILE", "certs/cert.pem")
    
    # Check if SSL certificates exist
    if os.path.exists(ssl_keyfile) and os.path.exists(ssl_certfile):
        logger.info("SSL certificates found, starting with WSS support")
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8000,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile
        )
    else:
        logger.warning("SSL certificates not found, starting without WSS support")
        logger.info("To enable WSS, create SSL certificates in the 'certs' directory")
        uvicorn.run(app, host="0.0.0.0", port=8000)

