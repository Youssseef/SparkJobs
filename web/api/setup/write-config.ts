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

async function getFileShaAndContent(repo: string, path: string, token: string) {
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
  return {
    sha: data.sha,
    content: Buffer.from(data.content, 'base64').toString('utf-8')
  };
}

async function writeGithubFile(repo: string, path: string, token: string, base64Content: string, message: string, existingSha?: string) {
  const sha = existingSha || await getFileSha(repo, path, token);
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

async function updateWorkflowSchedule(repo: string, token: string, frequency: string) {
  const path = '.github/workflows/scan.yml';
  const fileData = await getFileShaAndContent(repo, path, token);
  if (!fileData) {
    console.log('scan.yml workflow file not found in repo.');
    return false;
  }
  
  let cronExpr = '*/20 * * * *';
  if (frequency === '1h') cronExpr = '0 * * * *';
  else if (frequency === '6h') cronExpr = '0 */6 * * *';
  else if (frequency === '1d') cronExpr = '0 0 * * *';
  
  const content = fileData.content;
  // Regex to replace cron: '...' or cron: "..."
  const updatedContent = content.replace(/cron:\s*['"]([^'"]+)['"]/g, `cron: '${cronExpr}'`);
  
  const base64Content = Buffer.from(updatedContent).toString('base64');
  return writeGithubFile(repo, path, token, base64Content, `setup: update scan frequency to ${frequency}`, fileData.sha);
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { github_token, repo_name, config_data, cv_filename, cv_base64, cover_letter_base64 } = req.body;

  if (!github_token || !repo_name || !config_data) {
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

    // 2. Commit CV file to data/cvs/ if provided
    if (cv_filename && cv_base64) {
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
    }

    // 3. Commit Cover Letter file to data/ if present
    if (cover_letter_base64) {
      const writeClOk = await writeGithubFile(
        repo_name,
        'data/cover_letter.txt',
        github_token,
        cover_letter_base64,
        'setup: save candidate cover letter inspiration'
      );
      if (!writeClOk) {
        return res.status(500).json({ error: 'Failed to write cover letter file to GitHub' });
      }
    }

    // 4. Update workflow cron schedule if custom scan frequency is provided
    const frequency = config_data.global_search?.scan_frequency || config_data.profiles?.[0]?.scan_frequency;
    if (frequency) {
      try {
        await updateWorkflowSchedule(repo_name, github_token, frequency);
      } catch (e) {
        console.error('Failed to update workflow schedule:', e);
      }
    }

    return res.status(200).json({ success: true });
  } catch (error) {
    console.error('Error committing configuration files:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}
