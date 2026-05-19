from .admin_router import admin_router
from .auth_router import auth_router
from .grades_router import grades_router
from .user_router import user_router

__all__ = [
    "admin_router", 
    "auth_router", 
    "grades_router", 
    "user_router"
]