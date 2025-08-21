import type { NextApiRequest, NextApiResponse } from 'next';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'POST') {
    // For development, simulate successful OAuth initiation
    res.status(200).json({
      auth_url: `/api/v1/etsy/oauth/callback?state=demo-state&code=demo-code`,
      state: 'demo-state',
      message: 'Development OAuth simulation - click the auth_url to complete connection'
    });
  } else {
    res.setHeader('Allow', ['POST']);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}