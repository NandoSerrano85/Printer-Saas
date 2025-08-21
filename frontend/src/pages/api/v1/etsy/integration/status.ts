import type { NextApiRequest, NextApiResponse } from 'next';

// Simple in-memory storage for demo (in production, use database)
let etsyConnection: any = null;

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    // Check if we have a stored connection from a previous OAuth flow
    const hasStoredConnection = typeof window !== 'undefined' && 
      localStorage.getItem('etsy_connected') === 'true';
    
    if (etsyConnection || hasStoredConnection) {
      res.status(200).json({
        connected: true,
        shop_name: etsyConnection?.shop_name || 'Demo Etsy Shop',
        shop_id: etsyConnection?.shop_id || 'demo-shop-id',
        last_sync: etsyConnection?.last_sync || new Date().toISOString(),
        error_message: null,
        listings_count: 234,
        orders_count: 67
      });
    } else {
      res.status(200).json({
        connected: false,
        shop_name: null,
        shop_id: null,
        last_sync: null,
        error_message: null
      });
    }
  } else if (req.method === 'POST') {
    // Simulate connecting
    etsyConnection = {
      connected: true,
      shop_name: 'Demo Etsy Shop',
      shop_id: 'demo-shop-id',
      last_sync: new Date().toISOString(),
      connected_at: new Date().toISOString()
    };
    
    res.status(200).json(etsyConnection);
  } else if (req.method === 'DELETE') {
    // Simulate disconnecting
    etsyConnection = null;
    
    res.status(200).json({
      connected: false,
      shop_name: null,
      shop_id: null,
      last_sync: null,
      error_message: null
    });
  } else {
    res.setHeader('Allow', ['GET', 'POST', 'DELETE']);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}

// Export the connection state for other modules to use
export { etsyConnection };