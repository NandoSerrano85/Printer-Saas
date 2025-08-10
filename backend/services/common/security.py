# services/common/security.py
from functools import wraps
import jwt
from fastapi import HTTPException

def require_tenant_access(required_permissions: List[str] = None):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract JWT token
            token = extract_token_from_request()
            
            try:
                payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
                tenant_id = payload.get("tenant_id")
                user_permissions = payload.get("permissions", [])
                
                # Verify tenant access
                if not tenant_id:
                    raise HTTPException(403, "No tenant access")
                
                # Check specific permissions if required
                if required_permissions:
                    if not any(perm in user_permissions for perm in required_permissions):
                        raise HTTPException(403, "Insufficient permissions")
                
                # Add to request context
                kwargs['tenant_id'] = tenant_id
                kwargs['user_permissions'] = user_permissions
                
            except jwt.InvalidTokenError:
                raise HTTPException(401, "Invalid token")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Usage example
@app.post("/designs/upload")
@require_tenant_access(["design:create"])
async def upload_design(tenant_id: str, user_permissions: List[str], file: UploadFile = File(...)):
    """Upload design with tenant isolation"""
    # Process upload with tenant context
    pass