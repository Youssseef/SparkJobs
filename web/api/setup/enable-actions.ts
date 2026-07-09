import { VercelRequest, VercelResponse } from '@vercel/node';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { github_token, repo_name } = req.body;

  if (!github_token || !repo_name) {
    return res.status(400).json({ error: 'Missing required parameters' });
  }

  // We want to trigger a manual run of 'scan.yml' workflow in GitHub Actions
  const url = `https://api.github.com/repos/${repo_name}/actions/workflows/scan.yml/dispatches`;

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${github_token}`,
        Accept: 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
        'User-Agent': 'SparkJobs-Setup',
      },
      body: JSON.stringify({
        ref: 'main', // Default branch
      }),
    });

    if (response.status === 204) {
      return res.status(200).json({ success: true, message: 'Actions workflow triggered successfully' });
    } else {
      const errorText = await response.text();
      return res.status(response.status).json({
        error: errorText || 'Failed to trigger Actions workflow. Ensure Action permissions are enabled on the repository.',
      });
    }
  } catch (error) {
    console.error('Error triggering actions workflow:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}
