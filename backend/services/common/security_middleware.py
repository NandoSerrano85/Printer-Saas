from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import hashlib
import json
import logging
from typing import Dict, Optional
import os

logger = logging.getLogger(__name__)

class TenantSecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for tenant isolation and rate limiting"""
    
    def __init__(self, app, rate_limit_enabled: bool = True):
        super().__init__(app)
        self.rate_limit_enabled = rate_limit_enabled
        self.rate_limits = {
            "api_calls": {"limit": 1000, "window": 3600},  # 1000 calls per hour
            "auth_attempts": {"limit": 5, "window": 900},   # 5 attempts per 15 minutes
        }
        # In-memory rate limiting for development (would use Redis in production)
        self._rate_limit_cache = {}
    
    async def dispatch(self, request: Request, call_next):
        """Main middleware dispatch method"""
        start_time = time.time()
        
        try:
            # Skip security checks for health and metrics endpoints
            if request.url.path in ["/health", "/health/", "/metrics", "/metrics/", "/", "/docs", "/openapi.json"]:
                return await call_next(request)
            
            # Rate limiting check
            if self.rate_limit_enabled:
                client_ip = self._get_client_ip(request)
                if not await self._check_rate_limit(client_ip, "api_calls"):
                    await self._log_security_event("rate_limit_exceeded", {
                        "client_ip": client_ip,
                        "path": request.url.path,
                        "method": request.method
                    })
                    return Response(
                        content=json.dumps({"error": "Rate limit exceeded"}),
                        status_code=429,
                        headers={"Content-Type": "application/json"}
                    )
            
            # Extract tenant context
            tenant_id = self._extract_tenant_from_request(request)
            if tenant_id:
                request.state.tenant_id = tenant_id
            
            # Add security headers
            response = await call_next(request)
            
            # Add security headers to response
            self._add_security_headers(response)
            
            # Log request for monitoring
            processing_time = time.time() - start_time
            logger.info(
                f"Request processed: {request.method} {request.url.path} "
                f"- {response.status_code} - {processing_time:.3f}s"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Security middleware error: {str(e)}")
            return Response(
                content=json.dumps({"error": "Internal server error"}),
                status_code=500,
                headers={"Content-Type": "application/json"}
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded headers first (for load balancers/proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client
        return request.client.host if request.client else "unknown"
    
    def _extract_tenant_from_request(self, request: Request) -> Optional[str]:
        """Extract tenant ID from request (subdomain, header, or path)"""
        # Method 1: From subdomain
        host = request.headers.get("host", "")
        if "." in host:
            subdomain = host.split(".")[0]
            if subdomain and subdomain not in ["www", "api", "app"]:
                return subdomain
        
        # Method 2: From X-Tenant-ID header
        tenant_header = request.headers.get("X-Tenant-ID")
        if tenant_header:
            return tenant_header
        
        # Method 3: From path parameter (if using /tenant/{tenant_id}/ pattern)
        path_parts = request.url.path.strip("/").split("/")
        if len(path_parts) >= 2 and path_parts[0] == "tenant":
            return path_parts[1]
        
        # Default tenant for development
        return os.getenv("DEFAULT_TENANT_ID", "default")
    
    async def _check_rate_limit(self, identifier: str, limit_type: str) -> bool:
        """Check if request is within rate limits (in-memory implementation)"""
        if not self.rate_limit_enabled:
            return True
        
        config = self.rate_limits.get(limit_type)
        if not config:
            return True
        
        current_time = int(time.time())
        window_start = current_time - config["window"]
        
        # Clean up old entries
        if identifier not in self._rate_limit_cache:
            self._rate_limit_cache[identifier] = {}
        
        if limit_type not in self._rate_limit_cache[identifier]:
            self._rate_limit_cache[identifier][limit_type] = []
        
        # Remove old timestamps
        self._rate_limit_cache[identifier][limit_type] = [
            timestamp for timestamp in self._rate_limit_cache[identifier][limit_type]
            if timestamp > window_start
        ]
        
        # Check if over limit
        current_count = len(self._rate_limit_cache[identifier][limit_type])
        if current_count >= config["limit"]:
            return False
        
        # Add current timestamp
        self._rate_limit_cache[identifier][limit_type].append(current_time)
        return True
    
    def _add_security_headers(self, response: Response):
        """Add security headers to response"""
        response.headers.update({
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()"
        })
    
    async def _log_security_event(self, event_type: str, details: Dict):
        """Log security-related events"""
        logger.warning(
            f"Security event: {event_type}",
            extra={
                "event_type": event_type,
                "details": details,
                "timestamp": time.time()
            }
        )
        
        # In production, this would also send to a SIEM system or security monitoring service