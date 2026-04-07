"""
API module for Digital FTE Agent.
"""

from src.api.health import router as health_router

__all__ = [
    "health_router",
]
