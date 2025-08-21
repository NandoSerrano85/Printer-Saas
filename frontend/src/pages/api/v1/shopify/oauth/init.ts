import type { NextApiRequest, NextApiResponse } from 'next';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'POST') {
    const { shop_domain } = req.body;
    
    if (!shop_domain) {
      return res.status(400).json({
        error: 'shop_domain is required'
      });
    }
    
    // For development, simulate successful OAuth initiation
    res.status(200).json({
      auth_url: `/api/v1/shopify/oauth/callback?shop=${encodeURIComponent(shop_domain)}&state=demo-state&code=demo-code`,
      shop_domain,
      state: 'demo-state',
      message: 'Development OAuth simulation - click the auth_url to complete connection'
    });
  } else {
    res.setHeader('Allow', ['POST']);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}