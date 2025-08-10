# services/billing/main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, Any
import stripe

app = FastAPI(title="Billing Service")

# Subscription tiers configuration
SUBSCRIPTION_TIERS = {
    "starter": {
        "name": "Starter",
        "monthly_price": 29,
        "limits": {
            "max_listings": 100,
            "max_designs": 50,
            "max_mockups_per_month": 500,
            "api_calls_per_hour": 100
        }
    },
    "professional": {
        "name": "Professional", 
        "monthly_price": 79,
        "limits": {
            "max_listings": 1000,
            "max_designs": 500,
            "max_mockups_per_month": 5000,
            "api_calls_per_hour": 500
        }
    },
    "enterprise": {
        "name": "Enterprise",
        "monthly_price": 199,
        "limits": {
            "max_listings": -1,  # Unlimited
            "max_designs": -1,   # Unlimited
            "max_mockups_per_month": -1,  # Unlimited
            "api_calls_per_hour": 2000
        }
    }
}

class BillingService:
    def __init__(self, tenant_id: str, db: Session):
        self.tenant_id = tenant_id
        self.db = db
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics for tenant"""
        
        # Query current month usage
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0)
        
        usage_stats = {
            "current_listings": await self._count_active_listings(),
            "total_designs": await self._count_designs(),
            "mockups_this_month": await self._count_mockups_since(current_month),
            "api_calls_this_hour": await self._count_api_calls_last_hour()
        }
        
        # Get subscription limits
        subscription = await self._get_tenant_subscription()
        tier_limits = SUBSCRIPTION_TIERS[subscription.tier]["limits"]
        
        # Calculate usage percentages
        usage_percentages = {}
        for metric, current_value in usage_stats.items():
            limit_key = f"max_{metric}" if metric != "api_calls_this_hour" else "api_calls_per_hour"
            limit = tier_limits.get(limit_key, -1)
            
            if limit == -1:  # Unlimited
                usage_percentages[metric] = 0
            else:
                usage_percentages[metric] = (current_value / limit) * 100
        
        return {
            "tenant_id": self.tenant_id,
            "subscription_tier": subscription.tier,
            "usage": usage_stats,
            "limits": tier_limits,
            "usage_percentages": usage_percentages,
            "billing_period": {
                "start": subscription.current_period_start,
                "end": subscription.current_period_end
            }
        }
    
    async def check_usage_limits(self, resource_type: str, requested_amount: int = 1) -> bool:
        """Check if tenant can use more resources"""
        
        usage_stats = await self.get_usage_stats()
        current_usage = usage_stats["usage"]
        limits = usage_stats["limits"]
        
        resource_mapping = {
            "listings": ("current_listings", "max_listings"),
            "designs": ("total_designs", "max_designs"),
            "mockups": ("mockups_this_month", "max_mockups_per_month"),
            "api_calls": ("api_calls_this_hour", "api_calls_per_hour")
        }
        
        if resource_type not in resource_mapping:
            raise ValueError(f"Unknown resource type: {resource_type}")
        
        usage_key, limit_key = resource_mapping[resource_type]
        current_value = current_usage[usage_key]
        limit = limits[limit_key]
        
        if limit == -1:  # Unlimited
            return True
        
        return (current_value + requested_amount) <= limit
    
    async def create_stripe_checkout_session(self, 
                                           new_tier: str, 
                                           success_url: str,
                                           cancel_url: str) -> str:
        """Create Stripe checkout session for subscription upgrade/downgrade"""
        
        if new_tier not in SUBSCRIPTION_TIERS:
            raise HTTPException(400, f"Invalid subscription tier: {new_tier}")
        
        tenant = await self._get_tenant()
        price_amount = SUBSCRIPTION_TIERS[new_tier]["monthly_price"] * 100  # Stripe uses cents
        
        checkout_session = stripe.checkout.Session.create(
            customer_email=tenant.primary_email,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': price_amount,
                    'product_data': {
                        'name': f'Etsy Seller Automater - {SUBSCRIPTION_TIERS[new_tier]["name"]}',
                        'description': f'Monthly subscription to {new_tier} tier'
                    },
                    'recurring': {
                        'interval': 'month'
                    }
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=cancel_url,
            metadata={
                'tenant_id': self.tenant_id,
                'subscription_tier': new_tier
            }
        )
        
        return checkout_session.url

@app.get("/billing/usage")
async def get_tenant_usage(tenant_id: str = Depends(get_tenant_id)):
    """Get detailed usage statistics for tenant"""
    billing_service = BillingService(tenant_id, get_db())
    return await billing_service.get_usage_stats()

@app.post("/billing/upgrade")
async def create_upgrade_session(
    new_tier: str,
    tenant_id: str = Depends(get_tenant_id)
):
    """Create Stripe checkout session for subscription upgrade"""
    billing_service = BillingService(tenant_id, get_db())
    
    checkout_url = await billing_service.create_stripe_checkout_session(
        new_tier=new_tier,
        success_url=f"https://{tenant_id}.yourdomain.com/billing/success",
        cancel_url=f"https://{tenant_id}.yourdomain.com/billing/cancel"
    )
    
    return {"checkout_url": checkout_url}

@app.post("/billing/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks for subscription events"""
    payload = await request.body()
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(400, "Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(400, "Invalid signature")
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        tenant_id = session['metadata']['tenant_id']
        new_tier = session['metadata']['subscription_tier']
        
        # Update tenant subscription
        await update_tenant_subscription(tenant_id, new_tier, session)
        
    elif event['type'] == 'invoice.payment_failed':
        # Handle failed payment
        invoice = event['data']['object']
        await handle_payment_failure(invoice)
    
    return {"status": "success"}