# services/jobs/worker.py
from rq import Worker, Queue, Connection
import redis
from typing import Dict, Any
import logging

# Job definitions
async def process_bulk_listings(tenant_id: str, listings_data: List[Dict]) -> Dict[str, Any]:
    """Process bulk listing creation for a tenant"""
    results = {
        "tenant_id": tenant_id,
        "total_listings": len(listings_data),
        "successful": 0,
        "failed": 0,
        "errors": []
    }
    
    etsy_service = EtsyService(tenant_id)
    
    for listing_data in listings_data:
        try:
            result = await etsy_service.create_listing(listing_data)
            results["successful"] += 1
            
            # Store success in tenant database
            await store_listing_result(tenant_id, listing_data["id"], result)
            
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({
                "listing_id": listing_data.get("id"),
                "error": str(e)
            })
            
            # Log error for tenant
            await log_tenant_error(tenant_id, "listing_creation", str(e))
    
    return results

def generate_mockup_images(tenant_id: str, design_id: str, mockup_config: Dict) -> Dict[str, Any]:
    """Generate mockup images for a design"""
    import PIL.Image
    import numpy as np
    
    try:
        # Load design from MinIO
        design_service = DesignService(tenant_id)
        design_data = design_service.get_design(design_id)
        
        # Load base mockup templates
        mockup_templates = load_mockup_templates(mockup_config["template_type"])
        
        generated_mockups = []
        
        for template in mockup_templates:
            # Apply design to template
            mockup_image = apply_design_to_template(
                design_data["image_data"],
                template,
                mockup_config.get("mask_data", {})
            )
            
            # Save mockup to MinIO
            mockup_path = f"{tenant_id}/mockups/{design_id}_{template['name']}.png"
            mockup_url = design_service.save_mockup(mockup_path, mockup_image)
            
            generated_mockups.append({
                "template_name": template["name"],
                "mockup_url": mockup_url,
                "size": mockup_image.size
            })
        
        return {
            "tenant_id": tenant_id,
            "design_id": design_id,
            "generated_mockups": generated_mockups,
            "status": "completed"
        }
        
    except Exception as e:
        logging.error(f"Mockup generation failed for {tenant_id}:{design_id}: {e}")
        return {
            "tenant_id": tenant_id,
            "design_id": design_id,
            "status": "failed",
            "error": str(e)
        }

async def sync_etsy_data(tenant_id: str) -> Dict[str, Any]:
    """Sync Etsy data for tenant (orders, listings, etc.)"""
    etsy_service = EtsyService(tenant_id)
    
    # Get latest sync timestamp
    last_sync = get_last_sync_timestamp(tenant_id)
    
    sync_results = {
        "tenant_id": tenant_id,
        "sync_started": datetime.utcnow().isoformat(),
        "orders_synced": 0,
        "listings_synced": 0,
        "errors": []
    }
    
    try:
        # Sync orders
        new_orders = await etsy_service.get_orders_since(last_sync)
        for order in new_orders:
            await store_tenant_order(tenant_id, order)
            sync_results["orders_synced"] += 1
        
        # Sync listings
        updated_listings = await etsy_service.get_listings_updates_since(last_sync)
        for listing in updated_listings:
            await store_tenant_listing(tenant_id, listing)
            sync_results["listings_synced"] += 1
        
        # Update sync timestamp
        await update_sync_timestamp(tenant_id, datetime.utcnow())
        
        sync_results["status"] = "completed"
        sync_results["sync_completed"] = datetime.utcnow().isoformat()
        
    except Exception as e:
        sync_results["status"] = "failed"
        sync_results["errors"].append(str(e))
        logging.error(f"Etsy sync failed for {tenant_id}: {e}")
    
    return sync_results

# Worker setup
if __name__ == '__main__':
    redis_conn = redis.from_url(REDIS_URL)
    
    # Create queues with priorities
    high_priority_queue = Queue('high_priority', connection=redis_conn)
    normal_queue = Queue('normal', connection=redis_conn)
    low_priority_queue = Queue('low_priority', connection=redis_conn)
    
    # Start worker
    worker = Worker([high_priority_queue, normal_queue, low_priority_queue], 
                   connection=redis_conn)
    worker.work()