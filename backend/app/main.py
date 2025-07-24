from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import home_router, workflow_router, settings_router
from app.auth import auth_router
from app.config import APP_NAME, APP_VERSION
from app.db.database import db_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db_service.initialize()
    yield
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

