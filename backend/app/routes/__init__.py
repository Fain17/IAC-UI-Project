from .home_routes import router as home_router
from .workflow_routes import router as workflow_router
from .settings_routes import router as settings_router

__all__ = ["home_router", "workflow_router", "settings_router"] 