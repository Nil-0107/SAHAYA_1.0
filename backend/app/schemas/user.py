"""Current-user response schemas.

The detailed user contract is defined in ``schemas.auth`` and re-exported here
for route modules that need a user-shaped response.
"""

from app.schemas.auth import UserResponse

__all__ = ("UserResponse",)
