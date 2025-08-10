# services/analytics/main.py
from fastapi import FastAPI, Depends
from sqlalchemy import text
import pandas as pd
from datetime import datetime, timedelta

app = FastAPI(title="Analytics Service")

class AnalyticsService:
    def __init__(self, tenant_id: str, db: Session):
        self.tenant_id = tenant_id
        self.db = db
    
    async def get_sales_analytics(self, 
                                date_from: datetime,
                                date_to: datetime) -> dict:
        """Generate comprehensive sales analytics for tenant"""
        
        # Query tenant-specific sales data
        query = text("""
        SELECT 
            DATE(created_at) as sale_date,
            SUM(total_amount) as daily_revenue,
            COUNT(*) as daily_orders,
            AVG(total_amount) as avg_order_value
        FROM tenant_orders 
        WHERE tenant_id = :tenant_id 
        AND created_at BETWEEN :date_from AND :date_to
        GROUP BY DATE(created_at)
        ORDER BY sale_date
        """)
        
        result = self.db.execute(query, {
            "tenant_id": self.tenant_id,
            "date_from": date_from,
            "date_to": date_to
        })
        
        # Convert to pandas for analysis
        df = pd.DataFrame(result.fetchall(), 
                         columns=['sale_date', 'daily_revenue', 
                                'daily_orders', 'avg_order_value'])
        
        analytics = {
            "summary": {
                "total_revenue": df['daily_revenue'].sum(),
                "total_orders": df['daily_orders'].sum(),
                "avg_daily_revenue": df['daily_revenue'].mean(),
                "revenue_growth": self._calculate_growth_rate(df)
            },
            "daily_breakdown": df.to_dict('records'),
            "top_performing_days": df.nlargest(5, 'daily_revenue').to_dict('records')
        }
        
        return analytics
    
    async def get_product_performance(self) -> dict:
        """Analyze product performance metrics"""
        
        query = text("""
        SELECT 
            p.name,
            p.etsy_listing_id,
            COUNT(oi.id) as total_sales,
            SUM(oi.quantity) as units_sold,
            SUM(oi.price * oi.quantity) as total_revenue,
            AVG(oi.price) as avg_price
        FROM products p
        LEFT JOIN order_items oi ON p.id = oi.product_id
        LEFT JOIN tenant_orders o ON oi.order_id = o.id
        WHERE o.tenant_id = :tenant_id
        GROUP BY p.id, p.name, p.etsy_listing_id
        ORDER BY total_revenue DESC
        """)
        
        result = self.db.execute(query, {"tenant_id": self.tenant_id})
        
        products = []
        for row in result:
            products.append({
                "name": row.name,
                "etsy_listing_id": row.etsy_listing_id,
                "total_sales": row.total_sales,
                "units_sold": row.units_sold,
                "total_revenue": float(row.total_revenue or 0),
                "avg_price": float(row.avg_price or 0)
            })
        
        return {
            "top_products": products[:10],
            "total_products": len(products),
            "products_with_sales": len([p for p in products if p['total_sales'] > 0])
        }

@app.get("/analytics/dashboard")
async def get_dashboard_data(
    tenant_id: str = Depends(get_tenant_id),
    date_range: str = "30d"
):
    """Get comprehensive dashboard analytics"""
    
    analytics_service = AnalyticsService(tenant_id, get_db())
    
    # Calculate date range
    end_date = datetime.utcnow()
    days = int(date_range.replace('d', ''))
    start_date = end_date - timedelta(days=days)
    
    sales_data = await analytics_service.get_sales_analytics(start_date, end_date)
    product_data = await analytics_service.get_product_performance()
    
    return {
        "tenant_id": tenant_id,
        "date_range": date_range,
        "sales": sales_data,
        "products": product_data,
        "generated_at": datetime.utcnow().isoformat()
    }