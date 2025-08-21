import type { NextApiRequest, NextApiResponse } from 'next';

// Simple in-memory storage for demo (in production, use database)
let shopifyConnection: any = null;

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    // Check if we have a stored connection from a previous OAuth flow
    const hasStoredConnection = typeof window !== 'undefined' && 
      localStorage.getItem('shopify_connected') === 'true';
    
    if (shopifyConnection || hasStoredConnection) {
      res.status(200).json({
        connected: true,
        shop_name: shopifyConnection?.shop_name || 'Demo Shopify Store',
        shop_domain: shopifyConnection?.shop_domain || 'demo-store.myshopify.com',
        last_sync: shopifyConnection?.last_sync || new Date().toISOString(),
        error_message: null,
        products_count: 156,
        orders_count: 89,
        collections_count: 12
      });
    } else {
      res.status(200).json({
        connected: false,
        shop_name: null,
        shop_domain: null,
        last_sync: null,
        error_message: null
      });
    }
  } else if (req.method === 'POST') {
    // Simulate connecting
    const { shop_domain } = req.body;
    shopifyConnection = {
      connected: true,
      shop_name: `Demo Store (${shop_domain})`,
      shop_domain,
      last_sync: new Date().toISOString(),
      connected_at: new Date().toISOString()
    };
    
    res.status(200).json(shopifyConnection);
  } else if (req.method === 'DELETE') {
    // Simulate disconnecting
    shopifyConnection = null;
    
    res.status(200).json({
      connected: false,
      shop_name: null,
      shop_domain: null,
      last_sync: null,
      error_message: null
    });
  } else {
    res.setHeader('Allow', ['GET', 'POST', 'DELETE']);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}

// Export the connection state for other modules to use
export { shopifyConnection };