from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import main_router, api_router
from app.auth import auth_router
from app.config import APP_NAME, APP_VERSION
from app.db.database import db_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for database initialization and cleanup."""
    # Startup
    await db_service.initialize()
    yield
    # Shutdown
    await db_service.close()

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=APP_NAME,
        version=APP_VERSION,
        description="IAC UI Agent for managing EC2 instances and launch templates",
        lifespan=lifespan
    )
    
    # Include routers
    app.include_router(main_router)
    app.include_router(api_router)
    app.include_router(auth_router)
    
    # Allow CORS for the frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_methods=["*"],
        allow_headers=["*"]
    )
    
    return app

# Create the application instance
app = create_app()

