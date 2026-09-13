"""Role-based access control decorator for Phase 0."""
from functools import wraps
from fastapi import Request, HTTPException
import inspect


def require_role(*allowed_roles):
    """Decorator to enforce role-based access control.
    
    Verifies that the authenticated user's role is in the allowed_roles list.
    Works with both sync and async endpoint functions.
    
    Args:
        *allowed_roles: Allowed roles (e.g., "bidder", "officer", "admin")
        
    Returns:
        Decorated function that enforces role check
        
    Raises:
        HTTPException 401: If user not authenticated
        HTTPException 403: If user role not in allowed_roles
    """
    def decorator(func):
        # Determine if function is async or sync
        is_async = inspect.iscoroutinefunction(func)
        
        if is_async:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Find request in args/kwargs
                request = _get_request_from_args_kwargs(args, kwargs)
                
                if not request:
                    raise HTTPException(status_code=401, detail="Unauthorized: no request found")
                
                # Extract user from request (from token in Authorization header)
                from app.main import get_user_from_request
                try:
                    user = get_user_from_request(request)
                    request.state.user = user
                except HTTPException:
                    raise
                
                user_role = user.get("role")
                if user_role not in allowed_roles:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Forbidden: role '{user_role}' not authorized. Required roles: {allowed_roles}"
                    )
                
                return await func(*args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Find request in args/kwargs
                request = _get_request_from_args_kwargs(args, kwargs)
                
                if not request:
                    raise HTTPException(status_code=401, detail="Unauthorized: no request found")
                
                # Extract user from request (from token in Authorization header)
                from app.main import get_user_from_request
                try:
                    user = get_user_from_request(request)
                    request.state.user = user
                except HTTPException:
                    raise
                
                user_role = user.get("role")
                if user_role not in allowed_roles:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Forbidden: role '{user_role}' not authorized. Required roles: {allowed_roles}"
                    )
                
                return func(*args, **kwargs)
            return sync_wrapper
    
    return decorator


def _get_request_from_args_kwargs(args, kwargs):
    """Helper to extract Request object from function args or kwargs.
    
    Args:
        args: Positional arguments
        kwargs: Keyword arguments
        
    Returns:
        Request object if found, None otherwise
    """
    # Check kwargs first (common in FastAPI with Depends)
    if "request" in kwargs and isinstance(kwargs["request"], Request):
        return kwargs["request"]
    
    # Check args for Request instance
    for arg in args:
        if isinstance(arg, Request):
            return arg
    
    return None
