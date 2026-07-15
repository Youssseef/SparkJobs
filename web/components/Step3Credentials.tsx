import React, { useState } from 'react';
import { HelpCircle, RotateCw } from 'lucide-react';

interface Step3CredentialsProps {
  language: 'ar' | 'en';
  t: any;
  GUIDE_COMPONENTS: any;
  geminiKey: string;
  setGeminiKey: (key: string) => void;
  tgToken: string;
  setTgToken: (token: string) => void;
  tgChatId: string;
  setTgChatId: (chatId: string) => void;
  scraperApiKey: string;
  setScraperApiKey: (apiKey: string) => void;
  onBack: () => void;
  onNext: () => void;
}

export default function Step3Credentials({
  language,
  t,
  GUIDE_COMPONENTS,
  geminiKey,
  setGeminiKey,
  tgToken,
  setTgToken,
  tgChatId,
  setTgChatId,
  scraperApiKey,
  setScraperApiKey,
  onBack,
  onNext
}: Step3CredentialsProps) {
  const [activeHelp, setActiveHelp] = useState<string | null>(null);

  // Telegram Tester States
  const [testLoading, setTestLoading] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; msg: string } | null>(null);

  // Gemini Tester States
  const [geminiTestLoading, setGeminiTestLoading] = useState(false);
  const [geminiTestResult, setGeminiTestResult] = useState<{ success: boolean; msg: string } | null>(null);

  const hasCredentials = tgToken.trim() !== '' && tgChatId.trim() !== '';

  return (
    <div className="space-y-5 text-start">
      
      {/* Gemini Key */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-slate-300 text-xs font-bold">{t.geminiLabel}</label>
          <button 
            onClick={() => setActiveHelp(activeHelp === 'gemini' ? null : 'gemini')}
            className="text-blue-400 text-[10px] font-semibold flex items-center gap-1 hover:underline"
          >
            <HelpCircle className="h-3 w-3" />
            {t.helpLink}
          </button>
        </div>
        {activeHelp === 'gemini' && (
          <div className="p-3 mb-2 rounded bg-white/[0.03] border border-white/[0.05] text-[11px] text-slate-400 leading-relaxed">
            {GUIDE_COMPONENTS.gemini}
          </div>
        )}
        <input
          type="password"
          value={geminiKey}
          onChange={(e) => setGeminiKey(e.target.value)}
          placeholder="AIStudio key..."
          className="w-full h-10 px-4 rounded-md border border-white/[0.08] bg-[#030712] text-sm text-slate-100 placeholder-slate-600 focus:ring-1 focus:ring-blue-500 outline-none"
        />
        <div className="pt-2">
          <button
            type="button"
            onClick={async () => {
              if (!geminiKey) return;
              setGeminiTestLoading(true);
              setGeminiTestResult(null);
              try {
                let res = await fetch('/api/setup/test-gemini', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ gemini_key: geminiKey })
                });

                let isSuccess = false;
                let errorMsg = '';

                const contentType = res.headers.get('content-type') || '';
                if (res.ok && contentType.includes('application/json')) {
                  const data = await res.json();
                  isSuccess = data.success;
                  errorMsg = data.error;
                } else {
                  // Fallback: Perform direct browser-side validation to Google's Gemini API (useful in local dev without Vercel CLI)
                  const directUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${geminiKey}`;
                  try {
                    const directRes = await fetch(directUrl, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        contents: [{ parts: [{ text: 'ping' }] }]
                      })
                    });
                    if (directRes.ok) {
                      isSuccess = true;
                    } else {
                      const directData = await directRes.json().catch(() => ({}));
                      errorMsg = directData.error?.message || (language === 'ar' ? 'مفتاح غير صالح. تأكد من نسخه بشكل صحيح.' : 'Invalid key. Make sure you copied it correctly.');
                    }
                  } catch (directErr) {
                    errorMsg = language === 'ar'
                      ? 'فشل الاتصال بخادم Gemini. تحقق من جودة اتصالك بالإنترنت.'
                      : 'Failed to reach Gemini API. Please check your internet connection.';
                  }
                }

                if (isSuccess) {
                  setGeminiTestResult({ success: true, msg: language === 'ar' ? 'مفتاح Gemini صالح ومؤكد!' : 'Gemini Key is valid!' });
                } else {
                  setGeminiTestResult({ success: false, msg: errorMsg || (language === 'ar' ? 'مفتاح غير صالح. تأكد من نسخه بشكل صحيح.' : 'Invalid key. Make sure you copied it correctly.') });
                }
              } catch (e: any) {
                setGeminiTestResult({
                  success: false,
                  msg: language === 'ar'
                    ? 'خطأ في الشبكة. تأكد من اتصالك بالإنترنت وإعادة المحاولة.'
                    : 'Network error. Check your connection and try again.'
                });
              } finally {
                setGeminiTestLoading(false);
              }
            }}
            disabled={geminiTestLoading || !geminiKey}
            className="w-full h-9 rounded-md border border-blue-500/30 bg-blue-500/10 hover:bg-blue-500/20 text-xs font-semibold text-blue-400 transition-all flex items-center justify-center gap-1.5 disabled:opacity-40 disabled:hover:bg-blue-500/10 disabled:cursor-not-allowed"
          >
            {geminiTestLoading ? (
              <>
                <RotateCw className="h-3 w-3 animate-spin" />
                {language === 'ar' ? 'جاري فحص المفتاح...' : 'Testing Gemini Key...'}
              </>
            ) : (
              <>
                {language === 'ar' ? 'فحص مفتاح Gemini' : 'Test Gemini Connection'}
              </>
            )}
          </button>
          {geminiTestResult && (
            <div className={`mt-2 p-2.5 rounded text-xs border ${
              geminiTestResult.success 
                ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' 
                : 'bg-rose-500/10 border-rose-500/20 text-rose-400'
            }`}>
              {geminiTestResult.msg}
            </div>
          )}
        </div>
      </div>

      {/* Telegram Bot Token */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-slate-300 text-xs font-bold">{t.telegramTokenLabel}</label>
          <button 
            onClick={() => setActiveHelp(activeHelp === 'bot' ? null : 'bot')}
            className="text-blue-400 text-[10px] font-semibold flex items-center gap-1 hover:underline"
          >
            <HelpCircle className="h-3 w-3" />
            {t.helpLink}
          </button>
        </div>
        {activeHelp === 'bot' && (
          <div className="p-3 mb-2 rounded bg-white/[0.03] border border-white/[0.05] text-[11px] text-slate-400 leading-relaxed">
            {GUIDE_COMPONENTS.bot}
          </div>
        )}
        <input
          type="password"
          value={tgToken}
          onChange={(e) => setTgToken(e.target.value)}
          placeholder="123456:ABC-DEF..."
          className="w-full h-10 px-4 rounded-md border border-white/[0.08] bg-[#030712] text-sm text-slate-100 placeholder-slate-600 focus:ring-1 focus:ring-blue-500 outline-none"
        />
      </div>

      {/* Telegram Chat ID */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-slate-300 text-xs font-bold">{t.telegramChatIdLabel}</label>
          <button 
            onClick={() => setActiveHelp(activeHelp === 'chat' ? null : 'chat')}
            className="text-blue-400 text-[10px] font-semibold flex items-center gap-1 hover:underline"
          >
            <HelpCircle className="h-3 w-3" />
            {t.helpLink}
          </button>
        </div>
        {activeHelp === 'chat' && (
          <div className="p-3 mb-2 rounded bg-white/[0.03] border border-white/[0.05] text-[11px] text-slate-400 leading-relaxed">
            {GUIDE_COMPONENTS.chat}
          </div>
        )}
        <input
          type="text"
          value={tgChatId}
          onChange={(e) => setTgChatId(e.target.value)}
          placeholder="987654321"
          className="w-full h-10 px-4 rounded-md border border-white/[0.08] bg-[#030712] text-sm text-slate-100 placeholder-slate-600 focus:ring-1 focus:ring-blue-500 outline-none"
        />

        {/* Telegram Connection Tester Button */}
        <div className="pt-2">
          <button
            type="button"
            onClick={async () => {
              if (!tgToken || !tgChatId) return;
              setTestLoading(true);
              setTestResult(null);
              try {
                const res = await fetch('/api/test-alert', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({
                    bot_token: tgToken.trim(),
                    chat_id: tgChatId.trim(),
                    language
                  })
                });
                if (res.ok) {
                  setTestResult({ success: true, msg: language === 'ar' ? 'تم إرسال رسالة تجريبية بنجاح! تفقد تطبيق تليجرام.' : 'Test message sent successfully! Check Telegram.' });
                } else {
                  const data = await res.json().catch(() => ({}));
                  const rawDesc = data.error || '';
                  let friendlyError = '';
                  
                  if (res.status === 401 || rawDesc.toLowerCase().includes('unauthorized')) {
                    friendlyError = language === 'ar'
                      ? 'الـ Bot Token غير صحيح. تأكد من نسخه بدقة من BotFather.'
                      : 'The Bot Token is invalid. Make sure to copy it correctly from BotFather.';
                  } else if (rawDesc.toLowerCase().includes('chat not found')) {
                    friendlyError = language === 'ar'
                      ? 'لم يتم العثور على الـ Chat ID. تأكد من إدخال الرقم الصحيح وإرسال رسالة /start للبوت أولاً.'
                      : 'Chat ID not found. Ensure the ID is correct and you have started the bot with /start first.';
                  } else if (rawDesc.toLowerCase().includes('blocked')) {
                    friendlyError = language === 'ar'
                      ? 'البوت محظور من قبلك. يرجى إلغاء حظر البوت على تليجرام والمحاولة مجدداً.'
                      : 'The bot is blocked. Please unblock the bot on Telegram and try again.';
                  } else {
                    friendlyError = rawDesc || (language === 'ar' ? 'فشل إرسال رسالة الاختبار. تحقق من صحة البيانات.' : 'Failed to send test message. Check your credentials.');
                  }
                  
                  setTestResult({ success: false, msg: friendlyError });
                }
              } catch (e: any) {
                setTestResult({
                  success: false,
                  msg: language === 'ar'
                    ? 'خطأ في الشبكة. تعذّر الاتصال بخوادم تليجرام.'
                    : 'Network error. Could not connect to Telegram servers.'
                });
              } finally {
                setTestLoading(false);
              }
            }}
            disabled={testLoading || !tgToken || !tgChatId}
            className="w-full h-9 rounded-md border border-blue-500/30 bg-blue-500/10 hover:bg-blue-500/20 text-xs font-semibold text-blue-400 transition-all flex items-center justify-center gap-1.5 disabled:opacity-40 disabled:hover:bg-blue-500/10 disabled:cursor-not-allowed"
          >
            {testLoading ? (
              <>
                <RotateCw className="h-3 w-3 animate-spin" />
                {language === 'ar' ? 'جاري فحص الاتصال...' : 'Testing Connection...'}
              </>
            ) : (
              <>
                {language === 'ar' ? 'إجراء فحص اتصال تليجرام' : 'Test Telegram Connection'}
              </>
            )}
          </button>
          {testResult && (
            <div className={`mt-2 p-2.5 rounded text-xs border ${
              testResult.success 
                ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' 
                : 'bg-rose-500/10 border-rose-500/20 text-rose-400'
            }`}>
              {testResult.msg}
            </div>
          )}
        </div>
      </div>

      {/* ScraperAPI Key */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-slate-300 text-xs font-bold">{t.scraperApiKeyLabel}</label>
          <button 
            onClick={() => setActiveHelp(activeHelp === 'proxy' ? null : 'proxy')}
            className="text-blue-400 text-[10px] font-semibold flex items-center gap-1 hover:underline"
          >
            <HelpCircle className="h-3 w-3" />
            {t.helpLink}
          </button>
        </div>
        {activeHelp === 'proxy' && (
          <div className="p-3 mb-2 rounded bg-white/[0.03] border border-white/[0.05] text-[11px] text-slate-400 leading-relaxed">
            {GUIDE_COMPONENTS.proxy}
          </div>
        )}
        <input
          type="password"
          value={scraperApiKey}
          onChange={(e) => setScraperApiKey(e.target.value)}
          className="w-full h-10 px-4 rounded-md border border-white/[0.08] bg-[#030712] text-sm text-slate-100 placeholder-slate-600 focus:ring-1 focus:ring-blue-500 outline-none"
        />
        <p className="mt-1.5 text-[10px] text-slate-500 leading-relaxed font-sans">
          {language === 'ar' 
            ? 'مطلوب للبحث في Indeed. بدونه، سيتم فحص وظائف Google فقط.' 
            : 'Required to scan Indeed. Without this, only Google Jobs will be queried.'}
        </p>
      </div>

      <div className="flex gap-4 mt-8">
        <button
          onClick={onBack}
          className="flex-1 h-10 rounded-md border border-white/[0.08] hover:bg-white/[0.04] text-slate-300 text-sm transition-all"
        >
          {t.backBtn}
        </button>
        <button
          onClick={onNext}
          disabled={!hasCredentials}
          className="flex-1 h-10 rounded-md bg-blue-600 hover:bg-blue-700 hover:scale-[1.02] active:scale-[0.98] transition-all text-white font-semibold text-sm flex items-center justify-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
        >
          {t.nextBtn}
        </button>
      </div>

    </div>
  );
}
