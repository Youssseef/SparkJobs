import { VercelRequest, VercelResponse } from '@vercel/node';

async function getFileSha(repo: string, path: string, token: string): Promise<string | null> {
  const url = `https://api.github.com/repos/${repo}/contents/${path}`;
  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github.v3+json',
      'User-Agent': 'SparkJobs-Setup',
    },
  });
  if (!res.ok) return null;
  const data = await res.json();
  return data.sha;
}

async function writeGithubFile(repo: string, path: string, token: string, base64Content: string, message: string) {
  const sha = await getFileSha(repo, path, token);
  const url = `https://api.github.com/repos/${repo}/contents/${path}`;
  
  const body: any = {
    message,
    content: base64Content,
  };
  if (sha) {
    body.sha = sha;
  }

  const res = await fetch(url, {
    method: 'PUT',
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github.v3+json',
      'Content-Type': 'application/json',
      'User-Agent': 'SparkJobs-Setup',
    },
    body: JSON.stringify(body),
  });
  
  return res.ok;
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { github_token, repo_name, config_data, cv_filename, cv_base64 } = req.body;

  if (!github_token || !repo_name || !config_data || !cv_filename || !cv_base64) {
    return res.status(400).json({ error: 'Missing required configuration parameters' });
  }

  try {
    // 1. Commit config.json
    const configBase64 = Buffer.from(JSON.stringify(config_data, null, 2)).toString('base64');
    const writeConfigOk = await writeGithubFile(
      repo_name,
      'data/config.json',
      github_token,
      configBase64,
      'setup: initialize search profiles'
    );

    if (!writeConfigOk) {
      return res.status(500).json({ error: 'Failed to write data/config.json file to GitHub' });
    }

    // 2. Commit CV file to data/cvs/
    const writeCvOk = await writeGithubFile(
      repo_name,
      `data/cvs/${cv_filename}`,
      github_token,
      cv_base64,
      'setup: upload candidate resume'
    );

    if (!writeCvOk) {
      return res.status(500).json({ error: 'Failed to write CV file to GitHub' });
    }

    return res.status(200).json({ success: true });
  } catch (error) {
    console.error('Error committing configuration files:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}
