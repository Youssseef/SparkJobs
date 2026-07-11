import { VercelRequest, VercelResponse } from '@vercel/node';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { gemini_key } = req.body;

  if (!gemini_key) {
    return res.status(400).json({ error: 'Missing required parameter: gemini_key' });
  }

  const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${gemini_key}`;

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        contents: [
          {
            parts: [
              {
                text: 'ping'
              }
            ]
          }
        ]
      })
    });

    if (response.ok) {
      return res.status(200).json({ success: true });
    } else {
      const errorData = await response.json().catch(() => ({}));
      const errorMsg = errorData.error?.message || 'Invalid Gemini API Key or access denied';
      return res.status(response.status).json({ success: false, error: errorMsg });
    }
  } catch (error: any) {
    console.error('Error validating Gemini key:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}
