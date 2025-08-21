import type { NextApiRequest, NextApiResponse } from 'next';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    res.status(200).json({
      revenue: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        data: [1200, 1900, 3000, 5000, 2000, 3000]
      },
      orders: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        data: [12, 19, 30, 50, 20, 30]
      },
      top_products: [
        { name: 'Custom T-Shirt', sales: 45 },
        { name: 'Business Cards', sales: 32 },
        { name: 'Poster Print', sales: 28 }
      ]
    });
  } else {
    res.setHeader('Allow', ['GET']);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}