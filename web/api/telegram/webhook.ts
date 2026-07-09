import { VercelRequest, VercelResponse } from '@vercel/node';
import { createClient } from '@vercel/kv';

// Initialize Vercel KV Client using env variables
const kv = createClient({
  url: process.env.KV_REST_API_URL || '',
  token: process.env.KV_REST_API_TOKEN || '',
});

// Helper: Fetch file content from GitHub API
async function getGithubFile(repo: string, path: string, token: string) {
  const url = `https://api.github.com/repos/${repo}/contents/${path}`;
  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github.v3+json',
      'User-Agent': 'SparkJobs-Webhook',
    },
  });
  if (!res.ok) return null;
  const data = await res.json();
  const content = Buffer.from(data.content, 'base64').toString('utf-8');
  return { content, sha: data.sha };
}

// Helper: Update file in GitHub API
async function updateGithubFile(repo: string, path: string, token: string, content: string, sha: string, message: string) {
  const url = `https://api.github.com/repos/${repo}/contents/${path}`;
  const res = await fetch(url, {
    method: 'PUT',
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github.v3+json',
      'Content-Type': 'application/json',
      'User-Agent': 'SparkJobs-Webhook',
    },
    body: JSON.stringify({
      message,
      content: Buffer.from(content).toString('base64'),
      sha,
    }),
  });
  return res.ok;
}

// Helper: Send message to Telegram
async function sendTelegramMessage(botToken: string, chatId: number, text: string) {
  const url = `https://api.telegram.org/bot${botToken}/sendMessage`;
  await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chat_id: chatId,
      text,
      parse_mode: 'HTML',
    }),
  });
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const update = req.body;
  if (!update || !update.message) {
    return res.status(200).send('No message found');
  }

  const chatId = update.message.chat.id;
  const text = update.message.text || '';

  // Get user credentials from Vercel KV
  const userConfig: any = await kv.get(`user:${chatId}`);
  if (!userConfig) {
    // If not configured yet, notify them
    const botToken = process.env.TELEGRAM_BOT_TOKEN || '';
    if (text.startsWith('/start')) {
      await sendTelegramMessage(
        botToken,
        chatId,
        `👋 أهلاً بك في <b>SparkJobs</b>!\n\nيرجى إكمال الإعداد أولاً من موقعنا الرسمي لتتمكن من استخدام البوت:\n🔗 <a href="${process.env.NEXT_PUBLIC_SITE_URL || ''}">${process.env.NEXT_PUBLIC_SITE_URL || 'sparkjobs.app'}</a>`
      );
    }
    return res.status(200).send('User not configured');
  }

  const { github_repo, github_token, telegram_bot_token } = userConfig;

  // Command Router
  try {
    if (text.startsWith('/start') || text.startsWith('/help')) {
      const helpMsg = `🤖 <b>أوامر التحكم في البوت:</b>\n\n` +
        `/profiles — عرض كل الـ Profiles الوظيفية وحالتها\n` +
        `/pause [Index] — إيقاف مؤقت لـ Profile معين (مثال: <code>/pause 0</code>)\n` +
        `/resume [Index] — تشغيل الـ Profile الموقوف (مثال: <code>/resume 0</code>)\n` +
        `/status — فحص حالة التشغيل والمزامنة\n` +
        `\n🌐 <a href="${process.env.NEXT_PUBLIC_SITE_URL || ''}">زيارة موقعنا الرسمي للمزيد من الأدوات</a>`;
      await sendTelegramMessage(telegram_bot_token, chatId, helpMsg);
    } 
    
    else if (text.startsWith('/profiles')) {
      const fileData = await getGithubFile(github_repo, 'data/config.json', github_token);
      if (!fileData) {
        await sendTelegramMessage(telegram_bot_token, chatId, '❌ فشل قراءة الإعدادات من GitHub. تأكد من صلاحية الـ Token.');
        return res.status(200).send('OK');
      }

      const config = JSON.parse(fileData.content);
      const profiles = config.profiles || [];
      
      if (profiles.length === 0) {
        await sendTelegramMessage(telegram_bot_token, chatId, '⚠️ لا توجد Profiles وظيفية مضافة حالياً.');
        return res.status(200).send('OK');
      }

      let responseText = `📋 <b>الـ Profiles الحالية الخاصة بك:</b>\n\n`;
      profiles.forEach((p: any, idx: number) => {
        const status = p.active ? '🟢 نشط' : '🔴 موقوف';
        responseText += `<b>[${idx}] - ${p.name}</b>\n`;
        responseText += `• الحالة: ${status}\n`;
        responseText += `• المسمى: ${p.job_titles.join(', ')}\n`;
        responseText += `• البلدان: ${p.countries.join(', ')}\n\n`;
      });
      
      await sendTelegramMessage(telegram_bot_token, chatId, responseText);
    } 
    
    else if (text.startsWith('/pause') || text.startsWith('/resume')) {
      const isPause = text.startsWith('/pause');
      const index = parseInt(text.split(' ')[1]);
      
      if (isNaN(index)) {
        await sendTelegramMessage(telegram_bot_token, chatId, `⚠️ يرجى تحديد رقم الـ Profile. مثال: <code>${isPause ? '/pause' : '/resume'} 0</code>`);
        return res.status(200).send('OK');
      }

      const fileData = await getGithubFile(github_repo, 'data/config.json', github_token);
      if (!fileData) {
        await sendTelegramMessage(telegram_bot_token, chatId, '❌ فشل الاتصال بمستودع GitHub.');
        return res.status(200).send('OK');
      }

      const config = JSON.parse(fileData.content);
      const profiles = config.profiles || [];

      if (index < 0 || index >= profiles.length) {
        await sendTelegramMessage(telegram_bot_token, chatId, `❌ الرقم غير صحيح. أقصى رقم متاح هو ${profiles.length - 1}.`);
        return res.status(200).send('OK');
      }

      profiles[index].active = !isPause;
      const updatedContent = JSON.stringify(config, null, 2);
      
      const success = await updateGithubFile(
        github_repo,
        'data/config.json',
        github_token,
        updatedContent,
        fileData.sha,
        `update: ${isPause ? 'Pause' : 'Resume'} profile [${index}] via Telegram`
      );

      if (success) {
        await sendTelegramMessage(
          telegram_bot_token,
          chatId,
          `✅ تم ${isPause ? 'إيقاف' : 'تشغيل'} الـ Profile [<b>${profiles[index].name}</b>] بنجاح.`
        );
      } else {
        await sendTelegramMessage(telegram_bot_token, chatId, '❌ فشل تحديث الملف على GitHub.');
      }
    } 
    
    else if (text.startsWith('/status')) {
      // Fetch workflow runs using Github API
      const url = `https://api.github.com/repos/${github_repo}/actions/runs?per_page=1`;
      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${github_token}`,
          Accept: 'application/vnd.github.v3+json',
          'User-Agent': 'SparkJobs-Webhook',
        },
      });
      
      let workflowStatus = '🔴 غير نشط';
      if (response.ok) {
        const data = await response.json();
        const runs = data.workflow_runs || [];
        if (runs.length > 0) {
          const lastRun = runs[0];
          workflowStatus = lastRun.status === 'completed' && lastRun.conclusion === 'success' 
            ? `🟢 نشط ويعمل بنجاح (آخر تشغيل: ${new Date(lastRun.updated_at).toLocaleTimeString()})`
            : `🟡 في وضع التشغيل أو به تنبيهات (${lastRun.status})`;
        }
      }
      
      const statusMsg = `ℹ️ <b>حالة نظام التوظيف الخاص بك:</b>\n\n` +
        `• المستودع: <code>${github_repo}</code>\n` +
        `• حالة التحديث التلقائي: ${workflowStatus}\n` +
        `• حساب التليجرام: مرتبط بنجاح ✅`;
      await sendTelegramMessage(telegram_bot_token, chatId, statusMsg);
    }
  } catch (error) {
    console.error('Error handling webhook update:', error);
  }

  return res.status(200).send('OK');
}
