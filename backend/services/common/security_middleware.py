# services/common/security_middleware.py
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import time
import hashlib
from typing import Dict, List
import redis

security = HTTPBearer()
redis_client = redis.Redis.from_url(REDIS_URL)

class SecurityMiddleware:
    def __init__(self):
        self.rate_limits = {
            "api_calls": {"limit": 1000, "window": 3600},  # 1000 calls per hour
            "auth_attempts": {"limit": 5, "window": 900},   # 5 attempts per 15 minutes
        }
    
    async def rate_limit_check(self, identifier: str, limit_type: str) -> bool:
        """Check if request is within rate limits"""
        config = self.rate_limits.get(limit_type)
        if not config:
            return True
        
        key = f"rate_limit:{limit_type}:{identifier}"
        current_time = int(time.time())
        window_start = current_time - config["window"]
        
        # Remove old entries
        redis_client.zremrangebyscore(key, 0, window_start)
        
        # Count current requests in window
        current_count = redis_client.zcard(key)
        
        if current_count >= config["limit"]:
            return False
        
        # Add current request
        redis_client.zadd(key, {str(current_time): current_time})
        redis_client.expire(key, config["window"])
        
        return True
    
    async def validate_jwt_token(self, token: str) -> Dict:
        """Validate JWT token and extract claims"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            
            # Check if token is blacklisted
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            if redis_client.get(f"blacklist:{token_hash}"):
                raise HTTPException(401, "Token has been revoked")
            
            # Check token expiration
            if payload.get("exp", 0) < time.time():
                raise HTTPException(401, "Token has expired")
            
            return payload
            
        except jwt.InvalidTokenError:
            raise HTTPException(401, "Invalid token")
    
    async def check_tenant_access(self, token_payload: Dict, requested_tenant: str) -> bool:
        """Verify user has access to requested tenant"""
        token_tenant = token_payload.get("tenant_id")
        
        if not token_tenant:
            return False
        
        if token_tenant != requested_tenant:
            # Check if user has multi-tenant access (admin users)
            user_permissions = token_payload.get("permissions", [])
            if "admin:cross_tenant" not in user_permissions:
                return False
        
        return True
    
    async def log_security_event(self, event_type: str, details: Dict):
        """Log security-related events"""
        security_logger = TenantLogger("security")
        security_logger.warning(f"Security event: {event_type}", **details)
        
        # Store in Redis for monitoring
        event_key = f"security_events:{int(time.time())}"
        event_data = {
            "type": event_type,
            "timestamp": time.time(),
            "details": details
        }
        redis_client.setex(event_key, 86400, json.dumps(event_data))  # 24 hours

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    security_handler = SecurityMiddleware()
    
    # Skip security checks for health endpoints
    if request.url.path in ["/health", "/metrics"]:
        return await call_next(request)
    
    # Rate limiting based on IP
    client_ip = request.client.host
    if not await security_handler.rate_limit_check(client_ip, "api_calls"):
        await security_handler.log_security_event("rate_limit_exceeded", {
            "client_ip": client_ip,
            "path": request.url.path
        })
        raise HTTPException(429, "Rate limit exceeded")
    
    # Token validation for protected endpoints
    if request.url.path.startswith("/api/"):
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(401, "Missing or invalid authorization header")
        
        token = auth_header.split(" ")[1]
        payload = await security_handler.validate_jwt_token(token)
        
        # Extract tenant from subdomain or header
        tenant_id = extract_tenant_from_request(request)
        
        if not await security_handler.check_tenant_access(payload, tenant_id):
            await security_handler.log_security_event("unauthorized_tenant_access", {
                "user_id": payload.get("user_id"),
                "requested_tenant": tenant_id,
                "user_tenant": payload.get("tenant_id"),
                "client_ip": client_ip
            })
            raise HTTPException(403, "Access denied to tenant")
        
        # Add to request state
        request.state.tenant_id = tenant_id
        request.state.user_id = payload.get("user_id")
        request.state.permissions = payload.get("permissions", [])
    
    response = await call_next(request)
    return response