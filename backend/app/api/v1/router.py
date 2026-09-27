"""Version 1 API router.

Only implemented, authenticated feature routes should be attached here. The
controlled demo seed is intentionally absent from the API.
"""

from fastapi import APIRouter

from app.api.v1 import admin, ai, assignments, auth, cases, checkins, counsellor, district, notifications, profile, support
from app.schemas.common import HealthResponse

api_router = APIRouter()


@api_router.get("/health", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    return HealthResponse(status="ok")


api_router.include_router(auth.router)

api_router.include_router(profile.router)
api_router.include_router(checkins.router)
api_router.include_router(ai.router)
api_router.include_router(cases.router)
api_router.include_router(support.router)
api_router.include_router(assignments.router)
api_router.include_router(notifications.router)
api_router.include_router(district.router)
api_router.include_router(counsellor.router)
api_router.include_router(admin.router)
