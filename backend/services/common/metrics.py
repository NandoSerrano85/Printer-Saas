# services/common/metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
from functools import wraps

# Metrics definitions
REQUEST_COUNT = Counter('http_requests_total', 
                       'Total HTTP requests', 
                       ['method', 'endpoint', 'status', 'tenant_id'])

REQUEST_DURATION = Histogram('http_request_duration_seconds',
                           'HTTP request duration',
                           ['method', 'endpoint', 'tenant_id'])

ACTIVE_CONNECTIONS = Gauge('active_connections_total',
                         'Active database connections',
                         ['tenant_id'])

ETSY_API_CALLS = Counter('etsy_api_calls_total',
                        'Total Etsy API calls',
                        ['tenant_id', 'endpoint', 'status'])

JOB_PROCESSING_TIME = Histogram('job_processing_seconds',
                              'Job processing time',
                              ['tenant_id', 'job_type'])

TENANT_RESOURCE_USAGE = Gauge('tenant_resource_usage',
                            'Tenant resource usage',
                            ['tenant_id', 'resource_type'])

def track_metrics(func):
    """Decorator to track API endpoint metrics"""
    @wraps(func)
    async def wrapper(request, *args, **kwargs):
        start_time = time.time()
        tenant_id = getattr(request.state, 'tenant_id', 'unknown')
        
        try:
            response = await func(request, *args, **kwargs)
            status = getattr(response, 'status_code', 200)
            
            # Record metrics
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=status,
                tenant_id=tenant_id
            ).inc()
            
            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=request.url.path,
                tenant_id=tenant_id
            ).observe(time.time() - start_time)
            
            return response
            
        except Exception as e:
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=500,
                tenant_id=tenant_id
            ).inc()
            raise
    
    return wrapper

class TenantMetrics:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
    
    def record_etsy_api_call(self, endpoint: str, status_code: int):
        """Record Etsy API call metrics"""
        ETSY_API_CALLS.labels(
            tenant_id=self.tenant_id,
            endpoint=endpoint,
            status=status_code
        ).inc()
    
    def record_job_processing_time(self, job_type: str, duration: float):
        """Record job processing time"""
        JOB_PROCESSING_TIME.labels(
            tenant_id=self.tenant_id,
            job_type=job_type
        ).observe(duration)
    
    def update_resource_usage(self, resource_type: str, current_usage: int):
        """Update current resource usage"""
        TENANT_RESOURCE_USAGE.labels(
            tenant_id=self.tenant_id,
            resource_type=resource_type
        ).set(current_usage)

# Start metrics server
def start_metrics_server(port: int = 9090):
    """Start Prometheus metrics server"""
    start_http_server(port)