import logging

import httpx
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

logger = logging.getLogger(__name__)

# auto_error=False allows us to check cookies if Bearer is not present
security = HTTPBearer(auto_error=False)


async def verify_session(
    request: Request, token: HTTPAuthorizationCredentials | None = Depends(security)
) -> str:
    """
    Dependency to verify NextAuth session and extract user_id.
    It checks for Bearer token first, then falls back to NextAuth cookies.
    Rejects invalid/missing sessions with HTTP 401 Unauthorized.
    """
    cookies = request.cookies
    session_token = cookies.get("authjs.session-token") or cookies.get(
        "__Secure-authjs.session-token"
    )

    headers = {}
    if session_token:
        headers["Cookie"] = (
            f"authjs.session-token={session_token}; __Secure-authjs.session-token={session_token}"
        )
    elif token:
        headers["Authorization"] = f"Bearer {token.credentials}"
    else:
        raise HTTPException(
            status_code=401, detail="Not authenticated: No session token found"
        )

    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
    session_url = f"{frontend_url.rstrip('/')}/api/auth/session"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(session_url, headers=headers, timeout=5.0)

        if response.status_code != 200:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated: Invalid session from frontend",
            )

        session_data = response.json()
        if not session_data or not session_data.get("user"):
            raise HTTPException(
                status_code=401, detail="Not authenticated: Session expired or invalid"
            )

        user = session_data["user"]
        # NextAuth places the user's ID or email here. Fallback to email if ID is missing.
        user_id = user.get("id") or user.get("email")
        if not user_id:
            raise HTTPException(
                status_code=401, detail="Not authenticated: User ID missing in session"
            )

        return user_id

    except httpx.RequestError as e:
        logger.error(f"Failed to contact frontend session endpoint: {e}")
        # Fail closed on network errors
        raise HTTPException(
            status_code=401, detail="Not authenticated: Could not verify session"
        )


def get_current_user_id(user_id: str = Depends(verify_session)) -> str:
    """
    Helper dependency ready to be used in all backend routers for row-level access control.
    """
    return user_id
