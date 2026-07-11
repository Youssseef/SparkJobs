import { VercelRequest, VercelResponse } from '@vercel/node';
import { createClient } from '@vercel/kv';

// Initialize Vercel KV Client using env variables
const kv = createClient({
  url: process.env.KV_REST_API_URL || '',
  token: process.env.KV_REST_API_TOKEN || '',
});

const SPARKGEN_FOOTER = `\n\n─────────────────\nPowered by <a href="https://sparkgen.net">SparkGen</a>`;

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
    body: JSON.stringify({ message, content: Buffer.from(content).toString('base64'), sha }),
  });
  return res.ok;
}

// Helper: Trigger GitHub Actions workflow dispatch (manual scan)
async function triggerGithubWorkflow(repo: string, token: string, workflowFile: string = 'scan.yml'): Promise<boolean> {
  const url = `https://api.github.com/repos/${repo}/actions/workflows/${workflowFile}/dispatches`;
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github.v3+json',
      'Content-Type': 'application/json',
      'User-Agent': 'SparkJobs-Webhook',
    },
    body: JSON.stringify({ ref: 'main' }),
  });
  return res.ok || res.status === 204;
}

// Helper: Send message to Telegram
async function sendTelegramMessage(botToken: string, chatId: number, text: string, disablePreview: boolean = true) {
  const url = `https://api.telegram.org/bot${botToken}/sendMessage`;
  await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chat_id: chatId,
      text,
      parse_mode: 'HTML',
      disable_web_page_preview: disablePreview,
    }),
  });
}

// Bilingual command response strings
const WEBHOOK_STRINGS = {
  ar: {
    helpTitle: (name: string) => `أهلاً <b>${name}</b>! مساعدك الشخصي يعمل بنجاح الآن`,
    helpBody: (siteUrl: string) =>
      `كيف يبحث البوت؟\n` +
      `يقرأ البوت ملف الـ CV والـ Cover Letter الحقيقيين اللذين رفعتهما ويطابقهما مع كل وظيفة تُنشر حديثاً كل 20 دقيقة.\n\n` +
      `<b>التحكم السريع (الأوامر):</b>\n\n` +
      `/scan\n   <i>لتشغيل فحص فوري للوظائف الآن دون انتظار الـ 20 دقيقة</i>\n\n` +
      `/profiles\n   <i>لعرض ملفات البحث والبلدان المستهدفة حالياً</i>\n\n` +
      `/status\n   <i>لفحص حالة التشغيل وتفاصيل آخر عملية بحث ناجحة</i>\n\n` +
      `/pause [رقم]\n   <i>لإيقاف ملف بحث مؤقتاً (مثال: /pause 0)</i>\n\n` +
      `/resume [رقم]\n   <i>لإعادة تشغيل ملف بحث موقوف (مثال: /resume 0)</i>\n\n` +
      `/deleteaccount\n   <i>حذف حسابك وبياناتك من النظام نهائياً</i>\n\n` +
      `<b>تعديل الـ CV أو الإعدادات:</b>\n` +
      `لتحديث سيرتك الذاتية، رسالة التغطية، أو تعديل الكلمات المفتاحية، افتح لوحة التحكم:\n` +
      `رابط الموقع: <a href="${siteUrl}">${siteUrl}</a>`,
    scanAck: `🔍 <b>جاري تشغيل فحص وظائف فوري...</b>\n\n⏳ سيأخذ دقيقتين تقريباً. ستصلك تنبيهات للوظايف المناسبة فوراً لو فيه حاجة جديدة!`,
    scanOk: `✅ <b>تم إطلاق الفحص بنجاح!</b>\n\nGitHub Actions بدأ يشتغل دلوقتي على مستودعك الخاص.\nاكتب /status تعرف أخر أخبار التشغيل.`,
    scanFail: `❌ <b>فشل تشغيل الفحص.</b>\n\nتأكد إن الـ GitHub Token لسه صالح وإن الـ Workflow موجود في المستودع.\nاكتب /status للمزيد من التفاصيل.`,
    profilesEmpty: `⚠️ لا توجد Profiles وظيفية مضافة حالياً.\nافتح لوحة التحكم لإضافة بحث جديد.`,
    profilesHeader: `<b>الـ Profiles الوظيفية بتاعتك:</b>\n\n`,
    profileActive: '🟢 نشط',
    profilePaused: '🔴 موقوف',
    profileFooter: `<i>لإيقاف Profile: /pause [رقم] — لتشغيله: /resume [رقم]</i>`,
    pauseNeedIndex: (cmd: string) => `⚠️ يرجى تحديد رقم الـ Profile.\n مثال: <code>${cmd} 0</code>`,
    pauseConnFail: `❌ فشل الاتصال بمستودع GitHub.`,
    pauseOutOfRange: (len: number) => `❌ الرقم غير صحيح. الأرقام المتاحة: 0 إلى ${len - 1}.`,
    pauseOk: (action: string, name: string) => `✅ تم <b>${action}</b> الـ Profile [<b>${name}</b>] بنجاح.`,
    pauseActionPause: 'إيقاف',
    pauseActionResume: 'تشغيل',
    pauseFileFail: `❌ فشل تحديث الملف على GitHub.`,
    statusNoRun: '🔴 لا يوجد تشغيل مسجّل بعد',
    statusOk: '🟢 يعمل بنجاح',
    statusRunning: '🟡 يعمل الآن...',
    statusFail: (c: string) => `🔴 فشل أو توقف (${c})`,
    statusLastRun: (t: string) => `آخر تشغيل ناجح: ${t}`,
    statusStarted: (t: string) => `بدأ في: ${t}`,
    statusAt: (t: string) => `في: ${t}`,
    statusMsg: (repo: string, wf: string, last: string) =>
      `📊 <b>حالة نظام SparkJobs:</b>\n\n` +
      `• المستودع: <code>${repo}</code>\n` +
      `• حالة GitHub Actions: ${wf}\n` +
      `${last}` +
      `• تليجرام: مرتبط ✅\n\n` +
      `<i>البوت يفحص تلقائياً كل 20 دقيقة.\nاكتب /scan لتشغيل فحص فوري.</i>`,
    deleteConfirm: `⚠️ <b>هل أنت متأكد؟</b>\n\nسيتم حذف جميع بيانات حسابك من النظام نهائياً. هذا الإجراء لا يمكن التراجع عنه.\n\nأرسل <code>نعم، احذف حسابي</code> للتأكيد، أو أي رسالة أخرى للإلغاء.`,
    deleteSuccess: `✅ تم حذف حسابك وجميع بياناتك من النظام بنجاح. شكراً لاستخدامك SparkJobs.`,
    deleteCancelled: `تم إلغاء العملية. حسابك لا يزال نشطاً.`,
    unknownCmd: `❓ أمر غير معروف.\nاكتب /help لعرض الأوامر المتاحة.`,
    configFail: `❌ فشل قراءة الإعدادات من GitHub.\n تأكد من صلاحية الـ Token.`,
  },
  en: {
    helpTitle: (name: string) => `Hello <b>${name}</b>! Your personal bot is running successfully`,
    helpBody: (siteUrl: string) =>
      `How does the bot work?\n` +
      `The bot reads your uploaded CV and Cover Letter and matches them against every new job posting published in the last 24 hours.\n\n` +
      `<b>Quick Controls (Commands):</b>\n\n` +
      `/scan\n   <i>Trigger an immediate job scan without waiting 20 minutes</i>\n\n` +
      `/profiles\n   <i>View your active search profiles and target countries</i>\n\n` +
      `/status\n   <i>Check system status and last successful scan details</i>\n\n` +
      `/pause [number]\n   <i>Pause a search profile (e.g. /pause 0)</i>\n\n` +
      `/resume [number]\n   <i>Resume a paused search profile (e.g. /resume 0)</i>\n\n` +
      `/deleteaccount\n   <i>Permanently delete your account and data from the system</i>\n\n` +
      `<b>Update CV or Settings:</b>\n` +
      `To update your resume, cover letter, or keywords, open the dashboard:\n` +
      `Dashboard: <a href="${siteUrl}">${siteUrl}</a>`,
    scanAck: `🔍 <b>Running an immediate job scan...</b>\n\n⏳ This will take about 2 minutes. You'll receive alerts for any matching new jobs!`,
    scanOk: `✅ <b>Scan launched successfully!</b>\n\nGitHub Actions is now running on your private repository.\nType /status to check the latest run details.`,
    scanFail: `❌ <b>Failed to trigger scan.</b>\n\nMake sure your GitHub Token is still valid and the Workflow exists in the repository.\nType /status for more details.`,
    profilesEmpty: `⚠️ No job search profiles configured yet.\nOpen the dashboard to add a new search profile.`,
    profilesHeader: `<b>Your Job Search Profiles:</b>\n\n`,
    profileActive: '🟢 Active',
    profilePaused: '🔴 Paused',
    profileFooter: `<i>To pause a profile: /pause [number] — To resume: /resume [number]</i>`,
    pauseNeedIndex: (cmd: string) => `⚠️ Please specify a profile number.\n Example: <code>${cmd} 0</code>`,
    pauseConnFail: `❌ Failed to connect to GitHub repository.`,
    pauseOutOfRange: (len: number) => `❌ Invalid number. Available range: 0 to ${len - 1}.`,
    pauseOk: (action: string, name: string) => `✅ Profile [<b>${name}</b>] has been <b>${action}</b> successfully.`,
    pauseActionPause: 'paused',
    pauseActionResume: 'resumed',
    pauseFileFail: `❌ Failed to update the file on GitHub.`,
    statusNoRun: '🔴 No runs recorded yet',
    statusOk: '🟢 Running successfully',
    statusRunning: '🟡 Running now...',
    statusFail: (c: string) => `🔴 Failed or stopped (${c})`,
    statusLastRun: (t: string) => `Last successful run: ${t}`,
    statusStarted: (t: string) => `Started at: ${t}`,
    statusAt: (t: string) => `At: ${t}`,
    statusMsg: (repo: string, wf: string, last: string) =>
      `📊 <b>SparkJobs System Status:</b>\n\n` +
      `• Repository: <code>${repo}</code>\n` +
      `• GitHub Actions: ${wf}\n` +
      `${last}` +
      `• Telegram: Connected ✅\n\n` +
      `<i>The bot scans automatically every 20 minutes.\nType /scan to trigger an immediate scan.</i>`,
    deleteConfirm: `⚠️ <b>Are you sure?</b>\n\nThis will permanently delete all your account data from the system. This action cannot be undone.\n\nSend <code>yes, delete my account</code> to confirm, or any other message to cancel.`,
    deleteSuccess: `✅ Your account and all data have been permanently deleted. Thank you for using SparkJobs.`,
    deleteCancelled: `Operation cancelled. Your account is still active.`,
    unknownCmd: `❓ Unknown command.\nType /help to see available commands.`,
    configFail: `❌ Failed to read config from GitHub.\n Make sure your Token is still valid.`,
  }
};

// Helper: Register bot commands with Telegram (auto-branding)
async function registerBotCommands(botToken: string) {
  const url = `https://api.telegram.org/bot${botToken}/setMyCommands`;
  await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      commands: [
        { command: 'start',         description: '🚀 بدء تشغيل البوت / Start the bot' },
        { command: 'help',          description: '📋 عرض قائمة الأوامر / Show all commands' },
        { command: 'scan',          description: '🔍 تشغيل فحص وظائف فوري / Trigger manual job scan' },
        { command: 'profiles',      description: '👤 عرض كل الـ Profiles / View job profiles' },
        { command: 'pause',         description: '⏸ إيقاف Profile مؤقتاً / Pause a profile (e.g. /pause 0)' },
        { command: 'resume',        description: '▶️ تشغيل Profile موقوف / Resume a profile (e.g. /resume 0)' },
        { command: 'status',        description: '📊 فحص حالة النظام / Check system status' },
        { command: 'deleteaccount', description: '🗑 حذف حسابك نهائياً / Delete your account' },
      ],
    }),
  });
}

// Helper: Set bot description (auto-branding)
async function registerBotDescription(botToken: string, language: string = 'ar') {
  const isAr = language === 'ar';
  const desc = isAr
    ? `🤖 SparkJobs — بوت التوظيف الذكي بالذكاء الاصطناعي\n\nيفحص وظايفك المفضلة كل 20 دقيقة ويرسلك تنبيه فوري للمناسب منها فقط، مع تقييم AI ورسالة تواصل جاهزة.\n\nPowered by SparkGen ⚡`
    : `🤖 SparkJobs — Smart AI Job Recruiter Bot\n\nScans job boards every 20 minutes and sends instant match alerts with CV scoring and custom recruiter messages.\n\nPowered by SparkGen ⚡`;

  const url = `https://api.telegram.org/bot${botToken}/setMyDescription`;
  await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ description: desc }),
  });

  const shortDesc = isAr
    ? `بوت AI للوظائف — يفحص ويرسلك المناسب فقط ⚡ SparkGen`
    : `AI Job Bot — Scans & alerts matching opportunities ⚡ SparkGen`;

  const urlShort = `https://api.telegram.org/bot${botToken}/setMyShortDescription`;
  await fetch(urlShort, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ short_description: shortDesc }),
  });
}

// Helper: Register WebApp Menu Button for dynamic dashboard access
async function registerBotMenuButton(botToken: string, chatId: number, siteUrl: string, language: string = 'ar') {
  const isAr = language === 'ar';
  const buttonText = isAr ? 'لوحة التحكم 📊' : 'Dashboard 📊';
  const url = `https://api.telegram.org/bot${botToken}/setChatMenuButton`;
  try {
    await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id: chatId,
        menu_button: {
          type: 'web_app',
          text: buttonText,
          web_app: {
            url: siteUrl
          }
        }
      }),
    });
  } catch (e) {
    console.error('Failed to set chat menu button:', e);
  }
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const update = req.body;
  if (!update) {
    return res.status(200).send('No update body');
  }

  // Handle Callback Queries (Applied / Ignore button clicks)
  if (update.callback_query) {
    const callbackQueryId = update.callback_query.id;
    const callbackData = update.callback_query.data || '';
    const message = update.callback_query.message;

    if (!message) {
      return res.status(200).send('No message in callback query');
    }

    const chatId = message.chat.id;
    const messageId = message.message_id;
    
    // Fallback to HTML formatting tags since raw text doesn't contain anchor tags correctly.
    // However, editing telegram message requires maintaining HTML mode parse_mode.
    const originalText = message.text || '';

    // Retrieve user config from KV
    const userConfig: any = await kv.get(`user:${chatId}`);
    if (!userConfig) {
      const defaultToken = process.env.TELEGRAM_BOT_TOKEN || '';
      try {
        await fetch(`https://api.telegram.org/bot${defaultToken}/answerCallbackQuery`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ callback_query_id: callbackQueryId, text: 'User not configured' })
        });
      } catch {}
      return res.status(200).send('OK');
    }

    const { telegram_bot_token, language = 'ar' } = userConfig;

    if (callbackData.startsWith('applied:') || callbackData.startsWith('ignore:')) {
      const isApplied = callbackData.startsWith('applied:');
      const toastText = language === 'ar'
        ? (isApplied ? 'تم التحديد كـ مقدّم ✅' : 'تم التحديد كـ تجاهل ❌')
        : (isApplied ? 'Marked as Applied ✅' : 'Marked as Ignored ❌');

      try {
        // 1. Answer Callback Query
        await fetch(`https://api.telegram.org/bot${telegram_bot_token}/answerCallbackQuery`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            callback_query_id: callbackQueryId,
            text: toastText
          })
        });

        // 2. Remove inline buttons leaving text untouched
        await fetch(`https://api.telegram.org/bot${telegram_bot_token}/editMessageReplyMarkup`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            chat_id: chatId,
            message_id: messageId,
            reply_markup: { inline_keyboard: [] }
          })
        });
      } catch (e) {
        console.error('Error handling Telegram callback query:', e);
      }
    }
    return res.status(200).send('OK');
  }

  if (!update.message) {
    return res.status(200).send('No message found');
  }

  const chatId = update.message.chat.id;
  const text = (update.message.text || '').trim();
  const firstName = update.message.from?.first_name || 'هناك';

  // ─── UNCONFIGURED USER ───────────────────────────────────────────────────────
  const userConfig: any = await kv.get(`user:${chatId}`);
  if (!userConfig) {
    const botToken = process.env.TELEGRAM_BOT_TOKEN || '';
    if (text.startsWith('/start') || text.startsWith('/help')) {
      const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://sparkjobs.app';

      // Auto-register commands and branding for the bot
      await registerBotCommands(botToken);
      const userLangCode = update.message.from?.language_code || '';
      const initialLang = userLangCode.startsWith('ar') ? 'ar' : 'en';
      await registerBotDescription(botToken, initialLang);
      await registerBotMenuButton(botToken, chatId, siteUrl, initialLang);

      const welcomeMsg =
        `أهلاً <b>${firstName}</b>! مرحباً بك في <b>SparkJobs</b>\n\n` +
        `─────────────────\n` +
        `<b>ما هو SparkJobs؟</b>\n` +
        `هو مساعدك الشخصي للبحث عن وظائف بالذكاء الاصطناعي. يقوم بفحص أشهر منصات التوظيف كل 20 دقيقة، ومطابقة متطلباتها مع الـ CV والـ Cover Letter الخاصين بك بدقة، ثم يرسل لك تنبيهاً فورياً بالوظائف المتوافقة فقط.\n\n` +
        `<b>كيف أبدأ الاستخدام؟ (سهل جداً):</b>\n` +
        `1. افتح رابط الموقع أدناه.\n` +
        `2. قم برفع ملف الـ CV الخاص بك (PDF أو Word) واكتب رسالة تغطية للـ AI.\n` +
        `3. أدخل مفاتيح Gemini و Telegram الموضحة بالخطوات.\n` +
        `4. اضغط على بدء التفعيل ودع البوت يتولى الباقي!\n\n` +
        `─────────────────\n` +
        `<b>ابدأ الإعداد الآن:</b>\n` +
        `<a href="${siteUrl}">${siteUrl}</a>\n\n` +
        `بعد إكمال الإعداد، ارجع هنا واكتب /help لعرض لوحة التحكم السريعة.` +
        SPARKGEN_FOOTER;

      await sendTelegramMessage(botToken, chatId, welcomeMsg);
    }
    return res.status(200).send('User not configured');
  }

  // ─── CONFIGURED USER ─────────────────────────────────────────────────────────
  const { github_repo, github_token, telegram_bot_token, language: userLang = 'ar' } = userConfig;
  const s = WEBHOOK_STRINGS[userLang as 'ar' | 'en'] || WEBHOOK_STRINGS.ar;
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://sparkjobs.app';

  // Register commands & branding automatically every time (idempotent)
  await registerBotCommands(telegram_bot_token);
  await registerBotDescription(telegram_bot_token, userLang);
  await registerBotMenuButton(telegram_bot_token, chatId, siteUrl, userLang);

  try {

    // ── /start  /help ──────────────────────────────────────────────────────────
    if (text.startsWith('/start') || text.startsWith('/help')) {
      const helpMsg = s.helpTitle(firstName) + '\n\n' + s.helpBody(siteUrl) + SPARKGEN_FOOTER;
      await sendTelegramMessage(telegram_bot_token, chatId, helpMsg);
    }

    // ── /scan ──────────────────────────────────────────────────────────────────
    else if (text.startsWith('/scan')) {
      // Immediately acknowledge so user doesn't wait
      await sendTelegramMessage(telegram_bot_token, chatId, s.scanAck + SPARKGEN_FOOTER);

      const triggered = await triggerGithubWorkflow(github_repo, github_token, 'scan.yml');
      await sendTelegramMessage(
        telegram_bot_token, chatId,
        (triggered ? s.scanOk : s.scanFail) + SPARKGEN_FOOTER
      );
    }

    // ── /profiles ──────────────────────────────────────────────────────────────
    else if (text.startsWith('/profiles')) {
      const fileData = await getGithubFile(github_repo, 'data/config.json', github_token);
      if (!fileData) {
        await sendTelegramMessage(telegram_bot_token, chatId, s.configFail + SPARKGEN_FOOTER);
        return res.status(200).send('OK');
      }
      const config = JSON.parse(fileData.content);
      
      const globalSearch = config.global_search || {};
      const profiles = config.profiles || [];
      const jobTitles = globalSearch.job_titles || (profiles[0]?.job_titles || []);
      const yearsExp = globalSearch.years_of_experience || (profiles[0]?.years_of_experience || '');
      
      let targetCountries = config.target_countries || [];
      if (targetCountries.length === 0 && profiles[0]) {
        targetCountries = (profiles[0].countries || []).map((countryId: string) => ({
          country: countryId,
          remote_only: (profiles[0].job_types || []).includes('remote'),
          requires_visa: (profiles[0].visa_types || []).includes('sponsor_required'),
          min_match_score: profiles[0].min_match_score || 65,
          active: profiles[0].active ?? true
        }));
      }

      if (targetCountries.length === 0) {
        await sendTelegramMessage(telegram_bot_token, chatId, s.profilesEmpty + SPARKGEN_FOOTER);
        return res.status(200).send('OK');
      }

      let responseText = userLang === 'ar'
        ? `📋 <b>إعدادات البحث الحالية الخاصة بك:</b>\n\n`
        : `📋 <b>Your Active Search Preferences:</b>\n\n`;
      
      responseText += `• ${userLang === 'ar' ? 'المسميات' : 'Job Titles'}: <b>${jobTitles.join(', ')}</b>\n`;
      responseText += `• ${userLang === 'ar' ? 'الخبرة' : 'Experience'}: <b>${yearsExp}</b>\n\n`;
      
      responseText += userLang === 'ar'
        ? `🌍 <b>البلدان المستهدفة وقواعد التصفية:</b>\n\n`
        : `🌍 <b>Target Locations & Filter Rules:</b>\n\n`;

      targetCountries.forEach((tc: any, idx: number) => {
        const status = tc.active ? s.profileActive : s.profilePaused;
        const remote = tc.remote_only
          ? (userLang === 'ar' ? 'عن بعد فقط 💻' : 'Remote Only 💻')
          : (userLang === 'ar' ? 'حضوري/هجين 🏢' : 'Onsite/Hybrid 🏢');
        const visa = tc.requires_visa
          ? (userLang === 'ar' ? 'مطلوب فيزا 🛡️' : 'Requires Visa 🛡️')
          : (userLang === 'ar' ? 'لا يتطلب فيزا' : 'No Visa Needed');
          
        responseText += `<b>[${idx}] ${tc.country}</b>\n`;
        responseText += `   ├ ${userLang === 'ar' ? 'الحالة' : 'Status'}: ${status}\n`;
        responseText += `   ├ ${userLang === 'ar' ? 'العمل' : 'Work'}: ${remote}\n`;
        if (tc.country !== 'Worldwide') {
          responseText += `   ├ ${userLang === 'ar' ? 'الفيزا' : 'Visa'}: ${visa}\n`;
        }
        responseText += `   └ ${userLang === 'ar' ? 'القبول' : 'Min Match'}: ${tc.min_match_score}%\n\n`;
      });

      responseText += userLang === 'ar'
        ? `<i>لإيقاف الفحص ببلد: /pause [الرقم]\nلتشغيله: /resume [الرقم]</i>`
        : `<i>To pause a country scan: /pause [number]\nTo resume: /resume [number]</i>`;

      await sendTelegramMessage(telegram_bot_token, chatId, responseText + SPARKGEN_FOOTER);
    }

    // ── /pause  /resume ────────────────────────────────────────────────────────
    else if (text.startsWith('/pause') || text.startsWith('/resume')) {
      const isPause = text.startsWith('/pause');
      const parts = text.split(' ');
      const index = parseInt(parts[1]);
      if (isNaN(index)) {
        await sendTelegramMessage(telegram_bot_token, chatId,
          s.pauseNeedIndex(isPause ? '/pause' : '/resume') + SPARKGEN_FOOTER);
        return res.status(200).send('OK');
      }
      const fileData = await getGithubFile(github_repo, 'data/config.json', github_token);
      if (!fileData) {
        await sendTelegramMessage(telegram_bot_token, chatId, s.pauseConnFail + SPARKGEN_FOOTER);
        return res.status(200).send('OK');
      }
      const config = JSON.parse(fileData.content);
      
      let targetCountries = config.target_countries || [];
      const profiles = config.profiles || [];
      if (targetCountries.length === 0 && profiles[0]) {
        targetCountries = (profiles[0].countries || []).map((countryId: string) => ({
          country: countryId,
          remote_only: (profiles[0].job_types || []).includes('remote'),
          requires_visa: (profiles[0].visa_types || []).includes('sponsor_required'),
          min_match_score: profiles[0].min_match_score || 65,
          active: profiles[0].active ?? true
        }));
      }

      if (index < 0 || index >= targetCountries.length) {
        await sendTelegramMessage(telegram_bot_token, chatId, s.pauseOutOfRange(targetCountries.length) + SPARKGEN_FOOTER);
        return res.status(200).send('OK');
      }

      targetCountries[index].active = !isPause;
      config.target_countries = targetCountries;
      if (config.profiles) delete config.profiles;

      const success = await updateGithubFile(
        github_repo, 'data/config.json', github_token,
        JSON.stringify(config, null, 2), fileData.sha,
        `update: ${isPause ? 'pause' : 'resume'} country [${index}] via Telegram`
      );
      const action = isPause ? s.pauseActionPause : s.pauseActionResume;
      const countryName = targetCountries[index].country;
      await sendTelegramMessage(telegram_bot_token, chatId,
        (success ? s.pauseOk(action, countryName) : s.pauseFileFail) + SPARKGEN_FOOTER);
    }

    // ── /status ────────────────────────────────────────────────────────────────
    else if (text.startsWith('/status')) {
      const runsUrl = `https://api.github.com/repos/${github_repo}/actions/runs?per_page=3`;
      const response = await fetch(runsUrl, {
        headers: {
          Authorization: `Bearer ${github_token}`,
          Accept: 'application/vnd.github.v3+json',
          'User-Agent': 'SparkJobs-Webhook',
        },
      });
      const locale = userLang === 'ar' ? 'ar-EG' : 'en-GB';
      const tz = userLang === 'ar' ? 'Africa/Cairo' : 'UTC';
      let workflowStatus = s.statusNoRun;
      let lastRunInfo = '';
      if (response.ok) {
        const data = await response.json();
        const runs = data.workflow_runs || [];
        if (runs.length > 0) {
          const lastRun = runs[0];
          const runTime = new Date(lastRun.updated_at).toLocaleString(locale, { timeZone: tz });
          if (lastRun.status === 'completed' && lastRun.conclusion === 'success') {
            workflowStatus = s.statusOk;
            lastRunInfo = `• ${s.statusLastRun(runTime)}\n`;
          } else if (lastRun.status === 'in_progress') {
            workflowStatus = s.statusRunning;
            lastRunInfo = `• ${s.statusStarted(runTime)}\n`;
          } else {
            workflowStatus = s.statusFail(lastRun.conclusion || lastRun.status);
            lastRunInfo = `• ${s.statusAt(runTime)}\n`;
          }
        }
      }
      await sendTelegramMessage(telegram_bot_token, chatId,
        s.statusMsg(github_repo, workflowStatus, lastRunInfo) + SPARKGEN_FOOTER);
    }

    // ── /deleteaccount ─────────────────────────────────────────────────────────
    else if (text.startsWith('/deleteaccount')) {
      await sendTelegramMessage(telegram_bot_token, chatId, s.deleteConfirm + SPARKGEN_FOOTER);
    }

    // ── Confirm delete (plain text response to deleteaccount prompt) ───────────
    else if (text.toLowerCase() === 'yes, delete my account' || text === 'نعم، احذف حسابي') {
      await kv.del(`user:${chatId}`);
      await sendTelegramMessage(telegram_bot_token, chatId, s.deleteSuccess + SPARKGEN_FOOTER);
    }

    // ── Unknown command ────────────────────────────────────────────────────────
    else if (text.startsWith('/')) {
      await sendTelegramMessage(telegram_bot_token, chatId, s.unknownCmd + SPARKGEN_FOOTER);
    }

  } catch (error) {
    console.error('Error handling webhook update:', error);
  }

  return res.status(200).send('OK');
}
