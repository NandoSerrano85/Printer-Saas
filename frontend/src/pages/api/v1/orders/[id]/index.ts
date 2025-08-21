import type { NextApiRequest, NextApiResponse } from 'next';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  const { id } = req.query;

  if (req.method === 'GET') {
    res.status(200).json({
      id,
      order_number: `ORD-${id}`,
      platform: 'manual',
      customer_email: 'customer@example.com',
      customer_name: 'John Doe',
      total_amount: 50.00,
      currency: 'USD',
      status: 'pending',
      items: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    });
  } else if (req.method === 'PUT') {
    res.status(200).json({
      id,
      ...req.body,
      updated_at: new Date().toISOString()
    });
  } else {
    res.setHeader('Allow', ['GET', 'PUT']);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}