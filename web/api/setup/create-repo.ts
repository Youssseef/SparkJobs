import { VercelRequest, VercelResponse } from '@vercel/node';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { github_token, repo_name } = req.body;

  if (!github_token || !repo_name) {
    return res.status(400).json({ error: 'Missing github_token or repo_name' });
  }

  const templateOwner = process.env.GITHUB_TEMPLATE_OWNER || 'sparkgen-net';
  const templateRepo = process.env.GITHUB_TEMPLATE_REPO || 'sparkjobs-bot';

  // Endpoint to create a repository from a template repository
  const url = `https://api.github.com/repos/${templateOwner}/${templateRepo}/generate`;

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
        name: repo_name,
        description: 'SparkJobs personal job alert scanner bot',
        private: true, // Crucial for privacy
        include_all_branches: false,
      }),
    });

    if (response.status === 201) {
      const data = await response.json();
      return res.status(201).json({
        success: true,
        full_name: data.full_name,
        clone_url: data.clone_url,
      });
    } else {
      const errorData = await response.json();
      return res.status(response.status).json({
        error: errorData.message || 'Failed to create repository from template',
      });
    }
  } catch (error) {
    console.error('Error creating repository:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}
