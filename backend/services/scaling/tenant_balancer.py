# services/scaling/tenant_balancer.py
import asyncio
import aiohttp
from typing import List, Dict, Any
from dataclasses import dataclass
import redis
import json

@dataclass
class ServiceNode:
    id: str
    host: str
    port: int
    capacity: int
    current_load: int
    health_status: str
    tenant_assignments: List[str]

class TenantLoadBalancer:
    """Manages tenant distribution across multiple service nodes"""
    
    def __init__(self, redis_url: str):
        self.redis = redis.Redis.from_url(redis_url)
        self.nodes: Dict[str, ServiceNode] = {}
        self.tenant_assignments: Dict[str, str] = {}  # tenant_id -> node_id
    
    async def register_node(self, node: ServiceNode):
        """Register a new service node"""
        self.nodes[node.id] = node
        
        # Store in Redis for persistence
        node_data = {
            "id": node.id,
            "host": node.host,
            "port": node.port,
            "capacity": node.capacity,
            "current_load": node.current_load,
            "health_status": node.health_status,
            "tenant_assignments": node.tenant_assignments
        }
        
        await self.redis.hset("service_nodes", node.id, json.dumps(node_data))
        print(f"✅ Registered service node: {node.id}")
    
    async def assign_tenant_to_node(self, tenant_id: str) -> str:
        """Assign tenant to the best available node"""
        
        # Find node with lowest load that has capacity
        best_node = None
        best_score = float('inf')
        
        for node in self.nodes.values():
            if node.health_status != "healthy":
                continue
            
            if len(node.tenant_assignments) >= node.capacity:
                continue
            
            # Calculate load score (current load + estimated tenant load)
            estimated_tenant_load = await self._estimate_tenant_load(tenant_id)
            load_score = (node.current_load + estimated_tenant_load) / node.capacity
            
            if load_score < best_score:
                best_score = load_score
                best_node = node
        
        if not best_node:
            raise Exception("No available nodes with capacity")
        
        # Assign tenant to node
        best_node.tenant_assignments.append(tenant_id)
        best_node.current_load += await self._estimate_tenant_load(tenant_id)
        self.tenant_assignments[tenant_id] = best_node.id
        
        # Update Redis
        await self._update_node_in_redis(best_node)
        await self.redis.hset("tenant_assignments", tenant_id, best_node.id)
        
        print(f"✅ Assigned tenant {tenant_id} to node {best_node.id}")
        return best_node.id
    
    async def get_node_for_tenant(self, tenant_id: str) -> ServiceNode:
        """Get the service node assigned to a tenant"""
        node_id = self.tenant_assignments.get(tenant_id)
        
        if not node_id:
            # Check Redis for assignment
            node_id = await self.redis.hget("tenant_assignments", tenant_id)
            if node_id:
                self.tenant_assignments[tenant_id] = node_id.decode()
        
        if not node_id:
            raise Exception(f"No node assigned to tenant: {tenant_id}")
        
        return self.nodes.get(node_id)
    
    async def rebalance_tenants(self):
        """Rebalance tenant distribution across nodes"""
        print("🔄 Starting tenant rebalancing...")
        
        # Calculate current load distribution
        total_capacity = sum(node.capacity for node in self.nodes.values())
        total_load = sum(node.current_load for node in self.nodes.values())
        
        if total_load == 0:
            return
        
        target_load_per_node = total_load / len(self.nodes)
        
        # Identify overloaded and underloaded nodes
        overloaded_nodes = [
            node for node in self.nodes.values() 
            if node.current_load > target_load_per_node * 1.2
        ]
        
        underloaded_nodes = [
            node for node in self.nodes.values() 
            if node.current_load < target_load_per_node * 0.8
        ]
        
        # Move tenants from overloaded to underloaded nodes
        for overloaded_node in overloaded_nodes:
            excess_load = overloaded_node.current_load - target_load_per_node
            
            # Sort tenants by load (move smallest first for minimal disruption)
            tenant_loads = []
            for tenant_id in overloaded_node.tenant_assignments:
                load = await self._estimate_tenant_load(tenant_id)
                tenant_loads.append((tenant_id, load))
            
            tenant_loads.sort(key=lambda x: x[1])
            
            for tenant_id, tenant_load in tenant_loads:
                if excess_load <= 0:
                    break
                
                # Find suitable underloaded node
                target_node = None
                for underloaded_node in underloaded_nodes:
                    if (underloaded_node.current_load + tenant_load) <= underloaded_node.capacity:
                        target_node = underloaded_node
                        break
                
                if target_node:
                    # Migrate tenant
                    await self._migrate_tenant(tenant_id, overloaded_node.id, target_node.id)
                    excess_load -= tenant_load
        
        print("✅ Tenant rebalancing completed")
    
    async def _migrate_tenant(self, tenant_id: str, from_node_id: str, to_node_id: str):
        """Migrate tenant from one node to another"""
        print(f"🔄 Migrating tenant {tenant_id} from {from_node_id} to {to_node_id}")
        
        from_node = self.nodes[from_node_id]
        to_node = self.nodes[to_node_id]
        tenant_load = await self._estimate_tenant_load(tenant_id)
        
        # Update node assignments
        from_node.tenant_assignments.remove(tenant_id)
        from_node.current_load -= tenant_load
        
        to_node.tenant_assignments.append(tenant_id)
        to_node.current_load += tenant_load
        
        self.tenant_assignments[tenant_id] = to_node_id
        
        # Update Redis
        await self._update_node_in_redis(from_node)
        await self._update_node_in_redis(to_node)
        await self.redis.hset("tenant_assignments", tenant_id, to_node_id)
        
        # Notify application of tenant migration
        await self._notify_tenant_migration(tenant_id, to_node)
    
    async def _estimate_tenant_load(self, tenant_id: str) -> int:
        """Estimate resource load for a tenant"""
        # Get historical metrics from Redis
        metrics_key = f"tenant_metrics:{tenant_id}"
        metrics_data = await self.redis.get(metrics_key)
        
        if not metrics_data:
            return 10  # Default load estimate
        
        metrics = json.loads(metrics_data)
        
        # Calculate load based on various factors
        api_calls_per_hour = metrics.get("api_calls_per_hour", 0)
        active_jobs = metrics.get("active_jobs", 0)
        data_size_mb = metrics.get("data_size_mb", 0)
        
        # Load calculation formula (can be refined based on actual usage patterns)
        estimated_load = (
            (api_calls_per_hour / 100) +  # Normalize API calls
            (active_jobs * 2) +            # Jobs have higher resource usage
            (data_size_mb / 1000)          # Storage factor
        )
        
        return max(1, int(estimated_load))
    
    async def _update_node_in_redis(self, node: ServiceNode):
        """Update node information in Redis"""
        node_data = {
            "id": node.id,
            "host": node.host,
            "port": node.port,
            "capacity": node.capacity,
            "current_load": node.current_load,
            "health_status": node.health_status,
            "tenant_assignments": node.tenant_assignments
        }
        await self.redis.hset("service_nodes", node.id, json.dumps(node_data))
    
    async def _notify_tenant_migration(self, tenant_id: str, target_node: ServiceNode):
        """Notify relevant services about tenant migration"""
        notification = {
            "type": "tenant_migration",
            "tenant_id": tenant_id,
            "new_node": {
                "id": target_node.id,
                "host": target_node.host,
                "port": target_node.port
            },
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Publish to Redis for service consumption
        await self.redis.publish("tenant_migrations", json.dumps(notification))

# Auto-scaling based on metrics
class AutoScaler:
    """Automatically scale services based on load metrics"""
    
    def __init__(self, load_balancer: TenantLoadBalancer):
        self.load_balancer = load_balancer
        self.scaling_cooldown = 300  # 5 minutes between scaling operations
        self.last_scale_time = {}
    
    async def check_scaling_needs(self):
        """Check if scaling is needed based on current metrics"""
        current_time = asyncio.get_event_loop().time()
        
        # Calculate overall system load
        total_capacity = sum(
            node.capacity for node in self.load_balancer.nodes.values()
            if node.health_status == "healthy"
        )
        total_load = sum(
            node.current_load for node in self.load_balancer.nodes.values()
            if node.health_status == "healthy"
        )
        
        if total_capacity == 0:
            return
        
        utilization = total_load / total_capacity
        
        # Scale up if utilization > 80%
        if utilization > 0.8:
            if self._can_scale("up", current_time):
                await self._scale_up()
                self.last_scale_time["up"] = current_time
        
        # Scale down if utilization < 20% and we have more than 1 node
        elif utilization < 0.2 and len(self.load_balancer.nodes) > 1:
            if self._can_scale("down", current_time):
                await self._scale_down()
                self.last_scale_time["down"] = current_time
    
    def _can_scale(self, direction: str, current_time: float) -> bool:
        """Check if scaling operation can be performed (respects cooldown)"""
        last_scale = self.last_scale_time.get(direction, 0)
        return (current_time - last_scale) > self.scaling_cooldown
    
    async def _scale_up(self):
        """Add a new service node"""
        print("📈 Scaling up: Adding new service node...")
        
        # In a real implementation, this would:
        # 1. Launch new container/VM
        # 2. Wait for health check to pass
        # 3. Register with load balancer
        
        # For demonstration, we'll simulate adding a node
        new_node_id = f"node_{len(self.load_balancer.nodes) + 1}"
        new_node = ServiceNode(
            id=new_node_id,
            host="localhost",
            port=8000 + len(self.load_balancer.nodes),
            capacity=50,
            current_load=0,
            health_status="healthy",
            tenant_assignments=[]
        )
        
        await self.load_balancer.register_node(new_node)
        print(f"✅ Added new service node: {new_node_id}")
    
    async def _scale_down(self):
        """Remove a service node with minimal disruption"""
        print("📉 Scaling down: Removing service node...")
        
        # Find node with lowest load for removal
        candidate_node = min(
            self.load_balancer.nodes.values(),
            key=lambda n: n.current_load
        )
        
        if candidate_node.tenant_assignments:
            # Migrate tenants to other nodes
            for tenant_id in candidate_node.tenant_assignments[:]:
                # Find alternative node
                target_node = min(
                    [n for n in self.load_balancer.nodes.values() 
                     if n.id != candidate_node.id and n.health_status == "healthy"],
                    key=lambda n: n.current_load
                )
                
                await self.load_balancer._migrate_tenant(
                    tenant_id, candidate_node.id, target_node.id
                )
        
        # Remove node
        del self.load_balancer.nodes[candidate_node.id]
        await self.load_balancer.redis.hdel("service_nodes", candidate_node.id)
        
        print(f"✅ Removed service node: {candidate_node.id}")

# Usage example
async def main():
    load_balancer = TenantLoadBalancer("redis://localhost:6379")
    auto_scaler = AutoScaler(load_balancer)
    
    # Register initial nodes
    for i in range(2):
        node = ServiceNode(
            id=f"node_{i+1}",
            host="localhost",
            port=8001 + i,
            capacity=50,
            current_load=0,
            health_status="healthy",
            tenant_assignments=[]
        )
        await load_balancer.register_node(node)
    
    # Assign some tenants
    tenants = ["tenant1", "tenant2", "tenant3", "tenant4"]
    for tenant in tenants:
        await load_balancer.assign_tenant_to_node(tenant)
    
    # Run auto-scaling check
    while True:
        await auto_scaler.check_scaling_needs()
        await load_balancer.rebalance_tenants()
        await asyncio.sleep(60)  # Check every minute

if __name__ == "__main__":
    asyncio.run(main())