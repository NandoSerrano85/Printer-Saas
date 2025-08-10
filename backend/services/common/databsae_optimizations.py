# services/common/database_optimizations.py
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import logging

# Connection pooling configuration for QNAP constraints
DATABASE_CONFIG = {
    "pool_size": 5,          # Limit connections due to QNAP resources
    "max_overflow": 10,      # Maximum additional connections
    "pool_pre_ping": True,   # Verify connections before use
    "pool_recycle": 3600,    # Recycle connections every hour
}

engine = create_engine(
    DATABASE_URL,
    **DATABASE_CONFIG,
    echo=False  # Set to True for query debugging
)

# Query performance monitoring
@event.listens_for(engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - context._query_start_time
    if total > 1.0:  # Log slow queries
        logging.warning(f"Slow query ({total:.2f}s): {statement[:200]}...")

# Optimized tenant data access patterns
class TenantDataAccess:
    def __init__(self, tenant_id: str, db: Session):
        self.tenant_id = tenant_id
        self.db = db
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Optimized dashboard data retrieval with single query"""
        
        # Single query to get all dashboard metrics
        result = self.db.execute(text("""
        WITH tenant_stats AS (
            SELECT 
                COUNT(DISTINCT o.id) as total_orders,
                COALESCE(SUM(o.total_amount), 0) as total_revenue,
                COUNT(DISTINCT p.id) as total_products,
                COUNT(DISTINCT d.id) as total_designs
            FROM {schema}.orders o
            FULL OUTER JOIN {schema}.products p ON true
            FULL OUTER JOIN {schema}.designs d ON true
            WHERE o.created_at >= CURRENT_DATE - INTERVAL '30 days'
        ),
        recent_activity AS (
            SELECT 
                'order' as activity_type,
                id::text as activity_id,
                created_at,
                total_amount::text as activity_data
            FROM {schema}.orders 
            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
            
            UNION ALL
            
            SELECT 
                'design' as activity_type,
                id::text as activity_id,
                created_at,
                name as activity_data
            FROM {schema}.designs
            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
            ORDER BY created_at DESC
            LIMIT 10
        )
        SELECT 
            json_build_object(
                'stats', row_to_json(ts),
                'recent_activity', json_agg(ra)
            ) as dashboard_data
        FROM tenant_stats ts, recent_activity ra
        GROUP BY ts.total_orders, ts.total_revenue, ts.total_products, ts.total_designs
        """.format(schema=f"tenant_{self.tenant_id}")))
        
        return result.fetchone()[0]