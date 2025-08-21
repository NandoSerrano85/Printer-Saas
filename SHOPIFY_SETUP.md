# Shopify Partner App Configuration

## 📝 **App Credentials** (Fill this out after creating your app)

```bash
# From Shopify Partner Dashboard → Apps → [Your App] → App info
SHOPIFY_CLIENT_ID=___________________________
SHOPIFY_CLIENT_SECRET=______________________

# App Details
SHOPIFY_APP_NAME=___________________________
SHOPIFY_APP_HANDLE=_________________________
```

## 🌐 **Domain Configuration** (Choose one)

### Option A: Local Development (Recommended to start)
```bash
SHOPIFY_OAUTH_REDIRECT_URI=http://localhost:8000/api/v1/shopify/oauth/callback
SHOPIFY_WEBHOOK_ENDPOINT=http://localhost:8000/api/v1/shopify/webhooks
```

### Option B: Ngrok (for external testing)
```bash
# Run: ngrok http 8000
# Then use the https URL provided
SHOPIFY_OAUTH_REDIRECT_URI=https://YOUR_NGROK_URL.ngrok.io/api/v1/shopify/oauth/callback
SHOPIFY_WEBHOOK_ENDPOINT=https://YOUR_NGROK_URL.ngrok.io/api/v1/shopify/webhooks
```

### Option C: Production Domain (when ready)
```bash
SHOPIFY_OAUTH_REDIRECT_URI=https://yourdomain.com/api/v1/shopify/oauth/callback
SHOPIFY_WEBHOOK_ENDPOINT=https://yourdomain.com/api/v1/shopify/webhooks
```

## 🏪 **Test Store Information**

```bash
# Test Store Details (after creating development store)
TEST_STORE_URL=_____________________________.myshopify.com
TEST_STORE_NAME=____________________________
```

## ⚙️ **Required App Permissions (Scopes)**

Configure these scopes in your Partner Dashboard:

```
read_products          # Read product data
write_products         # Create/update products
read_orders           # Read order data
write_orders          # Update order data
read_customers        # Read customer data
write_customers       # Update customer data
read_inventory        # Read inventory levels
write_inventory       # Update inventory
read_files           # Access uploaded files
read_themes          # For storefront integration (optional)
```

## 🔗 **URLs to Configure in Partner Dashboard**

### App URLs
```
App URL: http://localhost:8000
App proxy URL: (leave blank for now)
```

### Allowed Redirection URLs
```
http://localhost:8000/api/v1/shopify/oauth/callback
https://YOUR_NGROK_URL.ngrok.io/api/v1/shopify/oauth/callback (if using ngrok)
```

### Webhooks (configure these in Partner Dashboard)
```
Endpoint URL: http://localhost:8000/api/v1/shopify/webhooks
Format: JSON
```

### Webhook Topics (select these)
```
✅ orders/create
✅ orders/updated
✅ orders/paid
✅ orders/cancelled
✅ products/create
✅ products/update
✅ app/uninstalled
```

## 🧪 **Testing Checklist**

After setup, test these features:

### OAuth Flow
- [ ] Visit: http://localhost:8000/api/v1/shopify/oauth/init
- [ ] Complete OAuth authorization
- [ ] Verify shop connection in dashboard

### API Access
- [ ] Test shop info retrieval
- [ ] Test product listing
- [ ] Test order retrieval

### Webhooks
- [ ] Create a test product in your store
- [ ] Verify webhook received in application logs
- [ ] Test order creation webhook

## 🔐 **Security Notes**

- Generate a random webhook secret: `openssl rand -hex 32`
- Keep API credentials secure and never commit to version control
- Use HTTPS in production
- Regularly rotate webhook secrets

## 📞 **Next Steps**

1. **Create the app** in Shopify Partners
2. **Fill out the credentials** above
3. **Send me the completed configuration**
4. **I'll update the service** with your settings
5. **We'll test together** to ensure everything works

---

**Need Help?**
- Shopify Partner Documentation: https://shopify.dev/apps/getting-started
- Partner Dashboard: https://partners.shopify.com/
- API Documentation: https://shopify.dev/api/admin-rest