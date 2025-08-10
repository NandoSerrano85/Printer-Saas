# services/common/logging_config.py
import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any

class TenantFormatter(logging.Formatter):
    """Custom formatter that includes tenant context"""
    
    def format(self, record):
        # Add tenant context if available
        if hasattr(record, 'tenant_id'):
            record.tenant_context = f"[Tenant: {record.tenant_id}]"
        else:
            record.tenant_context = "[System]"
        
        # Create structured log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "service": getattr(record, 'service_name', 'unknown'),
            "tenant_id": getattr(record, 'tenant_id', None),
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)

class TenantLogger:
    """Logger with tenant context"""
    
    def __init__(self, service_name: str, tenant_id: str = None):
        self.service_name = service_name
        self.tenant_id = tenant_id
        self.logger = logging.getLogger(f"{service_name}.{tenant_id or 'system'}")
        
        if not self.logger.handlers:
            self._setup_logger()
    
    def _setup_logger(self):
        """Setup logger with proper formatting"""
        handler = logging.StreamHandler(sys.stdout)
        formatter = TenantFormatter()
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def _log_with_context(self, level: str, message: str, **kwargs):
        """Log message with tenant context"""
        extra = {
            'service_name': self.service_name,
            'tenant_id': self.tenant_id,
            'extra_fields': kwargs
        }
        
        getattr(self.logger, level.lower())(message, extra=extra)
    
    def info(self, message: str, **kwargs):
        self._log_with_context('INFO', message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log_with_context('ERROR', message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log_with_context('WARNING', message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        self._log_with_context('DEBUG', message, **kwargs)

# Usage example in services
def create_tenant_logger(service_name: str):
    def get_logger(tenant_id: str = None):
        return TenantLogger(service_name, tenant_id)
    return get_logger

# In each service
logger_factory = create_tenant_logger("etsy-service")

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    tenant_id = getattr(request.state, 'tenant_id', None)
    logger = logger_factory(tenant_id)
    
    start_time = time.time()
    
    logger.info("Request started", 
               method=request.method,
               path=request.url.path,
               client_ip=request.client.host)
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    logger.info("Request completed",
               method=request.method,
               path=request.url.path,
               status_code=response.status_code,
               process_time=process_time)
    
    return response