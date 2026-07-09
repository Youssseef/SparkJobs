import React, { useState } from 'react';
import { ShieldCheck, Calendar, Server, HelpCircle, Settings } from 'lucide-react';

interface DashboardProps {
  repoName: string;
  chatId: string;
  githubToken: string;
}

export default function Dashboard({ repoName, chatId, githubToken }: DashboardProps) {
  const [activeTab, setActiveTab] = useState('status');

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
          حالة النظام
        </button>
        <button
          onClick={() => setActiveTab('profiles')}
          className={`w-full h-10 px-4 rounded-md text-sm font-medium flex items-center gap-2 transition-all ${
            activeTab === 'profiles' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' : 'text-slate-400 hover:text-white hover:bg-white/[0.04]'
          }`}
        >
          <Settings className="h-4 w-4" />
          إدارة الوظائف
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
                <ShieldCheck className="h-5 w-5 text-emerald-400" />
                البوت يعمل بنجاح 
              </h3>
              <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                🟢 متصل ونشط
              </span>
            </div>

            {/* Health Matrix */}
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-xl border border-white/[0.04] bg-[#030712]/50">
                <span className="text-slate-400 text-xs block mb-1">Indeed / Google Jobs</span>
                <span className="text-white text-sm font-semibold flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                  مستقر (عبر ScraperAPI)
                </span>
              </div>
              <div className="p-4 rounded-xl border border-white/[0.04] bg-[#030712]/50">
                <span className="text-slate-400 text-xs block mb-1">Telegram Bot API</span>
                <span className="text-white text-sm font-semibold flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-emerald-500" />
                  مستقر ومتصل
                </span>
              </div>
              <div className="p-4 rounded-xl border border-white/[0.04] bg-[#030712]/50">
                <span className="text-slate-400 text-xs block mb-1">مستودع GitHub الخاص</span>
                <span className="text-white text-sm font-semibold truncate">
                  {repoName}
                </span>
              </div>
              <div className="p-4 rounded-xl border border-white/[0.04] bg-[#030712]/50">
                <span className="text-slate-400 text-xs block mb-1">تاريخ آخر دورة فحص</span>
                <span className="text-white text-sm font-semibold flex items-center gap-1">
                  <Calendar className="h-3.5 w-3.5 text-slate-400" />
                  منذ 5 دقائق
                </span>
              </div>
            </div>

            {/* Next Steps / Info Card */}
            <div className="p-5 rounded-2xl bg-blue-500/5 border border-blue-500/10 space-y-3">
              <h4 className="text-sm font-semibold text-white flex items-center gap-1.5">
                <HelpCircle className="h-4 w-4 text-blue-400" />
                كيف تتابع الوظائف الآن؟
              </h4>
              <p className="text-slate-400 text-xs leading-relaxed">
                البوت يقوم بمسح الوظائف تلقائياً كل 20 دقيقة في الخلفية. عندما يجد أي وظيفة متوافقة مع الـ CV الخاص بك بنسبة 65% فما فوق، سيرسل لك إشعاراً فورياً على تليجرام. يمكنك تعديل الإعدادات والملفات الوظيفية في أي وقت بكتابة الأوامر مباشرة في شات البوت.
              </p>
            </div>
          </div>
        )}

        {activeTab === 'profiles' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-white/[0.04]">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Settings className="h-5 w-5 text-blue-400" />
                الملفات الوظيفية النشطة
              </h3>
            </div>

            {/* Profile Row */}
            <div className="p-5 rounded-2xl border border-white/[0.04] bg-[#030712]/50 flex items-center justify-between">
              <div>
                <h4 className="text-white text-sm font-bold flex items-center gap-2">
                  Default Profile
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">
                    الأساسي
                  </span>
                </h4>
                <p className="text-slate-400 text-xs mt-1">تنبيهات فورية مرسلة لـ Telegram Chat: <code>{chatId}</code></p>
              </div>
              <div className="flex items-center gap-2">
                <a
                  href={`https://github.com/${repoName}`}
                  target="_blank"
                  rel="noreferrer"
                  className="h-9 px-4 rounded-md border border-white/[0.08] hover:bg-white/[0.04] text-xs font-semibold text-slate-300 transition-all flex items-center justify-center"
                >
                  فتح المستودع
                </a>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
