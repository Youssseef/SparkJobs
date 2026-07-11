import { VercelRequest, VercelResponse } from '@vercel/node';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { bot_token, chat_id, language = 'ar' } = req.body;

  if (!bot_token || !chat_id) {
    return res.status(400).json({ error: 'Missing bot_token or chat_id' });
  }

  const message = language === 'ar'
    ? `✅ <b>SparkJobs — رسالة تجريبية</b>\n\n` +
      `مرحباً! هذه رسالة اختبار تأكيدية من البوت الخاص بك.\n\n` +
      `<b>مثال على تنبيه وظيفي:</b>\n\n` +
      `<b>Senior Frontend Engineer</b>\n` +
      `<b>Notion</b> · Remote\n` +
      `المصدر: LinkedIn\n\n` +
      `──────────────────\n` +
      `تقييم الأمان: 🟢 <b>مخاطر منخفضة</b>\n\n` +
      `الراتب التقديري: $110,000 - $140,000\n\n` +
      `توافق الـ CV: 87%\n` +
      `<b>✅ نقاط القوة:</b>\n• خبرة React قوية\n• تجربة مع Design Systems\n\n` +
      `──────────────────\n` +
      `البوت يعمل بنجاح ومتصل بحسابك. ستصلك تنبيهات الوظائف الحقيقية تلقائياً.\n\n` +
      `─────────────────\nPowered by <a href="https://sparkgen.net">SparkGen</a>`
    : `✅ <b>SparkJobs — Test Alert</b>\n\n` +
      `Hi! This is a confirmation test message from your bot.\n\n` +
      `<b>Sample Job Alert:</b>\n\n` +
      `<b>Senior Frontend Engineer</b>\n` +
      `<b>Notion</b> · Remote\n` +
      `Source: LinkedIn\n\n` +
      `──────────────────\n` +
      `Safety Rating: 🟢 <b>LOW RISK</b>\n\n` +
      `Est. Salary: $110,000 - $140,000\n\n` +
      `CV Match Score: 87%\n` +
      `<b>✅ Strengths:</b>\n• Strong React experience\n• Design Systems background\n\n` +
      `──────────────────\n` +
      `Your bot is live and connected. Real job alerts will arrive automatically.\n\n` +
      `─────────────────\nPowered by <a href="https://sparkgen.net">SparkGen</a>`;

  try {
    const tgRes = await fetch(`https://api.telegram.org/bot${bot_token}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id,
        text: message,
        parse_mode: 'HTML',
        disable_web_page_preview: true,
      }),
    });

    const tgData = await tgRes.json();

    if (!tgRes.ok) {
      return res.status(400).json({
        error: tgData.description || 'Failed to send test message. Check your Bot Token and Chat ID.',
      });
    }

    return res.status(200).json({ success: true });
  } catch (err: any) {
    return res.status(500).json({ error: err.message || 'Internal server error' });
  }
}
