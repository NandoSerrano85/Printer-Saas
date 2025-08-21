import type { NextApiRequest, NextApiResponse } from 'next';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    res.status(200).json({
      templates: []
    });
  } else if (req.method === 'POST') {
    res.status(201).json({
      id: Date.now().toString(),
      ...req.body,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      usage_count: 0
    });
  } else {
    res.setHeader('Allow', ['GET', 'POST']);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}