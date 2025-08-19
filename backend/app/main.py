from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import home_router, settings_router, workflow_router, file_router, execution_router
from app.routes.admin_routes import router as admin_router
from app.routes.websocket_routes import router as websocket_router
from app.routes.workflow_automation_routes import router as workflow_automation_router
from app.routes.config_routes import router as config_router
from app.auth import auth_router
from app.db.database import db_service
from app.services.workflow_automation_service import workflow_automation_service
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="IAC UI Agent Backend", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(home_router)
app.include_router(settings_router)
app.include_router(workflow_router)
app.include_router(file_router)
app.include_router(execution_router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(websocket_router)
app.include_router(workflow_automation_router)
app.include_router(config_router)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    try:
        await db_service.initialize()
        await workflow_automation_service.start_scheduler()
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    try:
        await workflow_automation_service.stop_scheduler()
        await db_service.close()
        logger.info("Application shutdown successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

