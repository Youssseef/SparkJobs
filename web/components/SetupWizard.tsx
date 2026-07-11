import React, { useState } from 'react';
import { RotateCw, Check } from 'lucide-react';
import Step1Profile, { TargetCountryConfig } from './Step1Profile';
import CvUploadPanel from './CvUploadPanel';
import Step3Credentials from './Step3Credentials';
import Step4Deploy from './Step4Deploy';

interface SetupWizardProps {
  language: 'ar' | 'en';
  onSuccess: (repoName: string, chatId: string, token: string) => void;
  initialGithubToken?: string;
  initialRepoName?: string;
  initialChatId?: string;
}

const TRANSLATIONS = {
  ar: {
    wizardTitle: 'إعداد البوت الشخصي',
    step: 'الخطوة',
    of: 'من',
    jobTitlesLabel: 'المسميات الوظيفية المستهدفة',
    countriesLabel: 'الدول المستهدفة للبحث',
    jobTypesLabel: 'نوع العمل المطلوب',
    visaSponsorshipLabel: 'حالة رعاية التأشيرة',
    nextBtn: 'المتابعة للخطوة التالية',
    backBtn: 'الرجوع',
    deployBtn: 'بدء التفعيل والتشغيل',
    helpLink: 'من أين أحصل عليه؟',
    helpLinkPat: 'كيف أحصل عليه؟',
    jobSearchPlaceholder: 'ابحث أو اكتب مسمى وظيفي مخصص...',
    countrySearchPlaceholder: 'ابحث عن دولة للبحث بها...',
    customJobBtn: 'إضافة مسمى مخصص',
    geminiLabel: 'Google Gemini API Key (اختياري - لمطابقة الـ CV والرسائل)',
    telegramTokenLabel: 'Telegram Bot Token',
    telegramChatIdLabel: 'Telegram Chat ID (معرف شات تليجرام الخاص بك)',
    scraperApiKeyLabel: 'ScraperAPI Key (اختياري - لمنع حظر Indeed)',
    githubTokenLabel: 'GitHub Personal Access Token (PAT)',
    githubRepoLabel: 'اسم مستودع البوت الجديد',
    experienceLabel: 'سنوات الخبرة المطلوبة',
    step5Title: '🎉 اكتمل الإعداد بنجاح!',
    step5Desc: 'تم إنشاء مساعد الوظائف الخاص بك وتفعيله على خوادم GitHub. جاري تشغيل أول دورة فحص للوظائف في الخلفية الآن.',
    countdownLabel: 'الفحص الأول يبدأ خلال:',
    openTelegramBtn: 'فتح شات البوت على Telegram',
    goToDashboardBtn: 'الذهاب للوحة التحكم 📊',
    firstScanReady: 'البوت نشط ويعمل حالياً! تحقق من تليجرام.',
  },
  en: {
    wizardTitle: 'Setup Personal Bot',
    step: 'Step',
    of: 'of',
    jobTitlesLabel: 'Target Job Titles',
    countriesLabel: 'Target Countries',
    jobTypesLabel: 'Job Type Required',
    visaSponsorshipLabel: 'Visa Sponsorship Status',
    nextBtn: 'Continue to Next Step',
    backBtn: 'Back',
    deployBtn: 'Start Activation & Deploy',
    helpLink: 'How do I get this?',
    helpLinkPat: 'How do I get this?',
    jobSearchPlaceholder: 'Search or add a custom job title...',
    countrySearchPlaceholder: 'Search for target countries...',
    customJobBtn: 'Add custom title',
    geminiLabel: 'Google Gemini API Key (Optional - for CV matching & templates)',
    telegramTokenLabel: 'Telegram Bot Token',
    telegramChatIdLabel: 'Telegram Chat ID (Your Chat ID)',
    scraperApiKeyLabel: 'ScraperAPI Key (Optional - Prevents Indeed blocks)',
    githubTokenLabel: 'GitHub Personal Access Token (PAT)',
    githubRepoLabel: 'New Bot Repository Name',
    experienceLabel: 'Target Years of Experience',
    step5Title: '🎉 Setup Completed Successfully!',
    step5Desc: 'Your personal job assistant has been created and deployed to GitHub Actions. We are booting up and running the first scan cycle in the background now.',
    countdownLabel: 'First scan runs in:',
    openTelegramBtn: 'Open Bot Chat on Telegram',
    goToDashboardBtn: 'Go to Dashboard 📊',
    firstScanReady: 'Bot is active and running! Check Telegram for alerts.',
  }
};

const GUIDE_COMPONENTS = {
  ar: {
    gemini: (
      <span>
        1. اضغط على هذا الرابط المباشر: <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noreferrer" className="text-blue-400 hover:underline font-bold">إنشاء مفتاح Gemini مجاناً</a> وسجل دخولك بـ Gmail.<br />
        2. اضغط على زر <b>Create API Key</b>.<br />
        3. انسخ الرمز والزقه هنا. المفتاح مجاني بالكامل ولا يتطلب أي بطاقة بنكية.
      </span>
    ),
    bot: (
      <span>
        1. اضغط على هذا الرابط: <a href="https://t.me/botfather?start=newbot" target="_blank" rel="noreferrer" className="text-blue-400 hover:underline font-bold">فتح تليجرام BotFather</a>.<br />
        2. سيفتح معك تليجرام تلقائياً ويقوم بتهيئة إنشاء بوت جديد. اختر اسماً ومعرفاً للبوت الخاص بك.<br />
        3. انسخ رمز الـ <b>Token</b> الأحمر الناتج والزقه هنا.
      </span>
    ),
    chat: (
      <span>
        1. اضغط على هذا الرابط: <a href="https://t.me/userinfobot" target="_blank" rel="noreferrer" className="text-blue-400 hover:underline font-bold">معرفة الـ Chat ID الخاص بك</a>.<br />
        2. اضغط على زر <b>Start</b>.<br />
        3. سيرد عليك البوت بمعرف حسابك (ID) فوراً، انسخه والزقه هنا.
      </span>
    ),
    proxy: (
      <span>
        1. اذهب لموقع <a href="https://www.scraperapi.com/" target="_blank" rel="noreferrer" className="text-blue-400 hover:underline font-bold">موقع ScraperAPI الرسمي</a> وسجل حساباً مجانياً مجرد بريد إلكتروني وكلمة مرور.<br />
        2. ستجد الـ API Key الخاص بك مباشرة في لوحة التحكم، انسخه هنا (يعطيك 5000 طلب مجاني شهرياً لمنع حظر Indeed).
      </span>
    ),
    github: (
      <span>
        1. اضغط على هذا الرابط: <a href="https://github.com/settings/tokens/new?scopes=repo&description=SparkJobs%20Bot" target="_blank" rel="noreferrer" className="text-blue-400 hover:underline font-bold">إنشاء صلاحية GitHub PAT بنقرة واحدة</a> (لقد قمنا بتحديد الصلاحيات والخيارات الصحيحة لك تلقائياً!).<br />
        2. انزل مباشرة لأسفل الصفحة واضغط على زر <b>Generate token</b> الأخضر.<br />
        3. انسخ الرمز الناتج (يبدأ بـ <code>ghp_</code>) والزقه هنا.
      </span>
    )
  },
  en: {
    gemini: (
      <span>
        1. Click this direct link: <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noreferrer" className="text-blue-400 hover:underline font-bold">Create Gemini Key</a> and sign in.<br />
        2. Click the <b>Create API Key</b> button.<br />
        3. Copy the generated key and paste it here (100% free, no credit card required).
      </span>
    ),
    bot: (
      <span>
        1. Click this direct link: <a href="https://t.me/botfather?start=newbot" target="_blank" rel="noreferrer" className="text-blue-400 hover:underline font-bold">Open BotFather on Telegram</a>.<br />
        2. It will automatically trigger bot creation helper. Choose a name and username.<br />
        3. Copy the generated red <b>Token</b> string and paste it here.
      </span>
    ),
    chat: (
      <span>
        1. Click this direct link: <a href="https://t.me/userinfobot" target="_blank" rel="noreferrer" className="text-blue-400 hover:underline font-bold">Get Chat ID</a>.<br />
        2. Press <b>Start</b>.<br />
        3. Copy the ID number returned in the message and paste it here.
      </span>
    ),
    proxy: (
      <span>
        1. Go to <a href="https://www.scraperapi.com/" target="_blank" rel="noreferrer" className="text-blue-400 hover:underline font-bold">ScraperAPI Portal</a> and register a free account.<br />
        2. Copy your API Key from the dashboard (5,000 free requests per month).
      </span>
    ),
    github: (
      <span>
        1. Click this direct link: <a href="https://github.com/settings/tokens/new?scopes=repo&description=SparkJobs%20Bot" target="_blank" rel="noreferrer" className="text-blue-400 hover:underline font-bold">Create GitHub Token (One-click Scope Pre-select)</a>.<br />
        2. Scroll down and click the green <b>Generate token</b> button.<br />
        3. Copy the code (starts with <code>ghp_</code>) and paste it here.
      </span>
    )
  }
};

export default function SetupWizard({
  language,
  onSuccess,
  initialGithubToken,
  initialRepoName,
  initialChatId
}: SetupWizardProps) {
  const t = TRANSLATIONS[language];
  const [step, setStep] = useState(1);

  // Auto-load existing config from GitHub when editing
  React.useEffect(() => {
    if (initialRepoName && initialGithubToken) {
      const loadExistingConfig = async () => {
        try {
          const url = `https://api.github.com/repos/${initialRepoName}/contents/data/config.json`;
          const res = await fetch(url, {
            headers: {
              Authorization: `Bearer ${initialGithubToken}`,
              Accept: 'application/vnd.github.v3+json',
            }
          });
          if (res.ok) {
            const data = await res.json();
            const content = JSON.parse(Buffer.from(data.content, 'base64').toString('utf-8'));
            if (content) {
              if (content.gemini_api_key) setGeminiKey(content.gemini_api_key);
              if (content.telegram_bot_token) setTgToken(content.telegram_bot_token);
              if (content.scraperapi_key) setScraperApiKey(content.scraperapi_key);
              
              if (content.global_search) {
                const gs = content.global_search;
                if (gs.job_titles) setSelectedJobTitles(gs.job_titles);
                if (gs.years_of_experience) setYearsOfExperience(gs.years_of_experience);
                if (gs.exclude_keywords) setExcludeKeywords(gs.exclude_keywords.join(', '));
                if (gs.scan_frequency) setScanFrequency(gs.scan_frequency);
              }
              if (content.target_countries) {
                setTargetCountries(content.target_countries);
              } else if (content.profiles?.[0]) {
                const profile = content.profiles[0];
                if (profile.job_titles) setSelectedJobTitles(profile.job_titles);
                if (profile.years_of_experience) setYearsOfExperience(profile.years_of_experience);
                if (profile.exclude_keywords) setExcludeKeywords(profile.exclude_keywords.join(', '));
                if (profile.scan_frequency) setScanFrequency(profile.scan_frequency);
                
                const mappedCountries = (profile.countries || []).map((countryId: string) => ({
                  country: countryId,
                  remote_only: (profile.job_types || []).includes('remote'),
                  requires_visa: (profile.visa_types || []).includes('sponsor_required'),
                  min_match_score: profile.min_match_score || 65,
                  active: profile.active ?? true
                }));
                setTargetCountries(mappedCountries);
              }
            }
          }

          // Load Cover Letter from GitHub if exists
          try {
            const clUrl = `https://api.github.com/repos/${initialRepoName}/contents/data/cover_letter.txt`;
            const clRes = await fetch(clUrl, {
              headers: {
                Authorization: `Bearer ${initialGithubToken}`,
                Accept: 'application/vnd.github.v3+json',
              }
            });
            if (clRes.ok) {
              const clData = await clRes.json();
              const clText = Buffer.from(clData.content, 'base64').toString('utf-8');
              if (clText) setCoverLetterText(clText);
            }
          } catch (e) {
            console.error('Failed to load cover letter from GitHub:', e);
          }

          // Check if CV exists in repository
          try {
            const cvsUrl = `https://api.github.com/repos/${initialRepoName}/contents/data/cvs`;
            const cvsRes = await fetch(cvsUrl, {
              headers: {
                Authorization: `Bearer ${initialGithubToken}`,
                Accept: 'application/vnd.github.v3+json',
              }
            });
            if (cvsRes.ok) {
              const cvsData = await cvsRes.json();
              if (Array.isArray(cvsData) && cvsData.length > 0) {
                setCvFileName(cvsData[0].name);
              }
            }
          } catch (e) {
            console.error('Failed to check CV files from GitHub:', e);
          }

        } catch (e) {
          console.error('Failed to load config from GitHub:', e);
        }
      };
      loadExistingConfig();
    }
  }, [initialRepoName, initialGithubToken]);

  const [loading, setLoading] = useState(false);
  const [progressMsg, setProgressMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const [deployedRepo, setDeployedRepo] = useState('');
  const [deployedChatId, setDeployedChatId] = useState('');
  const [deployedToken, setDeployedToken] = useState('');
  const [botUsername, setBotUsername] = useState('');

  // Form States
  const [selectedJobTitles, setSelectedJobTitles] = useState<string[]>(['React Developer', 'Frontend Engineer']);
  const [targetCountries, setTargetCountries] = useState<TargetCountryConfig[]>([
    {
      country: 'Germany',
      remote_only: false,
      requires_visa: true,
      min_match_score: 65,
      active: true
    }
  ]);
  const [yearsOfExperience, setYearsOfExperience] = useState<string>('3-5');
  const [cvBase64, setCvBase64] = useState('');
  const [cvFileName, setCvFileName] = useState('');
  const [coverLetterText, setCoverLetterText] = useState('');
  const [geminiKey, setGeminiKey] = useState('');
  const [tgToken, setTgToken] = useState('');
  const [tgChatId, setTgChatId] = useState(initialChatId || '');
  const [scraperApiKey, setScraperApiKey] = useState('');
  const [githubToken, setGithubToken] = useState(initialGithubToken || '');
  const [githubRepo, setGithubRepo] = useState(initialRepoName ? initialRepoName.split('/')[1] : 'sparkjobs-alerts');

  // Exclusion Keywords & Scan Frequency
  const [excludeKeywords, setExcludeKeywords] = useState('');
  const [scanFrequency, setScanFrequency] = useState('20m');

  const handleDeploy = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      setProgressMsg(language === 'ar' ? '1/4: جاري إنشاء مستودع GitHub...' : '1/4: Creating GitHub repository...');
      const createRes = await fetch('/api/setup/create-repo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          github_token: githubToken,
          repo_name: githubRepo,
        }),
      });
      const createData = await createRes.json();
      if (!createRes.ok) throw new Error(createData.error || 'Failed to create repository');
      
      const fullRepoName = createData.full_name;

      setProgressMsg(language === 'ar' ? '2/4: جاري تهيئة ملفات الإعدادات والـ CV...' : '2/4: Committing configurations...');
      const configData = {
        gemini_api_key: geminiKey,
        telegram_bot_token: tgToken,
        telegram_chat_id: tgChatId,
        scraperapi_key: scraperApiKey,
        language: language,
        global_search: {
          job_titles: selectedJobTitles,
          years_of_experience: yearsOfExperience,
          exclude_keywords: excludeKeywords.split(',').map(s => s.trim()).filter(Boolean),
          cv_version: "default_cv",
          scan_frequency: scanFrequency
        },
        target_countries: targetCountries
      };

      let finalCvBase64 = cvBase64;
      let finalCvFileName = cvFileName;
      const isReconfiguring = !!initialRepoName;

      if (!finalCvBase64 && !isReconfiguring) {
        const fallbackText = `Skills: ${selectedJobTitles.join(', ')}. Target Locations: ${targetCountries.map(tc => tc.country).join(', ')}.`;
        finalCvBase64 = btoa(unescape(encodeURIComponent(fallbackText)));
        finalCvFileName = 'default_cv.txt';
      }

      const fileExt = finalCvFileName ? (finalCvFileName.split('.').pop() || 'txt') : 'txt';
      const cvFilenameOnRepo = finalCvFileName ? `default_cv.${fileExt}` : undefined;

      let clBase64 = '';
      if (coverLetterText.trim()) {
        clBase64 = btoa(unescape(encodeURIComponent(coverLetterText.trim())));
      }

      const configRes = await fetch('/api/setup/write-config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          github_token: githubToken,
          repo_name: fullRepoName,
          config_data: configData,
          cv_filename: cvFilenameOnRepo || undefined,
          cv_base64: finalCvBase64 || undefined,
          cover_letter_base64: clBase64 || undefined,
        }),
      });
      if (!configRes.ok) throw new Error('Failed to write configuration');

      setProgressMsg(language === 'ar' ? '3/4: جاري حفظ مفاتيح السرية...' : '3/4: Writing Actions secrets...');
      const secretsRes = await fetch('/api/setup/write-secrets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          github_token: githubToken,
          repo_name: fullRepoName,
          gemini_key: geminiKey,
          telegram_token: tgToken,
          telegram_chat_id: tgChatId,
          scraperapi_key: scraperApiKey,
          language: language,
        }),
      });
      if (!secretsRes.ok) throw new Error('Failed to write secrets');

      setProgressMsg(language === 'ar' ? '4/4: جاري بدء تشغيل البوت...' : '4/4: Starting Actions scan...');
      const enableRes = await fetch('/api/setup/enable-actions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          github_token: githubToken,
          repo_name: fullRepoName,
        }),
      });
      if (!enableRes.ok) throw new Error('Failed to trigger Action');

      setProgressMsg(language === 'ar' ? 'اكتمل الإعداد بنجاح!' : 'Setup completed successfully!');
      
      // Try to fetch Telegram Bot username
      let username = '';
      try {
        const getMeRes = await fetch(`https://api.telegram.org/bot${tgToken}/getMe`);
        if (getMeRes.ok) {
          const getMeData = await getMeRes.json();
          if (getMeData?.result?.username) {
            username = getMeData.result.username;
          }
        }
      } catch (e) {
        console.error('Failed to fetch bot username:', e);
      }
      
      setBotUsername(username);
      setDeployedRepo(fullRepoName);
      setDeployedChatId(tgChatId);
      setDeployedToken(githubToken);
      setStep(5);
      setLoading(false);
    } catch (err: any) {
      setErrorMsg(err.message || 'Error occurred during setup');
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-xl mx-auto rounded-2xl border border-white/[0.06] bg-[#050b18]/80 backdrop-blur-xl p-8 shadow-2xl relative" dir={language === 'ar' ? 'rtl' : 'ltr'}>
      
      {/* Background Glow - SparkGen brand Blue/Orange spotlights */}
      <div className="absolute top-0 right-1/2 translate-x-1/2 w-80 h-36 bg-gradient-to-r from-blue-500/10 via-orange-500/5 to-blue-500/5 blur-[60px] pointer-events-none -z-10" />

      {/* Steps Progress Header */}
      <div className="flex items-center justify-between mb-8 pb-4 border-b border-white/[0.04]">
        <h2 className="text-lg font-bold tracking-tight text-white">
          {t.wizardTitle}
        </h2>
        {step < 5 ? (
          <span className="text-xs text-slate-400 font-semibold bg-white/[0.03] px-2.5 py-1 rounded-full border border-white/[0.05]">
            {t.step} {step} {t.of} 4
          </span>
        ) : (
          <span className="text-xs text-emerald-400 font-semibold bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20">
            {language === 'ar' ? 'اكتمل التفعيل' : 'Complete'}
          </span>
        )}
      </div>

      {errorMsg && (
        <div className="mb-6 p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs text-start">
          {errorMsg}
        </div>
      )}

      {loading ? (
        <div className="py-16 text-center">
          <RotateCw className="h-10 w-10 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-slate-300 text-sm font-semibold">{progressMsg}</p>
        </div>
      ) : (
        <>
          {step === 1 && (
            <Step1Profile
              language={language}
              t={t}
              selectedJobTitles={selectedJobTitles}
              setSelectedJobTitles={setSelectedJobTitles}
              targetCountries={targetCountries}
              setTargetCountries={setTargetCountries}
              yearsOfExperience={yearsOfExperience}
              setYearsOfExperience={setYearsOfExperience}
              excludeKeywords={excludeKeywords}
              setExcludeKeywords={setExcludeKeywords}
              scanFrequency={scanFrequency}
              setScanFrequency={setScanFrequency}
              onNext={() => setStep(2)}
            />
          )}

          {step === 2 && (
            <CvUploadPanel
              language={language}
              cvFileName={cvFileName}
              coverLetterText={coverLetterText}
              onChangeCv={(fileName, base64) => {
                setCvFileName(fileName);
                setCvBase64(base64);
              }}
              onChangeCoverLetter={setCoverLetterText}
              onError={setErrorMsg}
              onBack={() => setStep(1)}
              onNext={() => setStep(3)}
            />
          )}

          {step === 3 && (
            <Step3Credentials
              language={language}
              t={t}
              GUIDE_COMPONENTS={GUIDE_COMPONENTS[language]}
              geminiKey={geminiKey}
              setGeminiKey={setGeminiKey}
              tgToken={tgToken}
              setTgToken={setTgToken}
              tgChatId={tgChatId}
              setTgChatId={setTgChatId}
              scraperApiKey={scraperApiKey}
              setScraperApiKey={setScraperApiKey}
              onBack={() => setStep(2)}
              onNext={() => setStep(4)}
            />
          )}

          {step === 4 && (
            <Step4Deploy
              language={language}
              t={t}
              GUIDE_COMPONENTS={GUIDE_COMPONENTS[language]}
              githubToken={githubToken}
              setGithubToken={setGithubToken}
              githubRepo={githubRepo}
              setGithubRepo={setGithubRepo}
              onBack={() => setStep(3)}
              onDeploy={handleDeploy}
            />
          )}

          {step === 5 && (
            <Step5Complete
              language={language}
              t={t}
              botUsername={botUsername}
              onGoToDashboard={() => onSuccess(deployedRepo, deployedChatId, deployedToken)}
            />
          )}
        </>
      )}
    </div>
  );
}

interface Step5CompleteProps {
  language: 'ar' | 'en';
  t: any;
  botUsername: string;
  onGoToDashboard: () => void;
}

function Step5Complete({ language, t, botUsername, onGoToDashboard }: Step5CompleteProps) {
  const [countdown, setCountdown] = useState(60);

  React.useEffect(() => {
    if (countdown <= 0) return;
    const timer = setInterval(() => {
      setCountdown(c => c - 1);
    }, 1000);
    return () => clearInterval(timer);
  }, [countdown]);

  const botUrl = botUsername ? `https://t.me/${botUsername}` : 'https://t.me';

  return (
    <div className="space-y-6 text-center py-6 font-sans">
      <div className="mx-auto h-16 w-16 bg-emerald-500/10 border border-emerald-500/20 rounded-full flex items-center justify-center text-emerald-400">
        <Check className="h-8 w-8 animate-pulse" />
      </div>

      <div className="space-y-2">
        <h3 className="text-xl font-bold text-white">{t.step5Title}</h3>
        <p className="text-xs text-slate-400 leading-relaxed max-w-sm mx-auto">{t.step5Desc}</p>
      </div>

      {/* Countdown Box */}
      <div className="p-4 rounded-xl border border-white/[0.04] bg-[#030712]/50 max-w-xs mx-auto">
        <span className="text-[10px] text-slate-500 block mb-1 uppercase font-bold tracking-wider">
          {t.countdownLabel}
        </span>
        {countdown > 0 ? (
          <span className="text-2xl font-black text-blue-400 font-mono">
            00:{countdown < 10 ? `0${countdown}` : countdown}
          </span>
        ) : (
          <span className="text-xs font-bold text-emerald-400 flex items-center justify-center gap-1">
            <Check className="h-3.5 w-3.5 animate-bounce" />
            {t.firstScanReady}
          </span>
        )}
      </div>

      {/* Actions */}
      <div className="space-y-3 pt-4">
        <a
          href={botUrl}
          target="_blank"
          rel="noreferrer"
          className="w-full h-10 rounded-md bg-gradient-to-r from-emerald-600 to-teal-600 hover:scale-[1.02] active:scale-[0.98] transition-all text-white font-bold text-xs flex items-center justify-center gap-1.5 shadow-lg shadow-emerald-500/10 font-sans"
        >
          {t.openTelegramBtn}
        </a>
        
        <button
          onClick={onGoToDashboard}
          className="w-full h-10 rounded-md border border-white/[0.08] hover:bg-white/[0.04] text-slate-300 font-semibold text-xs transition-all flex items-center justify-center gap-1 font-sans"
        >
          {t.goToDashboardBtn}
        </button>
      </div>
    </div>
  );
}
