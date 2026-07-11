import React, { useState, useEffect } from 'react';
import { ShieldCheck, Calendar, Server, HelpCircle, Settings, Play, Pause, RotateCw, Send, Briefcase, Bell, AlertTriangle } from 'lucide-react';

interface DashboardProps {
  repoName: string;
  chatId: string;
  githubToken: string;
  language?: 'ar' | 'en';
  onReSetup: () => void;
}

const DASHBOARD_TRANSLATIONS = {
  ar: {
    statusTab: 'حالة النظام',
    profilesTab: 'إعدادات البحث',
    botRunning: 'البوت يعمل بنجاح',
    botPaused: 'البوت موقوف مؤقتاً',
    activeStatus: 'متصل ونشط',
    pausedStatus: 'موقوف',
    indeedStatusLabel: 'Indeed / Google Jobs',
    indeedStatusProxy: 'مستقر (عبر ScraperAPI)',
    indeedStatusNoProxy: 'أساسي (بدون بروكسي - تخطي Indeed)',
    telegramStatusLabel: 'Telegram Bot API',
    telegramStatusValue: 'مستقر ومتصل',
    githubRepoLabel: 'مستودع GitHub الخاص',
    lastScanLabel: 'تاريخ آخر دورة فحص',
    howToTrackTitle: 'كيف تتابع الوظائف الآن؟',
    howToTrackDesc: 'البوت يقوم بمسح الوظائف تلقائياً كل 20 دقيقة في الخلفية. عندما يجد أي وظيفة متوافقة مع الـ CV الخاص بك بالنسبة المطلوبة، سيرسل لك إشعاراً فورياً على تليجرام. يمكنك تعديل الإعدادات والملفات الوظيفية في أي وقت بكتابة الأوامر مباشرة في شات البوت أو عبر لوحة التحكم.',
    activeProfilesTitle: 'حالة إعدادات البحث',
    defaultProfile: 'البحث الموحد النشط',
    primaryBadge: 'نشط',
    telegramChatMsg: 'تنبيهات فورية مرسلة لـ Telegram Chat:',
    editBtn: 'تعديل الإعدادات والـ CV',
    openRepoBtn: 'فتح المستودع',
    pauseBtn: 'إيقاف البوت مؤقتاً',
    resumeBtn: 'تشغيل البوت',
    loadingText: 'جاري تحميل تفاصيل المستودع...',
    noScanRecorded: 'لم يتم الفحص بعد',
    statsTitle: 'إحصائيات هذا الأسبوع',
    scansRun: 'عمليات الفحص',
    jobsEvaluated: 'وظائف مقيّمة',
    alertsSent: 'تنبيهات مرسلة',
    testAlertBtn: 'إرسال تنبيه تجريبي',
    testAlertSuccess: 'تم إرسال التنبيه التجريبي! تحقق من تطبيق تيليجرام.',
    testAlertError: 'فشل إرسال التنبيه. تحقق من بيانات البوت.',
  },
  en: {
    statusTab: 'System Status',
    profilesTab: 'Search Settings',
    botRunning: 'Bot Running Successfully',
    botPaused: 'Bot is Temporarily Paused',
    activeStatus: 'Connected & Active',
    pausedStatus: 'Paused',
    indeedStatusLabel: 'Indeed / Google Jobs',
    indeedStatusProxy: 'Stable (via ScraperAPI)',
    indeedStatusNoProxy: 'Basic (No Proxy - skips Indeed)',
    telegramStatusLabel: 'Telegram Bot API',
    telegramStatusValue: 'Stable & Connected',
    githubRepoLabel: 'Private GitHub Repository',
    lastScanLabel: 'Last Scan Cycle',
    howToTrackTitle: 'How to monitor job alerts?',
    howToTrackDesc: 'The bot automatically scans job postings every 20 minutes in the background. When it identifies a job matching your CV by the configured percentage or more, it will send a real-time notification to your Telegram. You can modify settings at any time by writing commands directly to the bot or via this dashboard.',
    activeProfilesTitle: 'Search Settings & Status',
    defaultProfile: 'Unified Search Settings',
    primaryBadge: 'Active',
    telegramChatMsg: 'Real-time alerts sent to Telegram Chat:',
    editBtn: 'Update Settings & CV',
    openRepoBtn: 'Open Repository',
    pauseBtn: 'Pause Bot Alerts',
    resumeBtn: 'Resume Bot Alerts',
    loadingText: 'Loading repository configuration...',
    noScanRecorded: 'No scans run yet',
    statsTitle: 'This Week\'s Stats',
    scansRun: 'Scans Run',
    jobsEvaluated: 'Jobs Evaluated',
    alertsSent: 'Alerts Sent',
    testAlertBtn: 'Send Test Alert',
    testAlertSuccess: 'Test alert sent! Check your Telegram app.',
    testAlertError: 'Failed to send. Check your bot credentials.',
  }
};

import DashboardSettings from './DashboardSettings';

export default function Dashboard({ repoName, chatId, githubToken, language = 'ar', onReSetup }: DashboardProps) {
  const [activeTab, setActiveTab] = useState('status');
  const t = DASHBOARD_TRANSLATIONS[language];

  const [config, setConfig] = useState<any>(null);
  const [statusTracker, setStatusTracker] = useState<any>(null);
  const [cvFileName, setCvFileName] = useState('');
  const [loading, setLoading] = useState(true);
  const [pauseLoading, setPauseLoading] = useState(false);
  const [testAlertLoading, setTestAlertLoading] = useState(false);
  const [testAlertMsg, setTestAlertMsg] = useState<{ success: boolean; text: string } | null>(null);

  useEffect(() => {
    let active = true;
    const fetchRepoDetails = async () => {
      try {
        // Fetch config.json
        const configUrl = `https://api.github.com/repos/${repoName}/contents/data/config.json`;
        const configRes = await fetch(configUrl, {
          headers: {
            Authorization: `Bearer ${githubToken}`,
            Accept: 'application/vnd.github.v3+json',
            'User-Agent': 'SparkJobs-Dashboard'
          }
        });
        let configObj = null;
        if (configRes.ok) {
          const data = await configRes.json();
          configObj = JSON.parse(Buffer.from(data.content, 'base64').toString('utf-8'));
        }

        // Fetch status_tracker.json
        const trackerUrl = `https://api.github.com/repos/${repoName}/contents/bot/data/status_tracker.json`;
        const trackerRes = await fetch(trackerUrl, {
          headers: {
            Authorization: `Bearer ${githubToken}`,
            Accept: 'application/vnd.github.v3+json',
            'User-Agent': 'SparkJobs-Dashboard'
          }
        });
        let trackerObj = null;
        if (trackerRes.ok) {
          const data = await trackerRes.json();
          trackerObj = JSON.parse(Buffer.from(data.content, 'base64').toString('utf-8'));
        }

        // Fetch CV filename
        let cvName = 'default_cv.pdf';
        try {
          const cvsUrl = `https://api.github.com/repos/${repoName}/contents/data/cvs`;
          const cvsRes = await fetch(cvsUrl, {
            headers: {
              Authorization: `Bearer ${githubToken}`,
              Accept: 'application/vnd.github.v3+json',
              'User-Agent': 'SparkJobs-Dashboard'
            }
          });
          if (cvsRes.ok) {
            const cvsData = await cvsRes.json();
            if (Array.isArray(cvsData) && cvsData.length > 0) {
              cvName = cvsData[0].name;
            }
          }
        } catch (e) {
          console.error('Failed to fetch CV file list:', e);
        }

        if (active) {
          if (configObj) setConfig(configObj);
          if (trackerObj) setStatusTracker(trackerObj);
          setCvFileName(cvName);
          setLoading(false);
        }
      } catch (e) {
        console.error('Error fetching dashboard states:', e);
        if (active) setLoading(false);
      }
    };
    fetchRepoDetails();
    return () => { active = false; };
  }, [repoName, githubToken]);

  const handleTogglePause = async () => {
    if (!config || pauseLoading) return;
    setPauseLoading(true);
    const updatedConfig = {
      ...config,
      paused: !config.paused
    };

    try {
      const res = await fetch('/api/setup/write-config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          github_token: githubToken,
          repo_name: repoName,
          config_data: updatedConfig
        })
      });
      if (res.ok) {
        setConfig(updatedConfig);
      }
    } catch (e) {
      console.error('Failed to toggle bot pause state:', e);
    } finally {
      setPauseLoading(false);
    }
  };

  const formatLastScan = () => {
    if (!statusTracker?.last_scan_time) {
      return t.noScanRecorded;
    }
    try {
      const scanDate = new Date(statusTracker.last_scan_time);
      const diffMs = Date.now() - scanDate.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      if (diffMins < 1) return language === 'ar' ? 'الآن' : 'Just now';
      if (diffMins < 60) {
        return language === 'ar' 
          ? `منذ ${diffMins} دقيقة` 
          : `${diffMins} minutes ago`;
      }
      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) {
        return language === 'ar' 
          ? `منذ ${diffHours} ساعة` 
          : `${diffHours} hours ago`;
      }
      return scanDate.toLocaleDateString(language === 'ar' ? 'ar-EG' : 'en-US');
    } catch {
      return statusTracker.last_scan_time;
    }
  };

  if (loading) {
    return (
      <div className="w-full max-w-4xl mx-auto flex items-center justify-center p-12 text-slate-400 text-sm font-semibold gap-2">
        <RotateCw className="h-4 w-4 animate-spin text-blue-500" />
        {t.loadingText}
      </div>
    );
  }

  const botIsPaused = !!config?.paused;
  const hasProxy = !!config?.scraperapi_key;

  return (
    <div className="w-full max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-6 p-4">
      
      {/* Sidebar Navigation */}
      <div className="md:col-span-1 rounded-2xl border border-white/[0.06] bg-[#050b18]/80 backdrop-blur-md p-4 space-y-2 h-fit">
        <button
          onClick={() => setActiveTab('status')}
          className={`w-full h-10 px-4 rounded-md text-sm font-medium flex items-center gap-2 transition-all ${
            activeTab === 'status' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' : 'text-slate-400 hover:text-white hover:bg-white/[0.04]'
          }`}
        >
          <Server className="h-4 w-4" />
          {t.statusTab}
        </button>
        <button
          onClick={() => setActiveTab('profiles')}
          className={`w-full h-10 px-4 rounded-md text-sm font-medium flex items-center gap-2 transition-all ${
            activeTab === 'profiles' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' : 'text-slate-400 hover:text-white hover:bg-white/[0.04]'
          }`}
        >
          <Settings className="h-4 w-4" />
          {t.profilesTab}
        </button>
      </div>

      {/* Main Content Pane */}
      <div className="md:col-span-3 rounded-2xl border border-white/[0.06] bg-[#050b18]/85 backdrop-blur-xl p-8 shadow-2xl relative overflow-hidden">
        
        {/* Spot Glow */}
        <div className="absolute top-0 right-1/2 -translate-x-1/2 w-64 h-32 bg-gradient-to-r from-blue-500/10 via-orange-500/5 to-blue-500/5 blur-[50px] pointer-events-none -z-10" />

        {activeTab === 'status' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-white/[0.04]">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <ShieldCheck className={`h-5 w-5 ${botIsPaused ? 'text-amber-500' : 'text-emerald-400'}`} />
                {botIsPaused ? t.botPaused : t.botRunning}
              </h3>
              <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${
                botIsPaused 
                  ? 'bg-amber-500/10 text-amber-500 border-amber-500/20' 
                  : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
              }`}>
                {botIsPaused ? t.pausedStatus : t.activeStatus}
              </span>
            </div>

            {/* Health Matrix */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl border border-white/[0.04] bg-[#030712]/50">
                <span className="text-slate-400 text-xs block mb-1">{t.indeedStatusLabel}</span>
                <span className="text-white text-sm font-semibold flex items-center gap-1.5">
                  <span className={`h-2 w-2 rounded-full ${hasProxy ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`} />
                  {hasProxy ? t.indeedStatusProxy : t.indeedStatusNoProxy}
                </span>
              </div>
              <div className="p-4 rounded-xl border border-white/[0.04] bg-[#030712]/50">
                <span className="text-slate-400 text-xs block mb-1">{t.telegramStatusLabel}</span>
                <span className="text-white text-sm font-semibold flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-emerald-500" />
                  {t.telegramStatusValue}
                </span>
              </div>
              <div className="p-4 rounded-xl border border-white/[0.04] bg-[#030712]/50">
                <span className="text-slate-400 text-xs block mb-1">{t.githubRepoLabel}</span>
                <span className="text-white text-sm font-semibold truncate block">
                  {repoName}
                </span>
              </div>
              <div className="p-4 rounded-xl border border-white/[0.04] bg-[#030712]/50">
                <span className="text-slate-400 text-xs block mb-1">{t.lastScanLabel}</span>
                <span className="text-white text-sm font-semibold flex items-center gap-1">
                  <Calendar className="h-3.5 w-3.5 text-slate-400" />
                  {formatLastScan()}
                </span>
              </div>
            </div>

            {/* Weekly Stats Grid */}
            {statusTracker && (
              <div>
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">{t.statsTitle}</h4>
                <div className="grid grid-cols-3 gap-3">
                  <div className="p-4 rounded-xl border border-white/[0.04] bg-[#030712]/50 text-center">
                    <Server className="h-4 w-4 text-blue-400 mx-auto mb-1" />
                    <p className="text-xl font-bold text-white">{statusTracker.scans_completed_this_week ?? 0}</p>
                    <p className="text-slate-500 text-[10px] mt-0.5">{t.scansRun}</p>
                  </div>
                  <div className="p-4 rounded-xl border border-white/[0.04] bg-[#030712]/50 text-center">
                    <Briefcase className="h-4 w-4 text-purple-400 mx-auto mb-1" />
                    <p className="text-xl font-bold text-white">{statusTracker.jobs_evaluated_this_week ?? 0}</p>
                    <p className="text-slate-500 text-[10px] mt-0.5">{t.jobsEvaluated}</p>
                  </div>
                  <div className="p-4 rounded-xl border border-white/[0.04] bg-[#030712]/50 text-center">
                    <Bell className="h-4 w-4 text-emerald-400 mx-auto mb-1" />
                    <p className="text-xl font-bold text-white">{statusTracker.alerts_sent_this_week ?? 0}</p>
                    <p className="text-slate-500 text-[10px] mt-0.5">{t.alertsSent}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Test Alert Button */}
            <div className="space-y-2">
              <button
                onClick={async () => {
                  if (testAlertLoading || !config?.telegram_bot_token) return;
                  setTestAlertLoading(true);
                  setTestAlertMsg(null);
                  try {
                    const res = await fetch('/api/test-alert', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        bot_token: config.telegram_bot_token,
                        chat_id: chatId,
                        language,
                      }),
                    });
                    const contentType = res.headers.get('content-type') || '';
                    if (!contentType.includes('application/json')) {
                      setTestAlertMsg({ success: false, text: t.testAlertError });
                      return;
                    }
                    const data = await res.json();
                    setTestAlertMsg({
                      success: res.ok && data.success,
                      text: res.ok && data.success ? t.testAlertSuccess : (data.error || t.testAlertError),
                    });
                  } catch {
                    setTestAlertMsg({ success: false, text: t.testAlertError });
                  } finally {
                    setTestAlertLoading(false);
                  }
                }}
                disabled={testAlertLoading || !config?.telegram_bot_token}
                className="w-full h-10 rounded-md border border-blue-500/30 bg-blue-500/10 hover:bg-blue-500/20 text-sm font-semibold text-blue-400 transition-all flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {testAlertLoading ? <RotateCw className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                {t.testAlertBtn}
              </button>
              {testAlertMsg && (
                <div className={`p-3 rounded-lg text-xs border ${
                  testAlertMsg.success
                    ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                    : 'bg-rose-500/10 border-rose-500/20 text-rose-400'
                }`}>
                  {testAlertMsg.text}
                </div>
              )}
            </div>

            {/* Next Steps / Info Card */}
            <div className="p-5 rounded-2xl bg-blue-500/5 border border-blue-500/10 space-y-3">
              <h4 className="text-sm font-semibold text-white flex items-center gap-1.5">
                <HelpCircle className="h-4 w-4 text-blue-400" />
                {t.howToTrackTitle}
              </h4>
              <p className="text-slate-400 text-xs leading-relaxed">
                {t.howToTrackDesc}
              </p>
            </div>
          </div>
        )}

        {activeTab === 'profiles' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-white/[0.04]">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Settings className="h-5 w-5 text-blue-400" />
                {t.activeProfilesTitle}
              </h3>
            </div>

            <DashboardSettings
              config={config}
              setConfig={setConfig}
              repoName={repoName}
              githubToken={githubToken}
              language={language}
              onReSetup={onReSetup}
              chatId={chatId}
              cvFileName={cvFileName}
              setCvFileName={setCvFileName}
            />
          </div>
        )}
      </div>
    </div>
  );
}
