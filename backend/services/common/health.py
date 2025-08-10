# services/common/health.py
from fastapi import FastAPI
import asyncio
import psycopg2
import redis

class HealthCheck:
    def __init__(self, app: FastAPI):
        self.app = app
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.get("/health")
        async def health_check():
            checks = {
                "database": await self.check_database(),
                "redis": await self.check_redis(),
                "service": "healthy"
            }
            
            all_healthy = all(
                status == "healthy" 
                for status in checks.values()
            )
            
            return {
                "status": "healthy" if all_healthy else "unhealthy",
                "checks": checks
            }
    
    async def check_database(self) -> str:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            conn.close()
            return "healthy"
        except Exception as e:
            return f"unhealthy: {str(e)}"
    
    async def check_redis(self) -> str:
        try:
            r = redis.Redis.from_url(REDIS_URL)
            r.ping()
            return "healthy"
        except Exception as e:
            return f"unhealthy: {str(e)}"