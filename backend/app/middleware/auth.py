"""JWT validation middleware for Phase 0."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from jose import JWTError
from app.security.auth import decode_access_token


class AuthMiddleware(BaseHTTPMiddleware):
    """JWT validation middleware.
    
    Extracts JWT token from Authorization header, validates it, and adds user info to request.state.
    Public endpoints (login, docs) skip authentication.
    Protected endpoints require valid JWT token.
    """
    
    # Public endpoints that don't require authentication
    PUBLIC_ENDPOINTS = {
        "/api/auth/login",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/",
        "/health",
    }
    
    async def dispatch(self, request: Request, call_next):
        """Process request through JWT middleware.
        
        Args:
            request: HTTP request
            call_next: Next middleware in chain
            
        Returns:
            Response from next middleware or error response
        """
        # Allow OPTIONS (preflight) requests to pass through without auth check
        if request.method == "OPTIONS":
            response = await call_next(request)
            return response
        
        # Skip auth for public endpoints
        if request.url.path in self.PUBLIC_ENDPOINTS:
            return await call_next(request)
        
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid Authorization header"}
            )
        
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        try:
            payload = decode_access_token(token)
            request.state.user = {
                "id": payload["user_id"],
                "role": payload["role"],
            }
        except JWTError as e:
            return JSONResponse(
                status_code=401,
                content={"detail": f"Invalid or expired token: {str(e)}"}
            )
        
        return await call_next(request)
