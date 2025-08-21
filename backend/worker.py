#!/usr/bin/env python3
"""
Celery worker configuration and task definitions
"""

from celery import Celery
from decouple import config
import os

# Initialize Celery app
celery_app = Celery('printer-saas-worker')

# Configuration
celery_app.conf.update(
    broker_url=config('CELERY_BROKER_URL', default='redis://redis:6379/1'),
    result_backend=config('CELERY_RESULT_BACKEND', default='redis://redis:6379/2'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_routes={
        'orders.*': {'queue': 'orders'},
        'sync.*': {'queue': 'sync'},
        'email.*': {'queue': 'email'},
    },
    task_default_queue='default',
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_ignore_result=False,
)

# Auto-discover tasks (disabled for now)
# celery_app.autodiscover_tasks([
#     'services.orders',
#     'services.etsy', 
#     'services.shopify',
#     'services.email',
# ])

@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing celery functionality"""
    print(f'Request: {self.request!r}')
    return 'Debug task completed successfully'

@celery_app.task
def ping():
    """Simple ping task"""
    return 'pong'

if __name__ == '__main__':
    celery_app.start()