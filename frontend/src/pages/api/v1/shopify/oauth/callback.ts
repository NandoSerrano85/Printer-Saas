import type { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    const { shop, state, code } = req.query;
    
    if (!shop || !code) {
      return res.status(400).json({
        error: 'Missing required parameters: shop and code'
      });
    }
    
    // For development, simulate successful OAuth completion
    // In production, this would exchange the code for an access token
    
    // Simulate saving the connection by calling the status endpoint
    const mockConnection = {
      shop_domain: shop as string,
      connected: true,
      access_token: 'demo-access-token',
      shop_name: `Demo Shop (${shop})`,
      connected_at: new Date().toISOString()
    };
    
    // Update the connection state via internal API call
    try {
      await fetch(`${req.headers.origin || 'http://localhost:3000'}/api/v1/shopify/integration/status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ shop_domain: shop })
      });
    } catch (error) {
      console.log('Error updating connection state:', error);
    }
    
    // Return success page that auto-closes and refreshes parent
    const successPage = `
      <!DOCTYPE html>
      <html>
        <head>
          <title>Shopify Connection Successful</title>
          <style>
            body { 
              font-family: system-ui, -apple-system, sans-serif; 
              display: flex; 
              justify-content: center; 
              align-items: center; 
              height: 100vh; 
              margin: 0; 
              background: #f3f4f6;
            }
            .container {
              background: white;
              padding: 2rem;
              border-radius: 8px;
              box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
              text-align: center;
              max-width: 400px;
            }
            .success { color: #059669; font-size: 1.5rem; margin-bottom: 1rem; }
            .info { color: #374151; margin-bottom: 1rem; }
            .loading { color: #6b7280; font-size: 0.875rem; }
          </style>
        </head>
        <body>
          <div class="container">
            <div class="success">✅ Successfully Connected!</div>
            <div class="info">Your Shopify store <strong>${shop}</strong> has been connected.</div>
            <div class="loading">Redirecting back to the application...</div>
          </div>
          <script>
            // Close this window and refresh the parent page
            setTimeout(() => {
              if (window.opener) {
                window.opener.location.reload();
                window.close();
              } else {
                window.location.href = '/integrations';
              }
            }, 2000);
          </script>
        </body>
      </html>
    `;
    
    res.setHeader('Content-Type', 'text/html');
    res.status(200).send(successPage);
  } else {
    res.setHeader('Allow', ['GET']);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}