import React, { useState } from 'react';
import { Sparkles, HelpCircle, ArrowRight, RotateCw, ChevronDown, Check, X, Search, Plus } from 'lucide-react';

interface SetupWizardProps {
  language: 'ar' | 'en';
  onSuccess: (repoName: string, chatId: string, token: string) => void;
}

const COMMON_JOB_TITLES = [
  'React Developer',
  'Frontend Engineer',
  'Backend Engineer',
  'Fullstack Developer',
  'UI/UX Designer',
  'Product Manager',
  'Mobile App Developer',
  'iOS Developer',
  'Android Developer',
  'Flutter Developer',
  'React Native Developer',
  'Game Developer',
  'Embedded Systems Engineer',
  'DevOps Engineer',
  'Cloud Architect',
  'Cybersecurity Engineer',
  'QA Engineer',
  'Test Automation Engineer',
  'Data Scientist',
  'Machine Learning Engineer',
  'Data Analyst',
  'Data Engineer',
  'AI Research Scientist',
  'UI/UX Designer',
  'Product Designer',
  'Graphic Designer',
  'Motion Designer',
  '3D Artist',
  'Product Manager',
  'Project Manager',
  'Scrum Master',
  'Business Analyst',
  'Digital Marketing Specialist',
  'Content Writer / Copywriter',
  'SEO Specialist',
  'Social Media Manager',
  'Growth Hacker',
  'Business Development Representative (BDR)',
  'Sales Manager',
  'Customer Success Manager',
  'Technical Support Specialist',
  'HR Manager / Recruiter',
  'Operations Manager',
  'Financial Analyst',
];

const COUNTRIES_LIST = {
  ar: [
    { id: 'Worldwide', name: 'عالمي / ريموت (Worldwide)' },
    { id: 'Egypt', name: 'مصر (Egypt)' },
    { id: 'Saudi Arabia', name: 'السعودية (KSA)' },
    { id: 'United Arab Emirates', name: 'الإمارات (UAE)' },
    { id: 'Qatar', name: 'قطر (Qatar)' },
    { id: 'Kuwait', name: 'الكويت (Kuwait)' },
    { id: 'Oman', name: 'عُمان (Oman)' },
    { id: 'Bahrain', name: 'البحرين (Bahrain)' },
    { id: 'Jordan', name: 'الأردن (Jordan)' },
    { id: 'Germany', name: 'ألمانيا (Germany)' },
    { id: 'United Kingdom', name: 'المملكة المتحدة (UK)' },
    { id: 'United States', name: 'الولايات المتحدة (USA)' },
    { id: 'Canada', name: 'كندا (Canada)' },
    { id: 'Netherlands', name: 'هولندا (Netherlands)' },
    { id: 'France', name: 'فرنسا (France)' },
    { id: 'Sweden', name: 'السويد (Sweden)' },
    { id: 'Switzerland', name: 'سويسرا (Switzerland)' },
    { id: 'Australia', name: 'أستراليا (Australia)' },
  ],
  en: [
    { id: 'Worldwide', name: 'Worldwide / Remote' },
    { id: 'Egypt', name: 'Egypt' },
    { id: 'Saudi Arabia', name: 'Saudi Arabia (KSA)' },
    { id: 'United Arab Emirates', name: 'United Arab Emirates (UAE)' },
    { id: 'Qatar', name: 'Qatar' },
    { id: 'Kuwait', name: 'Kuwait' },
    { id: 'Oman', name: 'Oman' },
    { id: 'Bahrain', name: 'Bahrain' },
    { id: 'Jordan', name: 'Jordan' },
    { id: 'Germany', name: 'Germany' },
    { id: 'United Kingdom', name: 'United Kingdom (UK)' },
    { id: 'United States', name: 'United States (USA)' },
    { id: 'Canada', name: 'Canada' },
    { id: 'Netherlands', name: 'Netherlands' },
    { id: 'France', name: 'France' },
    { id: 'Sweden', name: 'Sweden' },
    { id: 'Switzerland', name: 'Switzerland' },
    { id: 'Australia', name: 'Australia' },
  ]
};

const JOB_TYPES = {
  ar: [
    { id: 'remote', name: 'عن بعد' },
    { id: 'hybrid', name: 'هجين' },
    { id: 'onsite', name: 'من موقع العمل' },
  ],
  en: [
    { id: 'remote', name: 'Remote' },
    { id: 'hybrid', name: 'Hybrid' },
    { id: 'onsite', name: 'On-site' },
  ]
};

const VISA_TYPES = {
  ar: [
    { id: 'sponsor_required', name: 'مطلوب رعاية تأشيرة' },
    { id: 'no_sponsor', name: 'لا يتطلب رعاية تأشيرة' },
    { id: 'relocation_needed', name: 'مساعدة انتقال مطلوبة' },
  ],
  en: [
    { id: 'sponsor_required', name: 'Sponsorship Required' },
    { id: 'no_sponsor', name: 'No Sponsorship Needed' },
    { id: 'relocation_needed', name: 'Relocation Assistance' },
  ]
};

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
    deployBtn: 'بدء التفعيل والتشغيل 🚀',
    helpLink: 'من أين أحصل عليه؟',
    helpLinkPat: 'كيف أحصل عليه؟',
    jobSearchPlaceholder: 'ابحث أو اكتب مسمى وظيفي مخصص...',
    countrySearchPlaceholder: 'ابحث عن دولة للبحث بها...',
    customJobBtn: 'إضافة مسمى مخصص',
    geminiLabel: 'Google Gemini API Key (مجاني)',
    telegramTokenLabel: 'Telegram Bot Token',
    telegramChatIdLabel: 'Telegram Chat ID (معرف شات تليجرام الخاص بك)',
    scraperApiKeyLabel: 'ScraperAPI Key (اختياري - لمنع حظر Indeed)',
    githubTokenLabel: 'GitHub Personal Access Token (PAT)',
    githubRepoLabel: 'اسم مستودع البوت الجديد',
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
    deployBtn: 'Start Activation & Deploy 🚀',
    helpLink: 'How do I get this?',
    helpLinkPat: 'How do I get this?',
    jobSearchPlaceholder: 'Search or add a custom job title...',
    countrySearchPlaceholder: 'Search for target countries...',
    customJobBtn: 'Add custom title',
    geminiLabel: 'Google Gemini API Key (Free)',
    telegramTokenLabel: 'Telegram Bot Token',
    telegramChatIdLabel: 'Telegram Chat ID (Your Chat ID)',
    scraperApiKeyLabel: 'ScraperAPI Key (Optional - Prevents Indeed blocks)',
    githubTokenLabel: 'GitHub Personal Access Token (PAT)',
    githubRepoLabel: 'New Bot Repository Name',
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

export default function SetupWizard({ language, onSuccess }: SetupWizardProps) {
  const t = TRANSLATIONS[language];
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [progressMsg, setProgressMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  // Form States
  const [selectedJobTitles, setSelectedJobTitles] = useState<string[]>(['React Developer', 'Frontend Engineer']);
  const [selectedCountries, setSelectedCountries] = useState<string[]>(['Germany']);
  const [selectedJobTypes, setSelectedJobTypes] = useState<string[]>(['remote']);
  const [selectedVisaTypes, setSelectedVisaTypes] = useState<string[]>(['sponsor_required']);
  const [geminiKey, setGeminiKey] = useState('');
  const [tgToken, setTgToken] = useState('');
  const [tgChatId, setTgChatId] = useState('');
  const [scraperApiKey, setScraperApiKey] = useState('');
  const [githubToken, setGithubToken] = useState('');
  const [githubRepo, setGithubRepo] = useState('sparkjobs-alerts');

  // UI Dropdown States
  const [jobDropdownOpen, setJobDropdownOpen] = useState(false);
  const [jobSearch, setJobSearch] = useState('');
  const [countryDropdownOpen, setCountryDropdownOpen] = useState(false);
  const [countrySearch, setCountrySearch] = useState('');
  const [jobTypeDropdownOpen, setJobTypeDropdownOpen] = useState(false);
  const [visaDropdownOpen, setVisaDropdownOpen] = useState(false);
  const [activeHelp, setActiveHelp] = useState<string | null>(null);

  // Filter Functions
  const filteredJobTitles = COMMON_JOB_TITLES.filter(title => 
    title.toLowerCase().includes(jobSearch.toLowerCase()) && !selectedJobTitles.includes(title)
  );

  const countries = COUNTRIES_LIST[language];
  const filteredCountries = countries.filter(c => 
    c.name.toLowerCase().includes(countrySearch.toLowerCase()) || 
    c.id.toLowerCase().includes(countrySearch.toLowerCase())
  );

  const toggleCountry = (id: string) => {
    if (selectedCountries.includes(id)) {
      setSelectedCountries(selectedCountries.filter(c => c !== id));
    } else {
      setSelectedCountries([...selectedCountries, id]);
    }
  };

  const toggleJobType = (id: string) => {
    if (selectedJobTypes.includes(id)) {
      setSelectedJobTypes(selectedJobTypes.filter(t => t !== id));
    } else {
      setSelectedJobTypes([...selectedJobTypes, id]);
    }
  };

  const toggleVisaType = (id: string) => {
    if (selectedVisaTypes.includes(id)) {
      setSelectedVisaTypes(selectedVisaTypes.filter(v => v !== id));
    } else {
      setSelectedVisaTypes([...selectedVisaTypes, id]);
    }
  };

  const handleAddCustomJob = () => {
    const trimmed = jobSearch.trim();
    if (trimmed && !selectedJobTitles.includes(trimmed)) {
      setSelectedJobTitles([...selectedJobTitles, trimmed]);
      setJobSearch('');
    }
  };

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
        profiles: [
          {
            name: "Default Profile",
            job_titles: selectedJobTitles,
            countries: selectedCountries,
            job_types: selectedJobTypes,
            visa_types: selectedVisaTypes,
            min_match_score: 65,
            cv_version: "default_cv",
            active: true
          }
        ]
      };

      const cvText = `Skills: ${selectedJobTitles.join(', ')}. Locations: ${selectedCountries.join(', ')}. Types: ${selectedJobTypes.join(', ')}. Visa: ${selectedVisaTypes.join(', ')}.`;
      const cvBase64 = btoa(unescape(encodeURIComponent(cvText)));

      const configRes = await fetch('/api/setup/write-config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          github_token: githubToken,
          repo_name: fullRepoName,
          config_data: configData,
          cv_filename: 'default_cv.txt',
          cv_base64: cvBase64,
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

      setProgressMsg(language === 'ar' ? '✅ اكتمل الإعداد بنجاح!' : '✅ Setup completed successfully!');
      onSuccess(fullRepoName, tgChatId, githubToken);
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
        <span className="text-xs text-slate-400 font-semibold bg-white/[0.03] px-2.5 py-1 rounded-full border border-white/[0.05]">
          {t.step} {step} {t.of} 3
        </span>
      </div>

      {errorMsg && (
        <div className="mb-6 p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
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
            <div className="space-y-6">
              
              {/* Job Titles Search & Multi-Select */}
              <div className="relative">
                <label className="block text-slate-300 text-xs font-bold mb-2">{t.jobTitlesLabel}</label>
                <div className="flex flex-wrap gap-1.5 p-2 rounded-md border border-white/[0.08] bg-[#030712] min-h-[40px] items-center">
                  {selectedJobTitles.map(title => (
                    <span key={title} className="inline-flex items-center gap-1 bg-blue-500/10 text-blue-400 border border-blue-500/20 text-xs px-2.5 py-1 rounded">
                      {title}
                      <button type="button" onClick={() => setSelectedJobTitles(selectedJobTitles.filter(t => t !== title))}>
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  ))}
                  <button
                    type="button"
                    onClick={() => {
                      setJobDropdownOpen(!jobDropdownOpen);
                      setCountryDropdownOpen(false);
                      setJobTypeDropdownOpen(false);
                      setVisaDropdownOpen(false);
                    }}
                    className="text-slate-500 hover:text-white text-xs px-2 font-medium flex items-center gap-1 ms-auto"
                  >
                    <ChevronDown className="h-3 w-3" />
                  </button>
                </div>

                {jobDropdownOpen && (
                  <div className="absolute z-30 mt-1 w-full rounded-md border border-white/[0.08] bg-[#050b18] shadow-lg p-2 space-y-2">
                    <div className="relative">
                      <Search className="absolute right-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-500" />
                      <input
                        type="text"
                        placeholder={t.jobSearchPlaceholder}
                        value={jobSearch}
                        onChange={(e) => setJobSearch(e.target.value)}
                        className="w-full h-8 pr-9 pl-3 rounded bg-[#030712] border border-white/[0.08] text-xs text-slate-200 focus:ring-1 focus:ring-blue-500 outline-none"
                      />
                    </div>
                    <div className="max-h-36 overflow-y-auto space-y-0.5 [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:bg-white/[0.02] [&::-webkit-scrollbar-thumb]:bg-white/10 [&::-webkit-scrollbar-thumb]:rounded-full">
                      {filteredJobTitles.map(title => (
                        <button
                          key={title}
                          type="button"
                          onClick={() => {
                            setSelectedJobTitles([...selectedJobTitles, title]);
                            setJobSearch('');
                          }}
                          className="w-full h-8 px-3 rounded text-right text-xs text-slate-300 hover:bg-white/[0.04] block"
                        >
                          {title}
                        </button>
                      ))}
                      {jobSearch.trim() && !COMMON_JOB_TITLES.includes(jobSearch.trim()) && (
                        <button
                          type="button"
                          onClick={handleAddCustomJob}
                          className="w-full h-8 px-3 rounded text-right text-xs text-blue-400 hover:bg-white/[0.04] flex items-center justify-between"
                        >
                          <span>{t.customJobBtn} "{jobSearch.trim()}"</span>
                          <Plus className="h-3.5 w-3.5" />
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Searchable Multi-Select Countries */}
              <div className="relative">
                <label className="block text-slate-300 text-xs font-bold mb-2">{t.countriesLabel}</label>
                <div className="flex flex-wrap gap-1.5 p-2 rounded-md border border-white/[0.08] bg-[#030712] min-h-[40px] items-center">
                  {selectedCountries.map(id => {
                    const country = countries.find(c => c.id === id);
                    return (
                      <span key={id} className="inline-flex items-center gap-1 bg-blue-500/10 text-blue-400 border border-blue-500/20 text-xs px-2.5 py-1 rounded">
                        {country ? country.name.split(' ')[0] : id}
                        <button type="button" onClick={() => setSelectedCountries(selectedCountries.filter(c => c !== id))}>
                          <X className="h-3 w-3" />
                        </button>
                      </span>
                    );
                  })}
                  <button
                    type="button"
                    onClick={() => {
                      setCountryDropdownOpen(!countryDropdownOpen);
                      setJobDropdownOpen(false);
                      setJobTypeDropdownOpen(false);
                      setVisaDropdownOpen(false);
                    }}
                    className="text-slate-500 hover:text-white text-xs px-2 font-medium flex items-center gap-1 ms-auto"
                  >
                    <ChevronDown className="h-3 w-3" />
                  </button>
                </div>

                {countryDropdownOpen && (
                  <div className="absolute z-30 mt-1 w-full rounded-md border border-white/[0.08] bg-[#050b18] shadow-lg p-2 space-y-2">
                    <div className="relative">
                      <Search className="absolute right-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-500" />
                      <input
                        type="text"
                        placeholder={t.countrySearchPlaceholder}
                        value={countrySearch}
                        onChange={(e) => setCountrySearch(e.target.value)}
                        className="w-full h-8 pr-9 pl-3 rounded bg-[#030712] border border-white/[0.08] text-xs text-slate-200 focus:ring-1 focus:ring-blue-500 outline-none"
                      />
                    </div>
                    <div className="max-h-36 overflow-y-auto space-y-0.5 [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:bg-white/[0.02] [&::-webkit-scrollbar-thumb]:bg-white/10 [&::-webkit-scrollbar-thumb]:rounded-full">
                      {filteredCountries.map((country) => (
                        <button
                          key={country.id}
                          type="button"
                          onClick={() => toggleCountry(country.id)}
                          className="w-full h-8 px-3 rounded text-right text-xs text-slate-300 hover:bg-white/[0.04] flex items-center justify-between"
                        >
                          <span>{country.name}</span>
                          {selectedCountries.includes(country.id) && <Check className="h-3.5 w-3.5 text-blue-500" />}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Multi-Select Job Type */}
              <div className="relative">
                <label className="block text-slate-300 text-xs font-bold mb-2">{t.jobTypesLabel}</label>
                <button
                  type="button"
                  onClick={() => {
                    setJobTypeDropdownOpen(!jobTypeDropdownOpen);
                    setCountryDropdownOpen(false);
                    setJobDropdownOpen(false);
                    setVisaDropdownOpen(false);
                  }}
                  className="w-full h-10 px-4 rounded-md border border-white/[0.08] bg-[#030712] text-sm text-slate-100 flex items-center justify-between focus:ring-1 focus:ring-blue-500 outline-none"
                >
                  <span className="truncate">
                    {selectedJobTypes.length > 0
                      ? selectedJobTypes.map(t => JOB_TYPES[language].find(jt => jt.id === t)?.name).join(', ')
                      : '...'}
                  </span>
                  <ChevronDown className="h-4 w-4 text-slate-400" />
                </button>

                {jobTypeDropdownOpen && (
                  <div className="absolute z-30 mt-1 w-full rounded-md border border-white/[0.08] bg-[#050b18] shadow-lg p-1 space-y-0.5">
                    {JOB_TYPES[language].map((type) => (
                      <button
                        key={type.id}
                        type="button"
                        onClick={() => toggleJobType(type.id)}
                        className="w-full h-9 px-3 rounded text-right text-xs text-slate-300 hover:bg-white/[0.04] flex items-center justify-between"
                      >
                        <span>{type.name}</span>
                        {selectedJobTypes.includes(type.id) && <Check className="h-4 w-4 text-blue-500" />}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Multi-Select Visa Sponsorship */}
              <div className="relative">
                <label className="block text-slate-300 text-xs font-bold mb-2">{t.visaSponsorshipLabel}</label>
                <button
                  type="button"
                  onClick={() => {
                    setVisaDropdownOpen(!visaDropdownOpen);
                    setJobTypeDropdownOpen(false);
                    setCountryDropdownOpen(false);
                    setJobDropdownOpen(false);
                  }}
                  className="w-full h-10 px-4 rounded-md border border-white/[0.08] bg-[#030712] text-sm text-slate-100 flex items-center justify-between focus:ring-1 focus:ring-blue-500 outline-none"
                >
                  <span className="truncate">
                    {selectedVisaTypes.length > 0
                      ? selectedVisaTypes.map(v => VISA_TYPES[language].find(vt => vt.id === v)?.name).join(', ')
                      : '...'}
                  </span>
                  <ChevronDown className="h-4 w-4 text-slate-400" />
                </button>

                {visaDropdownOpen && (
                  <div className="absolute z-30 mt-1 w-full rounded-md border border-white/[0.08] bg-[#050b18] shadow-lg p-1 space-y-0.5">
                    {VISA_TYPES[language].map((type) => (
                      <button
                        key={type.id}
                        type="button"
                        onClick={() => toggleVisaType(type.id)}
                        className="w-full h-9 px-3 rounded text-right text-xs text-slate-300 hover:bg-white/[0.04] flex items-center justify-between"
                      >
                        <span>{type.name}</span>
                        {selectedVisaTypes.includes(type.id) && <Check className="h-4 w-4 text-blue-500" />}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <button
                onClick={() => {
                  setStep(2);
                  setCountryDropdownOpen(false);
                  setJobTypeDropdownOpen(false);
                  setJobDropdownOpen(false);
                  setVisaDropdownOpen(false);
                }}
                className="w-full h-10 mt-8 rounded-md bg-blue-600 hover:bg-blue-700 hover:scale-[1.02] active:scale-[0.98] transition-all text-white font-semibold text-sm flex items-center justify-center gap-2"
              >
                {t.nextBtn}
                <ArrowRight className={`h-4 w-4 ${language === 'ar' ? 'rotate-180' : ''}`} />
              </button>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-5">
              
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
                    {GUIDE_COMPONENTS[language].gemini}
                  </div>
                )}
                <input
                  type="password"
                  value={geminiKey}
                  onChange={(e) => setGeminiKey(e.target.value)}
                  placeholder="AIStudio key..."
                  className="w-full h-10 px-4 rounded-md border border-white/[0.08] bg-[#030712] text-sm text-slate-100 placeholder-slate-600 focus:ring-1 focus:ring-blue-500 outline-none"
                />
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
                    {GUIDE_COMPONENTS[language].bot}
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
                    {GUIDE_COMPONENTS[language].chat}
                  </div>
                )}
                <input
                  type="text"
                  value={tgChatId}
                  onChange={(e) => setTgChatId(e.target.value)}
                  placeholder="987654321"
                  className="w-full h-10 px-4 rounded-md border border-white/[0.08] bg-[#030712] text-sm text-slate-100 placeholder-slate-600 focus:ring-1 focus:ring-blue-500 outline-none"
                />
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
                    {GUIDE_COMPONENTS[language].proxy}
                  </div>
                )}
                <input
                  type="password"
                  value={scraperApiKey}
                  onChange={(e) => setScraperApiKey(e.target.value)}
                  className="w-full h-10 px-4 rounded-md border border-white/[0.08] bg-[#030712] text-sm text-slate-100 placeholder-slate-600 focus:ring-1 focus:ring-blue-500 outline-none"
                />
              </div>

              <div className="flex gap-4 mt-8">
                <button
                  onClick={() => {
                    setStep(1);
                    setActiveHelp(null);
                  }}
                  className="flex-1 h-10 rounded-md border border-white/[0.08] hover:bg-white/[0.04] text-slate-300 text-sm transition-all"
                >
                  {t.backBtn}
                </button>
                <button
                  onClick={() => {
                    setStep(3);
                    setActiveHelp(null);
                  }}
                  className="flex-1 h-10 rounded-md bg-blue-600 hover:bg-blue-700 hover:scale-[1.02] active:scale-[0.98] transition-all text-white font-semibold text-sm flex items-center justify-center gap-2"
                >
                  {t.nextBtn}
                  <ArrowRight className={`h-4 w-4 ${language === 'ar' ? 'rotate-180' : ''}`} />
                </button>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-5">
              
              {/* GitHub PAT */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-slate-300 text-xs font-bold">{t.githubTokenLabel}</label>
                  <button 
                    onClick={() => setActiveHelp(activeHelp === 'github' ? null : 'github')}
                    className="text-blue-400 text-[10px] font-semibold flex items-center gap-1 hover:underline"
                  >
                    <HelpCircle className="h-3 w-3" />
                    {t.helpLinkPat}
                  </button>
                </div>
                {activeHelp === 'github' && (
                  <div className="p-3 mb-2 rounded bg-white/[0.03] border border-white/[0.05] text-[11px] text-slate-400 leading-relaxed">
                    {GUIDE_COMPONENTS[language].github}
                  </div>
                )}
                <input
                  type="password"
                  value={githubToken}
                  onChange={(e) => setGithubToken(e.target.value)}
                  placeholder="ghp_..."
                  className="w-full h-10 px-4 rounded-md border border-white/[0.08] bg-[#030712] text-sm text-slate-100 placeholder-slate-600 focus:ring-1 focus:ring-blue-500 outline-none"
                />
              </div>

              {/* Repo Name */}
              <div>
                <label className="block text-slate-300 text-xs font-bold mb-2">{t.githubRepoLabel}</label>
                <input
                  type="text"
                  value={githubRepo}
                  onChange={(e) => setGithubRepo(e.target.value)}
                  className="w-full h-10 px-4 rounded-md border border-white/[0.08] bg-[#030712] text-sm text-slate-100 placeholder-slate-600 focus:ring-1 focus:ring-blue-500 outline-none"
                />
              </div>

              <div className="flex gap-4 mt-8">
                <button
                  onClick={() => {
                    setStep(2);
                    setActiveHelp(null);
                  }}
                  className="flex-1 h-10 rounded-md border border-white/[0.08] hover:bg-white/[0.04] text-slate-300 text-sm transition-all"
                >
                  {t.backBtn}
                </button>
                <button
                  onClick={handleDeploy}
                  className="flex-1 h-10 rounded-md bg-blue-600 hover:bg-blue-700 hover:scale-[1.02] active:scale-[0.98] transition-all text-white font-semibold text-sm flex items-center justify-center gap-2"
                >
                  {t.deployBtn}
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
