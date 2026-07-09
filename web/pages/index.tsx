import React, { useState } from 'react';
import Head from 'next/head';
import { Bot, Shield, MessageSquare, Zap, Globe, ChevronRight } from 'lucide-react';
import SetupWizard from '../components/SetupWizard';
import Dashboard from '../components/Dashboard';

const PAGE_TRANSLATIONS = {
  ar: {
    metaTitle: "SparkJobs — التقديم والبحث الذكي عن الوظائف 24/7",
    metaDesc: "أداة مجانية للبحث ومطابقة الوظائف بالذكاء الاصطناعي وإرسال إشعارات فورية على تليجرام",
    heroTitlePart1: "ابحث عن وظيفتك القادمة",
    heroTitlePart2: "بالذكاء الاصطناعي 24/7",
    heroDesc: "راقب منصات التوظيف العالمية والمحلية لحظة بلحظة. يقوم البوت بمطابقة الوصف الوظيفي مع سيرتك الذاتية بدقة، وتصفية الإعلانات الوهمية، وإرسال تنبيه مخصص فوري لك على تليجرام.",
    feat1Title: "بحث متزامن 24/7",
    feat1Desc: "يراقب منصات التوظيف الدولية والمحلية بشكل مستمر.",
    feat2Title: "كاشف الوظائف الوهمية",
    feat2Desc: "يصفي ويستبعد الإعلانات القديمة والمشبوهة تلقائياً.",
    feat3Title: "مطابقة ذكية بالـ AI",
    feat3Desc: "يقيس نسبة توافق مهاراتك وخبراتك مع متطلبات الوظيفة.",
    feat4Title: "رسالة تقديم جاهزة",
    feat4Desc: "يولد رسالة تواصل احترافية مخصصة لمسؤول التوظيف.",
    breadcrumbParent: "عائلة Spark",
    breadcrumbChild: "SparkJobs",
    keyCapabilities: "القدرات الأساسية"
  },
  en: {
    metaTitle: "SparkJobs — Smart Automated Job Scan & Matching 24/7",
    metaDesc: "Free AI job matching tool sending automated Telegram alerts.",
    heroTitlePart1: "Find your next career step",
    heroTitlePart2: "with AI, 24/7",
    heroDesc: "Monitor global and local job boards concurrently. Our bot automatically matches postings with your CV, filters out fake/spam alerts, and delivers structured Telegram updates instantly.",
    feat1Title: "Continuous Scans",
    feat1Desc: "Queries multiple developer platforms and search engines automatically.",
    feat2Title: "Fake Job Filter",
    feat2Desc: "Scans description lengths, age of posts, and flags sketchy listings.",
    feat3Title: "AI Match Score",
    feat3Desc: "Provides compatibility percentage based on your actual experiences.",
    feat4Title: "Recruiter Message",
    feat4Desc: "Generates tailored LinkedIn/email reachouts for every match.",
    breadcrumbParent: "SparkFamily",
    breadcrumbChild: "SparkJobs",
    keyCapabilities: "KEY CAPABILITIES"
  }
};

export default function Home() {
  const [language, setLanguage] = useState<'ar' | 'en'>('ar');
  const [setupData, setSetupData] = useState<{
    repoName: string;
    chatId: string;
    githubToken: string;
  } | null>(null);

  const t = PAGE_TRANSLATIONS[language];

  return (
    <div className="min-h-screen bg-[#030712] text-slate-100 flex flex-col font-sans select-none relative overflow-hidden py-16" dir={language === 'ar' ? 'rtl' : 'ltr'}>
      
      {/* Background Glows matching SparkGen Brand Theme */}
      <div className="absolute inset-0 max-h-full overflow-hidden pointer-events-none z-0">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-[1400px] h-[650px] bg-[radial-gradient(circle_at_top,rgba(59,130,246,0.08)_0%,rgba(230,135,56,0.03)_40%,transparent_70%)] pointer-events-none z-0" />
        <div className="absolute top-[400px] left-[5%] w-[500px] h-[500px] bg-blue-600/[0.01] rounded-full blur-[140px] pointer-events-none" />
        <div className="absolute top-[800px] right-[5%] w-[450px] h-[450px] bg-orange-600/[0.01] rounded-full blur-[120px] pointer-events-none" />
      </div>

      <Head>
        <title>{t.metaTitle}</title>
        <meta name="description" content={t.metaDesc} />
        <link rel="icon" href="/favicon.ico" />
        <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&family=Outfit:wght@400;500;700&display=swap" rel="stylesheet" />
      </Head>

      {/* Floating Language Switcher for Local Testing (Will be removed after merge since main site handles language) */}
      <div className="absolute top-6 right-6 z-50">
        <button
          onClick={() => setLanguage(language === 'ar' ? 'en' : 'ar')}
          className="h-8 px-3 rounded-lg border border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.06] text-xs font-semibold text-slate-300 flex items-center gap-1.5 transition-all shadow-md"
        >
          <Globe className="h-3.5 w-3.5 text-blue-400" />
          {language === 'ar' ? 'English' : 'العربية'}
        </button>
      </div>

      {/* Hero Section / Main Content Area */}
      <main className="flex-1 w-full max-w-6xl mx-auto px-6 flex flex-col justify-center relative z-10">
        
        {!setupData ? (
          <div className="w-full grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            
            {/* Left Column: Premium Pitch */}
            <div className="lg:col-span-6 space-y-6 text-start">
              
              {/* Breadcrumbs indicating open from SparkFamily */}
              <div className="flex items-center gap-1 text-[11px] font-bold text-slate-500 mb-2" dir={language === 'ar' ? 'rtl' : 'ltr'}>
                <a href="https://sparkgen.app" target="_blank" rel="noreferrer" className="hover:text-white transition-colors">
                  {t.breadcrumbParent}
                </a>
                <ChevronRight className={`h-3 w-3 text-slate-600 ${language === 'ar' ? 'rotate-180' : ''}`} />
                <span className="text-blue-400">{t.breadcrumbChild}</span>
              </div>
              
              <h1 className="text-3xl md:text-4xl font-black tracking-tight text-white leading-relaxed">
                {t.heroTitlePart1} <br />
                {t.heroTitlePart2}
              </h1>
              
              <p className="text-slate-400 text-sm md:text-base leading-relaxed max-w-md">
                {t.heroDesc}
              </p>

              {/* Divider and Key Capabilities header */}
              <div className="pt-6 border-t border-white/[0.04] max-w-lg">
                <div className="text-[11px] font-extrabold tracking-widest text-slate-500 uppercase mb-4">
                  {t.keyCapabilities}
                </div>
                
                {/* Grid of Features below the description */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-6 gap-x-4">
                  
                  <div className="flex items-start gap-4">
                    <div className="h-10 w-10 rounded-xl bg-white/[0.02] border border-white/[0.06] flex items-center justify-center shrink-0">
                      <Zap className="h-5 w-5 text-blue-400" />
                    </div>
                    <div>
                      <h4 className="text-xs sm:text-sm font-bold text-white">{t.feat1Title}</h4>
                      <p className="text-[10px] sm:text-xs text-slate-500 mt-1 leading-relaxed">{t.feat1Desc}</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-4">
                    <div className="h-10 w-10 rounded-xl bg-white/[0.02] border border-white/[0.06] flex items-center justify-center shrink-0">
                      <Shield className="h-5 w-5 text-blue-400" />
                    </div>
                    <div>
                      <h4 className="text-xs sm:text-sm font-bold text-white">{t.feat2Title}</h4>
                      <p className="text-[10px] sm:text-xs text-slate-500 mt-1 leading-relaxed">{t.feat2Desc}</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-4">
                    <div className="h-10 w-10 rounded-xl bg-white/[0.02] border border-white/[0.06] flex items-center justify-center shrink-0">
                      <Bot className="h-5 w-5 text-blue-400" />
                    </div>
                    <div>
                      <h4 className="text-xs sm:text-sm font-bold text-white">{t.feat3Title}</h4>
                      <p className="text-[10px] sm:text-xs text-slate-500 mt-1 leading-relaxed">{t.feat3Desc}</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-4">
                    <div className="h-10 w-10 rounded-xl bg-white/[0.02] border border-white/[0.06] flex items-center justify-center shrink-0">
                      <MessageSquare className="h-5 w-5 text-blue-400" />
                    </div>
                    <div>
                      <h4 className="text-xs sm:text-sm font-bold text-white">{t.feat4Title}</h4>
                      <p className="text-[10px] sm:text-xs text-slate-500 mt-1 leading-relaxed">{t.feat4Desc}</p>
                    </div>
                  </div>

                </div>
              </div>

            </div>

            {/* Right Column: Setup Wizard */}
            <div className="lg:col-span-6 w-full">
              <SetupWizard
                language={language}
                onSuccess={(repoName, chatId, githubToken) => {
                  setSetupData({ repoName, chatId, githubToken });
                }}
              />
            </div>

          </div>
        ) : (
          <Dashboard
            repoName={setupData.repoName}
            chatId={setupData.chatId}
            githubToken={setupData.githubToken}
          />
        )}
      </main>

      {/* Font Family Global Overrides */}
      <style jsx global>{`
        body {
          font-family: 'Cairo', 'Outfit', sans-serif !important;
        }
      `}</style>

    </div>
  );
}
