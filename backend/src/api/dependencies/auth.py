"""Authentication dependencies for FastAPI routes."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer

from src.auth.jwt import verify_token
from src.core.exceptions import AuthenticationError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user_id(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> UUID:
    """Get current user ID from JWT token."""
    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token payload")
        # TODO: Validate user exists in database
        # For now, generate a deterministic UUID from email
        import hashlib
        user_uuid = UUID(hashlib.md5(user_id.encode()).hexdigest())
        return user_uuid
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user_id(
    token: Annotated[str | None, Depends(oauth2_scheme)] = None,
    api_key: Annotated[str | None, Depends(api_key_header)] = None,
) -> UUID | None:
    """Get user ID if authenticated, None otherwise."""
    if token:
        try:
            return await get_current_user_id(token)
        except HTTPException:
            pass
    
    if api_key:
        # TODO: Validate API key and get associated user
        pass
    
    return None


async def get_current_user_id_from_api_key(
    api_key: Annotated[str, Depends(api_key_header)],
) -> UUID:
    """Get user ID from API key."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
        )
    
    # TODO: Validate API key against database
    # For now, placeholder
    import hashlib
    user_uuid = UUID(hashlib.md5(api_key.encode()).hexdigest())
    return user_uuid
