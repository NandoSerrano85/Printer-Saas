import type { NextApiRequest, NextApiResponse } from 'next';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    res.status(200).json({
      total_orders: 0,
      total_revenue: 0,
      active_templates: 0,
      integration_status: {
        shopify: false,
        etsy: false,
      },
      recent_orders: []
    });
  } else {
    res.setHeader('Allow', ['GET']);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}