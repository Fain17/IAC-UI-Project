from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import home_router, workflow_router, settings_router
from app.auth import auth_router
from app.config import APP_NAME, APP_VERSION, CLEANUP_INTERVAL_SECONDS
from app.db.database import db_service
from app.auth.service import auth_service
import logging

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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_methods=["*"],
        allow_headers=["*"]
    )
    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

