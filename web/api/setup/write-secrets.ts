import { VercelRequest, VercelResponse } from '@vercel/node';
import { createClient } from '@vercel/kv';
import sodium from 'libsodium-wrappers';

const kv = createClient({
  url: process.env.KV_REST_API_URL || '',
  token: process.env.KV_REST_API_TOKEN || '',
});

async function getRepoPublicKey(repo: string, token: string) {
  const url = `https://api.github.com/repos/${repo}/actions/secrets/public-key`;
  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github.v3+json',
      'User-Agent': 'SparkJobs-Setup',
    },
  });
  if (!res.ok) return null;
  return await res.json();
}

async function encryptSecretValue(secretValue: string, keyBase64: string) {
  await sodium.ready;
  const binkey = sodium.from_base64(keyBase64, sodium.base64_variants.ORIGINAL);
  const binsec = sodium.from_string(secretValue);
  const encryptedBytes = sodium.crypto_box_seal(binsec, binkey);
  return sodium.to_base64(encryptedBytes, sodium.base64_variants.ORIGINAL);
}

async function putRepoSecret(repo: string, token: string, secretName: string, encryptedValue: string, keyId: string) {
  const url = `https://api.github.com/repos/${repo}/actions/secrets/${secretName}`;
  const res = await fetch(url, {
    method: 'PUT',
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github.v3+json',
      'Content-Type': 'application/json',
      'User-Agent': 'SparkJobs-Setup',
    },
    body: JSON.stringify({
      encrypted_value: encryptedValue,
      key_id: keyId,
    }),
  });
  return res.ok;
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const {
    github_token,
    repo_name,
    gemini_key,
    telegram_token,
    telegram_chat_id,
    scraperapi_key,
    language,
  } = req.body;

  if (!github_token || !repo_name || !telegram_token || !telegram_chat_id) {
    return res.status(400).json({ error: 'Missing required configuration keys' });
  }

  try {
    // 1. Get Repo Public Key from GitHub
    const pubKeyData = await getRepoPublicKey(repo_name, github_token);
    if (!pubKeyData) {
      return res.status(500).json({ error: 'Failed to retrieve repository actions public key from GitHub' });
    }

    const { key, key_id } = pubKeyData;

    // 2. Define secrets to write
    const secretsMap: Record<string, string> = {
      GEMINI_API_KEY: gemini_key || '',
      TELEGRAM_BOT_TOKEN: telegram_token,
      TELEGRAM_CHAT_ID: telegram_chat_id,
      SCRAPERAPI_KEY: scraperapi_key || '',
    };

    // 3. Encrypt and write each secret sequentially
    for (const [name, val] of Object.entries(secretsMap)) {
      const encrypted = await encryptSecretValue(val, key);
      const putOk = await putRepoSecret(repo_name, github_token, name, encrypted, key_id);
      if (!putOk) {
        return res.status(500).json({ error: `Failed to write repository secret: ${name}` });
      }
    }

    // 4. Register mapping in Vercel KV database
    await kv.set(`user:${telegram_chat_id}`, {
      github_repo: repo_name,
      github_token: github_token,
      telegram_bot_token: telegram_token,
      language: language || 'ar',
    });

    // Also register Webhook to Telegram Bot
    const webhookUrl = `${process.env.NEXT_PUBLIC_SITE_URL || ''}/api/telegram/webhook`;
    const tgWebhookSetupUrl = `https://api.telegram.org/bot${telegram_token}/setWebhook?url=${webhookUrl}`;
    await fetch(tgWebhookSetupUrl);

    // Send immediate proactive welcome message on Telegram
    const welcomeMsg = language === 'ar'
      ? `✅ تم تفعيل بوت SparkJobs بنجاح على حسابك.\n\nسيقوم البوت بفحص منصات التوظيف وإرسال التنبيهات لك هنا تلقائياً.\nللتحكم في البوت وإدارته، اكتب /help في أي وقت.`
      : `✅ SparkJobs is now active on your account.\n\nYour bot will scan job boards every 20 minutes and alert you here.\nTo manage your bot, type /help at any time.`;
    const tgSendMessageUrl = `https://api.telegram.org/bot${telegram_token}/sendMessage`;
    try {
      await fetch(tgSendMessageUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chat_id: telegram_chat_id,
          text: welcomeMsg,
        }),
      });
    } catch (e) {
      console.error('Failed to send Telegram welcome message:', e);
    }

    return res.status(200).json({ success: true });
  } catch (error) {
    console.error('Error writing secrets or saving configuration:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}
